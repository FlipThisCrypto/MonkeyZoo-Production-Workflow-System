"""Evidence-backed visual QA reviews and canonical report promotion."""
from __future__ import annotations
import datetime as dt, hashlib, json, os, re, tempfile, time
from pathlib import Path
from typing import Any
from PIL import Image
import issue_workflow
from contextlib import contextmanager

REVIEW_ID=re.compile(r"^qa-\d{8}T\d{6}Z-[0-9a-f]{6}$")
VERDICTS={"pass":"PASS","hold":"HOLD","fail":"FAIL"}
class VisualQAError(ValueError):
 def __init__(self,message,status=400):super().__init__(message);self.status=status
def _now():return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def _hash(data):return hashlib.sha256(data).hexdigest()
def _workspace(folder):return folder/".qa-workspace"
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
 except (OSError,ValueError) as exc:raise VisualQAError(f"Malformed QA workspace record: {path.name}") from exc
def _stage(folder,root):
 active=issue_workflow.workflow_status(folder,root)["active_stage"]
 if active!="qa":raise VisualQAError(f"QA workspace requires active workflow stage qa; current stage is {active}",409)
@contextmanager
def _promotion_lock(folder):
 path=_workspace(folder)/".promotion.lock";path.parent.mkdir(parents=True,exist_ok=True)
 try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise VisualQAError("Another QA promotion is already in progress",409) from None
 try:os.write(fd,_now().encode());os.fsync(fd);os.close(fd);yield
 finally:
  try:os.close(fd)
  except OSError:pass
  try:path.unlink()
  except OSError:pass
def _plan(folder):
 data=issue_workflow._json(folder/"page_panel_plan.json")
 if not data:raise VisualQAError("Canonical page_panel_plan.json is missing or malformed",409)
 return data
def evidence(folder):
 plan=_plan(folder); selected=folder/"generated_art/selected_panels"; inventory=[];hashes={}
 planned=[]
 for page in plan.get("pages",[]):
  for panel in page.get("panels",[]):
   pid=panel.get("panel_id");planned.append(pid);path=selected/f"{pid}.png";entry={"panel_id":pid,"characters":panel.get("characters",[]),"dialogue":panel.get("dialogue"),"caption":panel.get("caption"),"continuity_notes":panel.get("continuity_notes"),"path":str(path.relative_to(folder)).replace("\\","/"),"exists":path.exists(),"format":None,"width":None,"height":None,"sha256":None,"error":None}
   if path.exists():
    try:
     with Image.open(path) as image:entry.update(format=image.format,width=image.width,height=image.height)
     entry["sha256"]=_hash(path.read_bytes());hashes.setdefault(entry["sha256"],[]).append(pid)
     if entry["format"]!="PNG":entry["error"]="Selected panel must be PNG"
    except Exception:entry["error"]="Selected panel is not a valid image"
   inventory.append(entry)
 duplicates=[ids for ids in hashes.values() if len(ids)>1]
 metadata=issue_workflow._json(folder/"metadata.json") or {};metadata_missing=[k for k in ("issue_id","title") if not metadata.get(k)]
 covers=sorted((folder/"generated_art").rglob("*cover*.png")) if (folder/"generated_art").exists() else []  # sorted: evidence hash must be order-stable across platforms/restores (matches release_workspace)
 files=[folder/"page_panel_plan.json",folder/"metadata.json",folder/"cover_prompt.md",folder/"final_export_checklist.md",*sorted(p for p in selected.glob("*.png")),*covers] if selected.exists() else [folder/"page_panel_plan.json",folder/"metadata.json",folder/"cover_prompt.md",folder/"final_export_checklist.md",*covers]
 digest=hashlib.sha256()
 for path in files:
  if path.exists():digest.update(str(path.relative_to(folder)).replace("\\","/").encode());digest.update(path.read_bytes())
 dimensions=[(x["width"],x["height"]) for x in inventory if x["exists"] and not x["error"]];expected_dimensions=max(set(dimensions),key=dimensions.count) if dimensions else None
 checks={"missing_panels":[x["panel_id"] for x in inventory if not x["exists"]],"duplicate_art":duplicates,"invalid_images":[x["panel_id"] for x in inventory if x["error"]],"dimension_mismatches":[x["panel_id"] for x in inventory if x["exists"] and not x["error"] and (x["width"],x["height"])!=expected_dimensions],"identity_missing":[x["panel_id"] for x in inventory if not x["characters"]],"unmapped_images":[p.stem for p in selected.glob("*.png") if p.stem not in planned] if selected.exists() else [],"dialogue_or_caption_panels":[x["panel_id"] for x in inventory if x["dialogue"] or x["caption"]],"continuity_missing":[x["panel_id"] for x in inventory if not str(x.get("continuity_notes") or "").strip()],"cover_prompt_exists":(folder/"cover_prompt.md").exists(),"cover_images":len(covers),"metadata_missing":metadata_missing,"checklist_exists":(folder/"final_export_checklist.md").exists()}
 blockers=[]
 for key in ("missing_panels","duplicate_art","invalid_images","dimension_mismatches","identity_missing","unmapped_images","metadata_missing"):
  if checks[key]:blockers.append(f"{key.replace('_',' ')}: {checks[key]}")
 if not checks["cover_prompt_exists"]:blockers.append("cover prompt is missing")
 if checks["continuity_missing"]:blockers.append(f"continuity notes missing: {checks['continuity_missing']}")
 if not checks["checklist_exists"]:blockers.append("final export checklist is missing")
 advisories=[]
 if not checks["cover_images"]:advisories.append("cover image is absent; Release owns the blocking cover-deliverable requirement")
 return {"evidence_hash":digest.hexdigest(),"panels":inventory,"checks":checks,"blockers":blockers,"advisories":advisories,"planned_panel_count":len(planned),"selected_panel_count":sum(x["exists"] for x in inventory)}
