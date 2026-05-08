/* =========================================================================
   BookFinder UI - app.js
   -----------------------------------------------------------------------
   Talks to the Flask backend at /api/* (same origin when served by Flask,
   otherwise falls back to http://localhost:5000).
   ========================================================================= */

const API_BASE = (() => {
  if (location.port === "5000" || location.port === "") return "";
  return "http://localhost:5000";
})();

const els = {
  q:               document.getElementById("q"),
  clearBtn:        document.getElementById("clear-btn"),
  searchWrap:      document.querySelector(".search-input-wrap"),
  suggestions:     document.getElementById("suggestions"),
  sort:            document.getElementById("sort"),
  inStock:         document.getElementById("in-stock"),
  ratingMin:       document.getElementById("rating-min"),
  ratingMinOut:    document.getElementById("rating-min-out"),
  yearMin:         document.getElementById("year-min"),
  yearMax:         document.getElementById("year-max"),
  resetBtn:        document.getElementById("reset-filters"),
  health:          document.getElementById("health-indicator"),
  healthText:      document.getElementById("health-text"),
  results:         document.getElementById("results"),
  resultsCount:    document.getElementById("results-count"),
  resultsTime:     document.getElementById("results-time"),
  pagination:      document.getElementById("pagination"),
  emptyState:      document.getElementById("empty-state"),
  modal:           document.getElementById("modal"),
  modalBody:       document.getElementById("modal-body"),
  facets: {
    genres:    document.getElementById("facet-genres"),
    language:  document.getElementById("facet-language"),
    publisher: document.getElementById("facet-publisher"),
    tags:      document.getElementById("facet-tags"),
    year:      document.getElementById("facet-year"),
  },
};

const state = {
  q: "",
  page: 1,
  pageSize: 12,
  sort: "score desc",
  inStock: false,
  ratingMin: 0,
  yearMin: "",
  yearMax: "",
  selected: {
    genres:    new Set(),
    language:  new Set(),
    publisher: new Set(),
    tags:      new Set(),
  },
};

let suggestTimer = null;
let searchTimer  = null;
let suggestController = null;
let searchController  = null;
let activeSuggestion  = -1;

// --------------------------------------------------------------------------
// API helpers
// --------------------------------------------------------------------------
async function apiGet(path, params = {}, signal) {
  const url = new URL(API_BASE + path, location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (Array.isArray(v)) v.forEach(x => url.searchParams.append(k, x));
    else if (v !== "" && v !== null && v !== undefined)
      url.searchParams.append(k, v);
  });
  const resp = await fetch(url, { signal });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

// --------------------------------------------------------------------------
// Health
// --------------------------------------------------------------------------
async function refreshHealth() {
  try {
    const data = await apiGet("/api/health");
    els.health.classList.remove("bad");
    els.health.classList.add("ok");
    els.healthText.textContent = `Solr OK · ${data.documents} docs`;
  } catch (e) {
    els.health.classList.remove("ok");
    els.health.classList.add("bad");
    els.healthText.textContent = "Solr unreachable";
  }
}

// --------------------------------------------------------------------------
// Search
// --------------------------------------------------------------------------
function buildSearchParams() {
  const filters = {};
  if (state.q) filters.q = state.q;
  filters.page = state.page;
  filters.rows = state.pageSize;
  filters.sort = state.sort;
  if (state.inStock) filters.in_stock = 1;
  if (state.ratingMin > 0) filters.rating_min = state.ratingMin;
  if (state.yearMin) filters.year_min = state.yearMin;
  if (state.yearMax) filters.year_max = state.yearMax;
  for (const [k, set] of Object.entries(state.selected)) {
    if (set.size === 0) continue;
    const apiKey = ({ genres: "genre", language: "language",
                      publisher: "publisher", tags: "tag" })[k];
    filters[apiKey] = [...set];
  }
  return filters;
}

async function runSearch() {
  if (searchController) searchController.abort();
  searchController = new AbortController();

  els.results.setAttribute("aria-busy", "true");

  try {
    const data = await apiGet("/api/search", buildSearchParams(),
                              searchController.signal);
    renderResults(data);
    renderFacets(data.facets);
    renderPagination(data);
  } catch (e) {
    if (e.name === "AbortError") return;
    els.results.innerHTML =
      `<div class="empty-state"><h2>Search failed</h2><p>${e.message}</p></div>`;
  } finally {
    els.results.removeAttribute("aria-busy");
  }
}

