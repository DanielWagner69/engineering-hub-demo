/* v8 tree-page layout (Requirements v24.6 5.23 to 5.29): theme setting, filters that filter the page, Expand all, mobile rail. */
(function () {
  var K = "hub-theme", q = new URLSearchParams(location.search), t = q.get("theme") || localStorage.getItem(K) || "company";
  document.documentElement.setAttribute("data-theme", t);
  function ready(f) { if (document.readyState !== "loading") f(); else document.addEventListener("DOMContentLoaded", f); }
  ready(function () {
    var g = document.querySelector(".gear"), p = document.querySelector(".settings");
    if (g && p) {
      g.addEventListener("click", function () { var o = p.classList.toggle("open"); g.setAttribute("aria-expanded", o); });
      p.querySelectorAll("input[name=th]").forEach(function (i) { i.checked = i.value === t; i.addEventListener("change", function () { t = i.value; localStorage.setItem(K, t); document.documentElement.setAttribute("data-theme", t); }); });
    }
    var rb = document.querySelector(".rail-btn"); if (rb) rb.addEventListener("click", function () { document.body.classList.toggle("rail-open"); });
    var xa = document.querySelector(".xall");
    if (xa) xa.addEventListener("click", function () { var c = document.querySelectorAll("details.cat"), open = [].some.call(c, function (d) { return !d.open; }); c.forEach(function (d) { d.open = open; }); xa.textContent = open ? "Collapse all" : "Expand all"; });
    var sels = document.querySelectorAll("select[data-f]"), st = {};
    function inr(v) { if (!st.eff) return true; var a = st.eff.split("-"), b = (v || "").split("-"); if (b.length < 2) return true; return +b[0] <= +a[1] && +b[1] >= +a[0]; }
    function tag(el, k) { var v = el.getAttribute("data-" + k); if (!st[k] || v === null) return true; v = v.split(" "); return v.indexOf("ALL") >= 0 || v.indexOf(st[k]) >= 0; }
    function apply() {
      var on = [];
      sels.forEach(function (s) { st[s.getAttribute("data-f")] = s.value; s.closest(".f").classList.toggle("on", !!s.value); if (s.value) on.push(s.options[s.selectedIndex].text); });
      document.querySelectorAll("[data-row]").forEach(function (r) { r.hidden = !(inr(r.getAttribute("data-eff")) && tag(r, "lcs") && tag(r, "disc") && tag(r, "dty") && tag(r, "scope")); });
      document.querySelectorAll("details.cat").forEach(function (d) { var rs = d.querySelectorAll("[data-row]"), n = [].filter.call(rs, function (r) { return !r.hidden; }).length, c = d.querySelector(".cnt"); if (c && rs.length) c.textContent = n; var e = d.querySelector(".fempty"); if (e) e.hidden = !(rs.length && !n); });
      document.querySelectorAll(".tile[data-cat]").forEach(function (x) { var d = document.getElementById(x.getAttribute("data-cat")); if (!d) return; var rs = d.querySelectorAll("[data-row]" + (x.getAttribute("data-sel") || "")); if (!rs.length) return; x.querySelector("b").textContent = [].filter.call(rs, function (r) { return !r.hidden; }).length; });
      var fs = document.querySelector(".fstate"); if (fs) { fs.hidden = !on.length; var b = fs.querySelector("b"); if (b) b.textContent = on.join(" · "); }
      var u = new URLSearchParams(location.search); Object.keys(st).forEach(function (k) { if (st[k]) u.set(k, st[k]); else u.delete(k); }); var qs = u.toString(); history.replaceState(null, "", location.pathname + (qs ? "?" + qs : "") + location.hash);
    }
    sels.forEach(function (s) { var v = q.get(s.getAttribute("data-f")); if (v !== null && [].some.call(s.options, function (o) { return o.value === v; })) s.value = v; s.addEventListener("change", apply); });
    var rs = document.querySelector(".reset"); if (rs) rs.addEventListener("click", function () { sels.forEach(function (s) { s.value = ""; }); apply(); });
    var cl = document.querySelector(".fstate .clr"); if (cl) cl.addEventListener("click", function () { sels.forEach(function (s) { s.value = ""; }); apply(); });
    document.querySelectorAll(".tile[data-cat]").forEach(function (x) { x.addEventListener("click", function () { var d = document.getElementById(x.getAttribute("data-cat")); if (d) d.open = true; }); });
    if (location.hash) { var h = document.getElementById(location.hash.slice(1)); if (h && h.tagName === "DETAILS") h.open = true; }
    apply();
  });
})();
