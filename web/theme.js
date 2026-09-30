(() => {
  "use strict";

  const key = "foundry-evaluation-guide:theme:v1";
  let theme = "light";
  let warning = "";
  try {
    const saved = window.localStorage.getItem(key);
    if (saved === "light" || saved === "dark") theme = saved;
    else if (saved !== null) warning = "저장된 화면 설정이 올바르지 않아 밝은 모드로 열었습니다.";
  } catch {
    warning = "화면 설정을 읽을 수 없어 밝은 모드로 열었습니다. 변경은 현재 창에만 적용될 수 있습니다.";
  }
  document.documentElement.dataset.theme = theme;

  document.addEventListener("DOMContentLoaded", () => {
    const button = document.querySelector("[data-theme-toggle]");
    const feedback = document.querySelector("[data-theme-feedback]");
    if (!button || !feedback) return;

    function render() {
      document.documentElement.dataset.theme = theme;
      button.textContent = theme === "dark" ? "밝게" : "어둡게";
      button.setAttribute("aria-label", theme === "dark" ? "밝은 화면으로 전환" : "어두운 화면으로 전환");
      feedback.textContent = warning;
      feedback.hidden = !warning;
    }

    button.addEventListener("click", () => {
      theme = theme === "light" ? "dark" : "light";
      try {
        window.localStorage.setItem(key, theme);
        warning = "";
      } catch {
        warning = "화면 설정을 저장할 수 없어 현재 창에만 적용됩니다.";
      }
      render();
    });

    render();
    button.hidden = false;
  }, { once: true });
})();
