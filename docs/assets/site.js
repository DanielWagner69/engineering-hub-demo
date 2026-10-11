(function () {
  var root = document.documentElement.getAttribute("data-root") || "./";
  if (location.protocol === "file:") document.querySelectorAll("a[href]").forEach(function (a) { var h = a.getAttribute("href"); if (!/^[a-z]+:|^#/.test(h) && /\/$/.test(h)) a.setAttribute("href", h + "index.html"); });
  /* v0.8 hash links (#/p/ID, #/f/facet, #/home) redirect to the v1.0 readable address */
  var m = (location.hash || "").match(/^#\/(p|f)\/([^?&]+)/);
  if (m && window.HUB_ALIASES) { var k = decodeURIComponent(m[2]), t = window.HUB_ALIASES[m[1] === "f" ? "facet:" + k : k] || window.HUB_ALIASES["*"]; if (t) location.replace(root + t); }
  var f = document.getElementById("ask"), q = document.getElementById("q"), out = document.getElementById("results");
  if (!f) return;
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  f.addEventListener("submit", function (e) {
    e.preventDefault();
    window.HubAI.askHub(q.value).then(function (r) {
      out.innerHTML = '<p><b>' + esc(r.answer) + '</b></p>' + r.citations.map(function (c) { return '<a href="' + root + c.url + '">' + esc(c.title) + ' <small>(' + esc(c.id) + ')</small></a>'; }).join("") + '<p><small>' + esc(r.note) + '</small></p>';
      out.style.display = "block"; out.setAttribute("tabindex", "-1"); out.focus();
    });
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") out.style.display = "none"; });
})();
