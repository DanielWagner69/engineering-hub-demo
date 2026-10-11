"""Project D negative tests: the 43 carried from Worked Example v4 (neg4.py) plus new
cases for R-15, R-18, purity and schema. Each mutation must make the gate fail."""
import copy
CASES = []
def setlinks(r,t,targets): r["links"]=[l for l in r["links"] if l["link_type"]!=t]+[{"link_type":t,"target":x} for x in targets]
def stripgov(r,keep): r["links"]=[l for l in r["links"] if l["link_type"]!="Governs" or l["target"] in keep]
def add(J,base,new_id,typ,**kw):
    r=copy.deepcopy(base); r.update({"id":new_id,"type":typ}); r.update(kw); J["records"].append(r)
# v3 tests that still apply
CASES.append(('Remove VER-D-0000313 from the D-FUE-FED-004 statement', lambda I,J:I["CS-D-0001202"].__setitem__("evidence",["VER-D-0000301","VER-D-0000302"])))
CASES.append(('Extend VER-D-0000302 (bulkhead-union spool) back to effectivity 3', lambda I,J:I["VER-D-0000302"]["effectivity"].__setitem__("from",3)))
CASES.append(('D-PP-GEN-003 non-applicability approved by M. Ellis (Fuel Feed only)', lambda I,J:I["CS-D-0001207"].__setitem__("approved_by","user:m.ellis")))
CASES.append(('TSM-BIE evidence without the strainer qualification', lambda I,J:I["CS-D-0001210"].__setitem__("evidence",["VER-D-0000305"])))
CASES.append(('ACT-D-0000102 closure accepted by its owner', lambda I,J:I["ACT-D-0000102"]["closure"].__setitem__("accepted_by","user:p.hale")))
CASES.append(('Rev B range left open after rev C release', lambda I,J:I["FR-D-0000034"]["effectivity"].__setitem__("to",999)))
CASES.append(('Bulkhead-union spool numbered D2822004-002', lambda I,J:(I["PD-D-0000113"].__setitem__("part_number","D2822004-002"),I["PD-D-0000113"].__setitem__("dash","002"))))
CASES.append(('Checklist No (EF-C-02) without follow-up', lambda I,J:I["CK-D-0000012"].pop("follow_up")))
CASES.append(('R-01: Thermal Management break approved by the designer, P. Hale, not the Fuel Feed Design Lead', lambda I,J:I["FD-D-0000017"]["interface_breaks"][0].__setitem__("approved_by","user:p.hale")))
CASES.append(('R-01: Thermal Management break removed (no agreement recorded for that System)', lambda I,J:I["FD-D-0000017"].__setitem__("interface_breaks",[])))
CASES.append(('R-02: bonding evidence from effectivity 3 without the P-clamps (TSM-FLU 5.1)', lambda I,J:I["VER-D-0000312"].__setitem__("basis_revisions",[b for b in I["VER-D-0000312"]["basis_revisions"] if b!="PR-D-0000210"])))
CASES.append(('R-02: bolt GFS 1001-05-016 without Design Type Standard Part', lambda I,J:I["PD-D-0000110"].pop("design_type")))
CASES.append(('R-02 (OR rule): TSM-FLU System and Discipline tags removed, Pipework kept', lambda I,J:stripgov(I["TSM-D-0000065"],["VR-DTY-0009"])))
CASES.append(('R-02: joggle statement TSM-MET 4.2.3 claimed for the twin bracket without evidence', lambda I,J:I["CS-D-0001209"].__setitem__("statements_claimed",I["CS-D-0001209"]["statements_claimed"]+[{"clause":"4.2.3","parts":["PD-D-0000108"]}])))
CASES.append(('R-02: TSM-FZ non-applicability approved by A. Quinn (Design Authority for Design Types that do not reach it)', lambda I,J:I["CS-D-0001213"].__setitem__("approved_by","user:a.quinn")))
CASES.append(('R-04: Assembly Instance with no Build Station', lambda I,J:setlinks(I["AI-D-0000210"],"Located at",[])))
CASES.append(('R-04: bush within the Assembly Located at aircraft Build Station BS2', lambda I,J:setlinks(I["PI-D-0004106"],"Located at",["VR-BS-0006"])))
CASES.append(('R-06: mid-span clamp bolt homed in Brackets and Supports, not the Sub-system of the clamp it holds', lambda I,J:setlinks(I["PI-D-0004115"],"Homed in",["VR-SUB-0005"])))
CASES.append(('R-06: twin-bracket bolt without a Secures link', lambda I,J:setlinks(I["PI-D-0004113"],"Secures",[])))
CASES.append(('R-05: substantial assessment recorded against an undefined criterion', lambda I,J:I["CR-D-0000304"]["fdps_assessments"][0].__setitem__("criteria",["affects requirement compliance"])))
CASES.append(('R-07: valve control number D2822007-001 (made-part style)', lambda I,J:(I["PD-D-0000107"].__setitem__("part_number","D2822007-001"),I["PD-D-0000107"].__setitem__("dash","001"))))
CASES.append(('R-08: valve bracket stem from its own home System (D5112001)', lambda I,J:(I["PD-D-0000104"].__setitem__("part_number","D5112001-001"),I["PD-D-0000104"].__setitem__("stem","D5112001"))))
# new in v4
CASES.append(("R-09: Brackets and Supports Sub-structure page lists every System ('interfaces with all')", lambda I,J:I["PG-D-0000322"].__setitem__("interfaces",[e["id"] for e in J["register_entries"] if e["id"].startswith("VR-SYS")])))
CASES.append(('R-10: Fuel Feed page does not name the structure it attaches to', lambda I,J:I["PG-D-0000320"].__setitem__("interfaces",[s for s in I["PG-D-0000320"]["interfaces"] if s not in("VR-SYS-0001","VR-SYS-0002")])))
CASES.append(('R-09: FD-D-0000017 treated as a Sub-structure FDPS (lead Brackets and Supports), so the Sub-structure list flows to it', lambda I,J:I["FD-D-0000017"].__setitem__("lead_sub_system","VR-SUB-0005")))
CASES.append(('1.7.7: FD-D-0000017 lead Sub-system set to one in which none of its parts is homed', lambda I,J:I["FD-D-0000017"].__setitem__("lead_sub_system","VR-SUB-0012")))
CASES.append(('1.7.7: context FDPS without a lead Sub-system', lambda I,J:I["FD-D-0000009"].pop("lead_sub_system")))
CASES.append(("Role: FD-D-0000017 break approved by Y. Hart (Brackets and Supports), not its lead Sub-system's Design Lead", lambda I,J:I["FD-D-0000017"]["interface_breaks"][0].__setitem__("approved_by","user:y.hart")))
CASES.append(('Role: FD-D-0000009 break approved by M. Ellis, not the Frames and Bulkheads Design Lead', lambda I,J:I["FD-D-0000009"]["interface_breaks"][0].__setitem__("approved_by","user:m.ellis")))
CASES.append(('Role: FDPS Design Lead Role Assignment reinstated', lambda I,J:add(J,I["RA-D-0000009"],"RA-D-0000033","Role Assignment",area={"kind":"FDPS","ref":"FD-D-0000017"})))
CASES.append(('R-09: FD-D-0000009 breaks a System it does not inherit (Thermal Management)', lambda I,J:I["FD-D-0000009"].__setitem__("interface_breaks",I["FD-D-0000009"]["interface_breaks"]+[dict(I["FD-D-0000009"]["interface_breaks"][0],system="VR-SYS-0016")])))
CASES.append(('R-12: Secures link from the frame, which is not a Fastener Part', lambda I,J:setlinks(I["PI-D-0005001"],"Secures",["PI-D-0004105"])))
CASES.append(("R-12: cross-FDPS bolt Secures link missing from FD-D-0000017's stage C snapshot", lambda I,J:I["RS-D-0000003"]["content"].__setitem__("fdps_interfaces",[])))
CASES.append(('R-12: cross-FDPS Secures links not flagged to FD-D-0000017', lambda I,J:[J["records"].remove(I[x]) for x in ("RF-D-0003308","RF-D-0003309")]))
CASES.append(('R-11: Design Team page without its Disciplines', lambda I,J:I["PG-D-0000300"].__setitem__("applicable_disciplines",[])))
CASES.append(('R-14: whole-FDPS claim to TSM-FLU 5.4 without the routing inspection', lambda I,J:I["CS-D-0001211"].__setitem__("evidence",["VER-D-0000306","VER-D-0000312"])))
CASES.append(('R-14: whole-FDPS claim to a statement the TSM does not contain', lambda I,J:I["CS-D-0001211"]["statements_claimed"][1].__setitem__("clause","5.9")))
CASES.append(('R-13: Non-compliant statement without an Issue', lambda I,J:I["CS-D-0001205"].pop("issue")))
CASES.append(('R-13: Issue closed while effectivities 1 to 2 remain Non-compliant', lambda I,J:I["ISS-D-0000058"].__setitem__("status","Closed")))
CASES.append(('R-13: rev A released while its frozen D-FUE-FED-011 statement was Non-compliant', lambda I,J:I["CS-D-0001205"]["record_history"][0].__setitem__("position","Non-compliant")))
CASES.append(('R-13: rev B made effective back to effectivity 1, over the Non-compliant range', lambda I,J:I["FR-D-0000034"]["effectivity"].__setitem__("from",1)))
CASES.append(('R-13: Concession record held (Future Development)', lambda I,J:add(J,I["ISS-D-0000058"],"CON-D-0000001","Concession",links=[])))
CASES.append(('R-13: Compliance Statement references a Concession', lambda I,J:I["CS-D-0001205"].__setitem__("concession","CON-D-0000001")))
# ---- new in the rebuild: R-15 lead Sub-system
CASES.append(("R-15: FD-D-0000017 lead Sub-system approved by Y. Hart (Brackets and Supports), not a Fuel Feed Design Lead", lambda I,J: I["FD-D-0000017"]["lead_sub_system_approval"].__setitem__("approved_by","user:y.hart")))
CASES.append(("R-15: FD-D-0000009 without a lead Sub-system approval", lambda I,J: I["FD-D-0000009"].pop("lead_sub_system_approval")))
CASES.append(("R-15: FD-D-0000017 lead Sub-system set by the Frames Design Lead, outside the owning Fuel Sub-team", lambda I,J: I["FD-D-0000017"]["lead_sub_system_approval"].__setitem__("set_by","user:g.burns")))
def _lead_change(I, with_cr):
    f = I["FD-D-0000017"]; f["record_history"] = [dict(record_version=1, lead_sub_system="VR-SUB-0031", modified_at=f["created_at"])]; f["record_version"] = 2
    if with_cr:
        I["CR-D-0000304"]["change_types"] = I["CR-D-0000304"]["change_types"] + ["VR-CHG-0011"]; f["lead_sub_system_approval"]["change_record"] = "CR-D-0000304"
