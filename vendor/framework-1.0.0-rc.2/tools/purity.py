"""Framework purity (plan 2.4 step 6). On the store: framework records are hub FW and
hold no project data; project data adds no framework records. On a repository tree:
no workbook or personal files, no code that reads a workbook, no blocked terms.
Blocked terms are stored only as SHA-256 hashes so the list itself publishes nothing."""
import json, os, re, hashlib, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_ID = re.compile(r"\b[A-Z]{2,4}-(?!FW-)[A-Z]-\d{7}\b|\bPRJ-[A-Z]-\d{7}\b")
def blocked_hashes(): return set(json.load(open(os.path.join(HERE, "blocked_terms.sha256.json")))["sha256"])
def _h(s): return hashlib.sha256(s.encode()).hexdigest()
def blocked_hits(text, H):
    w = re.findall(r"[a-z0-9]+", text.lower()); hits = set()
    for n in (1, 2, 3):
        for i in range(len(w) - n + 1):
            g = " ".join(w[i:i+n])
            if _h(g) in H: hits.add(_h(g)[:12])
    return sorted(hits)
def store_checks(store, project_mode):
    res = []; H = blocked_hashes()
    def chk(name, ok, detail=""): res.append(("P", name, bool(ok), detail))
    fw = set(store["framework_records"]); R = [r for r in store["records"] if r["id"] in fw]
    bad = [r["id"] for r in R if r["hub"] != "FW" or PROJ_ID.search(json.dumps({k: v for k, v in r.items() if k != "id"}))]
    bad += [r["id"] for r in R if r["type"] == "Production Link" or (r["type"] == "Image" and r.get("view_kind") == "product")]
    fwe = [e for e in store["register_entries"] if e["id"] in set(store["framework_entries"])]
    bad += [e["id"] for e in fwe if PROJ_ID.search(json.dumps(e)) or "Tailoring" in e.get("source", "")]
    chk("Framework holds no project data: framework records are hub FW, reference no project record, include no Production Link or product view image (6.2, 6.10)", not bad, bad[:10])
    chk("No blocked (real programme or employer) term in framework data", not blocked_hits(json.dumps(R) + json.dumps(fwe), H))
    if project_mode:
        P = [r for r in store["records"] if r["id"] not in fw]
        pb = [r["id"] for r in P if r["hub"] == "FW" or "-FW-" in r["id"]]
        chk("Project data adds no framework record and edits none (framework changes only through Tailoring Records) (6.4, 1.8)", not pb, pb[:10])
        chk("No blocked (real programme or employer) term in project data", not blocked_hits(json.dumps(P), H))
        prj = [r for r in P if r["type"] == "Project"]
        chk("Demo project is marked fictional in its Project record (title and name) (plan constraints)", prj and all("fictional" in (r.get("title", "") + "|" + r.get("name", "")).lower().split("|")[0] and "fictional" in r.get("name", "").lower() for r in prj))
    return res
def tree_checks(root):
    res = []; H = blocked_hashes()
    def chk(name, ok, detail=""): res.append(("P", name, bool(ok), detail))
    try: files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root, capture_output=True, text=True, check=True).stdout.split()
    except Exception: files = [os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) if ".git" not in d for f in fs]
    wb = [f for f in files if re.search(r"\.(xlsx|xlsm|xls|ods|csv)$", f, re.I) or re.search(r"tracker|self.?assess|evidence_register", f, re.I)]
    chk("No workbook, tracker, self-assessment or Evidence file in the repository (decision 6)", not wb, wb)
    rd = []; hits = []
    for f in files:
        if f.endswith((".py", ".js", ".html", ".json", ".md", ".yml", ".yaml", ".css", ".txt", ".svg")) and os.path.isfile(os.path.join(root, f)):
            t = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
            if f.endswith((".py", ".js", ".yml")) and re.search(r"openpyxl|xlrd|pandas\.read_excel|load_workbook", t) and not f.endswith("purity.py"): rd.append(f)
            if not f.endswith("blocked_terms.sha256.json") and blocked_hits(t.replace("zqx canary programme", ""), H): hits.append(f)
    chk("No build tool reads a workbook (public builds never read the tracker workbook) (decision 6)", not rd, rd)
    chk("No blocked (real programme or employer) term in any repository file", not hits, hits)
    return res
