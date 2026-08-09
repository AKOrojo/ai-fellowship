"use strict";

const CATEGORY_TITLES = {
  "industry-residency": "Industry AI Residencies",
  "research-safety": "Research & Safety",
  "academic-phd": "Academic & PhD",
  "policy-grants": "Policy, Nonprofit & Grants",
};

// Research areas — a fellowship can belong to several. Order drives chip order.
const AREAS = [
  ["technical", "Technical"],
  ["interpretability", "Interpretability"],
  ["governance", "Governance"],
  ["security", "Security"],
  ["biosecurity", "Biosecurity"],
  ["societal", "Societal"],
  ["generalist", "Generalist"],
  ["other", "Other"],
];
const AREA_LABELS = Object.fromEntries(AREAS);

const STATUS_LABELS = {
  open: "Open",
  upcoming: "Upcoming",
  rolling: "Rolling",
  closed: "Closed",
};

// Status rank for the default "active first" sort.
const STATUS_RANK = { open: 0, upcoming: 1, rolling: 2, closed: 3 };

const FAR_FUTURE = "9999-12-31";
const MINUTE = 60 * 1000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

const state = { all: [], filtered: [], areas: new Set(), counts: {}, timers: [] };

function isSafeUrl(url) {
  // Defense in depth: only render https links, even though data is pre-validated.
  return typeof url === "string" && /^https:\/\//i.test(url);
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function updateToggleButton(theme) {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  const dark = theme === "dark";
  btn.textContent = dark ? "☀" : "☾";
  btn.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
  btn.setAttribute("aria-pressed", String(!dark));
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try { localStorage.setItem("theme", theme); } catch (e) { /* storage unavailable */ }
  updateToggleButton(theme);
}

function initTheme() {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  // theme.js already applied the initial theme before paint; just sync the icon.
  updateToggleButton(document.documentElement.getAttribute("data-theme") || "dark");
  btn.addEventListener("click", function () {
    const next =
      document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

/* ---------- deadlines, status, countdown ---------- */

// "2026-09-30" -> local midnight at the start of that day, or null.
function parseDate(value) {
  if (typeof value !== "string") return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return isNaN(d.getTime()) ? null : d;
}

// Mirrors scripts/generate.py derive_status(): the deadline day itself counts
// as closed, so the site never disagrees with the generated README badges.
function statusOf(item, now) {
  if (item.deadline === "Rolling") return "rolling";
  if (item.deadline === "Closed") return "closed";
  const deadline = parseDate(item.deadline);
  if (deadline && now >= deadline) return "closed";
  const opens = parseDate(item.opens);
  if (opens && now < opens) return "upcoming";
  return "open";
}

function plural(n, word) {
  return n + " " + word + (n === 1 ? "" : "s");
}

// Live "time left" string. Days+hours far out, down to seconds in the last day.
function countdownText(item, now) {
  const status = statusOf(item, now);
  if (status === "rolling") return "Rolling — applications reviewed continuously";
  if (status === "closed") {
    const past = parseDate(item.deadline);
    return past ? "Closed — deadline passed " + item.deadline : "Closed";
  }
  const deadline = parseDate(item.deadline);
  if (!deadline) return "Deadline not announced yet";

  if (status === "upcoming") {
    const opens = parseDate(item.opens);
    const untilOpen = opens ? opens.getTime() - now.getTime() : 0;
    const days = Math.ceil(untilOpen / DAY);
    return "Opens in " + plural(days, "day") + " (" + item.opens + ")";
  }

  let left = deadline.getTime() - now.getTime();
  if (left < 0) left = 0;
  const days = Math.floor(left / DAY);
  const hours = Math.floor((left % DAY) / HOUR);
  const mins = Math.floor((left % HOUR) / MINUTE);
  const secs = Math.floor((left % MINUTE) / 1000);
  if (days >= 7) return plural(days, "day") + " left to apply";
  if (days >= 1) return days + "d " + hours + "h " + mins + "m left to apply";
  return hours + "h " + mins + "m " + secs + "s left to apply";
}

// Under a week left (and still open) — worth shouting about.
function isUrgent(item, now) {
  if (statusOf(item, now) !== "open") return false;
  const deadline = parseDate(item.deadline);
  return !!deadline && deadline.getTime() - now.getTime() < 7 * DAY;
}

function deadlineKey(item) {
  const d = item.deadline;
  if (!d || d === "Rolling" || d === "Unknown" || d === "Closed") return FAR_FUTURE;
  return d;
}

/* ---------- rendering ---------- */

function card(item, now) {
  const status = statusOf(item, now);
  const c = el("article", "card" + (status === "closed" ? " past" : ""));

  const h = el("h2");
  if (isSafeUrl(item.url)) {
    const a = el("a", null, item.name || "");
    a.href = item.url;
    a.rel = "noopener noreferrer";
    a.target = "_blank";
    h.appendChild(a);
  } else {
    h.textContent = item.name || "";
  }
  c.appendChild(h);
  c.appendChild(el("p", "org", item.organization));
  c.appendChild(el("p", "desc", item.description));

  const countdown = el(
    "p",
    "countdown " + status + (isUrgent(item, now) ? " urgent" : ""),
    countdownText(item, now)
  );
  c.appendChild(countdown);

  const areas = el("div", "area-tags");
  for (const a of item.areas || []) {
    areas.appendChild(el("span", "area-tag area-" + a, AREA_LABELS[a] || a));
  }
  c.appendChild(areas);

  const meta = el("div", "meta");
  const badge = el("span", "badge " + status, STATUS_LABELS[status] || status);
  meta.appendChild(badge);
  if (item.cycle) meta.appendChild(el("span", "cycle", item.cycle));
  meta.appendChild(el("span", null, "Deadline: " + (item.deadline || "Unknown")));
  meta.appendChild(el("span", null, item.location || ""));
  meta.appendChild(el("span", null, CATEGORY_TITLES[item.category] || item.category));
  c.appendChild(meta);

  // Re-read the item on every tick so a deadline passing mid-session updates live.
  state.timers.push({ node: countdown, badge: badge, card: c, item: item });
  return c;
}

function render() {
  const now = new Date();
  const list = document.getElementById("list");
  list.textContent = "";
  state.timers = [];
  for (const it of state.filtered) list.appendChild(card(it, now));
  if (!state.filtered.length) {
    list.appendChild(el("p", "empty", "No fellowships match these filters."));
  }
  const open = state.filtered.filter((it) => statusOf(it, now) === "open").length;
  document.getElementById("count").textContent =
    state.filtered.length + " of " + state.all.length + " entries · " + open + " open now";
}

// Cheap 1s tick: only rewrites the countdown line, never re-sorts under the user.
function tick() {
  const now = new Date();
  for (const t of state.timers) {
    t.node.textContent = countdownText(t.item, now);
    const status = statusOf(t.item, now);
    t.node.className = "countdown " + status + (isUrgent(t.item, now) ? " urgent" : "");
    t.badge.textContent = STATUS_LABELS[status] || status;
    t.badge.className = "badge " + status;
    t.card.classList.toggle("past", status === "closed");
  }
}

/* ---------- filtering ---------- */

function apply() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const cat = document.getElementById("category").value;
  const status = document.getElementById("status").value;
  const sort = document.getElementById("sort").value;
  const now = new Date();

  const items = state.all.filter((it) => {
    if (cat && it.category !== cat) return false;
    if (status && statusOf(it, now) !== status) return false;
    if (state.areas.size) {
      const areas = it.areas || [];
      if (!areas.some((a) => state.areas.has(a))) return false;
    }
    if (q) {
      const hay = [
        it.name, it.organization, it.description, it.cycle, it.location,
        (it.areas || []).join(" "), (it.tags || []).join(" "),
      ].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  if (sort === "name") {
    items.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  } else if (sort === "deadline") {
    items.sort((a, b) => deadlineKey(a).localeCompare(deadlineKey(b)));
  } else {
    // Default: still-active first (soonest deadline on top), closed last.
    items.sort((a, b) => {
      const ra = STATUS_RANK[statusOf(a, now)];
      const rb = STATUS_RANK[statusOf(b, now)];
      if (ra !== rb) return ra - rb;
      if (ra === STATUS_RANK.closed) {
        // Most recently closed first — the freshest history is the useful part.
        return deadlineKey(b).localeCompare(deadlineKey(a));
      }
      const byDeadline = deadlineKey(a).localeCompare(deadlineKey(b));
      return byDeadline || String(a.name).localeCompare(String(b.name));
    });
  }

  state.filtered = items;
  render();
}

/* ---------- controls ---------- */

function populateCategories() {
  const sel = document.getElementById("category");
  sel.appendChild(el("option", null, "All program types")).value = "";
  for (const [val, label] of Object.entries(CATEGORY_TITLES)) {
    const o = el("option", null, label);
    o.value = val;
    sel.appendChild(o);
  }
}

function buildAreaChips() {
  const wrap = document.getElementById("area-chips");
  wrap.textContent = "";
  state.counts = {};
  for (const it of state.all) {
    for (const a of it.areas || []) state.counts[a] = (state.counts[a] || 0) + 1;
  }
  for (const [val, label] of AREAS) {
    const chip = el("button", "chip area-" + val);
    chip.type = "button";
    chip.setAttribute("aria-pressed", "false");
    chip.appendChild(el("span", "chip-label", label));
    chip.appendChild(el("span", "chip-count", String(state.counts[val] || 0)));
    chip.addEventListener("click", function () {
      if (state.areas.has(val)) state.areas.delete(val);
      else state.areas.add(val);
      chip.classList.toggle("on", state.areas.has(val));
      chip.setAttribute("aria-pressed", String(state.areas.has(val)));
      apply();
    });
    wrap.appendChild(chip);
  }
}

function resetFilters() {
  document.getElementById("search").value = "";
  document.getElementById("category").value = "";
  document.getElementById("status").value = "";
  document.getElementById("sort").value = "smart";
  state.areas.clear();
  for (const chip of document.querySelectorAll("#area-chips .chip")) {
    chip.classList.remove("on");
    chip.setAttribute("aria-pressed", "false");
  }
  apply();
}

async function init() {
  initTheme();
  populateCategories();
  for (const id of ["search", "category", "status", "sort"]) {
    document.getElementById(id).addEventListener("input", apply);
  }
  document.getElementById("reset").addEventListener("click", resetFilters);
  try {
    const res = await fetch("data.json", { cache: "no-cache" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    state.all = Array.isArray(data) ? data : [];
  } catch (err) {
    document.getElementById("count").textContent = "Could not load data.";
    return;
  }
  buildAreaChips();
  apply();
  setInterval(tick, 1000);
}

document.addEventListener("DOMContentLoaded", init);
