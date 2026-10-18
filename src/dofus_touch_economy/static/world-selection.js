"use strict";

(() => {
  const world = document.body.dataset.world;
  window.economyStorageKey = (key) => world === "touch-blair" ? key : `${key}:${world}`;
  window.economyWorldUrl = (value) => {
    const url = new URL(value, window.location.href);
    if (url.origin === window.location.origin &&
        !/^\/(static|item-icons|oauth2)\//.test(url.pathname) &&
        url.pathname !== "/select-world") {
      url.searchParams.set("world", world);
    }
    return url.href;
  };

  const pin = (root) => {
    root.querySelectorAll("a[href]").forEach((link) => {
      if (!link.getAttribute("href").startsWith("#")) link.href = window.economyWorldUrl(link.href);
    });
    root.querySelectorAll("form:not(.world-selector)").forEach((form) => {
      form.action = window.economyWorldUrl(form.action);
    });
  };
  pin(document);
  // Dynamically created calculator links and forms receive the same tab context.
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (link && !link.getAttribute("href").startsWith("#")) {
      link.href = window.economyWorldUrl(link.href);
    }
  }, true);
  document.addEventListener("submit", (event) => {
    if (!event.target.matches(".world-selector")) {
      event.target.action = window.economyWorldUrl(event.target.action);
    }
  }, true);
  document.addEventListener("htmx:configRequest", (event) => {
    event.detail.headers["X-Economy-World"] = world;
    event.detail.parameters.world = world;
  });
  document.addEventListener("htmx:afterSwap", () => pin(document));
  // Fetch-based inline editors and sync polling also belong to the open tab.
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, options = {}) => {
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    if (url.origin !== location.origin) return nativeFetch(input, options);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    new Headers(options.headers).forEach((value, key) => headers.set(key, value));
    headers.set("X-Economy-World", world);
    return nativeFetch(input, {...options, headers});
  };

  const game = document.querySelector("#world-game");
  const server = document.querySelector("#world-server");
  const options = Array.from(server.options).map((option) => option.cloneNode(true));
  const updateServers = () => {
    server.replaceChildren(...options.filter((option) => option.dataset.game === game.value)
      .map((option) => option.cloneNode(true)));
  };
  game.addEventListener("change", updateServers);
  updateServers();
  // Keep the current tab's workspace explicit across reloads and browser Back.
  const current = new URL(location.href);
  current.searchParams.set("world", world);
  history.replaceState(history.state, "", current);
  document.addEventListener("htmx:pushedIntoHistory", () => {
    history.replaceState(history.state, "", window.economyWorldUrl(location.href));
  });
})();
