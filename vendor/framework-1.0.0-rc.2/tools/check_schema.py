"""Schema conformance of every record and register entry (plan 2.4 step 2)."""
import json, os
from schemalite import Schemas
def run(store, schema_dir):
    S = Schemas(schema_dir); idx = json.load(open(os.path.join(schema_dir, "index.json")))["types"]; bad = []
    for r in store["records"]:
        if r["type"] not in idx: bad.append((r["id"], "unknown data type " + r["type"])); continue
        for e in S.validate(r, {"$ref": idx[r["type"]]}, ""): bad.append((r["id"], e))
    for e in store["register_entries"]:
        for x in S.validate(e, {"$ref": "register_entry.schema.json"}, ""): bad.append((e["id"], x))
    return [("S", "Every record conforms to the schema of its data type, with the R-15 and R-18 deltas (2A.2, schema 1.8)", not [b for b in bad if not b[0].startswith("VR-")], [b for b in bad if not b[0].startswith("VR-")][:10]),
            ("S", "Every register entry conforms to the register entry schema (schema 2.1)", not [b for b in bad if b[0].startswith("VR-")], [b for b in bad if b[0].startswith("VR-")][:10])]
