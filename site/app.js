"use strict";

const CATEGORY_TITLES = {
  "industry-residency": "Industry AI Residencies",
  "research-safety": "Research & Safety",
  "academic-phd": "Academic & PhD",
  "policy-grants": "Policy, Nonprofit & Grants",
};

const state = { all: [], filtered: [] };

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

function deadlineKey(item) {
  const d = item.deadline;
  if (!d || d === "Rolling" || d === "Unknown") return "9999-12-31";
  return d;
}

function card(item) {
  const c = el("article", "card");
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

  const meta = el("div", "meta");
  meta.appendChild(el("span", "badge " + (item.status || ""), (item.status || "")));
  if (item.cycle) meta.appendChild(el("span", "cycle", item.cycle));
  meta.appendChild(el("span", null, "Deadline: " + (item.deadline || "Unknown")));
  meta.appendChild(el("span", null, item.location || ""));
  meta.appendChild(el("span", null, CATEGORY_TITLES[item.category] || item.category));
  c.appendChild(meta);
  return c;
}

function apply() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const cat = document.getElementById("category").value;
  const status = document.getElementById("status").value;
  const sort = document.getElementById("sort").value;

  let items = state.all.filter((it) => {
    if (cat && it.category !== cat) return false;
    if (status && it.status !== status) return false;
    if (q) {
      const hay = [it.name, it.organization, it.description, it.cycle].join(" ").toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  items.sort((a, b) =>
    sort === "name"
      ? String(a.name).localeCompare(String(b.name))
      : deadlineKey(a).localeCompare(deadlineKey(b))
  );

  state.filtered = items;
  render();
}

function render() {
  const list = document.getElementById("list");
  list.textContent = "";
  for (const it of state.filtered) list.appendChild(card(it));
  document.getElementById("count").textContent =
    state.filtered.length + " of " + state.all.length + " fellowships";
}

function populateCategories() {
  const sel = document.getElementById("category");
  sel.appendChild(el("option", null, "All categories")).value = "";
  for (const [val, label] of Object.entries(CATEGORY_TITLES)) {
    const o = el("option", null, label);
    o.value = val;
    sel.appendChild(o);
  }
}

async function init() {
  initTheme();
  populateCategories();
  for (const id of ["search", "category", "status", "sort"]) {
    document.getElementById(id).addEventListener("input", apply);
  }
  try {
    const res = await fetch("data.json", { cache: "no-cache" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    state.all = Array.isArray(data) ? data : [];
  } catch (err) {
    document.getElementById("count").textContent = "Could not load data.";
    return;
  }
  apply();
}

document.addEventListener("DOMContentLoaded", init);