def _id(data):return f"qa-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_hash((json.dumps(data,sort_keys=True)+str(time.time_ns())).encode())[:6]}"
def create_review(folder,root):
 _stage(folder,root);ev=evidence(folder);rid=_id(ev);record={"schema_version":"1.0","review_id":rid,"issue_id":issue_workflow._read_issue_id(folder),"created_at":_now(),"evidence_hash":ev["evidence_hash"],"evidence":ev,"owner_notes":"","continuity_checks":[],"verdict":None,"approval":None}
 _write_json(_workspace(folder)/"reviews"/f"{rid}.json",record);return decorate(record,folder)
def _safe(value):
 if not REVIEW_ID.fullmatch(str(value or "")):raise VisualQAError("Invalid QA review ID")
 return value
def _load(folder,rid):
 data=_read_json(_workspace(folder)/"reviews"/f"{_safe(rid)}.json")
 if not isinstance(data,dict):raise VisualQAError("Unknown QA review")
 return data
def decorate(record,folder):
 result=dict(record);result["evidence_stale"]=record.get("evidence_hash")!=evidence(folder)["evidence_hash"]
 result["approval_current"]=bool(record.get("approval") and record["approval"].get("evidence_hash")==record.get("evidence_hash") and not result["evidence_stale"]);return result
def reviews(folder):
 base=_workspace(folder)/"reviews";return [decorate(_read_json(p),folder) for p in sorted(base.glob("*.json"))] if base.exists() else []
def finalize(folder,root,rid,verdict,notes="",continuity_checks=None):
 _stage(folder,root);record=decorate(_load(folder,rid),folder)
 if record.get("approval"):raise VisualQAError("QA review is already finalized and immutable",409)
 if record["evidence_stale"]:raise VisualQAError("QA evidence changed since review creation",409)
 key=str(verdict or "").lower()
 if key not in VERDICTS:raise VisualQAError("Verdict must be pass, hold, or fail")
 if key=="pass" and record["evidence"]["blockers"]:raise VisualQAError("PASS is blocked by unresolved QA evidence",409)
 record["owner_notes"]=str(notes or "")[:5000];record["continuity_checks"]=[str(x)[:500] for x in (continuity_checks or [])][:100];record["verdict"]=VERDICTS[key];record["approval"]={"approved_at":_now(),"verdict":record["verdict"],"evidence_hash":record["evidence_hash"],"actor":"project_owner"}
 clean={k:v for k,v in record.items() if k not in {"evidence_stale","approval_current"}};_write_json(_workspace(folder)/"reviews"/f"{rid}.json",clean);return decorate(clean,folder)
