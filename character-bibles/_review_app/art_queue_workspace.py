"""Panel prompt and manual art-attempt queue."""
from __future__ import annotations
import contextlib, datetime as dt, hashlib, io, json, os, re, tempfile, time
from pathlib import Path
from PIL import Image
import bible_store, canon_catalog, issue_workflow

PANEL_ID=re.compile(r"^MZ-\d{4}-\d{2}-\d{2}_P\d{2}_PANEL\d{2}$")
ATTEMPT_ID=re.compile(r"^attempt-\d{8}T\d{6}Z-[0-9a-f]{6}$")
FORMATS={"PNG":".png","JPEG":".jpg","WEBP":".webp"}; MAX_BYTES=25*1024*1024

class ArtQueueError(ValueError):
    def __init__(self,message:str,status:int=400): super().__init__(message); self.status=status

def _now(): return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
def _hash(data:bytes): return hashlib.sha256(data).hexdigest()
def _workspace(folder): return folder/".art-workspace"
def _atomic_bytes(path:Path,data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True); fd,temp=tempfile.mkstemp(prefix=f".{path.name}.",suffix=".tmp",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp,path)
    except Exception:
        try: os.unlink(temp)
        except OSError: pass
        raise
def _write_json(path,data): _atomic_bytes(path,(json.dumps(data,indent=2,ensure_ascii=False)+"\n").encode())
def _read_json(path,default=None):
    if not path.exists(): return default
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError) as exc: raise ArtQueueError(f"Malformed art workspace record: {path.name}") from exc
@contextlib.contextmanager
def _selection_lock(folder):
    path=_workspace(folder)/".selection.lock";path.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError as exc:raise ArtQueueError("Preferred-art selection is already in progress",409) from exc
    try:
        with os.fdopen(fd,"w") as stream:stream.write(str(os.getpid()))
        yield
    finally:
        try:path.unlink()
        except FileNotFoundError:pass
def _stage(folder,root,allowed):
    active=issue_workflow.workflow_status(folder,root)["active_stage"]
    if active not in allowed: raise ArtQueueError(f"Art Queue requires workflow stage {' or '.join(sorted(allowed))}; current stage is {active}",409)
    return active
def _plan(folder):
    data=issue_workflow._json(folder/"page_panel_plan.json")
    if not data: raise ArtQueueError("Canonical page_panel_plan.json is missing or malformed",409)
    return data
def _plan_hash(folder): return _hash((folder/"page_panel_plan.json").read_bytes())
def _panel(plan,panel_id):
    if not PANEL_ID.fullmatch(str(panel_id or "")): raise ArtQueueError("Invalid panel ID")
    for page in plan.get("pages",[]):
        for panel in page.get("panels",[]):
            if panel.get("panel_id")==panel_id:return panel
    raise ArtQueueError("Panel is not present in the canonical plan")
def _refs(root,characters):
    result=[]
    for raw in characters:
        try:
            cid=bible_store.resolve_character_id(raw,root/"character-bibles")
            if cid in [x["character_id"] for x in result]:continue
            bible=bible_store.load_bible(cid,root/"character-bibles"); visual=bible.get("visual_canon",{}); ref=visual.get("primary_reference_image")
            result.append({"character_id":cid,"display_name":bible.get("identification",{}).get("current_display_name"),"primary_reference":ref,"visual_constraints":visual.get("features_that_must_never_change",[]),"reference_kind":"individual_character",**({"error":"Approved individual character reference unavailable"} if not ref else {})})
        except ValueError: result.append({"character_id":raw,"error":"Approved individual character reference unavailable"})
    return result
def _scene_refs(root,panel):
    location_ref=canon_catalog.resolve_location_ref(root,panel.get("location"))
    prop_refs=canon_catalog.resolve_prop_refs(root,panel.get("props",[]))
    return location_ref,prop_refs
def all_attempts(folder):
    base = _workspace(folder) / "attempts"
    result = {}
    if base.exists():
        for json_path in base.glob("*/attempt-*.json"):
            record = _read_json(json_path)
            if record and "panel_id" in record:
                result.setdefault(record["panel_id"], []).append(record)
    for items in result.values():
        items.sort(key=lambda x: x.get("attempt_id", ""))
    return result