function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(runSearch, 220);
}

// --------------------------------------------------------------------------
// Render results
// --------------------------------------------------------------------------
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;",
    '"': "&quot;", "'": "&#39;",
  })[c]);
}

function renderResults(data) {
  const { documents, total, elapsed_ms, qtime_ms, page_size, page } = data;

  els.resultsCount.textContent = total === 0
    ? "No results"
    : `${total.toLocaleString()} result${total === 1 ? "" : "s"}` +
      (state.q ? ` for "${state.q}"` : "");
  els.resultsTime.textContent =
    `Solr QTime ${qtime_ms}ms · round-trip ${elapsed_ms}ms`;

  if (documents.length === 0) {
    els.results.innerHTML = "";
    els.emptyState.hidden = false;
    return;
  }
  els.emptyState.hidden = true;

  els.results.innerHTML = documents.map(doc => {
    const hl = doc._highlight || {};
    const titleHtml = (hl.title && hl.title[0]) || escapeHtml(doc.title);
    const descHtml  = (hl.description && hl.description[0])
                       || escapeHtml((doc.description || "").slice(0, 220));
    const genres    = (doc.genres || []).slice(0, 2).map(g =>
      `<span class="card-tag">${escapeHtml(g)}</span>`).join("");
    return `
      <article class="card" data-id="${escapeHtml(doc.id)}">
        <h2 class="card-title">${titleHtml}</h2>
        <div class="card-author">by ${escapeHtml(doc.author)}</div>
        <div class="card-meta">
          <span class="pill star">&#9733; ${(doc.rating ?? 0).toFixed(1)}</span>
          <span class="pill">${doc.year ?? ""}</span>
          <span class="pill">${doc.pages ?? "?"} pp</span>
          <span class="pill">${escapeHtml(doc.language || "")}</span>
        </div>
        <div class="card-snippet">${descHtml}&hellip;</div>
        <div class="card-tags">${genres}</div>
        <div class="card-bottom">
          <span class="card-price">$${(doc.price ?? 0).toFixed(2)}</span>
          <span class="${doc.in_stock ? 'in-stock-yes' : 'in-stock-no'}">
            ${doc.in_stock ? "In stock" : "Out of stock"}
          </span>
        </div>
      </article>`;
  }).join("");

  els.results.querySelectorAll(".card").forEach(card => {
    card.addEventListener("click",
      () => openDetails(card.dataset.id));
  });
}

// --------------------------------------------------------------------------
// Render facets
// --------------------------------------------------------------------------
function renderFacets(facets) {
  if (!facets) return;
  const { fields, ranges } = facets;

  const map = [
    ["genres",    fields.genres,    "genres"],
    ["language",  fields.language,  "language"],
    ["publisher", fields.publisher, "publisher"],
    ["tags",      fields.tags,      "tags"],
  ];
  for (const [key, items, sel] of map) {
    const el = els.facets[key];
    if (!el || !items) continue;
    const selected = state.selected[sel];
    el.innerHTML = items.map(({ value, count }) => `
      <li data-value="${escapeHtml(value)}"
          class="${selected.has(value) ? "active" : ""}">
        <span>${escapeHtml(value)}</span>
        <span class="count">${count}</span>
      </li>`).join("");
    el.querySelectorAll("li").forEach(li => {
      li.addEventListener("click", () => {
        const v = li.dataset.value;
        if (selected.has(v)) selected.delete(v); else selected.add(v);
        state.page = 1;
        runSearch();
      });
    });
  }

  if (ranges && ranges.year && els.facets.year) {
    const yr = ranges.year;
    const buckets = (yr.buckets || []).filter(b => b.count > 0);
    els.facets.year.innerHTML = buckets.map(b => `
      <li data-from="${b.value}" data-to="${b.value + (yr.gap || 10) - 1}"
          class="${state.yearMin == b.value ? "active" : ""}">
        <span>${b.value}s</span>
        <span class="count">${b.count}</span>
      </li>`).join("");
    els.facets.year.querySelectorAll("li").forEach(li => {
      li.addEventListener("click", () => {
        if (state.yearMin == li.dataset.from && state.yearMax == li.dataset.to) {
          state.yearMin = state.yearMax = "";
        } else {
          state.yearMin = li.dataset.from;
          state.yearMax = li.dataset.to;
        }
        els.yearMin.value = state.yearMin;
        els.yearMax.value = state.yearMax;
        state.page = 1;
        runSearch();
      });
    });
  }
}