def _render(record):
 ev=record["evidence"];lines=[f"# QA Report — {record['issue_id']}",f"Review ID: {record['review_id']}",f"Evidence hash: {record['evidence_hash']}","",f"VERDICT: {record['verdict']}","",f"Owner notes: {record['owner_notes'] or 'None'}","","## Panel inventory"]
 for p in ev["panels"]:lines.append(f"- {p['panel_id']}: {'present' if p['exists'] else 'missing'}; {p['format'] or 'no format'}; {p['width'] or '?'}x{p['height'] or '?'}; {p['error'] or 'no file error'}")
 lines += ["","## Evidence blockers"] + ([f"- {x}" for x in ev["blockers"]] or ["- None"])
 lines += ["","## Evidence advisories"] + ([f"- {x}" for x in ev.get("advisories",[])] or ["- None"])
 lines += ["","## Continuity review"] + ([f"- {x}" for x in record["continuity_checks"]] or ["- No owner notes"])
 return "\n".join(lines)+"\n"
def promote(folder,root,rid,replace=False):
 _stage(folder,root)
 with _promotion_lock(folder):
  record=decorate(_load(folder,rid),folder)
  if not record["approval_current"]:raise VisualQAError("A current finalized QA review is required",409)
  destination=folder/"qa_report.md";provenance=_workspace(folder)/"promotions"/f"{rid}.json"
  if provenance.exists():raise VisualQAError("QA review was already promoted",409)
  if destination.exists() and not replace:raise VisualQAError("qa_report.md already exists; explicit replacement confirmation is required",409)
  rendered=_render(record)
  expected=(f"Review ID: {rid}",f"Evidence hash: {record['evidence_hash']}",f"VERDICT: {record['verdict']}")
  if any(rendered.splitlines().count(value)!=1 for value in expected):raise VisualQAError("Rendered QA report does not match the finalized review",409)
  report_before=destination.read_bytes() if destination.exists() else None;provenance_before=provenance.read_bytes() if provenance.exists() else None
  backup=_workspace(folder)/"promotions"/f"backup-{rid}.md" if destination.exists() else None;backup_before=backup.read_bytes() if backup and backup.exists() else None
  prov={"review_id":rid,"promoted_at":_now(),"evidence_hash":record["evidence_hash"],"verdict":record["verdict"],"destination":"qa_report.md","backup":str(backup.relative_to(folder)).replace("\\","/") if backup else None,"actor":"project_owner"}
  try:
   if backup:_atomic_bytes(backup,report_before)
   _atomic(destination,rendered)
   written=destination.read_text(encoding="utf-8")
   if written!=rendered or any(written.splitlines().count(value)!=1 for value in expected):raise VisualQAError("Written QA report does not match the finalized review",409)
   _write_json(provenance,prov)
   saved=_read_json(provenance)
   if any(saved.get(key)!=prov[key] for key in ("review_id","evidence_hash","verdict","destination")):raise VisualQAError("QA report and promotion provenance disagree",409)
   workflow=issue_workflow.workflow_status(folder,root)
  except Exception:
   if report_before is None:
    try:destination.unlink()
    except FileNotFoundError:pass
   else:_atomic_bytes(destination,report_before)
   if provenance_before is None:
    try:provenance.unlink()
    except FileNotFoundError:pass
   else:_atomic_bytes(provenance,provenance_before)
   if backup:
    if backup_before is None:
     try:backup.unlink()
     except FileNotFoundError:pass
    else:_atomic_bytes(backup,backup_before)
   raise
  return {"ok":True,"promotion":saved,"workflow":workflow}
def summary(folder,root):
 workflow=issue_workflow.workflow_status(folder,root)
 try:ev=evidence(folder)
 except VisualQAError as exc:ev={"panels":[],"checks":{},"blockers":[str(exc)]}
 return {"issue_id":issue_workflow._read_issue_id(folder),"workflow":workflow,"evidence":ev,"reviews":reviews(folder)}
