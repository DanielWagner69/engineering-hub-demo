/* Engineering Hub - "Ask the Hub" AI provision (v0.6).
 *
 * Interface:  HubAI.askHub(query) -> Promise<{ answer, citations, mode, note }>
 *   answer     plain text answer (string)
 *   citations  [{ id, title }]  Hub pages / records the answer is based on (permanent IDs)
 *   mode       "ai" (internal AI service) or "keyword" (local fallback)
 *   note       optional explanation shown with the result
 *
 * Configuration: set window.HUB_AI_ENDPOINT (before this file loads, e.g. in a small config script)
 * to the URL of the internal AI service. It is null by default, so the Hub falls back to keyword
 * search over its own pages. Expected service contract (POST, JSON):
 *   request   { query, hub: { kind, version }, sources: "controlled-hub-data" }
 *   response  { answer: string, citations: [{ id: string }] }
 * The service must answer only from controlled Hub data, cite permanent IDs and enforce the
 * caller's access rights. Citations that do not resolve to a Hub page are dropped here.
 */
(function () {
  "use strict";
  if (typeof window.HUB_AI_ENDPOINT === "undefined") window.HUB_AI_ENDPOINT = null;

  function data() { return window.HUB_DATA || { pages: [] }; }
  function pageText(p) {
    return [p.id, p.title, p.description, p.summary, p.category]
      .concat((p.sections || []).map(function (s) { return s.heading + " " + s.body; }))
      .concat((p.images || []).map(function (i) { return i.caption + " " + i.alt; }))
      .filter(Boolean).join(" ").replace(/\[\[|\]\]/g, "");
  }
  function bodyText(p) {
    return [p.description, p.summary].concat((p.sections || []).map(function (s) { return s.heading + ". " + s.body; }))
      .concat((p.images || []).map(function (i) { return i.caption; })).filter(Boolean).join(" ").replace(/\[\[|\]\]/g, "").replace(/\n- /g, " \u2022 ").replace(/\s+/g, " ");
  }
  function snippet(text, terms) {
    if (!text) return "";
    var low = text.toLowerCase(), at = -1;
    terms.some(function (t) { at = low.indexOf(t); return at >= 0; });
    if (at < 0) return text.slice(0, 160);
    var s = Math.max(0, at - 60);
    return (s ? "\u2026" : "") + text.slice(s, s + 180).trim() + (s + 180 < text.length ? "\u2026" : "");
  }
  var STOP = { the: 1, and: 1, for: 1, with: 1, what: 1, how: 1, does: 1, are: 1, is: 1, a: 1, an: 1, of: 1, to: 1, in: 1, on: 1, do: 1, i: 1, me: 1, about: 1, which: 1, who: 1 };

  /** Local keyword search over Hub pages (the fallback). Returns ranked [{id,title,type,score,snippet}]. */
  function keywordSearch(query, limit) {
    var terms = String(query || "").toLowerCase().split(/[^a-z0-9\-]+/).filter(function (t) { return t.length > 1 && !STOP[t]; });
    if (!terms.length) return [];
    return data().pages.map(function (p) {
      var text = pageText(p), low = text.toLowerCase(), title = (p.title || "").toLowerCase(), score = 0;
      terms.forEach(function (t) {
        if (p.id.toLowerCase() === t) score += 20;
        if (title.indexOf(t) >= 0) score += 6;
        var n = low.split(t).length - 1; score += Math.min(n, 5);
      });
      return { id: p.id, title: p.title, type: p.type, score: score, snippet: snippet(bodyText(p), terms) };
    }).filter(function (r) { return r.score > 0; })
      .sort(function (a, b) { return b.score - a.score || a.id.localeCompare(b.id); })
      .slice(0, limit || 8);
  }

  function knownCitations(list) {
    var byId = {}; data().pages.forEach(function (p) { byId[p.id] = p; });
    return (list || []).map(function (c) { return typeof c === "string" ? { id: c } : c; })
      .filter(function (c) { return c && byId[c.id]; })
      .map(function (c) { return { id: c.id, title: byId[c.id].title }; });
  }

  function fallback(query, note) {
    var hits = keywordSearch(query, 8);
    return {
      mode: "keyword",
      answer: hits.length ? "No AI service is connected, so these are the Hub pages that best match your words." : "No AI service is connected, and no Hub pages match your words.",
      citations: hits.map(function (h) { return { id: h.id, title: h.title, snippet: h.snippet }; }),
      note: note || "Keyword search over controlled Hub pages only. When the internal AI service is connected, answers will be generated from the same controlled sources, with citations."
    };
  }

  /** askHub(query) -> Promise<{answer, citations, mode, note}> */
  function askHub(query) {
    var ep = window.HUB_AI_ENDPOINT;
    if (!ep || typeof fetch !== "function") return Promise.resolve(fallback(query));
    var meta = data().meta || {};
    return fetch(ep, {
      method: "POST", headers: { "Content-Type": "application/json" }, credentials: "include",
      body: JSON.stringify({ query: query, hub: { kind: meta.hubKind || "Framework", version: meta.version }, sources: "controlled-hub-data" })
    }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) {
        var cites = knownCitations(j.citations);
        return { mode: "ai", answer: String(j.answer || ""), citations: cites,
                 note: cites.length ? "Answer from the internal AI service, based only on the cited Hub sources." : "The AI service returned no citable Hub sources; treat this answer as unverified." };
      })
      .catch(function (e) { return fallback(query, "The AI service could not be reached (" + e.message + "), so keyword search was used instead."); });
  }

  window.HubAI = { askHub: askHub, keywordSearch: keywordSearch, isConnected: function () { return !!window.HUB_AI_ENDPOINT; } };
})();
