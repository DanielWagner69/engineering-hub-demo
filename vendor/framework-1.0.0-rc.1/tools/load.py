"""Load framework data (a data/framework folder or a released bundle .json) and,
optionally, a project folder into one store {meta, register_entries, records}.
Fails on malformed JSON or a duplicate identifier (plan 2.4 step 1)."""
import json, os, glob
class LoadError(Exception): pass
def _read(path):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception as e: raise LoadError("Malformed JSON: %s (%s)" % (path, e))
def load_framework(src):
    if os.path.isfile(src):
        b = _read(src); return {"meta": b["meta"], "register_entries": b["register_entries"], "records": b["records"]}
    regs, recs = [], []
    for f in sorted(glob.glob(os.path.join(src, "registers", "*.json"))): regs += _read(f)["entries"]
    for sub in ("considerations", "records", "pages", "lessons"):
        for f in sorted(glob.glob(os.path.join(src, sub, "*.json"))):
            x = _read(f); recs += x if isinstance(x, list) else [x]
    return {"meta": {"source": "data/framework"}, "register_entries": regs, "records": recs}
def load_project(d):
    recs = []
    for f in sorted(glob.glob(os.path.join(d, "records", "*.json"))): recs += _read(f)
    # Tailoring Records live beside the project data (data/tailoring/, plan 2.2)
    for f in sorted(glob.glob(os.path.join(d, "..", "tailoring", "*.json"))): recs += _read(f)
    regs = _read(os.path.join(d, "register_entries.json")) if os.path.exists(os.path.join(d, "register_entries.json")) else []
    meta = _read(os.path.join(d, "project.json"))
    return meta, regs, recs
def load(framework, project=None):
    st = load_framework(framework); st["framework_records"] = [r["id"] for r in st["records"]]
    st["framework_entries"] = [e["id"] for e in st["register_entries"]]
    if project:
        meta, regs, recs = load_project(project)
        st["meta"] = dict(st["meta"], project=meta); st["register_entries"] += regs; st["records"] += recs
    ids = [r["id"] for r in st["records"]] + [e["id"] for e in st["register_entries"]]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup: raise LoadError("Duplicate identifiers: %s" % dup[:10])
    return st
def project_config(project):
    p = os.path.join(project, "config.json")
    return _read(p) if os.path.exists(p) else {}
