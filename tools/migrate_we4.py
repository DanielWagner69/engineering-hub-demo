"""One-off migration of Worked Example v4 records into the Demo layout (plan 5.2):
framework-held records (Design Considerations, the promoted framework lesson) move to
the framework; Project D records are split by type; R-15 and R-18 deltas applied.
Usage: tools/migrate_we4.py <worked_example_records_v4.json> <framework data dir> <demo project dir>"""
import json, os, sys, collections, copy
src, fwdir, out = sys.argv[1:4]
J = json.load(open(src)); R = J["records"]; I = {r["id"]: r for r in R}
os.makedirs(os.path.join(out, "records"), exist_ok=True)
# 1. framework-held records: lesson to framework; Design Considerations come from the framework set
for r in R:
    if r["hub"] == "FW" and r["type"] == "Lesson Learned":
        json.dump(r, open(os.path.join(fwdir, "records", r["id"] + ".json"), "w"), indent=1, ensure_ascii=False)
fw_dc = {}
for f in os.listdir(os.path.join(fwdir, "considerations")):
    d = json.load(open(os.path.join(fwdir, "considerations", f))); fw_dc[d["id"]] = d
for r in R:
    if r["type"] == "Design Consideration":
        have = {i["item_id"]: i for c in fw_dc[r["id"]]["checklists"] for i in c["items"]}
        for c in r["checklists"]:
            for i in c["items"]:
                assert i["item_id"] in have, ("worked-example item missing from framework", i["item_id"])
                for k in ("question", "topic", "applies_to"):
                    assert have[i["item_id"]].get(k) == i.get(k), (i["item_id"], k)
proj = [r for r in R if r["hub"] != "FW"]
# 2. R-15: lead Sub-system set by the owning Sub-team, approved by a Design Lead of that Sub-system
APPROVAL = {"FD-D-0000017": ("user:r.okafor", "user:m.ellis"), "FD-D-0000009": ("user:g.burns", "user:g.burns")}
for r in proj:
    if r["type"] == "FDPS":
        sb, ab = APPROVAL[r["id"]]
        r["lead_sub_system_approval"] = {"set_by": sb, "set_at": r["created_at"], "approved_by": ab, "approved_at": r["created_at"]}
# 3. R-18: cross-FDPS Secures flags are decided Accept or Query by the other FDPS's owner
for r in proj:
    if r["type"] == "Review Flag" and r["via_link"].startswith("Secures (FDPS interface"):
        r["fdps_interface"] = True; r["decision"] = "Accept"; r["status"] = "Accept"
# 4. framework version reference
for r in proj:
    if r.get("framework_version") == "FV-FW-0000004": r["framework_version"] = "FV-FW-0000001"
# 5. project register entries: only the project's own access marking (Annex A lists come from the framework placeholders, TR-D-0000001)
regs = [{"id": "VR-ACCESS-0001", "register": "ACCESS_MARKING", "code": "D-GEN", "label": "Project D general (fictional)",
         "definition": "Fictional project marking for all Project D demo data.", "state": "Active", "source": "TR-D-0000001", "sort_order": 2, "is_catch_all": False}]
json.dump(regs, open(os.path.join(out, "register_entries.json"), "w"), indent=1)
by = collections.defaultdict(list)
for r in proj: by[r["type"]].append(r)
for t, rs in by.items():
    json.dump(sorted(rs, key=lambda x: x["id"]), open(os.path.join(out, "records", t.replace(" ", "_") + ".json"), "w"), indent=1, ensure_ascii=False)
meta = dict(J["meta"]); meta["conforms_to"] = "Data Schema - Draft v6 with R-15 and R-18 deltas"
meta["notes"] = [n for n in meta["notes"] if "Register entries listed are the subset" not in n] + [
    "Migrated from Worked Example v4 by tools/authoring/migrate_we4.py (12 Oct 2026). Register entries come from the pinned framework bundle.",
    "R-15: each FDPS records lead_sub_system_approval. R-18: cross-FDPS Secures flags carry fdps_interface true and a decision of Accept or Query."]
json.dump(meta, open(os.path.join(out, "project.json"), "w"), indent=1, ensure_ascii=False)
print({t: len(v) for t, v in by.items()}, len(proj))
