"""Framework-only negative tests: mutations of framework data that the gate must catch."""
import copy
def _add(st, base, **kw):
    r = copy.deepcopy(base); r.update(kw); st["records"].append(r); st["framework_records"].append(r["id"])
def _entry(I, i): return I[i]
CASES = [
 ("Purity: framework record placed in a project hub", lambda I, st: I["FV-FW-0000001"].__setitem__("hub", "PRJ-D-0000001")),
 ("Purity: framework lesson cites a project record", lambda I, st: I["LL-FW-0000040"].__setitem__("summary", I["LL-FW-0000040"]["summary"] + " See FD-D-0000017.")),
 ("Purity: Production Link held in the framework", lambda I, st: _add(st, I["FV-FW-0000001"], id="PL-FW-0000001", type="Production Link", title="Released drawing link")),
 ("Purity: blocked term (test canary) in a framework consideration", lambda I, st: I["DC-FW-0000001"].__setitem__("guidance", "As done on the zqx canary programme.")),
 ("Registers: second General Sub-system for Fuel", lambda I, st: st["register_entries"].append(dict(I["VR-SUB-0032"], id="VR-SUB-0999", code="9", is_catch_all=True))),
 ("Registers: Centre Fuselage Bench flag removed", lambda I, st: I["VR-BS-0031"].__setitem__("is_bench", False)),
 ("Registers: Discipline without a Discipline type", lambda I, st: I["VR-DISC-0026"].pop("discipline_type")),
 ("Registers: duplicate Discipline (Fluid Systems listed twice)", lambda I, st: st["register_entries"].append(dict(I["VR-DISC-0026"], id="VR-DISC-0027", code="FLU2"))),
 ("Registers: Sub-system parent does not resolve", lambda I, st: I["VR-SUB-0032"].__setitem__("parent", "VR-SYS-0099")),
 ("Registers: stage C aligned to Lifecycle Stage 7", lambda I, st: I["VR-STAGE-0003"].__setitem__("lifecycle_stage", "VR-LCS-0007")),
 ("Considerations: Weight consideration has no stage C checklist", lambda I, st: I["DC-FW-0000025"].__setitem__("checklists", I["DC-FW-0000025"]["checklists"][:2])),
 ("Considerations: duplicate checklist item id", lambda I, st: I["DC-FW-0000025"]["checklists"][0]["items"].append(dict(I["DC-FW-0000001"]["checklists"][0]["items"][0]))),
 ("Considerations: checklist item without a review state", lambda I, st: I["DC-FW-0000024"]["checklists"][1]["items"][0].pop("item_status")),
 ("Schema: Design Consideration with an unknown verification status", lambda I, st: I["DC-FW-0000003"].__setitem__("verification_status", "Approved")),
 ("Schema: register entry with an invalid state", lambda I, st: I["VR-SYS-0010"].__setitem__("state", "Gone")),
 ("Load: duplicate identifier", lambda I, st: st["register_entries"].append(dict(I["VR-SYS-0010"]))),
]