// --------------------------------------------------------------------------
// Pagination
// --------------------------------------------------------------------------
function renderPagination({ total, page, page_size }) {
  const totalPages = Math.max(1, Math.ceil(total / page_size));
  if (totalPages <= 1) {
    els.pagination.innerHTML = "";
    return;
  }

  const make = (label, p, opts = {}) => `
    <button class="page-btn ${opts.current ? "current" : ""}"
            ${opts.disabled ? "disabled" : ""}
            data-page="${p}">${label}</button>`;

  const pages = [];
  pages.push(make("&laquo;", page - 1, { disabled: page === 1 }));

  const window = 2;
  const start = Math.max(1, page - window);
  const end   = Math.min(totalPages, page + window);

  if (start > 1) {
    pages.push(make(1, 1, { current: page === 1 }));
    if (start > 2) pages.push(`<span class="page-btn" disabled>&hellip;</span>`);
  }
  for (let p = start; p <= end; p++) {
    pages.push(make(p, p, { current: p === page }));
  }
  if (end < totalPages) {
    if (end < totalPages - 1) pages.push(`<span class="page-btn" disabled>&hellip;</span>`);
    pages.push(make(totalPages, totalPages, { current: page === totalPages }));
  }
  pages.push(make("&raquo;", page + 1, { disabled: page === totalPages }));

  els.pagination.innerHTML = pages.join("");
  els.pagination.querySelectorAll("button[data-page]").forEach(b => {
    b.addEventListener("click", () => {
      state.page = +b.dataset.page;
      runSearch();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
}

// --------------------------------------------------------------------------
// Suggestions
// --------------------------------------------------------------------------
async function fetchSuggestions(q) {
  if (suggestController) suggestController.abort();
  suggestController = new AbortController();

  if (!q || q.length < 2) { els.suggestions.hidden = true; return; }

  try {
    const data = await apiGet("/api/suggest", { q }, suggestController.signal);
    const items = (data.suggestions || []).slice(0, 8);
    if (items.length === 0) { els.suggestions.hidden = true; return; }
    els.suggestions.innerHTML = items.map((s, i) => `
      <li data-term="${escapeHtml(s.term)}" data-i="${i}">
        <span>${escapeHtml(s.term)}</span>
        <small>${escapeHtml(s.source || "")}</small>
      </li>`).join("");
    els.suggestions.hidden = false;
    activeSuggestion = -1;
    els.suggestions.querySelectorAll("li").forEach(li => {
      li.addEventListener("mousedown", e => {
        e.preventDefault();
        els.q.value = li.dataset.term;
        state.q = li.dataset.term;
        state.page = 1;
        els.suggestions.hidden = true;
        runSearch();
      });
    });
  } catch (e) {
    if (e.name !== "AbortError") els.suggestions.hidden = true;
  }
}

// --------------------------------------------------------------------------
// Modal
// --------------------------------------------------------------------------
async function openDetails(id) {
  try {
    const doc = await apiGet(`/api/book/${encodeURIComponent(id)}`);
    els.modalBody.innerHTML = `
      <h2>${escapeHtml(doc.title)}</h2>
      <p style="color: var(--text-soft); margin-top: 4px;">
        by <strong>${escapeHtml(doc.author)}</strong>
      </p>
      <h3>Overview</h3>
      <p style="color: var(--text-soft);">${escapeHtml(doc.description || "")}</p>
      <h3>Details</h3>
      <div class="grid">
        <span>Year</span><b>${doc.year ?? ""}</b>
        <span>Pages</span><b>${doc.pages ?? "?"}</b>
        <span>Language</span><b>${escapeHtml(doc.language || "")}</b>
        <span>Publisher</span><b>${escapeHtml(doc.publisher || "")}</b>
        <span>ISBN</span><b style="font-family:monospace">${escapeHtml(doc.isbn || "")}</b>
        <span>Rating</span><b>&#9733; ${(doc.rating ?? 0).toFixed(1)}</b>
        <span>Price</span><b>$${(doc.price ?? 0).toFixed(2)}</b>
        <span>In stock</span><b>${doc.in_stock ? "Yes (" + (doc.stock_count ?? 0) + ")" : "No"}</b>
      </div>
      <h3>Genres</h3>
      <div class="card-tags">
        ${(doc.genres || []).map(g =>
          `<span class="card-tag">${escapeHtml(g)}</span>`).join("")}
      </div>
      <h3>Tags</h3>
      <div class="card-tags">
        ${(doc.tags || []).map(t =>
          `<span class="card-tag">${escapeHtml(t)}</span>`).join("")}
      </div>`;
    els.modal.hidden = false;
  } catch (e) {
    els.modalBody.innerHTML = `<p>Could not load: ${e.message}</p>`;
    els.modal.hidden = false;
  }
}

// --------------------------------------------------------------------------
// Wire up events
// --------------------------------------------------------------------------
function bindEvents() {
  els.q.addEventListener("input", () => {
    state.q = els.q.value.trim();
    els.searchWrap.classList.toggle("has-text", state.q.length > 0);
    state.page = 1;
    debounceSearch();
    clearTimeout(suggestTimer);
    suggestTimer = setTimeout(() => fetchSuggestions(state.q), 120);
  });

  els.q.addEventListener("keydown", e => {
    if (els.suggestions.hidden) return;
    const items = els.suggestions.querySelectorAll("li");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      activeSuggestion = (activeSuggestion + 1) % items.length;
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      activeSuggestion = (activeSuggestion - 1 + items.length) % items.length;
    } else if (e.key === "Enter" && activeSuggestion >= 0) {
      e.preventDefault();
      const li = items[activeSuggestion];
      els.q.value = li.dataset.term;
      state.q = li.dataset.term;
      els.suggestions.hidden = true;
      runSearch();
      return;
    } else if (e.key === "Escape") {
      els.suggestions.hidden = true;
      return;
    }
    items.forEach((li, i) => li.classList.toggle("active", i === activeSuggestion));
  });

  els.q.addEventListener("blur", () => {
    setTimeout(() => { els.suggestions.hidden = true; }, 120);
  });

  els.clearBtn.addEventListener("click", () => {
    els.q.value = "";
    state.q = "";
    els.searchWrap.classList.remove("has-text");
    els.suggestions.hidden = true;
    state.page = 1;
    runSearch();
  });

  els.sort.addEventListener("change", () => {
    state.sort = els.sort.value; state.page = 1; runSearch();
  });

  els.inStock.addEventListener("change", () => {
    state.inStock = els.inStock.checked; state.page = 1; runSearch();
  });

  els.ratingMin.addEventListener("input", () => {
    state.ratingMin = +els.ratingMin.value;
    els.ratingMinOut.value = state.ratingMin;
    state.page = 1;
    debounceSearch();
  });

  [els.yearMin, els.yearMax].forEach(el => {
    el.addEventListener("change", () => {
      state.yearMin = els.yearMin.value;
      state.yearMax = els.yearMax.value;
      state.page = 1;
      runSearch();
    });
  });

  els.resetBtn.addEventListener("click", () => {
    Object.values(state.selected).forEach(s => s.clear());
    state.inStock = false; els.inStock.checked = false;
    state.ratingMin = 0; els.ratingMin.value = 0; els.ratingMinOut.value = 0;
    state.yearMin = state.yearMax = "";
    els.yearMin.value = ""; els.yearMax.value = "";
    state.page = 1;
    runSearch();
  });

  els.modal.querySelectorAll("[data-close]").forEach(el =>
    el.addEventListener("click", () => { els.modal.hidden = true; }));
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") els.modal.hidden = true;
  });
}

// --------------------------------------------------------------------------
// Boot
// --------------------------------------------------------------------------
async function boot() {
  bindEvents();
  await refreshHealth();
  setInterval(refreshHealth, 30_000);
  await runSearch();
}

document.addEventListener("DOMContentLoaded", boot);
