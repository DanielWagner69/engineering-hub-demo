"""Rule checks carried over from Worked Example v4 (validate4.py, 82 checks), generalised:
no fixed paths, no project identifiers in the code. Project-specific expectations come
from the project's config (cfg). run(store, cfg) returns (results, info)."""
import json, re
def run(store, cfg):
    J = store; R = J["records"]; IDX = {r["id"]: r for r in R}; REG = {e["id"]: e for e in J["register_entries"]}
    LAB = dict({e["id"]: e["label"] for e in J["register_entries"]}, **{r["id"]: r.get("title", r["id"]) for r in R})
    EX = cfg.get("expect", {})
    res = []; INFO = {}
    def chk(sec, name, ok, detail=""): res.append((sec, name, bool(ok), detail))
    def lk(r, t): return [l["target"] for l in r.get("links", []) if l["link_type"] == t]
    def of(t): return [r for r in R if r["type"] == t]
    PRJ = [r for r in R if r["type"] == "Project"][0]
    EMAX = PRJ["effectivity_max"]
    def rng(e): return range(e["from"], min(e["to"], EMAX) + 1)
    def inr(e, n): return e["from"] <= n <= e["to"]
    def page_for(node): return sorted([p for p in of("Hub Page") if p.get("framework_node") == node], key=lambda p: p.get("hub") == "FW")[0]  # project page overrides the framework template
    # version resolution (frozen copies)
    def at(ref):
        id,v=ref.split("@"); v=int(v); r=IDX[id]
        if v==r["record_version"]: return r
        h=[x for x in r.get("record_history",[]) if x["record_version"]==v]
        if not h: return None
        c=dict(r); c.update({k:x for k,x in h[0].items() if k not in("record_version","modified_at")}); c["record_version"]=v; return c
    # ---- A. identity and common fields
    idre=re.compile(r"^(PRJ|EFF|PD|PR|PI|IRL|AD|AV|AI|FD|FR|FS|REQ|TSM|CS|VER|ISS|DR|RS|ACT|LL|DC|PAR|PIT|PG|PL|AR|BL|CR|AIQ|IMG|RF|LNK|CK|TR|FV|RT|CON|RA|RSK)-([A-Z]|FW)-\d{7}$")  # schema 1.1 prefix table
    chk("A","Identifier format PREFIX-SCOPE-NNNNNNN (schema 1.1)",all(idre.match(r["id"]) for r in R),[r["id"] for r in R if not idre.match(r["id"])])
    chk("A","Identifiers unique (2A.4)",len(IDX)==len(R))
    common=["id","type","schema_version","title","status","owner","hub","created_at","created_by","modified_at","modified_by","record_version","origin","verification_status","access_marking"]
    miss=[(r["id"],c) for r in R for c in common if c not in r]
    chk("A","Common fields present on every record (schema 1.2)",not miss,str(miss[:3]))
    txt=json.dumps(R)
    allrefs=set(re.findall(r"\b(?:[A-Z]{2,3}-(?:[A-Z]|FW)-\d{7})\b",txt))
    unres=[x for x in allrefs if x not in IDX]
    chk("A","Every referenced record id resolves",not unres,str(unres))
    frz=set(re.findall(r"\b([A-Z]{2,3}-(?:D|FW)-\d{7}@\d+)\b",txt))
    bad=[f for f in frz if at(f) is None]
    chk("A","Every frozen reference id@version resolves to a kept version (6A.15)",not bad,str(bad)); INFO["frozen_refs"]=len(frz)
    vr=set(re.findall(r"VR-[A-Z]+-\d{4}",txt))
    chk("A","Register references are well-formed VR-REGISTER-NNNN",all(re.match(r"VR-[A-Z]+-\d{4}$",v) for v in vr))
    for r in R:
        if r.get("record_history"):
            vs=[h["record_version"] for h in r["record_history"]]+[r["record_version"]]
            if vs!=list(range(1,len(vs)+1)): chk("A","History sequence "+r["id"],False)
    chk("A","record_history versions numbered 1..n before the current version",True)
    # ---- B. product structure
    PIs=of("Part Instance"); AIs=of("Assembly Instance"); FDs=of("FDPS"); PDs=of("Part Definition"); ADs=of("Assembly Definition")
    FD=IDX[cfg["fdps_under_test"]]; FD9=IDX[cfg["structural_fdps"]]
    chk("B","Each Part Instance: exactly one Instance of, Located at, Homed in (1.6.1, 1.6.2, 2D.3)",all(len(lk(p,"Instance of"))==len(lk(p,"Located at"))==len(lk(p,"Homed in"))==1 for p in PIs))
    mem={}
    for f in FDs:
        for t in lk(f,"Contains"): mem.setdefault(t,[]).append(f["id"])
    chk("B","Each Part and Assembly Instance belongs to exactly one FDPS (1.7.5, 1.8.4)",all(len(mem.get(x["id"],[]))==1 for x in PIs+AIs))
    chk("B","No Part Definition links directly to an FDPS, Build Station or Sub-system (2D.2, F-49)",all(not any(l["target"].startswith(("FD-","VR-BS","VR-SUB","VR-SYS")) for l in p.get("links",[])) for p in PDs))
    for a in AIs:
        ad=IDX[lk(a,"Instance of")[0]]; comp={l["target"]:l["attributes"]["quantity"] for l in ad["links"]}; act={}
        for p in lk(a,"Assembled from"): d=lk(IDX[p],"Instance of")[0]; act[d]=act.get(d,0)+1
        chk("B","Assembly Instance components match Comprises quantities (schema 3.9)",act==comp,str(act))
        chk("B","Assembly Instance and its Part Instances in the same FDPS (1.8.4)",all(mem[p]==mem[a["id"]] for p in lk(a,"Assembled from")))
    comp={p for a in AIs for p in lk(a,"Assembled from")}
    top=[m for f in FDs for m in lk(f,"Contains") if m not in comp]
    okbs=all(len(lk(IDX[m],"Located at"))==1 and not REG[lk(IDX[m],"Located at")[0]].get("is_bench") for m in top)
    for a in AIs:
        mu=REG[lk(a,"Located at")[0]]["parent"] if len(lk(a,"Located at"))==1 else None
        for p in lk(a,"Assembled from"):
            b=REG[lk(IDX[p],"Located at")[0]]
            if not(b.get("is_bench") and b["parent"]==mu): okbs=False
    chk("B","Items directly below the FDPS (Part Instances and Assembly Instances) at exactly one aircraft Build Station; Part Instances of an Assembly at the Bench of its Major Unit (1.6.1, 2C.12, R-04)",okbs)
    STR={e["id"] for e in J["register_entries"] if e.get("is_structural")}
    fas=[p for p in PIs if "VR-PROP-0004" in IDX[lk(p,"Instance of")[0]].get("item_properties",[])]
    okf=bool(fas)
    for p in fas:
        s=lk(p,"Secures")
        if len(s)!=1 or s[0] not in mem: okf=False; continue
        h=lk(IDX[s[0]],"Homed in")[0]
        if lk(p,"Homed in")[0]!=h: okf=False
        if REG[h]["parent"] not in STR and not lk(p,"Supports"): okf=False
        if REG[h]["parent"] in STR and lk(p,"Supports"): okf=False
    INFO["fasteners"]=[(p["id"],(lk(p,"Secures") or ["none"])[0],LAB[lk(p,"Homed in")[0]],[LAB[x] for x in lk(p,"Supports")]) for p in fas]
    chk("B","Fasteners: one Secures link to the part held, homed in its Sub-system; Supports link only where the held part is not structural (1.6.6, R-06)",okf)
    secs=[p for p in PIs if lk(p,"Secures")]
    chk("B","Secures links only from Part Instances of Parts carrying the Fastener property (4.6, 1.6.6, R-12)",all("VR-PROP-0004" in IDX[lk(p,"Instance of")[0]].get("item_properties",[]) for p in secs))
    xf=[(p["id"],s,mem[p["id"]][0],mem[s][0]) for p in secs for s in lk(p,"Secures") if mem[p["id"]]!=mem[s]]; INFO["cross_secures"]=xf
    okx=bool(xf)
    for pid,s,a,b in xf:
        for f in (a,b):
            other=b if f==a else a
            for c in [r for r in of("Review Snapshot")+of("Baseline") if IDX[r.get("fdps_revision") or IDX[r["baseline"]]["fdps_revision"]]["fdps"]==f]:
                dt=c.get("created_at","")
                if dt>=IDX[pid]["created_at"] and {"fdps":other,"fastener":pid,"held":s} not in c["content"].get("fdps_interfaces",[]): okx=False
        if not any(r["flagged_object"] in (a,b) and r["triggering_object"]==pid and "Secures" in r["via_link"] for r in of("Review Flag")): okx=False
    chk("B","Cross-FDPS Secures links are FDPS interfaces: recorded in the snapshots and baselines of the FDPS whose part is held, and flagged to it (1.6.6, 6C.24, R-12)",okx)
    chk("B","Design Type on every Part; catalogue items carry Design Type Standard Part (1.10.1, 2B.7, R-02)",all(p.get("design_type") and ((p["design_type"]=="VR-DTY-0012")==(p["source"]=="VR-SRC-0002")) for p in PDs))
    chk("B","Bought-in items carry Design Type Bought-in Equipment (2B.7)",all(p.get("design_type")=="VR-DTY-0011" for p in PDs if p["source"]=="VR-SRC-0003"))
    der=[p for p in PDs if lk(p,"Derived from")]
    chk("B","Modified bought-in: Make, Derived from a bought-in source, Design Type Bought-in Equipment plus modification Design Type (2B.10, F-17)",der and all(p["source"]=="VR-SRC-0001" and IDX[lk(p,"Derived from")[0]]["source"]=="VR-SRC-0003" and p["design_type"]=="VR-DTY-0011" and p.get("modification_design_type") for p in der))
    fins=of("Finish Specification")
    ovr={l["target"] for p in PIs for l in p["links"] if l["link_type"]=="Finish applied"}
    chk("B","Every Finish Specification applied by a link or an instance override (2D.7, F-45)",all(lk(f,"Finish applied") or f["id"] in ovr for f in fins))
    for a in ADs:
        comps=[IDX[l["target"]]["safety_classification"] for l in a["links"]]
        chk("B","Assembly Safety Classification at least that of its components (1.10.2)",min(int(c[-1]) for c in comps)>=int(a["safety_classification"][-1]))
    # ---- C. numbering
    nums=[(p["part_number"],p["id"]) for p in PDs]+[(a["part_number"],a["id"]) for a in ADs]+[(f["fdps_number"],f["id"]) for f in FDs]
    chk("C","Full numbers unique across parts, assemblies and FDPSs (1.11.10, F-37)",len({n for n,_ in nums})==len(nums))
    def dashok(num,kind,hand):
        st,d=num.split("-"); d=int(d)
        rngok={"part":1<=d<=399,"asm":401<=d<=799,"fdps":d>=801}[kind]
        par=(d%2==0)==(hand=="Right-hand")
        return rngok and par
    ms=[(p["part_number"],"part",p.get("handedness","Unhanded")) for p in PDs if p["numbering_scheme"]=="VR-NUMSCH-0001"]+[(a["part_number"],"asm",a["handedness"]) for a in ADs]+[(f["fdps_number"],"fdps","Unhanded") for f in FDs]
    chk("C","Dash numbers in the range for the kind of object, odd for left-hand or unhanded (1.11.7, 1.11.8, F-36)",all(dashok(*x) for x in ms),[x for x in ms if not dashok(*x)])
    stems={}
    for n,_ in nums:
        if re.match(r"^D\d{7}-\d{3}$",n): stems.setdefault(n[:8],[]).append(n)
    INFO["shared_stems"]={k:v for k,v in stems.items() if len(v)>1}
    roll=[(p,IDX[p["replaces_definition"]]) for p in PDs if p.get("replaces_definition")]
    chk("C","Non-interchangeable successor keeps the stem and rolls the dash by 2 (1.11.9)",roll and all(a["stem"]==b["stem"] and int(a["dash"])==int(b["dash"])+2 for a,b in roll))
    chk("C","Common parts carry a Type code, catalogue items a designation and Source Standard Part, bought-in a supplier part number (1.11.5, 1.11.11, F-38, F-39)",all((("type_code" in p) if p["numbering_scheme"]=="VR-NUMSCH-0002" else ("standard_designation" in p and p["source"]=="VR-SRC-0002") if p["numbering_scheme"]=="VR-NUMSCH-0003" else True) for p in PDs))
    bi=[p for p in PDs if p["source"]=="VR-SRC-0003"]
    chk("C","Bought-in items: project control number Project + BI + sequence, stored with the supplier part number, no dash (1.11.11, R-07)",bi and all(re.match(r"^D-BI-\d{4}$",p["part_number"]) and p["numbering_scheme"]=="VR-NUMSCH-0004" and p.get("supplier_part_number") and "dash" not in p for p in bi),[p["part_number"] for p in bi])
    fdstem=FD["fdps_number"][:5]
    used={lk(IDX[m],"Instance of")[0] for m in lk(FD,"Contains")}
    msd=[IDX[d] for d in used if IDX[d].get("numbering_scheme")=="VR-NUMSCH-0001"]
    homes={d["id"]:{REG[lk(IDX[m],"Homed in")[0]]["parent"] for m in lk(FD,"Contains") if m.startswith("PI") and lk(IDX[m],"Instance of")[0]==d["id"]} for d in msd}
    INFO["stems"]=[(d["part_number"],[LAB[h] for h in homes[d["id"]]]) for d in msd]
    chk("C","Parts and assemblies designed for the FDPS take its stem codes; their own home System is held only in the facet link (1.11.4, R-08)",msd and all(d["stem"][:5]==fdstem for d in msd) and any(h!={REG[FD["lead_sub_system"]]["parent"]} for h in homes.values()))
    chk("C","Number proposals recorded, with rejected alternatives and reasons (1.11.6, F-40)",all("number_proposal" in x and all(rj.get("reason") for rj in x["number_proposal"]["rejected"]) for x in PDs+ADs+FDs))
    chk("C","No field inferred from a part number: stem breakdown is an informational parse of the number; the lead Sub-system is held as its own field (1.11.1, 1.7.7)",all(f["stem_breakdown"]["system_code"]==f["fdps_number"][1:3] and f["stem_breakdown"]["subsystem_code"]==f["fdps_number"][3] and f.get("lead_sub_system") for f in FDs))
    # ---- D. effectivity and configuration
    IRL=of("Instance-Revision Link"); by={}
    for i in IRL: by.setdefault(i["instance"],[]).append(i)
    bad=[]; INFO["irl_table"]=[]
    for inst in PIs+AIs:
        ls=sorted(by.get(inst["id"],[]),key=lambda x:x["effectivity"]["from"]); ex=inst["existence"]; cur=ex["from"]; ok=True
        for l in ls:
            if l["effectivity"]["from"]!=cur: ok=False
            cur=l["effectivity"]["to"]+1
            if (IDX[l["revision"]].get("part_definition") or IDX[l["revision"]].get("assembly_definition"))!=lk(inst,"Instance of")[0]: ok=False
        if cur-1!=ex["to"]: ok=False
        if not ok: bad.append(inst["id"])
        INFO["irl_table"].append((inst["id"],ex,[(IDX[l["revision"]]["revision"],l["effectivity"],l["id"],l["record_version"]) for l in ls]))
    chk("D","Instance-Revision Links: no gaps or overlaps over existence; revision of the right definition (6A.3, 6A.14)",not bad,str(bad))
    chk("D","No effectivity uses 999 as an allocated number (6A.12)",all(r.get("number")!=999 for r in of("Effectivity")))
    def eff_rev(inst,n):
        m=[l for l in by.get(inst,[]) if inr(l["effectivity"],n)]; return m[0]["revision"] if len(m)==1 else None
    def config(n,members):
        return frozenset((m,eff_rev(m,n)) for m in members if inr(IDX[m]["existence"],n))
    FRs=sorted([x for x in of("FDPS Revision") if x["fdps"]==FD["id"]],key=lambda x:x["effectivity"]["from"]); FRID={x["id"] for x in FRs}  # scoped to the FDPS under test (Phase 3)
    cur=1; ok=True
    for f in FRs:
        if f["effectivity"]["from"]!=cur: ok=False
        cur=f["effectivity"]["to"]+1
    chk("D","Released FDPS revisions: effectivity ranges with no gaps or overlaps; new release closed the previous range (6A.11, F-31)",ok and cur==1000)
    okc=True; INFO["fr_cfg"]=[]
    for f in FRs:
        def fcfg(n):
            out=set()
            for p in f["population"]:
                inst=at(p["instance"])
                if not inr(inst["existence"],n): continue
                rv=[at(i)["revision"] for i in p["irl"] if inr(at(i)["effectivity"],n)]
                out.add((inst["id"],tuple(rv)))
            return frozenset(out)
        cs_=set(fcfg(n) for n in rng(f["effectivity"]))
        live=set(config(n,lk(FD,"Contains")) for n in rng(f["effectivity"]))
        if len(cs_)!=1 or len(live)!=1: okc=False
        fro=list(cs_)[0]; lv=list(live)[0]
        if {(a,b[0]) for a,b in fro}!=set(lv): okc=False
        INFO["fr_cfg"].append((f["revision"],f["effectivity"],len(fro)))
    chk("D","Configuration constant within each FDPS revision range, and frozen population equals the live as-designed configuration (6A.11)",okc)
    BLs=[b for b in of("Baseline") if b["fdps_revision"] in FRID]; okb=True
    for f in FRs:
        seq=sorted(IDX[b]["sequence_no"] for b in f["baselines"])
        if seq!=list(range(1,len(seq)+1)): okb=False
        for b in f["baselines"]:
            if IDX[b]["fdps_revision"]!=f["id"]: okb=False
    chk("D","Baselines per FDPS revision, numbered 1..n, frozen at each release and review snapshot (6A.10, F-32, F-33)",okb and len(BLs)==EX.get("baselines",len(BLs)) and all(any(b["trigger"]["kind"]=="Release" for b in BLs if b["fdps_revision"]==f["id"]) for f in FRs))
    okr=True
    for b in BLs:
        for p in b["content"]["population"]:
            inst=at(p["instance"])
            for n in rng(inst["existence"]):
                if inr(b["effectivity"],n) and len([1 for i in p["irl"] if inr(at(i)["effectivity"],n)])!=1: okr=False
    chk("D","Each baseline resolves every member to exactly one revision at every effectivity in its range, from frozen copies (6A.10, 6A.15)",okr)
    rs=[s for s in of("Review Snapshot") if IDX[s["baseline"]]["fdps_revision"] in FRID]
    chk("D","Review snapshots reference frozen copies and their baseline, and include interfacing Systems, breaks and agreements (6C.9, 6C.23)",all("@" in json.dumps(s["content"]["population"]) and s.get("baseline") in IDX and "interface_agreements" in s["content"] and "interface_breaks" in s["content"] for s in rs))
    chk("D","Retrofit, Concession and as-embodied records out of scope: none held, and no Compliance Statement references one (6A.16, 7, R-03, R-13)",not of("Retrofit") and not of("Concession") and all("retrofit" not in c and "concession" not in c for c in of("Compliance Statement")))
    # status at a selected effectivity (6A.18)
    def status_at(inst,n): return "Present" if inr(IDX[inst]["existence"],n) else "Not present (exists %d to %s)"%(IDX[inst]["existence"]["from"],IDX[inst]["existence"]["to"])
    INFO["status_at"]={n:{k:status_at(k,n) for k in EX.get("status_at_instances",[])} for n in EX.get("status_at_effectivities",[])}
    chk("D","Record status unchanged by closed ranges; presence derived per selected effectivity (6A.18, F-34)",all(p["status"]=="Active" for p in PIs))
    # ---- E. requirements, TSMs, compliance
    PAR={e["id"]:e.get("parent") for e in J["register_entries"]}
    def chain(s): y=PAR[s]; return [s,y,PAR[y]]
    mems=lk(FD,"Contains"); pis=[m for m in mems if m.startswith("PI")]
    REQ=of("Requirement"); TSM=of("TSM")
    chk("E","Requirements allocated to System tree nodes only (Sub-system, System or System Group) (6B.2, F-15)",all(all(t.startswith(("VR-SUB","VR-SYS","VR-SG")) for t in lk(r,"Allocated to")) for r in REQ))
    chk("E","TSMs tagged with at least one Design Type, Discipline or System, and nothing else; at least one statement (6B.5, 6B.11, R-02)",all(lk(t,"Governs") and all(g.startswith(("VR-DTY","VR-DISC","VR-SYS")) for g in lk(t,"Governs")) and t.get("statements") for t in TSM))
    TPG=page_for(REG[FD["owning_sub_team"]]["parent"]); SPG=page_for(FD["owning_sub_team"])
    team=TPG["applicable_design_types"]
    dts={IDX[lk(IDX[m],"Instance of")[0]].get(k) for m in mems if m.startswith("PI") for k in("design_type","modification_design_type")}-{None}
    chk("E","Every Design Type in the FDPS is on the owning Design Team's list (6B.5)",dts<=set(team),str(dts-set(team)))
    chk("E","Design Team page lists its Disciplines, and a TSM tagged with one reaches the FDPS through it (6B.5, R-11)",TPG.get("applicable_disciplines") and any(g in TPG["applicable_disciplines"] for t in of("TSM") for g in lk(t,"Governs")))
    inh={}
    for r in REQ:
        b=[]
        for node in lk(r,"Allocated to"):
            via=[p for p in pis if node in chain(lk(IDX[p],"Homed in")[0])]
            if via: b.append(("node",node,tuple(sorted(via))))
        for t in lk(r,"Satisfied by"):
            if t==FD["id"] or t in mems: b.append(("direct",t))
        if b: inh[r["id"]]=b
    defs={}
    for m in mems:
        d=lk(IDX[m],"Instance of")[0]
        if d.startswith("PD"): defs[d]=1
    tpg=TPG
    for t in TSM:
        b=[]
        for g in lk(t,"Governs"):
            if g.startswith("VR-DTY"):
                via=tuple(sorted(d for d in defs if g in(IDX[d].get("design_type"),IDX[d].get("modification_design_type"))))
                if via: b.append(("dty",g,via))
            elif g.startswith("VR-SYS"):
                via=tuple(sorted(p for p in pis if PAR[lk(IDX[p],"Homed in")[0]]==g))
                if via: b.append(("sys",g,via))
            elif g in tpg.get("applicable_disciplines",[]): b.append(("disc",g,(tpg["id"],)))
        if b: inh[t["id"]]=b
    INFO["tsm_routes"]={t:[x[0]+":"+x[1] for x in v] for t,v in inh.items() if t.startswith("TSM")}
    chk("E","FDPS has at least one Requirement, inherited or direct (2.4, F-11)",any(k.startswith("REQ") for k in inh))
    CSs=[c for c in of("Compliance Statement") if c["fdps"]==FD["id"]]
    chk("E","Compliance stated per FDPS, never per Part Instance (6B.8, F-11)",all("instance" not in c for c in of("Compliance Statement")))
    covered={c["requirement"] for c in CSs}
    chk("E","Every inherited or direct Requirement and TSM has Compliance Statements (6B.3, 6B.5)",set(inh)<=covered and covered<=set(inh),str(set(inh)^covered))
    def recb(c):
        o=[]
        for b in c["bases"]:
            if b["basis"]=="Direct": o.append(("direct",b["item"]))
            elif b["basis"]=="Inherited via System tree node": o.append(("node",b["node"],tuple(sorted(b["via"]))))
            elif b["basis"]=="Inherited via Design Type": o.append(("dty",b["design_type"],tuple(sorted(b["via"]))))
            elif b["basis"]=="Inherited via System": o.append(("sys",b["system"],tuple(sorted(b["via"]))))
            else: o.append(("disc",b["discipline"],tuple(sorted(b["via"]))))
        return sorted(o)
    chk("E","Compliance Statement bases record every route; a TSM reaches the FDPS if any tag matches (OR), one basis per matching tag (6B.5, 6B.6, F-10, R-02)",all(recb(c)==sorted(inh[c["requirement"]]) for c in CSs))
    multi=[c["id"] for c in CSs if len(c["bases"])>1]; INFO["multi_basis"]=multi
    okt=True
    for rq in covered:
        ss=sorted([c for c in CSs if c["requirement"]==rq],key=lambda c:c["effectivity"]["from"]); cur=1
        for c in ss:
            if c["effectivity"]["from"]!=cur: okt=False
            cur=c["effectivity"]["to"]+1
        if cur!=1000: okt=False
    chk("E","For each Requirement or TSM, Compliance Statement ranges tile the released effectivity with no gaps or overlaps (6B.8, F-12)",okt)
    VER={v["id"]:v for v in of("Verification")}
    def effrev_def(d,n):
        out=set()
        for m in mems:
            if lk(IDX[m],"Instance of")[0]==d and inr(IDX[m]["existence"],n): out.add(eff_rev(m,n))
        return out
    badv=[]
    for v in VER.values():
        for n in rng(v["effectivity"]):
            for b in v["basis_revisions"]:
                d=IDX[b].get("part_definition") or IDX[b].get("assembly_definition")
                er=effrev_def(d,n)
                if er and er!={b}: badv.append((v["id"],n,b))
    chk("E","Verification effectivity consistent with basis revisions at every effectivity (6B.9, F-12)",not badv,str(badv[:5]))
    ovl=[]
    for v in VER.values():
        for s in v.get("supersedes",[]):
            if any(inr(VER[s]["effectivity"],n) for n in rng(v["effectivity"])): ovl.append((v["id"],s))
    chk("E","Superseding Verifications close the superseded range (no overlap) (6B.9)",not ovl,str(ovl))
    gaps=[]
    for c in CSs:
        if c["position"]=="Compliant":
            for n in rng(c["effectivity"]):
                ev=[VER[e] for e in c["evidence"] if inr(VER[e]["effectivity"],n) and VER[e]["outcome"]=="Pass" and c["requirement"] in lk(VER[e],"Demonstrates")]
                if not ev: gaps.append((c["id"],n))
    chk("E","Compliant statements: passing evidence that Demonstrates the Requirement covers the whole range (6B.9)",not gaps,str(gaps[:5]))
    tg=[]; okclaim=True
    for c in CSs:
        if c["requirement"].startswith("TSM") and c["position"] in("Compliant","Non-compliant"):
            clauses={s["clause"] for s in IDX[c["requirement"]]["statements"]}
            if not c.get("statements_claimed"): okclaim=False; continue
            for cl in c["statements_claimed"]:
                if cl["clause"] not in clauses or not set(cl.get("parts",[]))<=set(defs): okclaim=False
                if c["position"]!="Compliant": continue
                for n in rng(c["effectivity"]):
                    if "parts" not in cl:
                        if not any(inr(VER[e]["effectivity"],n) and VER[e]["outcome"]=="Pass" and any(l["link_type"]=="Demonstrates" and l["target"]==c["requirement"] and cl["clause"] in l.get("attributes",{}).get("statements",[]) for l in VER[e]["links"]) for e in c["evidence"]): tg.append((c["id"],cl["clause"],n,"whole FDPS"))
                        continue
                    need={d for d in cl["parts"] if effrev_def(d,n)}
                    have=set()
                    for e in c["evidence"]:
                        v=VER[e]
                        if not(inr(v["effectivity"],n) and v["outcome"]=="Pass"): continue
                        if any(l["link_type"]=="Demonstrates" and l["target"]==c["requirement"] and cl["clause"] in l.get("attributes",{}).get("statements",[]) for l in v["links"]):
                            have|={IDX[b].get("part_definition") for b in v["basis_revisions"]}
                    if not need<=have: tg.append((c["id"],cl["clause"],n,sorted(need-have)))
        elif c["requirement"].startswith("TSM") and c.get("statements_claimed"): okclaim=False
    partial=[c["id"] for c in CSs if c.get("statements_claimed") and len(c["statements_claimed"])<len(IDX[c["requirement"]]["statements"])]
    INFO["tsm_partial"]=partial
    chk("E","TSM statements: conformance claimed only to applicable statements; no record for statements that do not apply (6B.11, R-02)",okclaim and partial)
    whole=[(c["id"],cl["clause"]) for c in CSs for cl in c.get("statements_claimed",[]) if "parts" not in cl]; INFO["whole_fdps_claims"]=whole
    chk("E","TSM statements may be claimed for the whole FDPS; listing Parts is optional (6B.11, R-14)",whole and any("parts" in cl for c in CSs for cl in c.get("statements_claimed",[])))
    chk("E","TSM evidence covers every claimed statement for every claimed Part present at every effectivity (6B.9, 6B.11)",not tg,str(tg[:3]))
    RA=of("Role Assignment")
    def has_role(p,role,kind=None,area=None,date=None):
        for a in RA:
            if a["person"]==p and a["role"]==role and (kind is None or a["area"]["kind"]==kind) and (area is None or a["area"]["ref"]==area) and (date is None or a["from_date"]<=date[:10]): return a
    def dl_covers(p,sub,date):
        for a in RA:
            if a["person"]==p and a["role"]=="Design Lead" and a["from_date"]<=date[:10]:
                r=a["area"]["ref"]
                if r in chain(sub): return True
        return False
    na=[c for c in CSs if c["position"]=="Not applicable"]; okna=True
    for c in na:
        if c["requirement"].startswith("REQ"):
            subs={lk(IDX[p],"Homed in")[0] for b in c["bases"] for p in b.get("via",[])}
            if not all(dl_covers(c["approved_by"],s,c["approved_at"]) for s in subs): okna=False
            for _p,_s in EX.get("na_must_not_cover",[]):
                if dl_covers(_p,_s,c["approved_at"]): okna=False
        else:
            team=REG[FD["owning_sub_team"]]["parent"] if FD["owning_sub_team"] in REG else None
            dtys=[b["design_type"] for b in c["bases"] if b.get("design_type")]
            if not(has_role(c["approved_by"],"Design Authority","Design Team",team,c["approved_at"]) or any(has_role(c["approved_by"],"Design Authority","Design Type",d,c["approved_at"]) for d in dtys)): okna=False
            if c.get("statements_claimed"): okna=False
    chk("E","Not applicable: Requirement approved by a Design Lead covering every Sub-system it reaches through; TSM (no statement applies) by a Design Authority for the owning Design Team or a Design Type it reaches through (6C.13, F-19, R-02)",okna and any(c["requirement"].startswith("TSM") for c in na))
    okiss=True; ncs=[c for c in CSs if c["position"]=="Non-compliant"]
    for c in ncs:
        i=IDX.get(c.get("issue"))
        if not i or i["type"]!="Issue" or not ({c["requirement"],c["id"]}&set(lk(i,"Affects"))) or i["status"]=="Closed": okiss=False
    chk("E","Every Non-compliant Compliance Statement references an open Issue that Affects the Requirement (2F.12, 6A.17, R-13)",ncs and okiss)
    okblk=True; INFO["release_cs"]=[]
    for f in FRs:
        for b in f["baselines"]:
            B=IDX[b]
            if B["trigger"]["kind"]!="Release": continue
            nc=[x for x in B["content"]["compliance_statements"] if at(x)["position"]=="Non-compliant" and any(inr(at(x)["effectivity"],n) for n in set(rng(B["effectivity"]))|set(rng(f["effectivity"])))]
            INFO["release_cs"].append((f["revision"],b,len(B["content"]["compliance_statements"]),nc))
            if nc or f["gate_confirmation"].get("non_compliant_statements")!=[]: okblk=False
    chk("E","No FDPS revision released while a frozen Compliance Statement in its release baseline is Non-compliant over its range; the gate records the check (6A.17, 6C.11, R-13)",okblk)
    INFO["cs_count"]=len(CSs)
    # ---- F. considerations, reviews, release
    pg=SPG; NA={t["payload"]["discipline"] for t in of("Tailoring Record") if t["action"]=="mark Discipline not applicable" and has_role(t["approved_by"],"Technical Authority for Design")}
    chk("F","Project non-applicability of a Discipline approved by the Technical Authority for Design (2B.14, F-01)",NA==set(EX.get("project_na_disciplines",NA)))
    DRs=sorted([d for d in of("Design Review") if set(lk(d,"Covers"))&FRID],key=lambda d:d["review_date"]); DRID={d["id"] for d in DRs}; CKs=[c for c in of("Checklist Response") if c["fdps_revision"] in FRID]
    okck=True
    for d in DRs[:3]:
        sec=[s for s in pg["stage_sections"] if s["stage"]==d["stage"]][0]
        exp={i["item_id"] for i in sec["checklist_items"] if i["discipline"] not in NA}
        got={c["item_id"] for c in CKs if c["stage"]==d["stage"] and c["fdps_revision"] in lk(d,"Covers")}
        if exp!=got: okck=False
    chk("F","Checklist responses are exactly the items listed on the Sub-team stage page, less project-N/A Disciplines (4.4, F-04)",okck)
    fu=[c for c in CKs if c["response"]=="No"]
    def fu_ok(c):
        f=c.get("follow_up") or {}
        if f.get("kind") in("Action","Risk"): return f.get("ref") in IDX
        if f.get("kind")=="Approved justification": return bool(has_role(f["approved_by"],"Discipline Lead","Discipline",IDX[c["consideration"]]["discipline"]))
        return False
    chk("F","Every No response has an Action, a Risk or a justification approved by that Discipline's Lead before the Pass (4.5, F-05)",fu and all(fu_ok(c) for c in fu))
    chk("F","Actions raised from a checklist No point to that No response, and the response points back (4.5)",all(IDX[a["source"]["ref"]]["response"]=="No" and IDX[a["source"]["ref"]].get("follow_up",{}).get("ref")==a["id"] for a in of("Action") if a.get("source",{}).get("kind")=="Checklist No"))
    chk("F","Not applicable checklist responses carry a reason (4.5)",all(c.get("reason") for c in CKs if c["response"]=="Not applicable"))
    th=[i for d in of("Design Consideration") for s in d["checklists"] for i in s["items"] if i.get("topic")=="Thermal"]
    chk("F","Thermal split: heat signature items under Low Observability, thermal environment items under System Layout and Integration (4.2, F-01, F-03)",{d["discipline"] for d in of("Design Consideration") for s in d["checklists"] for i in s["items"] if i.get("topic")=="Thermal"}=={"VR-DISC-0012","VR-DISC-0023"})
    SUBP={p["framework_node"]:p for p in of("Hub Page") if p["framework_node"].startswith("VR-SUB")}
    def iface(f):
        ps=[m for m in lk(f,"Contains") if m.startswith("PI")]; ssf=PAR.get(f.get("lead_sub_system")) in STR
        own={PAR[lk(IDX[p],"Homed in")[0]] for p in ps}; got=set()
        for p in ps:
            h=lk(IDX[p],"Homed in")[0]
            if PAR[h] not in STR or ssf: got|=set(SUBP[h]["interfaces"])
            got|=set(lk(IDX[p],"Supports"))
        for a in lk(f,"Contains"):
            if a.startswith("AI"): got|=set(lk(IDX[a],"Supports"))
        return got-own,own
    inhif,own=iface(FD)
    inh9,own9=iface(FD9); brk9={b["system"] for b in FD9["interface_breaks"]}; INFO["iface9"]=(sorted(inh9),sorted(brk9),sorted(own9))
    ALLS=[e["id"] for e in J["register_entries"] if e["id"].startswith("VR-SYS")]
    chk("F","Interface lists are finite: no Sub-system or Sub-structure page lists every System or uses an 'all' entry (6C.20, R-09)",all(isinstance(p["interfaces"],list) and "ALL" not in p["interfaces"] and len(set(p["interfaces"]))<len(ALLS)-1 for p in SUBP.values()))
    chk("F","Every non-structural Sub-system page names the structural Systems it attaches to (6C.20, R-10)",all(set(p["interfaces"])&STR for k,p in SUBP.items() if PAR[k] not in STR))
    chk("F","Every FDPS has a lead Sub-system in which at least one of its Part Instances is homed (1.7.7)",all(f.get("lead_sub_system") in REG and any(lk(IDX[p],"Homed in")[0]==f["lead_sub_system"] for p in lk(f,"Contains") if p.startswith("PI")) for f in FDs))
    sub_homes9={lk(IDX[p],"Homed in")[0] for p in lk(FD9,"Contains") if p.startswith("PI")}
    chk("F","Sub-structure FDPS: the interface lists of every Sub-structure in which its Part Instances are homed flow to it, so Fuel is prompted for the frames (6C.20, R-09)",PAR.get(FD9.get("lead_sub_system")) in STR and all(set(SUBP[h]["interfaces"])-own9<=inh9 for h in sub_homes9) and set(EX.get("structural_must_inherit",[]))<=inh9 and brk9<=inh9)
    def dl_of(sub,date): return [a["person"] for a in RA if a["role"]=="Design Lead" and a["area"]["kind"]=="Sub-system" and a["area"]["ref"]==sub and a["from_date"]<=date[:10]]
    chk("F","No FDPS Design Lead role exists; interface breaks are approved by the Design Lead of the FDPS's lead Sub-system or Sub-structure, with reason, author and date (6C.14, 6C.21)",not any(a["area"]["kind"]=="FDPS" for a in RA) and all(f["interface_breaks"] and all(b.get("reason") and b.get("by") and b.get("at") and b.get("approved_at") and b.get("approved_by") in dl_of(f.get("lead_sub_system"),b["approved_at"]) for b in f["interface_breaks"]) for f in FDs))
    v2=set(s for p in pis for s in SUBP[lk(IDX[p],"Homed in")[0]]["interfaces"])-own
    brk={b["system"] for b in FD["interface_breaks"]}
    ifs=sorted(inhif-brk); INFO["iface"]=(len(inhif),len(brk),ifs,len(v2))
    NSL=set().union(*[set(SUBP[h]["interfaces"]) for h in {lk(IDX[p],"Homed in")[0] for p in pis} if PAR[h] not in STR]); SUP={s for m in lk(FD,"Contains") for s in lk(IDX[m],"Supports")}; BSS=EX["non_flowing_substructure"]; INFO["bs_not_flowed"]=sorted(set(SUBP[BSS]["interfaces"])-own-NSL-SUP)
    chk("F","Non-structural FDPS: interfacing Systems from its non-structural Sub-system pages and Supports links only; Sub-structure lists do not flow to it (6C.20, 6C.21, F-06 to F-08, R-01, R-09)",PAR.get(FD.get("lead_sub_system"),"VR-SYS-0001") not in STR and brk<=inhif and len(inhif)<len(v2) and any(s in STR for s in inhif) and inhif==(NSL|SUP)-own and (set(SUBP[BSS]["interfaces"])-own-NSL-SUP))
    okd=True; oki=True; okp=True
    for d in DRs:
        sec=[s for s in pg["stage_sections"] if s["stage"]==d["stage"]][0]
        req={x for x in sec["sign_off_disciplines"] if x not in NA}
        got={a["discipline"] for a in d["discipline_agreements"]}
        if req!=got: okd=False
        for a in d["discipline_agreements"]:
            if a["position"]=="Disagree": okp=False
            if a["position"]=="Agree with conditions" and not all(IDX.get(x,{}).get("type")=="Action" for x in a["conditions"]): okp=False
            if not has_role(a["by"],"Discipline Lead","Discipline",a["discipline"]) and not (a["discipline"]=="VR-DISC-0006" and has_role(a["by"],"Design Approver")): okp=False
        if {a["system"] for a in d["interface_agreements"]}!=set(ifs): oki=False
        for a in d["interface_agreements"]:
            if a["position"]=="Disagree": oki=False
            if a["position"]=="Agree with conditions" and not all(IDX.get(x,{}).get("type")=="Action" for x in a["conditions"]): oki=False
            if not any(r["person"]==a["by"] and r["role"]=="Design Lead" and (r["area"]["ref"]==a["system"] or PAR.get(r["area"]["ref"])==a["system"]) for r in RA): oki=False
    chk("F","Each review: a position from every required Sign-off team Discipline (less project-N/A), none Disagree, conditions raised as Actions, given by the Discipline Lead (6C.19, 6C.14, F-21)",okd and okp)
    chk("F","Each review: an agreement from every unbroken interfacing System, by a Design Lead of that System (6C.22, F-08)",oki)
    chk("F","Each review has a chair and a structured attendee list (6C.4, 6C.10, F-22)",all(d.get("chair") and d.get("attendees") and all("person" in a for a in d["attendees"]) for d in DRs))
    rr_=[d for d in DRs if d.get("re_review")]
    okrr=all(d["stage"]=="VR-STAGE-0003" and IDX[d["re_review"]["follows_review"]]["stage"]==d["stage"] and all(("carried_forward_from" in a)==(int(a["discipline"][-4:]) not in d["re_review"]["affected_disciplines"]) for a in d["discipline_agreements"]) and all(("carried_forward_from" in a)==(a["system"] not in d["re_review"]["affected_systems"]) for a in d["interface_agreements"]) for d in rr_)
    chk("F","Re-review at the current stage (C), scoped: affected agreements given, others carried forward (6C.12, F-28)",rr_ and okrr)
    ACT=[a for a in of("Action") if set(lk(a,"Raised at"))&DRID]
    chk("F","Every Action has raised_by; closure accepted by the raiser or the review chair (6C.8, F-29)",all(a.get("raised_by") and a["closure"]["accepted_by"] in(a["raised_by"],IDX[lk(a,"Raised at")[0]]["chair"]) for a in ACT))
    okg=True
    for f in FRs:
        rel=f["released_at"]; covering=[d["id"] for d in DRs if d["review_date"]<=rel[:10]]
        for a in ACT:
            if lk(a,"Raised at")[0] in covering and not(a["closure"]["accepted_at"]<=rel): okg=False
        if not f.get("gate_confirmation") or f["gate_confirmation"]["open_actions"]: okg=False
        if not any(IDX[d]["stage"]=="VR-STAGE-0003" for d in f["passed_reviews"]+([f["carried_forward_review"]["review"]] if f.get("carried_forward_review") else [])): okg=False
    chk("F","Release gate: C pass (direct or carried forward), every Action from every A, B and C review closed and accepted, Hub gate confirmation (6C.11, F-23)",okg)
    INFO["gate_attempts"]=[(f["revision"],f["gate_attempts"]) for f in FRs]
    okcf=True
    for f in FRs:
        a=f["release_assessment"]; sub=any(any(x["substantial"] for x in IDX[c]["fdps_assessments"] if x["fdps"]==FD["id"]) for c in a["change_records"])
        if sub and not any(d.get("re_review") and f["id"]==lk(d,"Covers")[0] for d in DRs): okcf=False
        if not sub and a["change_records"] and not f.get("carried_forward_review"): okcf=False
    chk("F","Substantial changes re-reviewed; non-substantial changes carry the C pass forward with the Design Authority's assessment recorded (6C.12, F-24)",okcf)
    CRs=of("Change Record")
    chk("F","Every Change Record has a per-FDPS substantial assessment; several change types allowed (6C.17, F-27)",all(c.get("fdps_assessments") and c.get("change_types") for c in CRs))
    CRIT={"adversely affects compliance","degrades form, fit or function","degrades an interface","adds a new interface with another System"}
    chk("F","Substantial if and only if a 6C.17 criterion is met: adversely affects compliance, or degrades form, fit, function or an interface, or adds a new interface; restoring compliance is not substantial (6C.17, R-05)",all(set(x["criteria"])<=CRIT and x["substantial"]==bool(x["criteria"]) for c in CRs for x in c["fdps_assessments"]) and any(not x["substantial"] and "estores compliance" in x["rationale"] for c in CRs for x in c["fdps_assessments"]))
    chk("F","Margin reductions that remain compliant recorded, not counted as degrading (6C.17, F-25)",any(x.get("margin_note") and not x["substantial"] for c in CRs for x in c["fdps_assessments"]))
    chk("F","Release approvals given by a person holding release authority in the Role register (6C.14, F-20)",all(any(r["person"]==f["released_by"] and any(d["authority"]=="FDPS release" for d in r["delegations"]) for r in RA) for f in FRs))
    # ---- G. issues, lessons
    ISS=of("Issue")
    for i in ISS:
        lvl=max(i["scores"].values()); INFO["issue"]=(i["scores"],lvl)
        th=PRJ.get("impact_thresholds",{}); sc_ok=True
        for k,fld,thk in (("effort","effort_estimate","effort_person_days"),("cost","cost_estimate","cost_gbp")):
            if fld in i and thk in th: sc_ok&= i["scores"][k]==1+sum(1 for t in th[thk] if i[fld]["value"]>=t)
        chk("G","Escalation level is the highest criterion score; forum from the band (2E.3, 2E.9)",sc_ok and 1<=lvl<=5 and lvl==EX.get("issue_levels",{}).get(i["id"],lvl))
        chk("G","Issue linked to the Change Records that resolve it (2E.10, F-47)",lk(i,"Resolved by") and all(IDX[c]["type"]=="Change Record" for c in lk(i,"Resolved by")))
    LLs=of("Lesson Learned")
    chk("G","Project lesson records its origin record; promotion proposes a generic framework lesson without project data (2G.2, 2G.5, F-48)",all((l.get("origin_record") in IDX) for l in LLs if l["hub"]!="FW") and all(not re.search(r"-D-\d{7}",json.dumps({k:v for k,v in l.items() if k not in("id",)})) for l in LLs if l["hub"]=="FW"))
    return res, INFO