def build_queue(folder,root,persist=False):
    _stage(folder,root,{"art_prompts","art_production"}); plan=_plan(folder); plan_hash=_plan_hash(folder); existing=_read_json(_workspace(folder)/"queue.json",{}) or {}
    attempts_map = all_attempts(folder)
    items=[]
    for page in plan.get("pages",[]):
        for panel in page.get("panels",[]):
            pid=panel["panel_id"]
            panel_attempts=list(attempts_map.get(pid, []))
            for attempt in panel_attempts: attempt["plan_stale"]=attempt.get("plan_hash")!=plan_hash
            preferred=next((a["attempt_id"] for a in panel_attempts if a.get("status")=="preferred" and not a["plan_stale"]),None)
            location_ref,prop_refs=_scene_refs(root,panel)
            items.append({"panel_id":pid,"page_number":page.get("page_number"),"characters":panel.get("characters",[]),"location":panel.get("location"),"props":panel.get("props",[]),"action":panel.get("action"),"dialogue":panel.get("dialogue"),"caption":panel.get("caption"),"continuity_notes":panel.get("continuity_notes"),"art_prompt":panel.get("art_prompt"),"negative_prompt":panel.get("negative_prompt"),"references":_refs(root,panel.get("characters",[])),"location_ref":location_ref,"prop_refs":prop_refs,"attempt_count":len(panel_attempts),"attempts":panel_attempts,"preferred_attempt":preferred,"status":"approved" if preferred else "missing"})
    queue={"schema_version":"1.0","issue_id":plan.get("issue_id"),"plan_hash":plan_hash,"created_at":existing.get("created_at") or _now(),"updated_at":_now() if persist else existing.get("updated_at"),"items":items}
    if persist:_write_json(_workspace(folder)/"queue.json",queue)
    return queue

def prompt_package(folder,root,panel_id):
    _stage(folder,root,{"art_prompts","art_production"}); plan=_plan(folder); panel=_panel(plan,panel_id); refs=_refs(root,panel.get("characters",[]))
    if any(r.get("error") for r in refs):raise ArtQueueError("Panel has a character without an approved individual reference",409)
    location_ref,prop_refs=_scene_refs(root,panel)
    package={"generation_id":f"prompt-{int(time.time_ns())}","issue_id":plan["issue_id"],"panel_id":panel_id,"execution_mode":"manual","provider":"manual_prompt","plan_hash":_plan_hash(folder),"task":"Create one panel image; do not fabricate text, identities, or approval.","prompt":panel.get("art_prompt") or panel.get("action"),"negative_prompt":panel.get("negative_prompt") or "No text, duplicate characters, identity drift, or unapproved costume changes.","characters":refs,"location":panel.get("location"),"location_ref":location_ref,"props":panel.get("props",[]),"prop_refs":prop_refs,"continuity_notes":panel.get("continuity_notes"),"output_contract":{"formats":["PNG","JPEG","WEBP"],"one_panel_only":True}}
    package["prompt_hash"]=_hash(json.dumps(package,sort_keys=True).encode()); _write_json(_workspace(folder)/"prompts"/f"{panel_id}-{package['prompt_hash'][:8]}.json",package); return package
def _image(data):
    if not data or len(data)>MAX_BYTES:raise ArtQueueError("Image is empty or exceeds 25 MB")
    try:
        image=Image.open(io.BytesIO(data)); image.verify(); fmt=image.format
        image=Image.open(io.BytesIO(data)); width,height=image.size
    except Exception as exc:raise ArtQueueError("Uploaded file is not a valid supported image") from exc
    if fmt not in FORMATS:raise ArtQueueError("Image format must be PNG, JPEG, or WEBP")
    return fmt,width,height
def _attempt_id(data):return f"attempt-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_hash(data+str(time.time_ns()).encode())[:6]}"
def import_attempt(folder,root,panel_id,data,filename,provider="manual"):
    _stage(folder,root,{"art_production"}); plan=_plan(folder); _panel(plan,panel_id); fmt,w,h=_image(data); aid=_attempt_id(data); ext=FORMATS[fmt]
    asset=_workspace(folder)/"attempts"/panel_id/f"{aid}{ext}"; _atomic_bytes(asset,data)
    record={"attempt_id":aid,"panel_id":panel_id,"imported_at":_now(),"source_type":"manual_import","provider":str(provider or "manual")[:100],"original_name":Path(str(filename or "upload")).name[:200],"format":fmt,"width":w,"height":h,"sha256":_hash(data),"plan_hash":_plan_hash(folder),"asset_path":str(asset.relative_to(folder)).replace("\\","/"),"status":"candidate","actor":None}
    _write_json(asset.with_suffix(".json"),record); return record
def attempts(folder,panel_id):
    if not PANEL_ID.fullmatch(str(panel_id or "")):raise ArtQueueError("Invalid panel ID")
    base=_workspace(folder)/"attempts"/panel_id
    return [_read_json(p) for p in sorted(base.glob("attempt-*.json"))] if base.exists() else []
