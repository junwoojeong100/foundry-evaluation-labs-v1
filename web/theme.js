(() => {
  "use strict";

  const messages = JSON.parse(document.getElementById("guide-messages").textContent);
  const key = "foundry-evaluation-guide:theme:v1";
  const prefersDark = typeof window.matchMedia === "function"
    && window.matchMedia("(prefers-color-scheme: dark)").matches;
  let theme = prefersDark ? "dark" : "light";
  let warning = "";
  try {
    const saved = window.localStorage.getItem(key);
    if (saved === "light" || saved === "dark") theme = saved;
    else if (saved !== null) warning = messages.themeInvalid;
  } catch {
    warning = messages.themeReadError;
  }
  document.documentElement.dataset.theme = theme;

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-theme-toggle]");
    const feedback = document.querySelector("[data-theme-feedback]");
    if (!button || !feedback) return;

    function render() {
      document.documentElement.dataset.theme = theme;
      button.textContent = theme === "dark" ? messages.themeLight : messages.themeDark;
      button.setAttribute("aria-label", theme === "dark" ? messages.themeLightLabel : messages.themeDarkLabel);
      feedback.textContent = warning;
      feedback.hidden = !warning;
    }

    button.addEventListener("click", () => {
      theme = theme === "light" ? "dark" : "light";
      try {
        window.localStorage.setItem(key, theme);
        warning = "";
      } catch {
        warning = messages.themeWriteError;
      }
      render();
    });

    render();
    button.hidden = false;
  }, { once: true });
})();
