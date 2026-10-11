"""Phase 0 scaffold of the site generator (plan 2.4 step 7): runs the gate, then writes
an empty site shell with the data embedded as JavaScript. Templates arrive in Phase 2.
Usage: build_site.py --framework <dir or bundle> [--project <dir>] --out build/"""
import argparse, json, os, sys, html
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import validate
a = argparse.ArgumentParser(); a.add_argument("--framework", required=True); a.add_argument("--project"); a.add_argument("--out", required=True); o = a.parse_args()
res, info, st = validate.gate(o.framework, o.project)
if not all(r[2] for r in res): print("Gate failed; site not generated."); sys.exit(1)
os.makedirs(os.path.join(o.out, "data"), exist_ok=True)
data = {"meta": st["meta"], "register_entries": st["register_entries"], "records": st["records"]}
open(os.path.join(o.out, "data", "hub.js"), "w").write("window.HUB_DATA=" + json.dumps(data, ensure_ascii=False) + ";\n")
title = "Demo Production Hub (fictional)" if o.project else "Engineering Hub - Framework"
open(os.path.join(o.out, "index.html"), "w").write("""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{font-family:system-ui,sans-serif;color:#00405E;margin:2rem}</style></head>
<body><h1>%s</h1><p>Rebuild scaffold (v1.0 in progress). Gate: %d of %d checks passed. %d register entries, %d records.</p>
<script src="data/hub.js"></script></body></html>""" % (html.escape(title), html.escape(title), sum(r[2] for r in res), len(res), len(st["register_entries"]), len(st["records"])))
print("Site scaffold written to", o.out)
