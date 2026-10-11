"""Negative tests (plan 2.4 step 5): every mutation must make the gate fail.
  neg.py --framework <dir or bundle> --project <dir>     (cases in <project>/tests/neg_cases.py)
  neg.py --framework <dir>                               (framework cases in tools/neg_framework.py)
Exit status is non-zero if any mutation is not caught."""
import argparse, copy, json, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import load, validate
def _mod(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def main():
    a = argparse.ArgumentParser(); a.add_argument("--framework", required=True); a.add_argument("--project"); a.add_argument("--out"); o = a.parse_args()
    base = load.load(o.framework, o.project)
    res0, _, _ = validate.gate(o.framework, o.project, store=copy.deepcopy(base))
    if not all(r[2] for r in res0): print("Baseline does not pass; negative tests not meaningful."); sys.exit(2)
    cases = _mod(os.path.join(o.project, "tests", "neg_cases.py") if o.project else os.path.join(HERE, "neg_framework.py")).CASES
    out = []
    for label, mut in cases:
        st = copy.deepcopy(base); I = {r["id"]: r for r in st["records"]}; I.update({e["id"]: e for e in st["register_entries"]})
        try:
            mut(I, st); res, _, _ = validate.gate(o.framework, o.project, store=st); fails = [r[1] for r in res if not r[2]]
        except load.LoadError as e: fails = ["Load: " + str(e)[:80]]
        except Exception as e: fails = []; label += "  [mutation or gate crashed: %r]" % e
        out.append((label, fails))
    for l, f in out: print(("CAUGHT" if f else "MISSED"), l, "->", f)
    n = sum(1 for _, f in out if f); print(n, "/", len(out), "caught")
    if o.out: json.dump(out, open(o.out, "w"), indent=1)
    sys.exit(0 if n == len(out) else 1)
if __name__ == "__main__": main()