CASES.append(("R-15: lead Sub-system changed (Fuel Storage to Fuel Feed) with no Lead Sub-system change Change Record", lambda I,J: _lead_change(I, False)))
CASES.append(("R-15: lead Sub-system change recorded, but the existing Thermal Management break not flagged for re-confirmation", lambda I,J: _lead_change(I, True)))
# ---- R-18 cross-FDPS Secures flags
CASES.append(("R-18: cross-FDPS Secures flag decided 'No impact' instead of Accept or Query", lambda I,J: I["RF-D-0003308"].__setitem__("decision","No impact")))
CASES.append(("R-18: cross-FDPS Secures flag decided by the designer P. Hale, not FD-D-0000017's owner", lambda I,J: I["RF-D-0003309"].__setitem__("decided_by","user:p.hale")))
CASES.append(("R-18: a Query on a cross-FDPS flag closed while unresolved", lambda I,J: (I["RF-D-0003308"].__setitem__("decision","Query"), I["RF-D-0003308"].__setitem__("status","Closed"))))
def _confirm(I):
    for l in I["PI-D-0005002"]["links"]:
        if l["link_type"] == "Secures": l.setdefault("attributes", {})["confirmation_required"] = True
CASES.append(("R-18: cross-FDPS Secures link made to need confirmation by the other owner", lambda I,J: _confirm(I)))
CASES.append(("R-18: Accept used on an ordinary (non-interface) Review Flag", lambda I,J: I["RF-D-0003301"].__setitem__("decision","Accept")))
CASES.append(("R-18: cross-FDPS flag not marked as an FDPS-interface flag", lambda I,J: I["RF-D-0003308"].pop("fdps_interface")))
def _query_blocks(I):
    I["RF-D-0003309"]["decision"] = "Query"; I["RF-D-0003309"]["status"] = "Query"
    I["FR-D-0000035"]["gate_confirmation"]["blocked_by_flags"] = ["RF-D-0003309"]
