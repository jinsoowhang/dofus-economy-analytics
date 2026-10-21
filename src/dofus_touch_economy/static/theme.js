"use strict";

(() => {
  const key = "dofus-economy-theme";
  const choices = new Set(["system", "light", "dark"]);
  const valid = (value) => choices.has(value) ? value : "system";
  const read = () => {
    try {
      return valid(localStorage.getItem(key));
    } catch {
      return "system";
    }
  };
  const apply = (value) => {
    document.documentElement.dataset.theme = value;
    document.querySelectorAll("[data-theme-select]").forEach((select) => {
      select.value = value;
    });
  };

  // Run before the stylesheet to apply the saved choice on the first paint.
  apply(read());
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-theme-select]").forEach((select) => {
      select.value = document.documentElement.dataset.theme;
      select.closest(".theme-control").hidden = false;
      select.addEventListener("change", () => {
        const value = valid(select.value);
        apply(value);
        try {
          localStorage.setItem(key, value);
        } catch {
          // The selection still works for this page when storage is unavailable.
        }
      });
    });
  });
  window.addEventListener("storage", (event) => {
    if (event.key === key || event.key === null) apply(read());
  });
  window.addEventListener("pageshow", (event) => {
    if (event.persisted) apply(read());
  });
})();
