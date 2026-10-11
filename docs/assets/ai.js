/* Ask the Hub stub (interface kept from v0.8): HubAI.askHub(query) -> Promise<{answer, citations, mode, note}>.
   Set window.HUB_AI_ENDPOINT to an internal AI service URL; otherwise falls back to keyword search over
   this site's own index. Citations are permanent identifiers. The Framework index holds no production data. */
window.HubAI = (function () {
  function score(e, words) { var t = (e.t + " " + e.x).toLowerCase(), s = 0; words.forEach(function (w) { if (t.indexOf(w) >= 0) s += (e.t.toLowerCase().indexOf(w) >= 0 ? 3 : 1); }); return s; }
  function local(q) {
    var words = q.toLowerCase().split(/\s+/).filter(function (w) { return w.length > 1; });
    var hits = (window.HUB_INDEX || []).map(function (e) { return [score(e, words), e]; }).filter(function (x) { return x[0] > 0; })
      .sort(function (a, b) { return b[0] - a[0]; }).slice(0, 12).map(function (x) { return x[1]; });
    return { answer: hits.length ? "Pages that match your words (keyword search, not an AI answer):" : "No page in this Hub matches those words; the sources here hold no answer.",
             citations: hits.map(function (h) { return { id: h.id, title: h.t, url: h.u }; }), mode: "keyword", note: "Keyword fallback: no AI endpoint is configured." };
  }
  function askHub(q) {
    if (window.HUB_AI_ENDPOINT) return fetch(window.HUB_AI_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ q: q, hub: "FW" }) }).then(function (r) { return r.json(); }).catch(function () { return local(q); });
    return Promise.resolve(local(q));
  }
  return { askHub: askHub };
})();