CASES.append(("R-18: an open Query recorded as blocking the release gate", lambda I,J: _query_blocks(I)))
# ---- purity and schema
CASES.append(("Purity: a project record placed in the framework hub", lambda I,J: I["LL-D-0000031"].__setitem__("hub","FW")))
CASES.append(("Purity: blocked term (test canary) in project data", lambda I,J: I["ISS-D-0000058"].__setitem__("description", I["ISS-D-0000058"]["description"] + " Seen before on the zqx canary programme.")))
CASES.append(("Purity: Demo project no longer marked fictional", lambda I,J: I["PRJ-D-0000001"].update(name="Sparrow Light Trainer", title="Project D - Sparrow Light Trainer")))
CASES.append(("Schema: FDPS with an undefined status", lambda I,J: I["FD-D-0000009"].__setitem__("status","Frozen")))
CASES.append(("Schema: Part Instance existence without its upper bound", lambda I,J: I["PI-D-0004101"]["existence"].pop("to")))
CASES.append(("Schema: Review Flag decision outside the register", lambda I,J: I["RF-D-0003301"].__setitem__("decision","Ignored")))
CASES.append(("Example: Fuel Feed page loses Vehicle Management, so FD-D-0000017 no longer inherits 6 interfacing Systems", lambda I,J: I["PG-D-0000320"].__setitem__("interfaces",[s for s in I["PG-D-0000320"]["interfaces"] if s!="VR-SYS-0011"])))
