// Static data checks: node tests/check_data.js
const fs = require("fs"), vm = require("vm"), path = require("path");
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(__dirname, "../data/hub.js"), "utf8"), ctx);
const D = ctx.window.HUB_DATA, errs = [], byId = {};
D.pages.forEach(p => { if (byId[p.id]) errs.push("Duplicate ID " + p.id); byId[p.id] = p; });
const facets = D.facets.map(f => f.key);
D.pages.forEach(p => {
  Object.entries(p.tags || {}).forEach(([k, ids]) => {
    if (!facets.includes(k)) errs.push(p.id + ": unknown facet " + k);
    ids.forEach(id => { if (!byId[id]) errs.push(p.id + ": tag " + id + " not in taxonomy"); else if (byId[id].type !== k) errs.push(p.id + ": " + id + " is a " + byId[id].type + " not a " + k); });
  });
  const txt = [p.summary || ""].concat((p.sections || []).map(s => s.body)).join("\n");
  (txt.match(/\[\[([A-Z]{2,4}-[A-Z0-9]+)\]\]/g) || []).forEach(m => { const id = m.slice(2, -2); if (!byId[id]) errs.push(p.id + ": inline link " + id + " does not exist"); });
});
// Agreed-facet structure checks
D.pages.filter(p => p.type === "system").forEach(p => { if (!byId[p.group] || byId[p.group].type !== "sysgroup") errs.push(p.id + ": bad System Group " + p.group); });
D.pages.filter(p => p.type === "sysgroup").forEach(g => g.members.forEach(m => { if (!byId[m] || byId[m].group !== g.id) errs.push(g.id + ": member " + m + " inconsistent"); }));
D.pages.filter(p => p.type === "srcsystem").forEach(p => {
  const m = p.mapsTo || {}; if (!Object.keys(m).length) errs.push(p.id + ": tracker entry not mapped");
  Object.entries(m).forEach(([k, ids]) => ids.forEach(id => { if (!byId[id] || byId[id].type !== k) errs.push(p.id + ": maps to bad " + k + " " + id); }));
});
D.pages.forEach(p => (p.sources || []).forEach(id => { if (!byId[id] || byId[id].type !== "srcsystem") errs.push(p.id + ": bad source " + id); }));
D.pages.forEach(p => Object.keys(p.derived || {}).forEach(k => { if (!(p.tags || {})[k]) errs.push(p.id + ": derived note for untagged facet " + k); }));
D.pages.filter(p => p.type === "lesson" || p.type === "content").forEach(p => { if (!(p.tags.stage || []).length || !(p.tags.system || []).length) errs.push(p.id + ": mandatory stage/system tag missing"); if ((p.tags.sysgroup || []).length) errs.push(p.id + ": System Group must be derived, not stored"); });
// Facet levels: every facet has a level; views offered together share the level of their top facet
D.facets.forEach(f => { if (!f.level || !f.levelLabel) errs.push("facet " + f.key + " has no level"); });
const fl = Object.fromEntries(D.facets.map(f => [f.key, f.level])), grp = {};
D.views.forEach(v => { (grp[v.group] = grp[v.group] || []).push(fl[v.levels[0]]); });
Object.entries(grp).forEach(([g, ls]) => { if (new Set(ls).size > 1) errs.push("view group '" + g + "' mixes facet levels " + ls.join(",")); });
const srcCount = D.pages.filter(p => p.type === "srcsystem").length; if (srcCount !== 28) errs.push("expected 28 tracker Aircraft System entries, got " + srcCount);
D.issues.forEach(i => i.refs.forEach(id => { if (!byId[id]) errs.push(i.id + ": ref " + id + " missing"); }));
D.views.forEach(v => v.levels.forEach(l => { if (!facets.includes(l)) errs.push("view " + v.key + " level " + l); }));
// v0.6: images must exist in the site, with alt text and a caption; framework pages present; no production data in the framework
D.pages.forEach(p => (p.images || []).forEach(im => {
  if (!im.src || !fs.existsSync(path.join(__dirname, "..", im.src))) errs.push(p.id + ": image file missing " + im.src);
  if (!im.alt || !im.caption) errs.push(p.id + ": image needs alt text and caption");
}));
["HUB-FRAMEWORK", "HUB-PRODEX", "HUB-LESSONS", "HUB-ISSUES", "HUB-GLOSSARY", "HUB-BUILDLEVELS", "HUB-FINISH"].forEach(id => { if (!byId[id]) errs.push("missing hub page " + id); });
if (!["Framework","Production"].includes((D.meta || {}).hubKind)) errs.push("meta.hubKind must be Framework or Production");
if (D.meta.hubKind === "Production") {
  if (!D.meta.frameworkVersion) errs.push("Production Hub needs frameworkVersion");
  if (!D.production) errs.push("Production Hub needs production overlay");
  ["HUB-PROJECT","HUB-CONTACTS","HUB-AUTHORITY","HUB-MODEL","HUB-REQUIREMENTS","HUB-ITEMS","HUB-ISSUES-DEMO","HUB-FEEDBACK"].forEach(id => { if (!byId[id]) errs.push("missing demo page " + id); });
  (D.production.gaps || []).forEach(g => { if (!g.id || !g.title || !g.detail) errs.push("gap incomplete " + (g.id||"?")); });
  D.pages.filter(p => p.type === "item").forEach(p => {
    if ((p.tags.system || []).length !== 1 && !(p.derived && p.derived.system)) errs.push(p.id + ": item needs one home System (or derived)");
    ((p.supports || {}).system || []).forEach(id => { if ((p.tags.system || []).includes(id)) errs.push(p.id + ": supports repeats home System"); });
  });
  // sensitivity: no proficiency / self-assessment words in production overlay text
  const blob = JSON.stringify(D.production) + D.pages.filter(p => p.demo).map(p => JSON.stringify(p)).join("");
  ["proficien","self-assess","Self_Assessment","Evidence_Log"].forEach(w => { if (blob.toLowerCase().includes(w.toLowerCase())) errs.push("sensitive word in demo data: " + w); });
}
D.pages.forEach(p => { if (p.productionData) errs.push(p.id + ": production data is not allowed in the Framework Hub"); });
// v0.7 (requirements v13 decisions)
const of = t => D.pages.filter(p => p.type === t);
const dt = of("designtype").map(p => p.title);
if (dt.length !== 10) errs.push("expected 10 Design Types, got " + dt.length);
["DT-0011", "DT-0012", "DT-0013"].forEach(id => { if (byId[id]) errs.push(id + " is retired and must not be used"); });
if (dt.some(t => /standard|bought|coating/i.test(t))) errs.push("Design Type must not contain Standard Parts, Bought-in or Coatings");
const src = of("itemsource").map(p => p.title).join("|"); if (src !== "Make|Standard Part|Bought-in Equipment") errs.push("Source options wrong: " + src);
const mu = of("majorunit").map(p => p.title).join("|"); if (mu !== "Front Fuselage|Centre Fuselage|Rear Fuselage|Wings|Fins|Final Assembly") errs.push("Major Unit options wrong: " + mu);
of("majorunit").forEach(p => { if (JSON.stringify(p.scopes) !== '["PS-0001"]') errs.push(p.id + ": Major Unit must be Aircraft scope only"); });
const muView = D.views.find(v => v.key === "majorunit"); if (!muView || muView.fixedScope !== "PS-0001") errs.push("Major Unit view must be fixed to the Aircraft scope");
if (!D.views.find(v => v.key === "productscope")) errs.push("Product Scope view missing");
of("system").forEach(p => { if (!(p.scopes || []).length) errs.push(p.id + ": no applicable Product Scopes"); (p.scopes || []).forEach(id => { if (!byId[id] || byId[id].type !== "productscope") errs.push(p.id + ": bad scope " + id); }); });
const sc = id => (byId[id].scopes || []).join(",");
if (sc("SYS-0007") !== "PS-0001,PS-0002,PS-0004") errs.push("Fuel must apply to Aircraft, Ground Equipment, Facilities");
byId["SG-0006"].members.forEach(m => { if (sc(m) !== "PS-0001") errs.push(m + ": Mission Systems apply to Aircraft only"); });
D.facets.filter(f => ["sysgroup", "system"].includes(f.key)).forEach(f => { if (/level [12]/i.test(f.source + f.note)) errs.push(f.key + ": use upper tier / lower tier, not level 1 / level 2"); });
D.pages.filter(p => p.tags).forEach(p => {
  (p.all || []).forEach(k => { if (!facets.includes(k)) errs.push(p.id + ": 'all' for unknown facet " + k); if (p.recordKind !== "knowledge") errs.push(p.id + ": only knowledge records may be tagged All"); });
  ((p.supports || {}).system || []).forEach(id => { if (!byId[id] || byId[id].type !== "system") errs.push(p.id + ": supports link to non-System " + id); });
  const has = k => (p.tags && (p.tags[k] || []).length) || (p.all || []).includes(k);
  if (p.recordKind === "knowledge" && (!has("stage") || !has("system"))) errs.push(p.id + ": knowledge record lacks mandatory Lifecycle Stage / System");
  if ((p.tags.productscope || []).length) (p.tags.system || []).forEach(sid => { if (!(p.tags.productscope).some(ps => (byId[sid].scopes || []).includes(ps))) errs.push(p.id + ": System " + sid + " does not apply to any of its Product Scopes"); });
  if (p.exampleItem) { // items: exactly one option per facet
    Object.entries(p.exampleItem.tags).forEach(([k, id]) => { if (typeof id !== "string") errs.push(p.id + ": example item must take exactly one option for " + k); else if (!byId[id] || byId[id].type !== k) errs.push(p.id + ": example item bad " + k + " " + id); });
    if (p.exampleItem.tags.system && (p.exampleItem.supports || []).includes(p.exampleItem.tags.system)) errs.push(p.id + ": home System repeated as a supports link");
  }
});
const gl = (byId["HUB-GLOSSARY"] || {}).glossary || [], terms = gl.map(g => g[0].toLowerCase());
["data object", "item", "record", "page", "facet / option", "facet level", "build level", "tier", "data type", "link type"].forEach(t => { if (!terms.includes(t)) errs.push("glossary missing " + t); });
if (!/^0\.7/.test(D.meta.version)) errs.push("version should be 0.7");
const counts = {}; D.pages.forEach(p => counts[p.type] = (counts[p.type] || 0) + 1);
console.log("Pages:", JSON.stringify(counts), "Issues:", D.issues.length);
if (errs.length) { console.log("ERRORS:\n" + errs.join("\n")); process.exit(1); } else console.log("Data checks passed: all IDs unique, all tags and links resolve.");