def _attempt(folder,panel_id,attempt_id):
    if not ATTEMPT_ID.fullmatch(str(attempt_id or "")):raise ArtQueueError("Invalid attempt ID")
    record=next((x for x in attempts(folder,panel_id) if x.get("attempt_id")==attempt_id),None)
    if not record:raise ArtQueueError("Unknown art attempt")
    return record
def set_attempt_status(folder,root,panel_id,attempt_id,status):
    _stage(folder,root,{"art_production"}); record=_attempt(folder,panel_id,attempt_id)
    if status not in {"rejected","archived"}:raise ArtQueueError("Attempt status must be rejected or archived")
    if record.get("status")=="preferred":raise ArtQueueError("Preferred art cannot be rejected without selecting a replacement",409)
    record["status"]=status; record["reviewed_at"]=_now();record["actor"]="project_owner"; path=folder/record["asset_path"];_write_json(path.with_suffix(".json"),record);return record
def select_preferred(folder,root,panel_id,attempt_id):
    with _selection_lock(folder):
        _stage(folder,root,{"art_production"});plan=_plan(folder);_panel(plan,panel_id);record=_attempt(folder,panel_id,attempt_id)
        if record.get("plan_hash")!=_plan_hash(folder):raise ArtQueueError("Art attempt is stale because the canonical panel plan changed",409)
        if record.get("status") in {"rejected","archived"}:raise ArtQueueError("Rejected or archived art cannot be selected",409)
        source=folder/record["asset_path"]
        with Image.open(source) as image:
            output=io.BytesIO();image.convert("RGBA").save(output,format="PNG")
        normalized=output.getvalue();fmt,_,_=_image(normalized)
        if fmt!="PNG":raise ArtQueueError("Preferred art normalization did not produce PNG",409)
        destination=folder/"generated_art"/"selected_panels"/f"{panel_id}.png";queue_path=_workspace(folder)/"queue.json"
        attempt_records=attempts(folder,panel_id);attempt_paths={a["attempt_id"]:(folder/a["asset_path"]).with_suffix(".json") for a in attempt_records}
        attempt_snapshots={aid:path.read_bytes() for aid,path in attempt_paths.items()}
        destination_snapshot=destination.read_bytes() if destination.exists() else None
        queue_snapshot=queue_path.read_bytes() if queue_path.exists() else None
        selected_at=_now()
        updated=[]
        for attempt in attempt_records:
            changed=dict(attempt)
            if changed["attempt_id"]==attempt_id:
                changed.update({"status":"preferred","selected_at":selected_at,"actor":"project_owner"})
            elif changed.get("status")=="preferred":
                changed["status"]="candidate";changed.pop("selected_at",None)
            updated.append(changed)
        try:
            _atomic_bytes(destination,normalized)
            for changed in updated:_write_json(attempt_paths[changed["attempt_id"]],changed)
            queue=build_queue(folder,root,False)
            _write_json(queue_path,queue)
            persisted=attempts(folder,panel_id);preferred=[a for a in persisted if a.get("status")=="preferred"]
            queue_item=next((item for item in _read_json(queue_path,{"items":[]})["items"] if item.get("panel_id")==panel_id),None)
            if len(preferred)!=1 or preferred[0].get("attempt_id")!=attempt_id or not queue_item or queue_item.get("preferred_attempt")!=attempt_id or queue_item.get("status")!="approved" or _hash(destination.read_bytes())!=_hash(normalized):
                raise ArtQueueError("Preferred-art selection records are inconsistent",409)
            workflow=issue_workflow.workflow_status(folder,root)
        except Exception:
            if destination_snapshot is None:
                try:destination.unlink()
                except FileNotFoundError:pass
            else:_atomic_bytes(destination,destination_snapshot)
            for aid,path in attempt_paths.items():_atomic_bytes(path,attempt_snapshots[aid])
            if queue_snapshot is None:
                try:queue_path.unlink()
                except FileNotFoundError:pass
            else:_atomic_bytes(queue_path,queue_snapshot)
            raise
        selected=next(a for a in persisted if a["attempt_id"]==attempt_id)
        return {"ok":True,"attempt":selected,"selected_path":str(destination.relative_to(folder)).replace("\\","/"),"workflow":workflow}
def summary(folder,root):
    workflow=issue_workflow.workflow_status(folder,root)
    try:queue=build_queue(folder,root,False)
    except ArtQueueError as exc:queue={"items":[],"error":str(exc)}
    return {"issue_id":issue_workflow._read_issue_id(folder),"workflow":workflow,"queue":queue,"provider":{"type":"manual_prompt","execution_mode":"manual","available":True}}
