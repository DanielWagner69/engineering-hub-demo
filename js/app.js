/* Engineering Hub – Production (Demo) on Framework v0.8. Framework pages mirrored read-only;
   production overlay is entirely fictional demo data. */
(function () {
  "use strict";
  var D = window.HUB_DATA;
  if (!D) { document.getElementById("page").innerHTML = "<p>Data file data/hub.js not loaded.</p>"; return; }

  // ---------- indexes ----------
  var byId = {}, facetByKey = {}, viewByKey = {};
  D.pages.forEach(function (p) { byId[p.id] = p; });
  D.facets.forEach(function (f) { facetByKey[f.key] = f; });
  D.views.forEach(function (v) { viewByKey[v.key] = v; });
  var TYPE_LABEL = { stage: "Lifecycle Stage", sysgroup: "System Group", system: "System", designtype: "Design Type", productscope: "Product Scope", majorunit: "Major Unit", itemsource: "Source",
    discipline: "Discipline", skill: "Skill", trait: "Trait", srcsystem: "Tracker source entry", content: "Topic (example)", lesson: "Lesson Learned", special: "Hub page",
    prodrecord: "Production record", item: "Part Instance", requirement: "Requirement", verification: "Verification", issue: "Issue", finish: "Finish Specification" };
  var IS_PROD = (D.meta || {}).hubKind === "Production";
  var PROD = D.production || {};
  var FRAMEWORK_URL = (D.meta || {}).frameworkUrl || "https://danielwagner69.github.io/engineering-hub/";
  var TYPE_COLOUR = {};
  Object.keys(TYPE_LABEL).forEach(function (k) { TYPE_COLOUR[k] = "var(--" + k + ")"; });
  var TAG_FACETS = ["stage", "productscope", "majorunit", "system", "designtype", "itemsource", "discipline", "skill", "trait"]; // stored tags
  var SHOW_FACETS = ["stage", "productscope", "majorunit", "sysgroup", "system", "designtype", "itemsource", "discipline", "skill", "trait"]; // incl. derived
  var LL_FACETS = ["stage", "productscope", "system", "designtype", "discipline"];
  var HUB_PAGES = [["HUB-GLOSSARY", "special"], ["HUB-BUILDLEVELS", "special"], ["HUB-FINISH", "special"], ["HUB-FRAMEWORK", "special"], ["HUB-PRODEX", "special"]];

  function valuesOf(facet) { return D.pages.filter(function (p) { return p.type === facet; }).sort(function (a, b) { return a.order - b.order; }); }
  var contents = D.pages.filter(function (p) { return p.type === "content"; });
  var lessons = D.pages.filter(function (p) { return p.type === "lesson"; });
  var demoItems = D.pages.filter(function (p) { return p.type === "item"; });
  var demoReqs = D.pages.filter(function (p) { return p.type === "requirement"; });
  var demoVers = D.pages.filter(function (p) { return p.type === "verification"; });
  var demoIssues = D.pages.filter(function (p) { return p.type === "issue"; });
  var demoProds = D.pages.filter(function (p) { return p.type === "prodrecord"; });
  var demoFinishes = D.pages.filter(function (p) { return p.type === "finish"; });
  var items = contents.concat(lessons, demoItems, demoReqs, demoVers, demoIssues, demoProds, demoFinishes);

  function refsInText(t) { var out = [], re = /\[\[([A-Z]{2,4}-[A-Z0-9]+)\]\]/g, m; while ((m = re.exec(t || ""))) out.push(m[1]); return out; }
  // Knowledge records may carry several options per facet, or "All" (p.all lists the facets tagged with every option).
  function isAll(p, k) { return !!(p.all && p.all.indexOf(k) >= 0); }
  function rawTags(p, k) { return isAll(p, k) ? valuesOf(k).map(function (v) { return v.id; }) : (p.tags && p.tags[k]) || []; }
  function storedTags(p) { var o = []; TAG_FACETS.forEach(function (k) { rawTags(p, k).forEach(function (id) { o.push(id); }); }); return o; }
  // Derived tags: System Group comes from the System tag(s); never stored.
  function derivedGroups(p) { var g = []; rawTags(p, "system").forEach(function (s) { var grp = byId[s] && byId[s].group; if (grp && g.indexOf(grp) < 0) g.push(grp); }); return g; }
  function tagsOf(p, k) { return k === "sysgroup" ? derivedGroups(p) : rawTags(p, k); }
  function supportsOf(p) { return (p.supports && p.supports.system) || []; }
  // System applicability: each System records the Product Scopes it applies to
  function sysApplies(sysId, scope) { var s = byId[sysId]; return !scope || !s || !s.scopes || s.scopes.indexOf(scope) >= 0; }
  function allTags(p) { return storedTags(p).concat(derivedGroups(p)); }

  // Explicit outgoing links (tags, inline references, structural links), used for backlinks
  var outLinks = {};
  D.pages.forEach(function (p) {
    var s = storedTags(p).concat(refsInText(p.summary));
    (p.sections || []).forEach(function (sec) { s = s.concat(refsInText(sec.body)); });
    if (p.group) s.push(p.group);
    (p.members || []).forEach(function (m) { s.push(m); });
    (p.sources || []).forEach(function (m) { s.push(m); });
    supportsOf(p).forEach(function (m) { s.push(m); });
    (p.scopes || []).forEach(function (m) { s.push(m); });
    Object.keys(p.mapsTo || {}).forEach(function (k) { s = s.concat(p.mapsTo[k]); });
    outLinks[p.id] = s;
  });
  outLinks["HUB-ISSUES"] = [].concat.apply([], D.issues.map(function (i) { return i.refs; }));
  var backlinks = {};
  Object.keys(outLinks).forEach(function (src) { outLinks[src].forEach(function (t) { if (t !== src) (backlinks[t] = backlinks[t] || {})[src] = true; }); });

  function taggedWith(id) { return items.filter(function (c) { return allTags(c).indexOf(id) >= 0; }); }

  // ---------- helpers ----------
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function scopeOn() { return state.scope && viewByKey[state.view].scopeSelectable; }
  function href(id, ctx) { var h = "#/p/" + encodeURIComponent(id) + "?v=" + state.view + (scopeOn() ? "&s=" + state.scope : ""); if (ctx && ctx.length) h += "&c=" + ctx.map(encodeURIComponent).join(","); return h; }
  function link(id, ctx) { var p = byId[id]; if (!p) return '<span class="warn">Broken link: ' + esc(id) + "</span>"; return '<a href="' + href(id, ctx) + '">' + esc(p.title) + "</a>"; }
  function chip(id, extraCls) { var p = byId[id]; if (!p) return '<span class="chip c-special">missing ' + esc(id) + "</span>"; return '<a class="chip c-' + p.type + (extraCls ? " " + extraCls : "") + '" href="' + href(id) + '" title="' + esc(TYPE_LABEL[p.type]) + '"><span class="cid">' + esc(p.id) + "</span>" + esc(p.title) + "</a>"; }
  function rich(t) {
    var html = "", list = false;
    String(t || "").split("\n").forEach(function (line) {
      var l = esc(line).replace(/\[\[([A-Z]{2,4}-[A-Z0-9]+)\]\]/g, function (_, id) { return link(id); });
      if (/^- /.test(line)) { if (!list) { html += "<ul>"; list = true; } html += "<li>" + l.slice(2) + "</li>"; }
      else { if (list) { html += "</ul>"; list = false; } if (line.trim()) html += "<p>" + l + "</p>"; }
    });
    if (list) html += "</ul>";
    return html;
  }
  function figures(list) {
    if (!list || !list.length) return "";
    return list.map(function (im) {
      return '<figure class="hub-fig"><button type="button" class="fig-open" data-src="' + esc(im.src) + '" data-alt="' + esc(im.alt) + '" data-caption="' + esc(im.caption) + '" aria-label="Enlarge image: ' + esc(im.alt) + '">' +
        '<img src="' + esc(im.src) + '" alt="' + esc(im.alt) + '" loading="lazy"><span class="fig-zoom" aria-hidden="true">\u2922 Enlarge</span></button><figcaption>' + esc(im.caption) + "</figcaption></figure>";
    }).join("");
  }
  function formatEffectivity(eff) {
    if (eff == null || eff === "") return "\u2014";
    if (typeof eff === "string") return esc(eff);
    var t = eff.type || "", fr = eff.from || "", to = eff.to || "", notes = eff.notes || "";
    var label = t === "serial range" ? "Serial" : t === "build standard" ? "Build std" : t === "configuration" ? "Config" : esc(t);
    var range = fr && to ? (fr === to ? esc(fr) : esc(fr) + "\u2013" + esc(to)) : esc(fr || to || "");
    return '<span class="eff" title="' + esc(notes || t) + '"><span class="eff-type">' + label + "</span> " + range +
      (notes ? ' <span class="eff-notes">(' + esc(notes) + ")</span>" : "") + "</span>";
  }
  function scopesFromAffects(affects, issuePage) {
    var scopes = [], seen = {};
    function add(ps) { if (ps && !seen[ps]) { seen[ps] = 1; scopes.push(ps); } }
    (affects || []).forEach(function (id) {
      var o = byId[id]; if (!o) return;
      (o.tags && o.tags.productscope || []).forEach(add);
    });
    // Knowledge Issues may also carry Product Scope tags directly (several or All)
    if (issuePage && issuePage.tags) (issuePage.tags.productscope || []).forEach(add);
    return scopes;
  }
  function reqCell(ids) {
    ids = ids || [];
    if (!ids.length) return '<span class="empty">\u2014</span>';
    return ids.map(function (id) {
      var r = byId[id];
      if (!r) return '<span class="warn">' + esc(id) + "</span>";
      return '<a href="' + href(id) + '" class="req-link"><span class="mono">' + esc(id) + "</span> " + esc(r.title.length > 48 ? r.title.slice(0, 46) + "\u2026" : r.title) + "</a>";
    }).join("<br>");
  }
  function prodLinksSection(p) {
    var what = TYPE_LABEL[p.type].toLowerCase();
    var ids = p.productionLinks || [];
    var head = "<h2>Production data links</h2>";
    var thead = '<div class="table-wrap"><table class="list prod-links"><thead><tr><th>Production record</th><th>Type</th><th>Requirement</th><th>Current master</th><th>Version / issue</th><th>Baseline</th><th>Effectivity</th><th>Status</th></tr></thead>';
    if (!(typeof IS_PROD !== "undefined" && IS_PROD) || !ids.length) {
      // Framework (or empty): show schema headers; empty body
      if (!(typeof IS_PROD !== "undefined" && IS_PROD)) {
        return head + '<p class="section-note">In a project\'s Production Hub this table lists the production records linked to this ' + esc(what) +
          ' (models, calculations, test records), each under configuration control, with the Requirement it supports and structured effectivity. The Framework Hub holds no production data. See ' + link("HUB-FRAMEWORK") + ".</p>" +
          thead + '<tbody><tr><td colspan="8" class="empty-row"><span class="ph-tag">EMPTY IN FRAMEWORK</span>No production data. A Production Hub would show linked records here with Requirement (ID + title), version, baseline and structured effectivity (serial range, build standard or configuration).</td></tr></tbody></table></div>';
      }
      return head + '<p class="section-note">Production records linked to this ' + esc(what) + ".</p>" +
        thead + '<tbody><tr><td colspan="8" class="empty-row"><span class="ph-tag">EMPTY</span>No production records linked.</td></tr></tbody></table></div>';
    }
    var rows = ids.map(function (id) {
      var r = byId[id]; if (!r) return "";
      var st = r.status === "Verified" || r.status === "Released" ? "Resolved" : r.status === "In work" ? "Open" : "Partlyresolved";
      return "<tr><td>" + link(id) + ' <span class="mono nid">' + esc(id) + "</span></td><td>" + esc(r.recType) + "</td><td>" + reqCell(r.requirements) +
        "</td><td>" + esc(r.master) + '</td><td class="mono">' + esc(r.version) + "</td><td>" + esc(r.baseline) +
        "</td><td>" + formatEffectivity(r.effectivity) + '</td><td><span class="status s-' + st + '">' + esc(r.status) + "</span></td></tr>";
    }).join("");
    return head + '<p class="section-note">Demo production records linked to this ' + esc(what) +
      ". Requirement column links to the Requirement each record supports. Effectivity is structured (type, from, to). Current master from the " +
      (byId["HUB-AUTHORITY"] ? link("HUB-AUTHORITY") : "authority register") + ". All records are fictional.</p>" + thead + "<tbody>" + rows + "</tbody></table></div>";
  }
  function ph(text) { return '<div class="ph"><span class="ph-tag">PLACEHOLDER</span>' + esc(text) + "</div>"; }

  // ---------- state & routing ----------
  var state = { view: "lifecycle", route: "home", id: null, ctx: [], query: "", filter: [], scope: "" };
  try { var saved = window.localStorage && localStorage.getItem("eh-view"); if (saved && viewByKey[saved]) state.view = saved; } catch (e) {}

  function parseHash() {
    var h = (location.hash || "#/home").slice(1), q = {}, path = h, i = h.indexOf("?");
    if (i >= 0) { path = h.slice(0, i); h.slice(i + 1).split("&").forEach(function (kv) { var a = kv.split("="); q[a[0]] = decodeURIComponent(a[1] || ""); }); }
    if (q.v && viewByKey[q.v]) state.view = q.v;
    var parts = path.split("/").filter(Boolean);
    state.scope = q.s && byId[q.s] && byId[q.s].type === "productscope" ? q.s : "";
    state.filter = q.f ? q.f.split(",").filter(function (x) { return byId[x]; }) : [];
    state.ctx = q.c ? q.c.split(",").filter(function (x) { return byId[x]; }) : [];
    if (parts[0] === "p" && parts[1]) { state.route = "page"; state.id = decodeURIComponent(parts[1]); }
    else if (parts[0] === "f" && parts[1]) { state.route = "facet"; state.id = parts[1]; }
    else { state.route = "home"; state.id = null; }
    try { localStorage.setItem("eh-view", state.view); } catch (e) {}
  }
  function setView(v) {
    state.view = v;
    var h = location.hash || "#/home";
    h = h.replace(/([?&])v=[a-z]+/, "$1v=" + v).replace(/[?&]c=[^&]*/, "");
    if (!/[?&]v=/.test(h)) h += (h.indexOf("?") >= 0 ? "&" : "?") + "v=" + v;
    location.hash = h;
  }

  // ---------- tree (generated from tags, any number of levels) ----------
  var expanded = {};
  function buildLevel(levels, pool, ctx, scope) {
    if (!levels.length) return pool.map(function (c) { return { id: c.id, ctx: ctx, key: ctx.concat([c.id]).join("/"), children: [] }; });
    var facet = levels[0], rest = levels.slice(1), vals = valuesOf(facet);
    var sc = ctx.filter(function (id) { return byId[id].type === "productscope"; })[0] || scope || "";
    if (facet === "system") { // under a System Group, show only its member Systems; only Systems that apply to the scope
      var g = ctx.filter(function (id) { return byId[id].type === "sysgroup"; })[0];
      if (g) vals = vals.filter(function (s) { return s.group === g; });
      vals = vals.filter(function (s) { return sysApplies(s.id, sc); });
    }
    if (facet === "sysgroup" && sc) vals = vals.filter(function (g) { return g.members.some(function (m) { return sysApplies(m, sc); }); });
    var shown = vals.map(function (v) { return v.id; });
    var nodes = vals.map(function (v) {
      var sub = pool.filter(function (c) { return allTags(c).indexOf(v.id) >= 0; });
      return { id: v.id, ctx: ctx, key: ctx.concat([v.id]).join("/"), count: sub.length, children: buildLevel(rest, sub, ctx.concat([v.id]), scope) };
    });
    // records with no tag among the options shown at this level are listed directly, so nothing disappears from a view
    pool.filter(function (c) { return !tagsOf(c, facet).some(function (id) { return shown.indexOf(id) >= 0; }); }).forEach(function (c) { nodes.push({ id: c.id, ctx: ctx, key: ctx.concat([c.id]).join("/"), children: [] }); });
    return nodes;
  }
  // Product Scope (facet level 0) is selectable at the top of views whose top facet sits at facet level 1; fixedScope views use one scope
  function buildTree(viewKey, scope) {
    var v = viewByKey[viewKey], sc = v.fixedScope || (scope === undefined ? (v.scopeSelectable ? state.scope : "") : scope);
    var pool = sc ? items.filter(function (c) { return tagsOf(c, "productscope").indexOf(sc) >= 0; }) : items;
    return buildLevel(v.levels, pool, [], sc);
  }
  function registerTree() {
    var cats = {}, order = [];
    valuesOf("trait").forEach(function (t) { if (!cats[t.category]) { cats[t.category] = []; order.push(t.category); } cats[t.category].push(t); });
    function leaf(p) { return { id: p.id, ctx: [], key: "reg/" + p.id, children: [] }; }
    return [
      { label: "Product Scope", facet: "productscope", key: "reg/ps", children: valuesOf("productscope").map(leaf) },
      { label: "Source", facet: "itemsource", key: "reg/src-facet", children: valuesOf("itemsource").map(leaf) },
      { label: "Major Unit (Aircraft scope)", facet: "majorunit", key: "reg/mu", children: valuesOf("majorunit").map(leaf) },
      { label: "Skills Register", facet: "skill", key: "reg/skill", children: valuesOf("skill").map(leaf) },
      { label: "Traits Register", facet: "trait", key: "reg/trait", children: order.map(function (c) { return { label: c, key: "reg/trait/" + c, children: cats[c].map(leaf) }; }) },
      { label: "Tracker Aircraft Systems (source)", facet: "srcsystem", key: "reg/src", children: valuesOf("srcsystem").map(leaf) }
    ];
  }
  function sameCtx(a, b) { return a.join(",") === b.join(","); }
  function markExpanded(nodes, parents) {
    nodes.forEach(function (n) {
      if (n.id && n.id === state.id && (sameCtx(n.ctx || [], state.ctx) || !state.ctx.length)) { parents.forEach(function (k) { expanded[k] = true; }); if (sameCtx(n.ctx || [], state.ctx)) expanded[n.key] = true; }
      if (n.children && n.children.length) markExpanded(n.children, parents.concat([n.key]));
    });
  }
  function renderNodes(nodes) {
    return "<ul>" + nodes.map(function (n) {
      var has = n.children && n.children.length, open = expanded[n.key];
      var p = n.id ? byId[n.id] : null;
      var cur = p && p.id === state.id && sameCtx(n.ctx || [], state.ctx) ? " current" : "";
      var label = p ? '<span class="dot t-' + p.type + '"></span><a href="' + href(p.id, n.ctx) + '" title="' + esc(p.id + " " + p.title) + '">' + esc(p.title) + "</a>"
                    : '<span class="dot t-' + (n.facet || "trait") + '"></span><a href="' + (n.facet ? "#/f/" + n.facet + "?v=" + state.view : "javascript:void 0") + '" data-toggle="' + esc(n.key) + '">' + esc(n.label) + "</a>";
      // Derived badge: item/page whose System tags are derived, when shown under a System in a build/view tree
      var der = "";
      if (p && p.derived && p.derived.system) {
        var underSys = (n.ctx || []).some(function (id) { return byId[id] && byId[id].type === "system"; });
        if (underSys || state.view === "majorunit") der = ' <span class="derived-tag" title="' + esc(p.derived.system) + '">derived</span>';
      }
      var badge = n.count != null ? '<span class="badge' + (n.count ? " has" : "") + '" title="topic pages and lessons tagged here">' + n.count + "</span>" : "";
      return '<li><div class="node' + cur + '"><button class="twisty' + (has ? "" : " leaf") + '" data-toggle="' + esc(n.key) + '" aria-label="expand">' + (open ? "\u25BC" : "\u25B6") + "</button>" + label + der + badge + "</div>" +
             (has && open ? renderNodes(n.children) : "") + "</li>";
    }).join("") + "</ul>";
  }
  function simpleNode(hrefStr, dot, text, current) { return '<li><div class="node' + (current ? " current" : "") + '"><button class="twisty leaf"></button><span class="dot t-' + dot + '"></span><a href="' + hrefStr + '">' + text + "</a></div></li>"; }
  function renderTree() {
    var el = document.getElementById("tree");
    // Views are only offered as alternatives within the same facet level
    var groups = [];
    D.views.forEach(function (v) { var g = groups.filter(function (x) { return x.name === v.group; })[0]; if (!g) { g = { name: v.group, views: [] }; groups.push(g); } g.views.push(v); });
    document.getElementById("view-buttons").innerHTML = groups.map(function (g) {
      var sel = g.views.some(function (v) { return v.scopeSelectable; }) ? (function () {
        var enabled = viewByKey[state.view].scopeSelectable;
        return '<div class="scope-select"><label for="scope-select">Product Scope (facet level 0)</label><select id="scope-select"' + (enabled ? "" : ' disabled title="Product Scope applies to the System and Design Type views"') + '><option value="">All scopes</option>' +
          valuesOf("productscope").map(function (ps) { return '<option value="' + ps.id + '"' + (enabled && state.scope === ps.id ? " selected" : "") + ">" + esc(ps.title) + "</option>"; }).join("") + "</select></div>";
      })() : "";
      return '<div class="view-group' + (g.views.some(function (v) { return v.key === state.view; }) ? " has-active" : "") + '"><div class="view-group-label">' + esc(g.name) + "</div>" + sel + '<div class="view-row">' + g.views.map(function (v) {
        return '<button role="tab" data-view="' + v.key + '" class="' + (v.key === state.view ? "active" : "") + '" aria-selected="' + (v.key === state.view) + '" title="' + esc(v.description) + '">' + esc(v.label) + "</button>";
      }).join("") + "</div></div>";
    }).join("");
    document.getElementById("view-desc").textContent = viewByKey[state.view].description;
    if (state.query) { el.innerHTML = renderSearch(state.query); return; }
    var main = buildTree(state.view), reg = registerTree(), v = viewByKey[state.view];
    markExpanded(main, []); markExpanded(reg, []);
    el.innerHTML =
      '<div class="tree-section">Home</div><ul>' + simpleNode("#/home?v=" + state.view, "special", "Engineering Hub home", state.route === "home") + "</ul>" +
      '<div class="tree-section">' + esc(v.label) + " view: " + (v.fixedScope ? "Full Aircraft \u203a " : "") + esc(facetByKey[v.levels[0]].plural) + (scopeOn() ? " \u00b7 " + esc(byId[state.scope].title) : "") + "</div>" + renderNodes(main) +
      '<div class="tree-section">Registers</div>' + renderNodes(reg) +
      '<div class="tree-section">Hub pages</div><ul>' +
      (IS_PROD ? [["HUB-PROJECT","special"],["HUB-CONTACTS","special"],["HUB-AUTHORITY","special"],["HUB-MODEL","special"],["HUB-REQUIREMENTS","requirement"],["HUB-ITEMS","item"],["HUB-ISSUES-DEMO","issue"],["HUB-FEEDBACK","special"]] : []).concat(HUB_PAGES).map(function (h) { return byId[h[0]] ? simpleNode(href(h[0]), h[1], esc(byId[h[0]].title), state.id === h[0]) : ""; }).join("") +
      simpleNode(href("HUB-LESSONS"), "lesson", "Lessons Learned (" + lessons.length + ")", state.id === "HUB-LESSONS") +
      simpleNode(href("HUB-ISSUES"), "special", "Framework issues (" + D.issues.length + ")", state.id === "HUB-ISSUES") + "</ul>";
  }
  function renderSearch(q) {
    var s = q.toLowerCase();
    var hits = D.pages.filter(function (p) { return p.id.toLowerCase().indexOf(s) >= 0 || p.title.toLowerCase().indexOf(s) >= 0; });
    if (!hits.length) return '<p class="empty" style="padding:8px">No pages match \u201c' + esc(q) + "\u201d.</p>";
    return '<div class="tree-section">' + hits.length + " result" + (hits.length === 1 ? "" : "s") + '</div><ul class="search-results">' + hits.slice(0, 100).map(function (p) {
      return '<li><div class="node"><span class="dot t-' + p.type + '"></span><a href="' + href(p.id) + '">' + esc(p.title) + '</a><span class="nid">' + esc(p.id) + "</span></div></li>";
    }).join("") + "</ul>";
  }

  // ---------- breadcrumbs (reflect current view) ----------
  function facetLink(k) { return '<a href="#/f/' + k + "?v=" + state.view + '">' + esc(facetByKey[k].plural) + "</a>"; }
  function crumbs() {
    var v = viewByKey[state.view], out = ['<a href="#/home?v=' + state.view + '">Home</a>', '<span class="view-crumb">' + esc(v.label) + " view</span>"];
    if (scopeOn()) out.push('<a href="' + href(state.scope) + '">' + esc(byId[state.scope].title) + "</a>");
    if (state.route === "home") return out;
    if (state.route === "facet") { out.push(esc(facetByKey[state.id] ? facetByKey[state.id].plural : state.id)); return out; }
    var p = byId[state.id]; if (!p) return out;
    var L = v.levels, path = state.ctx.slice();
    if (!path.length) {
      if (p.type === "content" || p.type === "lesson") {
        L.forEach(function (k) { var gc = path.filter(function (id) { return byId[id].type === "sysgroup"; })[0], sc = path.filter(function (id) { return byId[id].type === "productscope"; })[0];
          var t = tagsOf(p, k).filter(function (id) { return (k !== "system" || !gc || byId[id].group === gc) && (k !== "system" || sysApplies(id, sc)) && (k !== "sysgroup" || !sc || byId[id].members.some(function (m) { return sysApplies(m, sc) && tagsOf(p, "system").indexOf(m) >= 0; })); })[0]; if (t) path.push(t); });
      } else if (p.type === "system" && L[0] === "sysgroup") path = [p.group];
      else if (p.type !== L[0]) {
        if (["skill", "trait", "srcsystem", "productscope", "itemsource", "majorunit"].indexOf(p.type) >= 0) out.push("Registers");
        if (facetByKey[p.type]) out.push(facetLink(p.type));
        if (p.type === "trait") out.push(esc(p.category));
      }
    }
    path.forEach(function (id, i) { out.push('<a href="' + href(id, path.slice(0, i)) + '">' + esc(byId[id].title) + "</a>"); });
    out.push("<b>" + esc(p.title) + "</b>");
    return out;
  }

  // ---------- page templates ----------
  function verificationPanel(p) {
    return '<div class="panel"><h4>Verification &amp; validation</h4><div class="kv">' +
      '<span class="k">Status</span><span><span class="vstatus">Not verified</span> <span class="ph-tag">PLACEHOLDER</span></span>' +
      '<span class="k">Owner</span><span class="empty">To be assigned (placeholder)</span>' +
      '<span class="k">Last reviewed</span><span class="empty">Not yet reviewed (placeholder)</span>' +
      '<span class="k">Next review</span><span class="empty">To be set (placeholder)</span></div></div>';
  }
  function metaPanel(p) {
    var f = facetByKey[p.type];
    var rows = '<span class="k">Permanent ID</span><span class="mono">' + esc(p.id) + "</span>" + '<span class="k">Page type</span><span>' + esc(TYPE_LABEL[p.type]) + "</span>";
    if (f) rows += '<span class="k">Facet</span><span><a href="#/f/' + f.key + "?v=" + state.view + '">' + esc(f.label) + "</a></span>" + '<span class="k">Source</span><span>' + esc(f.source) + "</span>" +
      '<span class="k">Level</span><span>' + esc(f.levelLabel) + "</span>";
    if (p.status) rows += '<span class="k">Status</span><span>' + esc(p.status) + "</span>";
    if (p.group) rows += '<span class="k">System Group</span><span>' + chip(p.group) + "</span>";
    if (p.sourceCategory && p.type !== "trait") rows += '<span class="k">Source category</span><span>' + esc(p.sourceCategory) + "</span>";
    if (p.category) rows += '<span class="k">Trait category</span><span>' + esc(p.category) + "</span>";
    if (p.sources) rows += '<span class="k">Source</span><span><div class="chips">' + p.sources.map(function (id) { return chip(id); }).join("") + "</div></span>";
    if (p.origin) rows += '<span class="k">Origin</span><span>' + (p.origin.url ? '<a href="' + esc(p.origin.url) + '">' + esc(p.origin.document) + "</a>" : esc(p.origin.document)) + ", issue: " + esc(p.origin.issue) + "</span>";
    var html = '<div class="panel"><h4>Metadata</h4><div class="kv">' + rows + "</div>";
    if (p.type === "system" && p.scopes) rows += '<span class="k">Applies to Product Scopes</span><span><div class="chips">' + p.scopes.map(function (id) { return chip(id); }).join("") + "</div>" + (p.scopesConfirmed ? "" : '<span class="derived-note">Initial proposal, to be confirmed</span>') + "</span>";
    if (p.type === "majorunit") rows += '<span class="k">Build level</span><span>Build Level 1 (Aircraft scope only)</span>';
    if (p.frameworkPage && IS_PROD) rows += '<span class="k">Origin kind</span><span><span class="kind-pill fw">Framework page</span> mirrored from Framework Hub v' + esc(D.meta.frameworkVersion) + ' · <a href="' + esc(FRAMEWORK_URL) + "#/p/" + encodeURIComponent(p.id) + '" target="_blank" rel="noopener">Open in Framework Hub \u2197</a></span>';
    if (p.demo) rows += '<span class="k">Demo</span><span><span class="kind-pill demo">Fictional demo data</span></span>';
    if (p.recordKind === "knowledge") rows += '<span class="k">Tagging rule</span><span>Knowledge record: may carry several options per facet, or All. Mandatory: at least one Lifecycle Stage and at least one System.</span>';
    if (storedTags(p).length) {
      var direct = SHOW_FACETS.filter(function (k) { return k !== "sysgroup" && tagsOf(p, k).length && !(p.derived && p.derived[k]); });
      var derived = SHOW_FACETS.filter(function (k) { return tagsOf(p, k).length && (k === "sysgroup" || (p.derived && p.derived[k])); });
      html += '<h4 style="margin-top:12px">Tags</h4>' + direct.map(function (k) {
        return '<div class="tag-row"><div class="tag-facet">' + esc(facetByKey[k].label) + (k === "system" && supportsOf(p).length ? ' <span class="home-tag" title="The one System the item is part of">home System</span>' : "") + '</div><div class="chips">' +
          (isAll(p, k) ? '<a class="chip all-chip c-' + k + '" href="#/f/' + k + "?v=" + state.view + '" title="Tagged with every option of this facet">All ' + esc(facetByKey[k].plural) + " (" + valuesOf(k).length + ")</a>" : tagsOf(p, k).map(function (id) { return chip(id); }).join("")) + "</div></div>";
      }).join("");
      if (supportsOf(p).length) html += '<h4 style="margin-top:12px">Supports links <span class="supports-tag">typed link, not a tag</span></h4><div class="tag-row"><div class="tag-facet">Systems carried or served</div><div class="chips">' +
        supportsOf(p).map(function (id) { return chip(id, "supports"); }).join("") + '</div><div class="derived-note">A change flags these Systems for review, but no further.</div></div>';
      if (derived.length) html += '<h4 style="margin-top:12px">Derived tags <span class="derived-tag">calculated, not stored</span></h4>' + derived.map(function (k) {
        var why = k === "sysgroup" ? "Derived from the System tag(s); never stored." : p.derived[k];
        return '<div class="tag-row"><div class="tag-facet">' + esc(facetByKey[k].label) + '</div><div class="chips">' + tagsOf(p, k).map(function (id) { return chip(id, "derived"); }).join("") + '</div><div class="derived-note">' + esc(why) + "</div></div>";
      }).join("");
    }
    return html + "</div>";
  }
  function backlinkSection(p) {
    var b = Object.keys(backlinks[p.id] || {});
    return "<h2>Pages that link here</h2>" + (b.length ? '<ul class="linklist">' + b.map(function (id) { return "<li>" + link(id) + ' <span class="mono" style="color:var(--muted)">' + esc(id) + "</span></li>"; }).join("") + "</ul>" : '<p class="empty">No pages link here yet.</p>');
  }
  function head(p) {
    return '<div class="page-head"><span class="type-pill" style="background:' + TYPE_COLOUR[p.type] + '">' + esc(TYPE_LABEL[p.type]) + '</span><div><div class="page-id">' + esc(p.id) + "</div><h1>" + esc(p.title) + "</h1></div></div>";
  }
  function relatedSection(p) {
    var html = "<h2>Related pages</h2>";
    if (p.members) html += '<h3>Systems in this group</h3><div class="chips">' + p.members.map(function (id) { return chip(id); }).join("") + "</div>";
    var tagged = taggedWith(p.id), topics = tagged.filter(function (c) { return c.type === "content"; });
    var sup = items.filter(function (c) { return supportsOf(c).indexOf(p.id) >= 0; });
    if (sup.length) html += '<h3>Supported by (typed supports links, not tags)</h3><div class="chips">' + sup.map(function (c) { return chip(c.id, "supports"); }).join("") + "</div>";
    if (topics.length) html += "<h3>Topic pages tagged with this " + esc(TYPE_LABEL[p.type].toLowerCase()) + '</h3><div class="chips">' + topics.map(function (c) { return chip(c.id); }).join("") + "</div>";
    var co = {};
    tagged.forEach(function (c) { allTags(c).forEach(function (id) { var t = byId[id].type; if (id !== p.id && t !== p.type && !(p.type === "system" && t === "sysgroup") && !(p.type === "sysgroup" && t === "system")) (co[t] = co[t] || {})[id] = true; }); });
    SHOW_FACETS.forEach(function (k) { if (co[k]) html += "<h3>Linked " + esc(facetByKey[k].plural) + ' (via shared topics and lessons)</h3><div class="chips">' + Object.keys(co[k]).map(function (id) { return chip(id); }).join("") + "</div>"; });
    var sibs = valuesOf(p.type).filter(function (x) { return (p.type !== "trait" || x.category === p.category) && (p.type !== "system" || x.group === p.group); });
    var i = sibs.map(function (x) { return x.id; }).indexOf(p.id), nb = [];
    if (i > 0) nb.push("\u2190 Previous: " + link(sibs[i - 1].id));
    if (i >= 0 && i < sibs.length - 1) nb.push("Next: " + link(sibs[i + 1].id) + " \u2192");
    if (nb.length) html += "<h3>" + (p.type === "stage" ? "Adjacent lifecycle stages" : "Neighbouring entries in the " + esc(p.type === "trait" ? p.category + " category" : p.type === "system" ? byId[p.group].title + " group" : facetByKey[p.type].label + " list")) + "</h3><p>" + nb.join(" &nbsp;|&nbsp; ") + "</p>";
    if (!tagged.length && p.type !== "srcsystem") html += ph("Cross-links to related values in other facets will appear automatically when topic pages or lessons are tagged with this value.");
    return html;
  }
  function contextBox(p) {
    if (!state.ctx.length || p.type === "content" || p.type === "lesson") return "";
    var ctxIds = state.ctx.concat([p.id]);
    var its = items.filter(function (c) { var t = allTags(c); return ctxIds.every(function (id) { return t.indexOf(id) >= 0; }); });
    return '<div class="ctx"><b>In this view context:</b> ' + ctxIds.map(function (id) { return esc(byId[id].title); }).join(" \u203a ") + ". " +
      (its.length ? "Topic pages and lessons tagged with all of these: " + its.map(function (c) { return link(c.id, ctxIds); }).join(", ") : "No topic pages or lessons are tagged with this combination yet.") + "</div>";
  }
  function lessonsSection(p) {
    var ls = lessons.filter(function (l) { return allTags(l).indexOf(p.id) >= 0; });
    var canFilter = LL_FACETS.indexOf(p.type) >= 0;
    return "<h2>Lessons learned</h2>" + (ls.length
      ? '<ul class="linklist">' + ls.map(function (l) { return "<li>" + link(l.id) + ' <span class="mono" style="color:var(--muted)">' + esc(l.id) + "</span> \u2013 " + esc(l.summary) + "</li>"; }).join("") + "</ul>"
      : '<p class="empty">No lessons are tagged with this value yet.</p>') +
      (canFilter ? '<p><a href="' + href("HUB-LESSONS") + "&f=" + encodeURIComponent(p.id) + '">Open Lessons Learned filtered to \u201c' + esc(p.title) + "\u201d \u2192</a></p>" : "");
  }
  function mappingBox(p) {
    var m = p.mapsTo || {};
    return '<div class="' + (p.mappingClean ? "ctx" : "warn") + '"><b>Tracker source entry, kept as a source reference.</b> It is no longer used for tagging. Maps to: ' +
      Object.keys(m).map(function (k) { return esc(facetByKey[k].label) + " " + m[k].map(function (id) { return chip(id); }).join(" "); }).join(" + ") +
      (p.mappingClean ? " (one-to-one)." : "<br><b>Not a clean mapping:</b> " + esc(p.mappingNote) + " See " + link("HUB-ISSUES") + ".") +
      (p.mappingClean && p.mappingNote ? "<br>" + esc(p.mappingNote) : "") + "</div>";
  }
  function renderValuePage(p) {
    var desc;
    if (p.description) desc = "<p>" + esc(p.description) + "</p>";
    else if (p.agreed) desc = ph("Description of this " + TYPE_LABEL[p.type].toLowerCase() + "'s function and boundary to be written (agreed by name and rule only).");
    else desc = '<div class="warn"><b>No description in the source register.</b> The tracker has no description for this entry, so it is shown here as a gap rather than invented. See ' + link("HUB-ISSUES") + ".</div>";
    var f = facetByKey[p.type];
    var rule = f && f.note && ["system", "sysgroup", "designtype", "productscope", "majorunit", "itemsource"].indexOf(p.type) >= 0 ? '<p class="facet-rule"><b>' + esc(f.label) + ":</b> " + esc(f.note) + "</p>" : "";
    var taggable = ["stage", "sysgroup", "system", "designtype", "productscope", "discipline", "majorunit", "itemsource"].indexOf(p.type) >= 0;
    var scopeBox = "";
    if (p.type === "system") scopeBox = "<h2>Applicable Product Scopes</h2><p>One shared System list is used for every Product Scope; each System records the scopes it applies to. Items in other scopes cannot take this System, and views filtered by Product Scope show only applicable Systems.</p>" +
      '<div class="scope-grid">' + valuesOf("productscope").map(function (ps) { var on = p.scopes.indexOf(ps.id) >= 0; return '<div class="scope-cell ' + (on ? "on" : "off") + '"><span class="scope-mark" aria-hidden="true">' + (on ? "\u2713" : "\u2013") + "</span>" + link(ps.id) + '<span class="sr">' + (on ? " applies" : " does not apply") + "</span></div>"; }).join("") + "</div>" +
      (p.scopesConfirmed ? '<p class="section-note">Confirmed (4 Oct 2026).</p>' : '<p class="section-note">Initial proposal, to be confirmed. See ' + link("HUB-ISSUES") + ".</p>");
    if (p.type === "productscope") scopeBox = "<h2>Systems that apply to this scope</h2>" + valuesOf("sysgroup").map(function (g) { var ms = g.members.filter(function (m) { return sysApplies(m, p.id); }); return ms.length ? "<h3>" + esc(g.title) + '</h3><div class="chips">' + ms.map(function (m) { return chip(m); }).join("") + "</div>" : ""; }).join("") +
      (p.id === "PS-0001" ? '<p>The Aircraft scope has a product-build hierarchy of build levels (Full Aircraft \u203a Major Unit or Final Assembly \u203a Assembly \u203a Sub-assembly \u203a Part). See ' + link("HUB-BUILDLEVELS") + ".</p>" : "<p>The lower build levels of this scope will be defined later. See " + link("HUB-BUILDLEVELS") + ".</p>");
    if (p.type === "system" && scopeOn() && !sysApplies(p.id, state.scope)) scopeBox = '<div class="warn"><b>Not applicable to ' + esc(byId[state.scope].title) + ".</b> This System does not apply to the selected Product Scope, so it is not shown in the filtered view.</div>" + scopeBox;
    if (p.type === "majorunit") scopeBox = '<p class="section-note">Part of the Aircraft scope (' + link("PS-0001") + "). See " + link("HUB-BUILDLEVELS") + " for how Build Level 1 relates to the other build levels.</p>";
    return head(p) + (IS_PROD ? demoBanner() : "") + '<div class="grid"><div>' + (p.type === "srcsystem" ? mappingBox(p) : "") + contextBox(p) + "<h2>Description</h2>" + desc + rule + scopeBox + figures(p.images) +
      "<h2>Key considerations</h2>" + ph("Key considerations for \u201c" + p.title + "\u201d to be written and verified by a nominated owner.") +
      (taggable ? lessonsSection(p) : "") +
      (["system", "designtype"].indexOf(p.type) >= 0 ? prodLinksSection(p) : "") +
      relatedSection(p) +
      "<h2>Learning resources</h2>" + ph("Links to courses, standards, handbooks and internal guidance to be added.") +
      backlinkSection(p) + "</div><div>" + metaPanel(p) + verificationPanel(p) + "</div></div>";
  }
  function lessonMatches(l, filter) {
    return LL_FACETS.every(function (k) {
      var sel = filter.filter(function (id) { return byId[id].type === k; });
      return !sel.length || sel.some(function (id) { return tagsOf(l, k).indexOf(id) >= 0; });
    });
  }
  function renderLessonsIndex(p) {
    var f = state.filter, res = lessons.filter(function (l) { return lessonMatches(l, f); });
    function opt(v, k) {
      var n = lessons.filter(function (l) { return tagsOf(l, k).indexOf(v.id) >= 0; }).length;
      return '<label class="' + (n ? "" : "zero") + '"><input type="checkbox" data-filter="' + v.id + '"' + (f.indexOf(v.id) >= 0 ? " checked" : "") + "> " + esc(v.title) + ' <span class="badge' + (n ? " has" : "") + '">' + n + "</span></label>";
    }
    var boxes = LL_FACETS.map(function (k) {
      var body = k === "system" ? valuesOf("sysgroup").map(function (g) { return '<div class="opt-group">' + esc(g.title) + "</div>" + valuesOf("system").filter(function (s) { return s.group === g.id; }).map(function (v) { return opt(v, k); }).join(""); }).join("")
                                : valuesOf(k).map(function (v) { return opt(v, k); }).join("");
      return '<div class="facet-box"><h4>' + esc(facetByKey[k].label) + '</h4><div class="facet-opts">' + body + "</div></div>";
    }).join("");
    return head(p) + "<p>" + esc(p.summary) + " Tick any combination: lessons must match at least one ticked value in <b>every</b> facet where something is ticked (OR within a facet, AND across facets), so you see all applicable and only applicable lessons.</p>" +
      '<div class="example-banner"><b>Example content.</b> All ' + lessons.length + " lessons in this prototype are fictional examples written to demonstrate the template and filtering; none is authoritative engineering guidance.</div>" +
      '<div class="facet-filters">' + boxes + "</div>" +
      "<p><b>" + res.length + " of " + lessons.length + " lessons match</b>" + (f.length ? ' \u00b7 filters: <span class="chips" style="display:inline-flex">' + f.map(function (id) { return chip(id); }).join("") + '</span> \u00b7 <a href="' + href("HUB-LESSONS") + '">Clear all</a>' : " (no filters applied)") + "</p>" +
      '<table class="list"><thead><tr><th>ID</th><th>Lesson</th><th>Summary</th><th>Tags</th></tr></thead><tbody>' +
      (res.length ? res.map(function (l) { return '<tr><td class="mono">' + esc(l.id) + "</td><td>" + link(l.id) + "</td><td>" + esc(l.summary) + '</td><td><div class="chips">' + LL_FACETS.map(function (k) { return isAll(l, k) ? '<span class="chip all-chip c-' + k + '">All ' + esc(facetByKey[k].plural) + "</span>" : tagsOf(l, k).map(function (id) { return chip(id); }).join(""); }).join("") + "</div></td></tr>"; }).join("")
                  : '<tr><td colspan="4" class="empty">No lessons match this combination.</td></tr>') + "</tbody></table>" + backlinkSection(p);
  }
  function renderLessonPage(p) {
    var others = lessons.filter(function (c) { return c.id !== p.id && storedTags(c).some(function (id) { return storedTags(p).indexOf(id) >= 0; }); });
    var o = p.origin || {};
    return head(p) + '<div class="example-banner"><b>EXAMPLE lesson.</b> ' + esc(p.exampleNote) + "</div>" +
      '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + "</p>" +
      "<h2>What happened</h2><p>" + esc(p.whatHappened) + "</p>" +
      "<h2>Root cause</h2><p>" + esc(p.rootCause) + "</p>" +
      "<h2>Recommendation</h2><p>" + esc(p.recommendation) + "</p>" +
      "<h2>Applicability</h2><p>" + esc(p.applicability) + "</p>" +
      "<h2>Source / origin</h2><p><b>Origin:</b> " + (o.url ? '<a href="' + esc(o.url) + '">' + esc(o.document) + "</a>" : esc(o.document || "Not recorded")) + ", issue " + esc(o.issue || "not recorded") + "</p>" +
      (o.url ? "" : ph("Link to the originating document, with its issue/revision and references, to be added. Once verified, this structured record is the authoritative (master) source; the original document is kept as its linked origin only.")) +
      "<h2>Related pages</h2>" + (others.length ? '<h3>Other lessons sharing a tag</h3><div class="chips">' + others.map(function (c) { return chip(c.id); }).join("") + "</div>" : '<p class="empty">No other lessons share a tag.</p>') +
      "<p>See all lessons: " + link("HUB-LESSONS") + ".</p>" +
      backlinkSection(p) + "</div><div>" + metaPanel(p) + verificationPanel(p) + "</div></div>";
  }
  // Example of an item's tags: exactly one option per facet, supports links shown separately
  function exampleItemTable(p) {
    var it = p.exampleItem; if (!it) return "";
    var rows = ["productscope", "majorunit", "system", "designtype", "itemsource"].filter(function (k) { return it.tags[k]; }).map(function (k) {
      return "<tr><td>" + esc(facetByKey[k].label) + (k === "system" ? " (home System)" : "") + "</td><td>" + chip(it.tags[k]) + "</td><td>Exactly one option</td></tr>"; }).join("") +
      "<tr><td>Supports links</td><td><div class=\"chips\">" + (it.supports || []).map(function (id) { return chip(id, "supports"); }).join("") + "</div></td><td>Typed links, not tags</td></tr>";
    return '<h2>Example item tagging</h2><p class="section-note">' + esc(it.name) + ". Illustrative only: the Framework Hub holds no project items.</p>" +
      '<div class="table-wrap"><table class="list item-tags"><thead><tr><th>Facet</th><th>Option</th><th>Rule</th></tr></thead><tbody>' + rows + "</tbody></table></div>";
  }
  function renderInfoPage(p) {
    var gl = p.glossary ? '<dl class="glossary">' + p.glossary.map(function (g) { return '<div class="gl-row" id="gl-' + esc(g[0].toLowerCase().replace(/[^a-z]+/g, "-")) + '"><dt>' + esc(g[0]) + "</dt><dd>" + rich(g[1]).replace(/^<p>|<\/p>$/g, "") + "</dd></div>"; }).join("") + "</dl>" : "";
    return head(p) + '<p class="lead">' + rich(p.summary).replace(/^<p>|<\/p>$/g, "") + "</p>" +
      '<div class="grid"><div>' + gl + figures(p.images) + (p.sections || []).map(function (sec) { return "<h2>" + esc(sec.heading) + "</h2>" + rich(sec.body); }).join("") +
      backlinkSection(p) + "</div><div>" + metaPanel(p) + verificationPanel(p) + "</div></div>";
  }
  function renderContentPage(p) {
    var others = contents.filter(function (c) { return c.id !== p.id && storedTags(c).some(function (id) { return storedTags(p).indexOf(id) >= 0; }); });
    return head(p) + '<div class="example-banner"><b>Example content.</b> ' + esc(p.exampleNote) + "</div>" +
      '<div class="grid"><div><p><i>' + rich(p.summary).replace(/^<p>|<\/p>$/g, "") + "</i></p>" +
      p.sections.map(function (s) { return "<h2>" + esc(s.heading) + "</h2>" + rich(s.body); }).join("") + exampleItemTable(p) + figures(p.images) +
      "<h2>Related pages</h2><p>Every tag in the metadata panel is a link to that value's page. This page is stored once and appears under each of its tags in every view.</p>" +
      (others.length ? '<h3>Other topics sharing a tag</h3><div class="chips">' + others.map(function (c) { return chip(c.id); }).join("") + "</div>" : "") +
      "<h2>Learning resources</h2>" + ph("Links to courses, standards and guidance to be added.") +
      backlinkSection(p) + "</div><div>" + metaPanel(p) + verificationPanel(p) + "</div></div>";
  }
  var FRAMEWORK_SVG =
    '<svg class="fp-diagram" viewBox="0 0 960 400" role="img" aria-labelledby="fpd-t fpd-d" font-family="Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif">' +
    '<title id="fpd-t">Framework Hub, Production Hub and production data</title><desc id="fpd-d">The Framework Hub holds generic pages, templates, facets and link types. A Production Hub is a versioned, tailored instance of the framework for one project and adds project working data. It links by permanent ID and version to production data whose master is still another system (PLM and CAD models, calculations, test records), under configuration control and effectivity. An authority register records when each data type moves to the Production Hub, which becomes master of everything.</desc>' +
    '<defs><marker id="fpa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#00405E"/></marker></defs>' +
    '<rect width="960" height="400" rx="10" fill="#F7FBFB"/>' +
    // column 1 framework
    '<rect x="20" y="20" width="260" height="290" rx="10" fill="#00405E"/>' +
    '<text x="150" y="50" fill="#fff" font-size="17" font-weight="700" text-anchor="middle">Framework Hub</text><text x="150" y="70" fill="#fff" font-size="12" text-anchor="middle">one standard, generic, open</text>' +
    ["Page templates & permanent IDs", "Controlled facets & levels", "Generic descriptions & guidance", "Typed link definitions", "Generic lessons learned"].map(function (t, i) {
      return '<rect x="40" y="' + (88 + i * 42) + '" width="220" height="32" rx="6" fill="#FFFFFF"/><text x="150" y="' + (109 + i * 42) + '" fill="#00405E" font-size="13" font-weight="600" text-anchor="middle">' + t + "</text>"; }).join("") +
    // arrow 1
    '<path d="M286 140H352" stroke="#00405E" stroke-width="3" marker-end="url(#fpa)"/><text x="319" y="126" fill="#00405E" font-size="12" font-weight="600" text-anchor="middle">instantiate</text><text x="319" y="162" fill="#526775" font-size="11" text-anchor="middle">+ tailor</text>' +
    '<path d="M352 210H286" stroke="#1D8C89" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#fpa)" transform="rotate(180 319 210)"/><text x="319" y="232" fill="#526775" font-size="11" text-anchor="middle">framework</text><text x="319" y="246" fill="#526775" font-size="11" text-anchor="middle">updates</text>' +
    // column 2 production hub
    '<rect x="360" y="20" width="260" height="290" rx="10" fill="#46C1BE"/>' +
    '<text x="490" y="50" fill="#00405E" font-size="17" font-weight="700" text-anchor="middle">Production Hub</text><text x="490" y="70" fill="#00405E" font-size="12" text-anchor="middle">one per project, internal, access-controlled</text>' +
    ["Framework pages (version vX)", "Points of contact & stats", "Live model views", "Configuration & effectivity", "Authority register"].map(function (t, i) {
      return '<rect x="380" y="' + (88 + i * 42) + '" width="220" height="32" rx="6" fill="' + (i ? "#FFFFFF" : "#D9F2F1") + '"/><text x="490" y="' + (109 + i * 42) + '" fill="#00405E" font-size="13" font-weight="600" text-anchor="middle">' + t + "</text>"; }).join("") +
    // arrow 2
    '<path d="M626 165H692" stroke="#00405E" stroke-width="3" marker-end="url(#fpa)"/><text x="659" y="138" fill="#00405E" font-size="12" font-weight="600" text-anchor="middle">typed links</text><text x="659" y="152" fill="#526775" font-size="11" text-anchor="middle">ID + version</text>' +
    // column 3 production data
    '<rect x="700" y="20" width="240" height="290" rx="10" fill="#9EDEDC"/>' +
    '<text x="820" y="50" fill="#00405E" font-size="17" font-weight="700" text-anchor="middle">Production data</text><text x="820" y="70" fill="#00405E" font-size="12" text-anchor="middle">current master until moved to the Hub</text>' +
    ["Part models (PLM / CAD)", "Parametric model parameters", "Calculation documents", "Test & verification records"].map(function (t, i) {
      return '<rect x="718" y="' + (88 + i * 42) + '" width="204" height="32" rx="6" fill="#FFFFFF"/><text x="820" y="' + (109 + i * 42) + '" fill="#00405E" font-size="13" font-weight="600" text-anchor="middle">' + t + "</text>"; }).join("") +
    // config band
    '<rect x="360" y="326" width="580" height="54" rx="10" fill="#FEF3DC" stroke="#F2A541" stroke-width="1.5"/>' +
    '<text x="650" y="349" fill="#7A5000" font-size="14" font-weight="700" text-anchor="middle">Configuration control &amp; effectivity</text>' +
    '<text x="650" y="368" fill="#7A5000" font-size="12" text-anchor="middle">version / issue \u00b7 baseline \u00b7 applicability by build standard, serial number or configuration</text>' +
    '<text x="20" y="346" fill="#526775" font-size="12">Framework pages never contain</text><text x="20" y="362" fill="#526775" font-size="12">production data; production records</text><text x="20" y="378" fill="#526775" font-size="12">link to framework page IDs and facets.</text>' +
    "</svg>";
  function renderFrameworkPage(p) {
    return head(p) + '<p class="lead">' + rich(p.summary).replace(/^<p>|<\/p>$/g, "") + "</p>" +
      '<figure class="hub-fig fig-wide fig-inline"><button type="button" class="fig-open" data-inline="1" data-caption="Framework Hub \u2192 Production Hub instance \u2192 links to production data, under configuration control and effectivity." aria-label="Enlarge diagram: Framework vs Production">' + FRAMEWORK_SVG +
      '<span class="fig-zoom" aria-hidden="true">\u2922 Enlarge</span></button><figcaption>Framework Hub \u2192 Production Hub instance \u2192 links to production data, under configuration control and effectivity.</figcaption></figure>' +
      '<div class="grid"><div>' +
      (p.sections || []).map(function (sec) { return "<h2>" + esc(sec.heading) + "</h2>" + rich(sec.body); }).join("") +
      "<h2>Typed links between data</h2>" + figures(p.images) +
      '<p>See ' + link("HUB-PRODEX") + " for an illustration of the panels a project would add.</p>" +
      backlinkSection(p) + "</div><div>" + metaPanel(p) +
      '<div class="panel"><h4>This site</h4><div class="kv"><span class="k">Hub kind</span><span><span class="kind-pill">Framework</span></span><span class="k">Framework version</span><span class="mono">' + esc(D.meta.version) + '</span><span class="k">Production data</span><span>None (by design)</span><span class="k">Hosting</span><span>Open (proposed rule: Production Hubs internal only)</span></div></div>' +
      "</div></div>";
  }
  function renderProductionExample(p) {
    function dash() { return '<span class="empty">\u2014</span>'; }
    var stats = ["Requirements", "Product records", "Verification coverage", "Items flagged for review", "Open issues", "Linked models"].map(function (l) {
      return '<div class="stat"><div class="n">\u2014</div><div class="l">' + l + "</div></div>"; }).join("");
    var poc = ["Engineering lead", "System lead", "Design Type lead", "Configuration manager", "Hub owner"].map(function (r) {
      return "<tr><td>" + r + "</td><td>" + dash() + "</td><td>" + dash() + "</td></tr>"; }).join("");
    return head(p) + '<div class="example-banner"><b>Illustrative placeholder.</b> This page shows the layout a Production Hub adds for one project. All panels are empty or fictional; no project data is held in the Framework Hub.</div>' +
      '<p class="lead">' + esc(p.summary) + "</p>" +
      '<div class="prod-grid">' +
      '<section class="prod-panel"><h3><span class="ph-tag">PLACEHOLDER</span>Points of contact</h3><table class="list"><thead><tr><th>Role</th><th>Name</th><th>Contact</th></tr></thead><tbody>' + poc + "</tbody></table></section>" +
      '<section class="prod-panel"><h3><span class="ph-tag">PLACEHOLDER</span>Project stats</h3><div class="stats">' + stats + '</div><p class="section-note">Live counts from the project\'s data once connected.</p></section>' +
      '<section class="prod-panel"><h3><span class="ph-tag">PLACEHOLDER</span>Live model view</h3><div class="model-view" role="img" aria-label="Empty live model viewer placeholder">' +
        '<svg viewBox="0 0 200 120" aria-hidden="true"><g fill="none" stroke="#9EDEDC" stroke-width="3" stroke-linejoin="round"><path d="M100 18L160 46V96L100 112L40 96V46Z"/><path d="M40 46L100 64L160 46M100 64V112"/></g></svg>' +
        '<p>Live view of the product model from its current master (PLM/CAD, or the Hub once that data type has moved), filtered to the configuration selected below.</p></div></section>' +
      '<section class="prod-panel"><h3><span class="ph-tag">PLACEHOLDER</span>Authority register</h3><p class="section-note">Current master of each data type and the date it moved to the Hub. Data types move one at a time, once their records are verified; the end goal is that the Production Hub is master of everything.</p>' +
        '<table class="list"><thead><tr><th>Data type</th><th>Current master</th><th>Moved to Hub</th></tr></thead><tbody>' +
        ["Requirements", "Part models", "Calculations", "Configuration & effectivity"].map(function (t) { return "<tr><td>" + esc(t) + "</td><td>" + dash() + "</td><td>" + dash() + "</td></tr>"; }).join("") + "</tbody></table></section>" +
      '<section class="prod-panel"><h3><span class="ph-tag">PLACEHOLDER</span>Configuration &amp; effectivity</h3>' +
        '<div class="cfg-row"><label>Baseline<select disabled><option>\u2014</option></select></label><label>Build standard<select disabled><option>\u2014</option></select></label><label>Serial / configuration<select disabled><option>\u2014</option></select></label></div>' +
        '<table class="list"><thead><tr><th>Record</th><th>Version / issue</th><th>Baseline</th><th>Effectivity</th></tr></thead><tbody><tr><td colspan="4" class="empty-row">No records: configuration-controlled records appear here in a Production Hub.</td></tr></tbody></table></section>' +
      "</div>" +
      '<div class="panel" style="margin-top:16px"><h4>Framework link</h4><div class="kv"><span class="k">Framework version</span><span class="mono">' + esc(D.meta.version) + '</span><span class="k">Tailoring</span><span class="empty">None recorded (placeholder)</span><span class="k">Concept</span><span>' + link("HUB-FRAMEWORK") + "</span></div></div>" +
      backlinkSection(p);
  }
  function renderIssues(p) {
    var counts = {}; D.issues.forEach(function (i) { counts[i.status] = (counts[i.status] || 0) + 1; });
    return head(p) + "<p>" + esc(p.summary) + "</p>" +
      "<p>" + Object.keys(counts).map(function (k) { return '<span class="status s-' + k.replace(/\s/g, "") + '">' + esc(k) + "</span> " + counts[k]; }).join(" &nbsp; ") + "</p>" +
      '<p style="font-size:.85rem;color:var(--muted)">Source: ' + esc(D.meta.source) + ". Generated " + esc(D.meta.generated) + ". Checks marked \u2018Auto-detected\u2019 are produced by scripts/build_data.py each time the data is regenerated.</p>" +
      D.issues.map(function (i) {
        return '<div class="issue i-' + i.status.replace(/\s/g, "") + '" id="' + i.id + '"><div class="kind">' + esc(i.id) + " \u00b7 " + esc(i.kind) + ' \u00b7 <span class="status s-' + i.status.replace(/\s/g, "") + '">' + esc(i.status) + "</span></div><h3>" + esc(i.title) + "</h3>" + (i.detail ? "<p>" + esc(i.detail) + "</p>" : "") +
          (i.resolution ? '<p class="resolution"><b>' + esc(i.status) + ":</b> " + esc(i.resolution.replace(/^(Resolved|Partly resolved|For review):\s*/i, "")) + "</p>" : "") +
          (i.refs.length ? '<div class="chips">' + i.refs.map(function (id) { return chip(id); }).join("") + "</div>" : "") + "</div>";
      }).join("") + backlinkSection(p);
  }
  function renderFacet(key) {
    var f = facetByKey[key]; if (!f) return "<p>Unknown facet.</p>";
    var vals = valuesOf(key), extra = key === "trait" ? "Category" : key === "system" ? "System Group \u00b7 Product Scopes" : key === "srcsystem" ? "Maps to" : key === "sysgroup" ? "Systems" : key === "majorunit" ? "Build level" : null;
    function extraCell(v) {
      if (key === "trait") return esc(v.category);
      if (key === "majorunit") return "Build Level 1 (Aircraft)";
      if (key === "system") return link(v.group) + '<div class="chips" style="margin-top:4px">' + v.scopes.map(function (id) { return chip(id); }).join("") + "</div>";
      if (key === "sysgroup") return v.members.length;
      if (key === "srcsystem") return '<div class="chips">' + Object.keys(v.mapsTo).map(function (k) { return v.mapsTo[k].map(function (id) { return chip(id); }).join(""); }).join("") + "</div>" + (v.mappingClean ? "" : '<span class="status s-Open">not clean</span>');
      return "";
    }
    return '<div class="page-head"><span class="type-pill" style="background:' + TYPE_COLOUR[key] + '">Facet</span><div><div class="page-id">' + esc(f.source) + "</div><h1>" + esc(f.plural) + "</h1></div></div>" +
      (f.note ? '<p class="facet-rule">' + esc(f.note) + "</p>" : "") + "<p><b>Level:</b> " + esc(f.levelLabel) + "</p><p>" + vals.length + " values. Each is a page with a permanent ID.</p>" +
      '<table class="list"><thead><tr><th>ID</th><th>' + esc(f.label) + "</th>" + (extra ? "<th>" + extra + "</th>" : "") + "<th>Description</th><th>Tagged items</th></tr></thead><tbody>" +
      vals.map(function (v) { return '<tr><td class="mono">' + esc(v.id) + "</td><td>" + link(v.id) + "</td>" + (extra ? "<td>" + extraCell(v) + "</td>" : "") + "<td>" + (v.description ? esc(v.description) : '<span class="empty">No description yet</span>') + "</td><td>" + taggedWith(v.id).length + "</td></tr>"; }).join("") + "</tbody></table>";
  }

  function renderHome() {
    if (IS_PROD) return renderProdHome();
    return '<div class="page-head"><h1>Engineering Hub</h1></div>';
  }
  function demoBanner() {
    return '<div class="demo-banner" role="note"><b>Fictional demo data only.</b> ' + esc(D.meta.demoNote) +
      ' Framework pages are mirrored from <a href="' + esc(FRAMEWORK_URL) + '" target="_blank" rel="noopener">Framework Hub v' + esc(D.meta.frameworkVersion) + ' \u2197</a>.</div>';
  }
  function renderProdHome() {
    var st = PROD.stats || {}, proj = D.meta.project || {};
    var cards = [
      ["Mass budget", st.massBudgetKg + " kg", ""],
      ["Current mass", st.massCurrentKg + " kg", st.massMarginKg < 0 ? "bad" : "ok"],
      ["Mass margin", (st.massMarginKg > 0 ? "+" : "") + st.massMarginKg + " kg", st.massMarginKg < 0 ? "bad" : "ok"],
      ["Open issues", st.openIssues, "warn"],
      ["Verification coverage", st.verificationCoveragePct + "%", "ok"],
      ["Baseline", st.baseline, ""],
      ["Effectivity", "Serial " + ((st.effectivityObj && st.effectivityObj.from) || "001") + "\u2013" + ((st.effectivityObj && st.effectivityObj.to) || "010"), ""],
      ["Requirements", st.requirements, ""],
      ["Part Instances", st.items, ""],
      ["Finish specs", st.finishes || 0, ""]
    ].map(function (c) {
      return '<div class="stat ' + c[2] + '"><div class="n">' + esc(String(c[1])) + '</div><div class="l">' + esc(c[0]) + '</div></div>';
    }).join("");
    var quick = [["HUB-PROJECT","Project overview"],["HUB-CONTACTS","Points of contact"],["HUB-AUTHORITY","Authority register"],["HUB-MODEL","Live model view"],["HUB-REQUIREMENTS","Requirements"],["HUB-ITEMS","Part Instances"],["HUB-ISSUES-DEMO","Project issues"],["HUB-FEEDBACK","Framework gaps (feedback)"]];
    var syss = [["SYS-0007","Fuel"],["SYS-0008","Electrical Power Generation & Distribution"],["SYS-0001","Primary Structure"]];
    return '<div class="page-head"><span class="type-pill" style="background:var(--accent)">Home</span><div><div class="page-id">' + esc(D.meta.version) +
      ' \u00b7 framework v' + esc(D.meta.frameworkVersion) + '</div><h1>Engineering Hub <span class="kind-pill demo">Production (Demo)</span></h1>' +
      '<p class="project-name">' + esc(proj.name) + ' <span class="mono">(' + esc(proj.code) + ')</span></p></div></div>' +
      demoBanner() +
      '<p class="lead">' + esc(proj.tagline) + ' Versioned instance of Framework Hub v' + esc(D.meta.frameworkVersion) +
      '. See ' + link("HUB-AUTHORITY") + '.</p>' +
      '<div class="stats prod-stats">' + cards + '</div>' +
      '<div class="prod-grid" style="margin-top:16px">' +
      '<section class="prod-panel filled"><h3>Quick links</h3><ul class="linklist">' +
      quick.map(function (x) { return '<li>' + link(x[0]) + ' \u2013 ' + esc(x[1]) + '</li>'; }).join('') + '</ul></section>' +
      '<section class="prod-panel filled"><h3>Filled Systems (production links)</h3><ul class="linklist">' +
      syss.map(function (x) { return '<li>' + link(x[0]) + ' \u2013 ' + esc(x[1]) + ' (' + ((byId[x[0]] && byId[x[0]].productionLinks) || []).length + ' records)</li>'; }).join('') +
      '</ul></section>' +
      '<section class="prod-panel filled"><h3>Example Part Instance</h3><p>' + link("PI-0001") +
      ' \u2013 bracket with home System Secondary Structure, supports links, and finish specifications.</p></section>' +
      '<section class="prod-panel filled"><h3>Framework</h3><p><a href="' + esc(FRAMEWORK_URL) + '" target="_blank" rel="noopener">Open Framework Hub v' + esc(D.meta.frameworkVersion) + ' \u2197</a></p></section></div>';
  }
  function renderProdProject(p) {
    var st = PROD.stats || {};
    return head(p) + demoBanner() + '<div class="grid"><div><h2>About this demo project</h2><p>' + esc((D.meta.project || {}).tagline) +
      '</p><p>Baseline <b>' + esc(st.baseline) + '</b>. Effectivity structured as serial range ' +
      esc((st.effectivityObj || {}).from || "001") + '\u2013' + esc((st.effectivityObj || {}).to || "010") + '.</p>' +
      '<h2>How this Production Hub is set up</h2><ul>' +
      '<li>Created from Framework Hub version <b>' + esc(D.meta.frameworkVersion) + '</b>.</li>' +
      '<li>Framework pages are mirrored read-only; production data links to them by permanent ID.</li>' +
      '<li>Tailoring is project data (this overlay), not edits to framework pages.</li>' +
      '<li>Data types move to the Hub one at a time \u2014 see ' + link("HUB-AUTHORITY") + '.</li></ul>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + '</div></div>';
  }
  function renderProdContacts(p) {
    var rows = (PROD.contacts || []).map(function (c) {
      return '<tr><td>' + esc(c.role) + '</td><td>' + esc(c.name) + '</td><td class="mono">' + esc(c.contact) + '</td></tr>';
    }).join('');
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Points of contact</h2><p class="section-note">All names and addresses are fictional.</p>' +
      '<table class="list"><thead><tr><th>Role</th><th>Name</th><th>Contact</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + '</div></div>';
  }
  function renderProdAuthority(p) {
    var rows = (PROD.authority || []).map(function (a) {
      return '<tr><td>' + esc(a.dataType) + '</td><td>' + esc(a.master) + '</td><td class="mono">' + esc(a.moved || '\u2014') + '</td><td>' + esc(a.note) + '</td></tr>';
    }).join('');
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Authority register</h2><p>Current master of each data type. History and move-evidence are not tracked in this version (gap 4 skipped).</p>' +
      '<table class="list"><thead><tr><th>Data type</th><th>Current master</th><th>Moved to Hub</th><th>Note</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + '</div></div>';
  }
  function renderProdModel(p) {
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Live model view</h2><p class="section-note">Placeholder only \u2014 no PLM or CAD is connected.</p>' +
      figures(p.images) + backlinkSection(p) + '</div><div>' + metaPanel(p) + '</div></div>';
  }
  function renderProdRequirements(p) {
    return head(p) + demoBanner() + '<p>' + esc(p.summary) + '</p>' +
      '<table class="list"><thead><tr><th>ID</th><th>Level</th><th>Requirement</th><th>Satisfied by</th><th>Verified by</th></tr></thead><tbody>' +
      demoReqs.map(function (r) {
        return '<tr><td class="mono">' + esc(r.id) + '</td><td>' + esc(r.reqLevel) + '</td><td>' + link(r.id) + '</td><td>' +
          (r.satisfiedBy || []).map(function (id) { return chip(id); }).join(' ') + '</td><td>' +
          (r.verifiedBy || []).map(function (id) { return chip(id); }).join(' ') + '</td></tr>';
      }).join('') + '</tbody></table>' + backlinkSection(p);
  }
  function renderProdItemsIndex(p) {
    return head(p) + demoBanner() + '<p>' + esc(p.summary) + '</p>' +
      '<table class="list"><thead><tr><th>ID</th><th>Part Instance</th><th>Home System</th><th>Supports</th><th>Finishes</th></tr></thead><tbody>' +
      demoItems.map(function (it) {
        return '<tr><td class="mono">' + esc(it.id) + '</td><td>' + link(it.id) + '</td><td>' + (it.tags.system || []).map(function (id) { return chip(id); }).join(' ') +
          '</td><td>' + ((it.supports && it.supports.system) || []).map(function (id) { return chip(id, 'supports'); }).join(' ') +
          '</td><td>' + (it.finishes || []).map(function (id) { return chip(id); }).join(' ') + '</td></tr>';
      }).join('') + '</tbody></table>' + backlinkSection(p);
  }
  function renderProdIssuesIndex(p) {
    return head(p) + demoBanner() + '<p>' + esc(p.summary) + '</p>' +
      '<table class="list"><thead><tr><th>ID</th><th>Issue</th><th>Level</th><th>Forum</th><th>Status</th><th>Product Scopes (from linked items)</th></tr></thead><tbody>' +
      demoIssues.map(function (i) {
        var sc = scopesFromAffects(i.affects, i);
        return '<tr><td class="mono">' + esc(i.id) + '</td><td>' + link(i.id) + '</td><td><b>' + i.level + '</b></td><td>' + esc(i.forum) +
          '</td><td><span class="status s-' + (i.status === 'Closed' ? 'Resolved' : 'Open') + '">' + esc(i.status) + '</span></td><td><div class="chips">' +
          (sc.length ? sc.map(function (id) { return chip(id); }).join('') : '<span class="empty">\u2014</span>') + '</div></td></tr>';
      }).join('') + '</tbody></table>' + backlinkSection(p);
  }
  function renderProdFeedback(p) {
    return head(p) + demoBanner() + '<p>' + esc(p.summary) + '</p>' +
      (PROD.gaps || []).map(function (g) {
        var st = (g.status || 'Open').replace(/\s/g, '');
        return '<div class="issue i-' + st + '" id="' + g.id + '"><div class="kind">' + esc(g.id) + ' \u00b7 Framework gap \u00b7 <span class="status s-' + st + '">' + esc(g.status || 'Open') +
          '</span></div><h3>' + esc(g.title) + '</h3><p><b>Where:</b> ' + esc(g.where) + '</p><p>' + esc(g.detail) + '</p>' +
          (g.resolution ? '<p class="resolution"><b>' + esc(g.status) + ':</b> ' + esc(g.resolution) + '</p>' : '') + '</div>';
      }).join('') + backlinkSection(p);
  }
  function renderItemPage(p) {
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + '</p>' +
      '<h2>Part Definition</h2><p class="mono">' + esc(p.definition) + ' <span class="section-note">(catalogue id; Part Definitions carry no System)</span></p>' +
      '<h2>Satisfies Requirements</h2><div class="chips">' + (p.satisfies || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      '<h2>Verified by</h2><div class="chips">' + (p.verifiedBy || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      ((p.finishes || []).length ? '<h2>Finish specifications</h2><div class="chips">' + p.finishes.map(function (id) { return chip(id); }).join('') + '</div><p class="section-note">Coatings, primers and treatments linked to this part (a part may have several).</p>' : '') +
      ((p.prodLinks || []).length ? '<h2>Production records</h2><div class="chips">' + p.prodLinks.map(function (id) { return chip(id); }).join('') + '</div>' : '') +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + verificationPanel(p) + '</div></div>';
  }
  function renderRequirementPage(p) {
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + '</p>' +
      '<h2>Breakdown</h2><div class="kv"><span class="k">Level</span><span>' + esc(p.reqLevel) + '</span>' +
      (p.parent ? '<span class="k">Parent</span><span>' + chip(p.parent) + '</span>' : '') +
      ((p.children || []).length ? '<span class="k">Decomposes into</span><span><div class="chips">' + p.children.map(function (id) { return chip(id); }).join('') + '</div></span>' : '') + '</div>' +
      '<h2>Satisfied by (items)</h2>' + ((p.satisfiedBy || []).length ? '<div class="chips">' + p.satisfiedBy.map(function (id) { return chip(id); }).join('') + '</div>' : '<p class="empty">None at this level.</p>') +
      '<h2>Verified by</h2>' + ((p.verifiedBy || []).length ? '<div class="chips">' + p.verifiedBy.map(function (id) { return chip(id); }).join('') + '</div>' : '<p class="empty">None at this level.</p>') +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + verificationPanel(p) + '</div></div>';
  }
  function renderVerificationPage(p) {
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + '</p>' +
      '<div class="kv"><span class="k">Method</span><span>' + esc(p.method) + '</span><span class="k">Status</span><span>' + esc(p.status) + '</span><span class="k">Version</span><span class="mono">' + esc(p.version) + '</span></div>' +
      '<h2>Demonstrates Requirements</h2><div class="chips">' + (p.demonstrates || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      '<h2>Supports items</h2><div class="chips">' + (p.supportsItems || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + verificationPanel(p) + '</div></div>';
  }
  function renderIssuePage(p) {
    var imp = p.impact || {}, sc = scopesFromAffects(p.affects, p);
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + '</p>' +
      '<div class="kv"><span class="k">Escalation level</span><span><b>' + p.level + '</b> (highest single criterion)</span>' +
      '<span class="k">Forum</span><span>' + esc(p.forum) + '</span><span class="k">Status</span><span>' + esc(p.status) + '</span></div>' +
      '<h2>Product Scopes</h2>' + (sc.length ? '<div class="chips">' + sc.map(function (id) { return chip(id); }).join('') + '</div><p class="section-note">From the Product Scope tags of linked items and of this Issue. Shown without a separate badge for cross-scope.</p>' : '<p class="empty">No Product Scopes on linked items.</p>') +
      '<h2>Impact scores (demo)</h2><table class="list"><thead><tr><th>Criterion</th><th>Score</th></tr></thead><tbody>' +
      [['Effort', imp.effort],['Cost', imp.cost],['Schedule', imp.schedule],['Safety / certification', imp.safety],['Highest build level affected', imp.buildLevel]].map(function (r) {
        return '<tr><td>' + esc(r[0]) + '</td><td><b>' + r[1] + '</b></td></tr>';
      }).join('') + '</tbody></table>' +
      '<h2>Affects</h2><div class="chips">' + (p.affects || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + verificationPanel(p) + '</div></div>';
  }
  function renderProdRecordPage(p) {
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + '</p>' +
      '<div class="kv"><span class="k">Record type</span><span>' + esc(p.recType) + '</span><span class="k">Current master</span><span>' + esc(p.master) +
      '</span><span class="k">Version / issue</span><span class="mono">' + esc(p.version) + '</span><span class="k">Baseline</span><span>' + esc(p.baseline) +
      '</span><span class="k">Effectivity</span><span>' + formatEffectivity(p.effectivity) + '</span><span class="k">Status</span><span>' + esc(p.status) + '</span></div>' +
      '<h2>Supports Requirements</h2><div class="chips">' + (p.requirements || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + verificationPanel(p) + '</div></div>';
  }
  function renderFinishPage(p) {
    return head(p) + demoBanner() + '<div class="grid"><div><h2>Summary</h2><p>' + esc(p.summary) + '</p>' +
      '<div class="kv"><span class="k">Finish kind</span><span>' + esc(p.finishKind) + '</span><span class="k">Specification</span><span>' + esc(p.spec) +
      '</span><span class="k">Issue / revision</span><span class="mono">' + esc(p.specIssue) + '</span></div>' +
      '<h2>Applied to parts</h2><div class="chips">' + (p.appliedTo || []).map(function (id) { return chip(id); }).join('') + '</div>' +
      '<p class="section-note">Typed finish-applied links. A change to this Finish Specification flags the linked parts for review.</p>' +
      backlinkSection(p) + '</div><div>' + metaPanel(p) + verificationPanel(p) + '</div></div>';
  }

  // ---------- render ----------
  var keepScroll = false;
  function render() {
    parseHash();
    var el = document.getElementById("page"), html;
    if (state.route === "home") { html = renderHome(); document.title = IS_PROD ? "Engineering Hub – Production (Demo)" : "Engineering Hub – Framework"; }
    else if (state.route === "facet") { html = renderFacet(state.id); document.title = (facetByKey[state.id] ? facetByKey[state.id].plural + " – " : "") + (IS_PROD ? "Production (Demo)" : "Framework"); }
    else {
      var p = byId[state.id];
      if (!p) html = '<h1>Page not found</h1><p>No page has ID <span class="mono">' + esc(state.id) + "</span>.</p>";
      else if (p.type === "content") html = renderContentPage(p);
      else if (p.id === "HUB-ISSUES") html = renderIssues(p);
      else if (p.id === "HUB-FRAMEWORK") html = renderFrameworkPage(p);
      else if (p.id === "HUB-PRODEX") html = renderProductionExample(p);
      else if (p.id === "HUB-LESSONS") html = renderLessonsIndex(p);
      else if (p.id === "HUB-PROJECT") html = renderProdProject(p);
      else if (p.id === "HUB-CONTACTS") html = renderProdContacts(p);
      else if (p.id === "HUB-AUTHORITY") html = renderProdAuthority(p);
      else if (p.id === "HUB-MODEL") html = renderProdModel(p);
      else if (p.id === "HUB-REQUIREMENTS") html = renderProdRequirements(p);
      else if (p.id === "HUB-ITEMS") html = renderProdItemsIndex(p);
      else if (p.id === "HUB-ISSUES-DEMO") html = renderProdIssuesIndex(p);
      else if (p.id === "HUB-FEEDBACK") html = renderProdFeedback(p);
      else if (p.type === "item") html = renderItemPage(p);
      else if (p.type === "requirement") html = renderRequirementPage(p);
      else if (p.type === "verification") html = renderVerificationPage(p);
      else if (p.type === "issue") html = renderIssuePage(p);
      else if (p.type === "prodrecord") html = renderProdRecordPage(p);
      else if (p.type === "finish") html = renderFinishPage(p);
      else if (p.type === "special") html = renderInfoPage(p);
      else if (p.type === "lesson") html = renderLessonPage(p);
      else html = renderValuePage(p);
      document.title = (p ? p.id + " " + p.title + " – " : "") + (IS_PROD ? "Production (Demo)" : "Framework");
    }
    el.innerHTML = html;
    document.getElementById("breadcrumbs").innerHTML = crumbs().join('<span class="sep">\u203a</span>');
    document.getElementById("footer").textContent = (IS_PROD ? "Engineering Hub – Production (Demo) · " + ((D.meta.project || {}).name || "") + " · " : "Engineering Hub – Framework ") + D.meta.version + " · data generated " + D.meta.generated + " · " + D.pages.length + " pages";
    renderTree();
    var cur = document.querySelector(".tree .node.current"); if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: "nearest" });
    if (state.id !== "HUB-LESSONS" || !keepScroll) document.querySelector(".main").scrollTop = 0;
    keepScroll = state.id === "HUB-LESSONS";
  }

  // ---------- events ----------
  document.getElementById("view-buttons").addEventListener("click", function (e) { var b = e.target.closest("button[data-view]"); if (b) setView(b.getAttribute("data-view")); });
  document.getElementById("view-buttons").addEventListener("change", function (e) {
    if (e.target.id !== "scope-select") return;
    var h = (location.hash || "#/home").replace(/[?&]s=[^&]*/, "").replace(/[?&]c=[^&]*/, "");
    if (e.target.value) h += (h.indexOf("?") >= 0 ? "&" : "?") + "s=" + e.target.value;
    location.hash = h;
  });
  document.getElementById("tree").addEventListener("click", function (e) {
    var t = e.target.closest("[data-toggle]");
    if (t && (t.tagName === "BUTTON" || t.getAttribute("href") === "javascript:void 0")) { e.preventDefault(); var k = t.getAttribute("data-toggle"); expanded[k] = !expanded[k]; renderTree(); }
  });
  document.getElementById("page").addEventListener("change", function (e) {
    var cb = e.target.closest("input[data-filter]"); if (!cb) return;
    var f = state.filter.slice(), id = cb.getAttribute("data-filter"), i = f.indexOf(id);
    if (cb.checked && i < 0) f.push(id); if (!cb.checked && i >= 0) f.splice(i, 1);
    location.hash = href("HUB-LESSONS") + (f.length ? "&f=" + f.map(encodeURIComponent).join(",") : "");
  });
  var search = document.getElementById("search");
  search.addEventListener("input", function () { state.query = search.value.trim(); renderTree(); });
  search.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { search.value = ""; state.query = ""; renderTree(); }
    if (e.key === "Enter" && !document.getElementById("ask-form")) { var a = document.querySelector(".search-results a"); if (a) location.hash = a.getAttribute("href"); }
  });
  // ---------- Ask the Hub (AI provision; see js/ai.js) ----------
  var askPanel = document.getElementById("ask-panel");
  if (!askPanel) { askPanel = document.createElement("section"); askPanel.id = "ask-panel"; askPanel.className = "ask-panel"; askPanel.hidden = true; document.body.appendChild(askPanel); }
  var askSeq = 0;
  function askIntro() {
    var on = window.HubAI && window.HubAI.isConnected();
    return '<div class="ask-head"><h2>Ask the Hub</h2><span class="ai-status ' + (on ? "on" : "off") + '">' + (on ? "Internal AI connected" : "AI not connected \u00b7 keyword fallback") + '</span><button type="button" class="ask-close" aria-label="Close Ask the Hub">\u00d7</button></div>' +
      '<p class="ask-about">Ask the Hub will connect through an API to the organisation\'s internal AI service. It will answer only from the controlled data sources in this Hub, cite the pages and records it used by permanent ID, and respect access control. Until it is connected, questions are answered by keyword search over Hub pages.</p>';
  }
  function openAsk(q) {
    askPanel.hidden = false;
    var my = ++askSeq;
    if (!q) { askPanel.innerHTML = askIntro() + '<p class="empty">Type a question or keywords in the Ask the Hub bar and press Enter.</p>'; return; }
    askPanel.innerHTML = askIntro() + '<p class="empty">Searching\u2026</p>';
    var ask = window.HubAI ? window.HubAI.askHub(q) : Promise.resolve({ mode: "keyword", answer: "Ask the Hub module (js/ai.js) not loaded.", citations: [], note: "" });
    ask.then(function (r) {
      if (my !== askSeq) return;
      askPanel.innerHTML = askIntro() + '<div class="ask-q">\u201c' + esc(q) + '\u201d</div><p class="ask-answer">' + esc(r.answer) + "</p>" +
        (r.citations.length ? '<ol class="ask-cites">' + r.citations.map(function (c) { return '<li><a href="' + href(c.id) + '">' + esc(c.title) + '</a> <span class="mono nid">' + esc(c.id) + "</span>" + (c.snippet ? '<div class="ask-snip">' + esc(c.snippet) + "</div>" : "") + "</li>"; }).join("") + "</ol>" : "") +
        (r.note ? '<p class="ask-note">' + esc(r.note) + "</p>" : "");
    });
  }
  function closeAsk() { askPanel.hidden = true; }
  askPanel.addEventListener("click", function (e) { if (e.target.closest(".ask-close")) closeAsk(); else if (e.target.closest("a[href^='#/']")) closeAsk(); });
  var askForm = document.getElementById("ask-form");
  if (askForm) askForm.addEventListener("submit", function (e) { e.preventDefault(); openAsk(search.value.trim()); });
  function askFromHash() { var m = (location.hash || "").match(/[?&]ask=([^&]*)/); if (m) { var q = decodeURIComponent(m[1].replace(/\+/g, " ")); search.value = q; openAsk(q); } }

  // ---------- image lightbox ----------
  var lb = document.createElement("div"); lb.id = "lightbox"; lb.className = "lightbox"; lb.hidden = true; lb.setAttribute("role", "dialog"); lb.setAttribute("aria-modal", "true"); lb.setAttribute("aria-label", "Enlarged image");
  document.body.appendChild(lb);
  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest(".fig-open");
    if (b) {
      var inner = b.getAttribute("data-inline") ? b.querySelector("svg").outerHTML : '<img src="' + esc(b.getAttribute("data-src")) + '" alt="' + esc(b.getAttribute("data-alt")) + '">';
      lb.innerHTML = '<div class="lb-box"><button type="button" class="lb-close" aria-label="Close enlarged image">\u00d7</button><div class="lb-media">' + inner + '</div><p class="lb-cap">' + esc(b.getAttribute("data-caption")) + "</p></div>";
      lb.hidden = false; lb.querySelector(".lb-close").focus(); return;
    }
    if (!lb.hidden && (e.target === lb || (e.target.closest && e.target.closest(".lb-close")))) lb.hidden = true;
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") { if (!lb.hidden) lb.hidden = true; else closeAsk(); } });

  window.addEventListener("hashchange", function () { render(); askFromHash(); });
  window.EH = { openAsk: openAsk, data: D, byId: byId, backlinks: backlinks, outLinks: outLinks, buildTree: buildTree, render: render, allTags: allTags };
  render();
  askFromHash();
})();
