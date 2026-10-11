"""Build gate (plan 2.4 steps 1 to 4 and 6). Exit status is non-zero on any failure.
  Framework only:  validate.py --framework data/framework
  With a project:  validate.py --framework <dir or bundle.json> --project data/project-d [--repo .]
Writes a JSON report with --out and prints a human summary."""
import argparse, json, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import load, check_schema, purity
from checks import core, late
def gate(framework, project=None, schema=None, repo=None, store=None):
    schema = schema or os.path.join(HERE, "..", "schema")
    if store is None: store = load.load(framework, project)
    cfg = load.project_config(project) if project else {}
    res = check_schema.run(store, schema)
    info = {}
    def safe(stage, fn):
        try: return fn()
        except Exception as e: return [("E!", "%s could not run on this data (data error stops the build): %r" % (stage, e), False, "")]
    if project:
        def _core():
            r, i = core.run(store, cfg); info.update(i); return r
        res += safe("Carried rule checks", _core)
    res += safe("Rebuild checks", lambda: late.run(store, cfg, project_mode=bool(project)))
    res += safe("Purity checks", lambda: purity.store_checks(store, bool(project)))
    if repo: res += purity.tree_checks(repo)
    if project and os.path.exists(os.path.join(project, "tests", "example_assertions.py")):
        spec = importlib.util.spec_from_file_location("ex", os.path.join(project, "tests", "example_assertions.py")); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        res += safe("Example assertions", lambda: m.run(store, cfg, info))
    return res, info, store
def main():
    a = argparse.ArgumentParser(); a.add_argument("--framework", required=True); a.add_argument("--project"); a.add_argument("--schema"); a.add_argument("--repo"); a.add_argument("--out"); a.add_argument("-q", action="store_true")
    o = a.parse_args()
    try: res, info, _ = gate(o.framework, o.project, o.schema, o.repo)
    except load.LoadError as e: print("LOAD FAILED:", e); sys.exit(2)
    if o.out: json.dump({"results": res, "info": info}, open(o.out, "w"), indent=1, default=str)
    by = {}
    for s, n, ok, d in res: by.setdefault(s, [0, 0]); by[s][0] += ok; by[s][1] += 1
    print("Gate:", sum(r[2] for r in res), "/", len(res), "checks passed  (" + ", ".join("%s %d/%d" % (k, v[0], v[1]) for k, v in sorted(by.items())) + ")")
    for s, n, ok, d in res:
        if not ok: print("FAIL [%s] %s :: %s" % (s, n, str(d)[:300]))
    sys.exit(0 if all(r[2] for r in res) else 1)
if __name__ == "__main__": main()
