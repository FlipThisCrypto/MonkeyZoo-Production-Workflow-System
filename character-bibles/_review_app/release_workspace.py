"""Evidence-backed release readiness, approval, and hash manifests."""
from __future__ import annotations
import datetime as dt, hashlib, json, os, re, tempfile, zipfile
from contextlib import contextmanager
from pathlib import Path
import issue_workflow, visual_qa_workspace

class ReleaseError(ValueError):
 def __init__(self,message,status=400):super().__init__(message);self.status=status
def _now():return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def _hash(data):return hashlib.sha256(data).hexdigest()
def _workspace(folder):return folder/".release-workspace"
def _atomic(path,text):
 path.parent.mkdir(parents=True,exist_ok=True);fd,temp=tempfile.mkstemp(prefix=f".{path.name}.",suffix=".tmp",dir=path.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as s:s.write(text);s.flush();os.fsync(s.fileno())
  os.replace(temp,path)
 except Exception:
  try:os.unlink(temp)
  except OSError:pass
  raise
def _atomic_bytes(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);fd,temp=tempfile.mkstemp(prefix=f".{path.name}.",suffix=".tmp",dir=path.parent)
 try:
  with os.fdopen(fd,"wb") as s:s.write(data);s.flush();os.fsync(s.fileno())
  os.replace(temp,path)
 except Exception:
  try:os.unlink(temp)
  except OSError:pass
  raise
def _write_json(path,data):_atomic(path,json.dumps(data,indent=2,ensure_ascii=False)+"\n")
def _read_json(path,default=None):
 if not path.exists():return default
 try:return json.loads(path.read_text(encoding="utf-8"))
 except (OSError,ValueError) as exc:raise ReleaseError(f"Malformed release workspace record: {path.name}") from exc
def _stage(folder,root):
 active=issue_workflow.workflow_status(folder,root)["active_stage"]
 if active not in {"release","published"}:raise ReleaseError(f"Release workspace requires active workflow stage release or published; current stage is {active}",409)
 return active
@contextmanager
def _lock(folder):
 path=_workspace(folder)/".manifest.lock";path.parent.mkdir(parents=True,exist_ok=True)
 try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise ReleaseError("Another release operation is already in progress",409) from None
 try:os.write(fd,_now().encode());os.fsync(fd);os.close(fd);yield
 finally:
  try:os.close(fd)
  except OSError:pass
  try:path.unlink()
  except OSError:pass
def _archive(folder,root):
 """Unique archive destination: year/full-issue-folder (avoids month collisions)."""
 return root/"05_RELEASE_ARCHIVE"/folder.name[:4]/folder.name
def _legacy_archive(folder,root):
 number=folder.name.split("_Issue_")[-1] if "_Issue_" in folder.name else ""
 return root/"05_RELEASE_ARCHIVE"/folder.name[:4]/f"Issue_{number}"
def _resolve_archive(folder,root):
 """Prefer unique path; fall back to legacy year/Issue_NN if already published there."""
 primary=_archive(folder,root)
 if primary.exists(): return primary
 legacy=_legacy_archive(folder,root)
 return legacy if legacy.exists() else primary
def _valid_package(path):
 try:
  with zipfile.ZipFile(path) as archive:
   members=[item for item in archive.infolist() if not item.is_dir()]
   if not members:return False
   if archive.testzip() is not None:return False
  return True
 except (OSError,EOFError,RuntimeError,zipfile.BadZipFile,zipfile.LargeZipFile):return False
def evidence(folder,root):
 metadata=issue_workflow._json(folder/"metadata.json") or {};exports=folder/"exports";pdfs=sorted(exports.glob("*.pdf")) if exports.exists() else [];package_candidates=sorted([*exports.glob("*.zip"),*exports.glob("*.cbz")]) if exports.exists() else [];packages=[path for path in package_candidates if _valid_package(path)];invalid_packages=[path.name for path in package_candidates if path not in packages];covers=sorted((folder/"generated_art").rglob("*cover*.png")) if (folder/"generated_art").exists() else []
 qa=issue_workflow._qa_verdict(folder);qa_report=(folder/"qa_report.md").read_text(encoding="utf-8",errors="replace") if (folder/"qa_report.md").exists() else "";reported_hashes=re.findall(r"(?m)^Evidence hash:\s*([0-9a-f]{64})\s*$",qa_report);current_qa_hash=None
 try:current_qa_hash=visual_qa_workspace.evidence(folder)["evidence_hash"]
 except visual_qa_workspace.VisualQAError:pass
 required_meta=["format","name","description","attributes","data"];missing_meta=[k for k in required_meta if k not in metadata or metadata.get(k) is None or metadata.get(k)==""];serialized=json.dumps(metadata);placeholders=[]
 if "TODO" in serialized.upper():placeholders.append("metadata contains unresolved TODO placeholders")
 if metadata.get("format")!="CHIP-0015":placeholders.append("metadata format must be CHIP-0015")
 files=[folder/"metadata.json",folder/"social_posts.md",folder/"final_export_checklist.md",folder/"cover_prompt.md",folder/"qa_report.md",*covers,*pdfs,*package_candidates];entries=[]
 for path in files:
  if path.is_file():entries.append({"path":str(path.relative_to(folder)).replace("\\","/"),"size":path.stat().st_size,"sha256":_hash(path.read_bytes())})
 blockers=[]
 if qa!="passed":blockers.append(f"QA verdict is {qa}; exact PASS is required")
 elif len(reported_hashes)!=1 or not current_qa_hash or reported_hashes[0]!=current_qa_hash:blockers.append("Canonical QA evidence is missing or stale")
 if not covers:blockers.append("No final cover image found")
 if not pdfs or not any(p.stat().st_size for p in pdfs):blockers.append("Final PDF is missing or empty")
 if invalid_packages:blockers.append(f"Invalid CBZ or ZIP packages: {', '.join(invalid_packages)}")
 if not packages:blockers.append("A readable, non-empty CBZ or ZIP package is required")
 for name in ("social_posts.md","final_export_checklist.md","cover_prompt.md"):
  if not (folder/name).is_file() or not (folder/name).stat().st_size:blockers.append(f"{name} is missing or empty")
 if missing_meta:blockers.append(f"Metadata missing fields: {', '.join(missing_meta)}")
 blockers+=placeholders
 archive=_resolve_archive(folder,root)
 publication_files=[p for p in archive.rglob("*") if p.is_file()] if archive.exists() else []
 publication_artifacts=[p for p in publication_files if p.stat().st_size>0 and (p.suffix.lower()==".pdf" or (p.suffix.lower() in {".cbz",".zip"} and _valid_package(p)))]
 digest=hashlib.sha256()
 for entry in entries:digest.update(entry["path"].encode());digest.update(entry["sha256"].encode())
 digest.update((current_qa_hash or "").encode())
 return {"evidence_hash":digest.hexdigest(),"files":entries,"blockers":blockers,"qa_verdict":qa,"qa_evidence_hash":reported_hashes[0] if len(reported_hashes)==1 else None,"qa_evidence_current":bool(current_qa_hash and len(reported_hashes)==1 and reported_hashes[0]==current_qa_hash),"covers":[str(p.relative_to(folder)).replace("\\","/") for p in covers],"pdfs":[p.name for p in pdfs],"packages":[p.name for p in packages],"invalid_packages":invalid_packages,"metadata":{"format":metadata.get("format"),"missing_fields":missing_meta,"placeholders":placeholders},"social_copy_exists":(folder/"social_posts.md").exists(),"checklist_exists":(folder/"final_export_checklist.md").exists(),"archive":{"path":str(archive.relative_to(root)).replace("\\","/"),"exists":archive.exists(),"publication_files":[p.name for p in publication_files],"publication_artifacts":[p.name for p in publication_artifacts]}}
def manifest(folder,root,persist=False):
 _stage(folder,root);ev=evidence(folder,root);data={"schema_version":"1.0","issue_id":issue_workflow._read_issue_id(folder),"created_at":_now() if persist else None,"evidence_hash":ev["evidence_hash"],"files":ev["files"]};data["manifest_hash"]=_hash(json.dumps({k:v for k,v in data.items() if k!="created_at"},sort_keys=True).encode())
 if persist:
  with _lock(folder):_write_json(_workspace(folder)/"manifests"/f"{data['manifest_hash']}.json",data)
 return data
def approval(folder):return _read_json(_workspace(folder)/"approval.json")
def approve(folder,root,note=""):
 _stage(folder,root)
 with _lock(folder):
  ev=evidence(folder,root)
  if ev["blockers"]:raise ReleaseError("Release approval blocked: "+"; ".join(ev["blockers"]),409)
  current=approval(folder)
  if current and current.get("evidence_hash")==ev["evidence_hash"]:raise ReleaseError("Current release evidence is already approved",409)
  man=manifest(folder,root,False);man["created_at"]=_now();_write_json(_workspace(folder)/"manifests"/f"{man['manifest_hash']}.json",man)
  record={"approved_at":_now(),"issue_id":issue_workflow._read_issue_id(folder),"evidence_hash":ev["evidence_hash"],"manifest_hash":man["manifest_hash"],"note":str(note or "")[:2000],"actor":"project_owner"};_write_json(_workspace(folder)/"approval.json",record);return record
def readiness(folder,root):
 ev=evidence(folder,root);approved=approval(folder);approval_current=bool(approved and approved.get("evidence_hash")==ev["evidence_hash"]);active=issue_workflow.workflow_status(folder,root)["active_stage"]
 return {"issue_id":issue_workflow._read_issue_id(folder),"workflow":issue_workflow.workflow_status(folder,root),"evidence":ev,"manifest":manifest(folder,root,False) if active in {"release","published"} else None,"approval":approved,"approval_current":approval_current,"release_ready":not ev["blockers"] and approval_current,"publication_ready":active=="published" and approval_current and ev["archive"]["exists"] and bool(ev["archive"]["publication_artifacts"])}
def promote_manifest(folder,root,replace=False):
 _stage(folder,root)
 with _lock(folder):
  status=readiness(folder,root)
  if not status["approval_current"]:raise ReleaseError("Current release approval is required",409)
  destination=folder/"release_hash_manifest.json"
  if destination.exists() and not replace:raise ReleaseError("release_hash_manifest.json already exists; explicit replacement confirmation is required",409)
  approved=status["approval"];source=_workspace(folder)/"manifests"/f"{approved['manifest_hash']}.json";data=_read_json(source)
  if not data:raise ReleaseError("Approved release manifest is missing",409)
  calculated=_hash(json.dumps({k:v for k,v in data.items() if k not in {"created_at","manifest_hash"}},sort_keys=True).encode())
  if data.get("manifest_hash")!=calculated or data.get("manifest_hash")!=approved.get("manifest_hash"):raise ReleaseError("Approved release manifest hash is missing or mismatched",409)
  if data.get("evidence_hash")!=approved.get("evidence_hash") or data.get("evidence_hash")!=status["evidence"]["evidence_hash"]:raise ReleaseError("Approved release manifest evidence is stale or mismatched",409)
  payload=json.dumps(data,indent=2,ensure_ascii=False)+"\n"
  if json.loads(payload)!=data:raise ReleaseError("Release manifest serialization failed",409)
  before=destination.read_bytes() if destination.exists() else None
  try:
   _atomic(destination,payload);written=_read_json(destination)
   written_hash=_hash(json.dumps({k:v for k,v in written.items() if k not in {"created_at","manifest_hash"}},sort_keys=True).encode())
   if written!=data or written_hash!=approved["manifest_hash"] or written.get("evidence_hash")!=status["evidence"]["evidence_hash"]:raise ReleaseError("Canonical release manifest verification failed",409)
   workflow=issue_workflow.workflow_status(folder,root)
  except Exception:
   if before is None:
    try:destination.unlink()
    except FileNotFoundError:pass
   else:_atomic_bytes(destination,before)
   raise
  return {"ok":True,"destination":"release_hash_manifest.json","manifest_hash":written["manifest_hash"],"evidence_hash":written["evidence_hash"],"workflow":workflow}

def publish_archive(folder, root, replace=False):
 """Copy verified release artifacts into 05_RELEASE_ARCHIVE with lock protection.

 Requires active stage release or published, current release approval, and a
 promoted release_hash_manifest.json that matches current evidence.
 """
 import shutil
 _stage(folder, root)
 with _lock(folder):
  status = readiness(folder, root)
  if not status["approval_current"]:
   raise ReleaseError("Current release approval is required before archive publication", 409)
  if not (folder / "release_hash_manifest.json").is_file():
   raise ReleaseError("release_hash_manifest.json must be promoted before archive publication", 409)
  manifest_data = _read_json(folder / "release_hash_manifest.json")
  if not manifest_data or manifest_data.get("evidence_hash") != status["evidence"]["evidence_hash"]:
   raise ReleaseError("Canonical release manifest evidence is stale or mismatched", 409)
  archive = _archive(folder, root)
  if archive.exists() and not replace:
   raise ReleaseError(f"Release archive already exists at {archive.as_posix()}; explicit replacement confirmation is required", 409)
  # Collect publication evidence files.
  exports = folder / "exports"
  candidates = []
  if exports.exists():
   for path in sorted(exports.iterdir()):
    if path.is_file() and path.suffix.lower() in {".pdf", ".zip", ".cbz"} and path.stat().st_size > 0:
     candidates.append(path)
  for name in ("release_hash_manifest.json", "metadata.json", "qa_report.md", "social_posts.md"):
   path = folder / name
   if path.is_file() and path.stat().st_size > 0:
    candidates.append(path)
  covers = sorted((folder / "generated_art").rglob("*cover*.png")) if (folder / "generated_art").exists() else []
  candidates.extend(covers)
  pdfs = [p for p in candidates if p.suffix.lower() == ".pdf"]
  packages = [p for p in candidates if p.suffix.lower() in {".zip", ".cbz"} and _valid_package(p)]
  if not pdfs or not packages:
   raise ReleaseError("Archive publication requires a non-empty PDF and a valid CBZ/ZIP package", 409)
  # Build the new archive in a staging dir and swap it in only after every
  # artifact copies successfully, so a failed/interrupted copy cannot destroy
  # the previously published release archive (which rmtree'd before copying).
  archive.parent.mkdir(parents=True, exist_ok=True)
  staging = archive.with_name(f".{archive.name}.staging-{os.getpid()}")
  if staging.exists():
   shutil.rmtree(staging)
  staging.mkdir(parents=True)
  copied = []
  try:
   for path in candidates:
    destination = staging / path.name
    # Avoid collisions when multiple covers share basename by using relative stem path hash prefix.
    if destination.exists() and path.parent != folder and path.parent != exports:
     destination = staging / f"{path.parent.name}_{path.name}"
    shutil.copy2(path, destination)
    copied.append(destination.name)
   if archive.exists():
    shutil.rmtree(archive)
   os.replace(staging, archive)
  except BaseException:
   shutil.rmtree(staging, ignore_errors=True)
   raise
  # Provenance record inside issue workspace.
  record = {
   "published_at": _now(),
   "issue_id": issue_workflow._read_issue_id(folder),
   "archive_path": str(archive.relative_to(root)).replace("\\", "/"),
   "evidence_hash": status["evidence"]["evidence_hash"],
   "manifest_hash": manifest_data.get("manifest_hash"),
   "files": copied,
   "actor": "project_owner",
  }
  _write_json(_workspace(folder) / "publication.json", record)
  refreshed = readiness(folder, root)
  if not refreshed["evidence"]["archive"]["exists"]:
   raise ReleaseError("Archive publication verification failed", 409)
  if not refreshed["evidence"]["archive"]["publication_artifacts"]:
   raise ReleaseError("Archive publication verification found no publication artifacts", 409)
  return {"ok": True, "publication": record, "readiness": refreshed, "workflow": issue_workflow.workflow_status(folder, root)}
