"use strict";
// Runs in <head> before paint so the correct theme is applied with no flash.
// Uses the saved choice if any, else the OS preference, else dark. No inline
// script (keeps the strict CSP intact); the toggle button is wired in app.js.
(function () {
  try {
    var saved = localStorage.getItem("theme");
    var theme =
      saved === "light" || saved === "dark"
        ? saved
        : window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches
        ? "light"
        : "dark";
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {
    document.documentElement.setAttribute("data-theme", "dark");
  }
})();
