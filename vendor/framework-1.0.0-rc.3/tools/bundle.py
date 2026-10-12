"""Build the framework release bundle (plan 2.2, 5.3): one JSON file holding every
framework register entry and record, the schema version, deltas and a content hash.
Usage: bundle.py --version 1.0.0-rc.1 --out dist/framework-1.0.0-rc.1.json"""
import argparse, hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import load, validate
a = argparse.ArgumentParser(); a.add_argument("--version", required=True); a.add_argument("--out", required=True); o = a.parse_args()
fw = os.path.join(HERE, "..", "data", "framework")
res, _, st = validate.gate(fw, repo=os.path.join(HERE, ".."))
if not all(r[2] for r in res): print("Gate failed; no bundle."); sys.exit(1)
body = {"register_entries": sorted(st["register_entries"], key=lambda e: e["id"]), "records": sorted(st["records"], key=lambda r: r["id"])}
h = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
try: commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True).stdout.strip()
except Exception: commit = ""
meta = {"framework_version": o.version, "framework_version_record": "FV-FW-0000001", "schema_version": "7.6", "schema_deltas": ["R-15", "R-18", "v7 EDR, line items and link maturity", "v7.4 to v7.6 Users"],
        "content_hash": "sha256:" + h, "source_commit": commit, "counts": {"register_entries": len(body["register_entries"]), "records": len(body["records"])}}
os.makedirs(os.path.dirname(os.path.abspath(o.out)), exist_ok=True)
json.dump(dict(meta=meta, **body), open(o.out, "w"), indent=1, ensure_ascii=False)
print("Bundle", o.out, meta["content_hash"][:23], meta["counts"])
