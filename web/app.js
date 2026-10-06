(() => {
  "use strict";

  const article = document.getElementById("guide-start");
  if (!article) return;
  const messages = JSON.parse(document.getElementById("guide-messages").textContent);
  const t = (key, values = {}) => messages[key].replace(/\{(\w+)\}/g, (_, name) => values[name]);

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const cleanText = (text) => text.normalize("NFC").replace(/\s+/g, " ").trim();
  const headings = $$("h1, h2, h3, h4, h5, h6", article);
  headings.forEach((heading, index) => {
    if (!heading.id) {
      let id = `guide-section-${index + 1}`;
      while (document.getElementById(id)) id += "-section";
      heading.id = id;
    }
  });

  const chapterHeadings = $$("h2", article);
  const chapters = (chapterHeadings.length ? chapterHeadings : $$("h1", article)).map((heading) => ({
    heading,
    id: heading.id,
    label: cleanText(heading.textContent),
  }));
  const chapterIds = new Set(chapters.map((chapter) => chapter.id));
  let currentChapter = chapters[0] || null;
  let currentTocId = null;
  let printState = null;
  const sidebar = $("#guide-sidebar");
  const header = $(".site-header");
  const main = $("#main-content");
  const menuToggle = $("[data-menu-toggle]");
  const menuClose = $("[data-menu-close]");
  const backdrop = $("[data-drawer-backdrop]");
  const mobile = window.matchMedia("(max-width: 70rem)");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let drawerOpen = false;
  let drawerOpener = null;
  let announcementTimer;

  function announce(message) {
    const live = $("#announcements");
    window.clearTimeout(announcementTimer);
    live.textContent = "";
    announcementTimer = window.setTimeout(() => { live.textContent = message; }, 30);
  }

  function idFromHash(value) {
    if (!value.startsWith("#")) return null;
    try { return decodeURIComponent(value.slice(1)); } catch { return value.slice(1); }
  }

  function idFromLink(link) {
    return idFromHash(link.getAttribute("href") || "");
  }

  function chapterForHeading(heading) {
    let result = chapters[0] || null;
    for (const chapter of chapters) {
      if (chapter.heading === heading || (chapter.heading.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING)) {
        result = chapter;
      }
    }
    return result;
  }

  function isPlainClick(event) {
    return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
  }

  function focusableIn(element) {
    return $$('a[href], button:not([disabled]), input:not([disabled]), select, textarea, summary, [tabindex]:not([tabindex="-1"])', element)
      .filter((item) => item.getClientRects().length && !item.closest("[inert]"));
  }

  function closeDrawer(restoreFocus = true) {
    const wasOpen = drawerOpen;
    drawerOpen = false;
    document.documentElement.classList.remove("drawer-open");
    document.body.classList.remove("scroll-locked");
    backdrop.hidden = true;
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", t("menuOpen"));
    main.removeAttribute("inert");
    header.removeAttribute("inert");
    sidebar.removeAttribute("role");
    sidebar.removeAttribute("aria-modal");
    sidebar.removeAttribute("aria-labelledby");
    sidebar.toggleAttribute("inert", mobile.matches);
    if (mobile.matches) sidebar.setAttribute("aria-hidden", "true");
    else sidebar.removeAttribute("aria-hidden");
    if (restoreFocus && wasOpen && drawerOpener && drawerOpener.getClientRects().length) {
      drawerOpener.focus({ preventScroll: true });
    }
  }

  function openDrawer() {
    if (!mobile.matches) return;
    drawerOpener = document.activeElement;
    drawerOpen = true;
    sidebar.removeAttribute("inert");
    sidebar.removeAttribute("aria-hidden");
    sidebar.setAttribute("role", "dialog");
    sidebar.setAttribute("aria-modal", "true");
    sidebar.setAttribute("aria-labelledby", "contents-heading");
    menuToggle.setAttribute("aria-expanded", "true");
    menuToggle.setAttribute("aria-label", t("menuClose"));
    document.documentElement.classList.add("drawer-open");
    document.body.classList.add("scroll-locked");
    backdrop.hidden = false;
    main.setAttribute("inert", "");
    header.setAttribute("inert", "");
    menuClose.focus({ preventScroll: true });
  }

  function navigateToHeading(id) {
    const heading = document.getElementById(id);
    if (!heading) return;
    closeDrawer(false);
    if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
    const hash = `#${encodeURIComponent(id)}`;
    if (window.location.hash !== hash) {
      try { window.history.pushState(null, "", hash); }
      catch { window.location.hash = hash; }
    }
    heading.focus({ preventScroll: true });
    const destinationChapter = chapterForHeading(heading);
    if (destinationChapter) updateChapter(destinationChapter);
    heading.scrollIntoView({ block: "start", behavior: reducedMotion.matches ? "auto" : "smooth" });
    requestReadingUpdate();
  }

  menuToggle.addEventListener("click", () => drawerOpen ? closeDrawer() : openDrawer());
  menuClose.addEventListener("click", () => closeDrawer());
  backdrop.addEventListener("click", () => closeDrawer());
  mobile.addEventListener("change", () => closeDrawer(false));
  $$("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    });
  });

  const documentId = document.body.dataset.documentId || window.location.pathname.split("/").pop() || "index.html";
  const chapterUnit = t(documentId === "index.html" ? "step" : "chapter");
  const progressRevision = document.body.dataset.progressRevision;
  const baseStorageKey = `foundry-evaluation-guide:progress:v2:${encodeURIComponent(documentId)}`;
  const storageKey = progressRevision ? `${baseStorageKey}:${encodeURIComponent(progressRevision)}` : baseStorageKey;
  const storageFeedback = $("#storage-feedback");
  let completed = new Set();
  try {
    let stored = window.localStorage.getItem(storageKey);
    if (stored === null && documentId === "index.html" && !progressRevision) {
      stored = window.localStorage.getItem("foundry-evaluation-guide:progress:v1");
    }
    if (stored === null && progressRevision && window.localStorage.getItem(baseStorageKey) !== null) {
      storageFeedback.textContent = t("progressMigrated");
    }
    if (stored) {
      const record = JSON.parse(stored);
      if (record.version !== 1 || !Array.isArray(record.completed) || !record.completed.every((id) => typeof id === "string")) {
        throw new Error("Invalid progress record");
      }
      completed = new Set(record.completed.filter((id) => chapterIds.has(id)));
    }
  } catch {
    storageFeedback.textContent = t("storageReadError");
    storageFeedback.classList.add("is-warning");
  }

  const checklist = $("#progress-checklist");
  const progressInputs = new Map();
  chapters.forEach((chapter) => {
    const label = document.createElement("label");
    label.className = "progress-item";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = chapter.id;
    input.checked = completed.has(chapter.id);
    const text = document.createElement("span");
    text.textContent = chapter.label;
    label.append(input, text);
    checklist.append(label);
    progressInputs.set(chapter.id, input);
    input.addEventListener("change", () => setComplete(chapter, input.checked));
  });

  function saveProgress() {
    try {
      window.localStorage.setItem(storageKey, JSON.stringify({
        version: 1,
        completed: chapters.filter((chapter) => completed.has(chapter.id)).map((chapter) => chapter.id),
      }));
      storageFeedback.textContent = t("storageSaved");
      storageFeedback.classList.remove("is-warning");
      return true;
    } catch {
      storageFeedback.textContent = t("storageWriteError");
      storageFeedback.classList.add("is-warning");
      return false;
    }
  }

  const markChapter = $("[data-mark-chapter]");
  const resetButton = $("[data-progress-reset]");
  const resetDialog = $("#reset-dialog");
  const tocLinks = $$('a[href^="#"]', $("#chapter-nav")).map((link) => ({
    link,
    id: idFromLink(link),
    heading: document.getElementById(idFromLink(link)),
  })).filter((entry) => entry.heading);

  function updateProgress() {
    const progress = $("#reading-progress");
    progress.max = chapters.length || 1;
    progress.value = completed.size;
    const summary = t("progressSummary", { completed: completed.size, total: chapters.length });
    if ($("#progress-summary").textContent !== summary) $("#progress-summary").textContent = summary;
    progressInputs.forEach((input, id) => { input.checked = completed.has(id); });
    tocLinks.forEach(({ link, id }) => link.classList.toggle("is-complete", completed.has(id)));
    resetButton.disabled = completed.size === 0;
    if (currentChapter) {
      const done = completed.has(currentChapter.id);
      markChapter.setAttribute("aria-pressed", String(done));
      markChapter.textContent = done ? t("markUnread") : t("markUnitRead", { unit: chapterUnit });
      markChapter.setAttribute("aria-label", `${currentChapter.label}: ${t(done ? "markUnread" : "markRead")}`);
    }
  }

  function setComplete(chapter, isComplete) {
    if (isComplete) completed.add(chapter.id);
    else completed.delete(chapter.id);
    const saved = saveProgress();
    updateProgress();
    announce(`${chapter.label}: ${t(isComplete ? "markedRead" : "markedUnread")}${saved ? "" : t("currentWindowOnly")}`);
  }

  function resetProgress() {
    completed.clear();
    const saved = saveProgress();
    updateProgress();
    announce(t(saved ? "progressReset" : "progressResetError"));
    $(".progress-details summary").focus({ preventScroll: true });
  }

  markChapter.addEventListener("click", () => {
    if (currentChapter) setComplete(currentChapter, !completed.has(currentChapter.id));
  });
  resetButton.addEventListener("click", () => {
    if (typeof resetDialog.showModal === "function") {
      resetDialog.returnValue = "";
      resetDialog.showModal();
    } else if (window.confirm(t("confirmReset"))) resetProgress();
  });
  resetDialog.addEventListener("close", () => {
    if (resetDialog.returnValue === "reset") resetProgress();
  });

  const previousChapter = $("[data-previous-chapter]");
  const nextChapter = $("[data-next-chapter]");
  function updateLanguageLinks() {
    const hashId = idFromHash(window.location.hash);
    const anchor = hashId ? document.getElementById(hashId) : null;
    const anchoredChapter = anchor && article.contains(anchor) ? chapterForHeading(anchor) : null;
    const fragment = anchor && anchoredChapter === currentChapter
      ? window.location.hash
      : currentChapter ? `#${encodeURIComponent(currentChapter.id)}` : "";
    $$("[data-language-link]").forEach((link) => {
      const target = new URL(link.href);
      target.search = window.location.search;
      target.hash = fragment;
      link.href = target.href;
    });
  }
  window.addEventListener("hashchange", updateLanguageLinks);
  function setChapterLink(link, chapter) {
    link.hidden = !chapter;
    if (!chapter) { link.removeAttribute("href"); return; }
    link.href = `#${encodeURIComponent(chapter.id)}`;
    $("strong", link).textContent = chapter.label;
  }

  function updateChapter(chapter) {
    currentChapter = chapter;
    const index = chapters.indexOf(chapter);
    $("#current-chapter-title").textContent = chapter.label;
    setChapterLink(previousChapter, chapters[index - 1]);
    setChapterLink(nextChapter, chapters[index + 1]);
    tocLinks.forEach(({ link, id }) => link.classList.toggle("is-current-chapter", id === chapter.id));
    updateLanguageLinks();
    updateProgress();
  }

  // Native links at chapter boundaries keep long, continuous chapters navigable.
  const authoredNextTargets = new Set($$("a[data-next-step]", article).map(idFromLink));
  chapters.forEach((chapter, index) => {
    const next = chapters[index + 1];
    if (!next || next.heading.parentElement !== article || authoredNextTargets.has(next.id)) return;
    const nav = document.createElement("nav");
    nav.className = "section-pagination no-print";
    nav.setAttribute("aria-label", t("sectionNavigation", { label: chapter.label, unit: chapterUnit }));
    [chapters[index - 1], next].forEach((target, direction) => {
      if (!target) return;
      const link = document.createElement("a");
      link.href = `#${encodeURIComponent(target.id)}`;
      link.rel = direction ? "next" : "prev";
      link.textContent = t(direction ? "nextSection" : "previousSection", { unit: chapterUnit, label: target.label });
      nav.append(link);
    });
    article.insertBefore(nav, next.heading);
  });

  function handleSectionLink(event) {
    const link = event.target.closest('a[href^="#"]');
    if (!link || !isPlainClick(event)) return;
    const id = idFromLink(link);
    if (!document.getElementById(id)) return;
    event.preventDefault();
    navigateToHeading(id);
  }
  $("#chapter-nav").addEventListener("click", handleSectionLink);
  $("[data-chapter-pagination]").addEventListener("click", handleSectionLink);
  article.addEventListener("click", handleSectionLink);

  let readingFrame = 0;
  function updateReadingPosition() {
    readingFrame = 0;
    if (printState) return;
    const threshold = header.getBoundingClientRect().bottom + 40;
    let chapter = chapters[0];
    for (const candidate of chapters) {
      if (candidate.heading.getBoundingClientRect().top <= threshold) chapter = candidate;
      else break;
    }
    if (chapters.length && window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4) {
      chapter = chapters[chapters.length - 1];
    }
    if (chapter && chapter !== currentChapter) updateChapter(chapter);
    let toc = tocLinks[0];
    for (const candidate of tocLinks) {
      if (candidate.heading.getBoundingClientRect().top <= threshold) toc = candidate;
      else break;
    }
    if (toc && toc.id !== currentTocId) {
      currentTocId = toc.id;
      tocLinks.forEach(({ link, id }) => {
        if (id === currentTocId) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    }
  }
  function requestReadingUpdate() {
    if (!readingFrame) readingFrame = window.requestAnimationFrame(updateReadingPosition);
  }
  window.addEventListener("scroll", requestReadingUpdate, { passive: true });
  window.addEventListener("resize", requestReadingUpdate, { passive: true });
  window.addEventListener("hashchange", requestReadingUpdate);
  window.addEventListener("load", requestReadingUpdate);

  async function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      try { await navigator.clipboard.writeText(text); return true; } catch { /* Try file://-compatible fallback. */ }
    }
    const activeElement = document.activeElement;
    const selection = window.getSelection();
    const ranges = selection ? Array.from({ length: selection.rangeCount }, (_, index) => selection.getRangeAt(index).cloneRange()) : [];
    const buffer = document.createElement("textarea");
    buffer.className = "copy-buffer";
    buffer.value = text;
    buffer.readOnly = true;
    buffer.tabIndex = -1;
    buffer.setAttribute("aria-hidden", "true");
    document.body.append(buffer);
    let success = false;
    try {
      buffer.focus({ preventScroll: true });
      buffer.select();
      buffer.setSelectionRange(0, buffer.value.length);
      success = typeof document.execCommand === "function" && document.execCommand("copy");
    } catch { success = false; }
    finally {
      buffer.remove();
      if (selection) {
        selection.removeAllRanges();
        ranges.forEach((range) => selection.addRange(range));
      }
      if (activeElement instanceof HTMLElement) activeElement.focus({ preventScroll: true });
    }
    return success;
  }

  let copyBlockIndex = 0;
  $$("pre", article).forEach((pre) => {
    const code = $("code", pre);
    if (!code) return;
    if (pre.classList.contains("implementation-source")) {
      pre.tabIndex = 0;
      pre.setAttribute("aria-label", t("implementationLabel"));
      return;
    }
    if (pre.previousElementSibling?.classList.contains("output-label")) {
      pre.tabIndex = 0;
      pre.setAttribute("aria-label", t("exampleLabel"));
      return;
    }
    const index = copyBlockIndex++;
    const isCommand = pre.classList.contains("terminal-command");
    const copyLabel = isCommand ? "copyCommand" : "copyCode";
    const wrapper = document.createElement("div");
    wrapper.className = isCommand ? "code-block is-command" : "code-block";
    const toolbar = document.createElement("div");
    toolbar.className = "code-toolbar no-print";
    const language = document.createElement("span");
    language.className = "code-language";
    const syntax = (Array.from(code.classList).find((name) => name.startsWith("language-")) || "language-code").slice(9);
    const shellLabels = new Map([["sh", "shellShared"], ["bash", "shellBash"], ["powershell", "shellPowerShell"]]);
    const syntaxLabel = shellLabels.has(syntax) ? t(shellLabels.get(syntax)) : syntax;
    language.textContent = isCommand ? t("commandLabel", { language: syntaxLabel }) : syntaxLabel;
    const button = document.createElement("button");
    button.className = "copy-button";
    button.type = "button";
    button.textContent = t(copyLabel);
    button.setAttribute("aria-label", t(isCommand ? "copyCommandLabel" : "copyCodeLabel", {
      index: index + 1, language: syntaxLabel,
    }));
    const feedback = document.createElement("span");
    feedback.id = `copy-feedback-${index + 1}`;
    feedback.className = "copy-feedback no-print";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    feedback.setAttribute("aria-atomic", "true");
    button.setAttribute("aria-describedby", feedback.id);
    toolbar.append(language, button);
    pre.before(wrapper);
    wrapper.append(toolbar, pre, feedback);
    pre.tabIndex = 0;
    pre.setAttribute("aria-label", t(isCommand ? "commandCodeLabel" : "codeLabel", { language: syntaxLabel }));
    let feedbackTimer;
    button.addEventListener("click", async () => {
      if (button.getAttribute("aria-busy") === "true") return;
      window.clearTimeout(feedbackTimer);
      button.setAttribute("aria-busy", "true");
      feedback.textContent = "";
      const success = await copyText(code.textContent);
      button.removeAttribute("aria-busy");
      button.dataset.copyState = success ? "success" : "error";
      button.textContent = t(success ? "copied" : "copyFailed");
      feedback.textContent = t(success ? "copySuccess" : "copyError");
      if (success) {
        feedbackTimer = window.setTimeout(() => {
          button.textContent = t(copyLabel);
          button.removeAttribute("data-copy-state");
          feedback.textContent = "";
        }, 3000);
      }
    });
  });

  $$("table", article).forEach((table, index) => {
    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll";
    wrapper.tabIndex = 0;
    wrapper.setAttribute("role", "region");
    const caption = $("caption", table);
    wrapper.setAttribute("aria-label", t("tableScroll", {
      label: caption ? cleanText(caption.textContent) : t("tableLabel", { index: index + 1 }),
    }));
    table.before(wrapper);
    wrapper.append(table);
    $$("thead th", table).forEach((cell) => {
      if (!cell.hasAttribute("scope")) cell.setAttribute("scope", "col");
    });
  });
  $$('img[src$=".svg"]', article).forEach((image) => {
    const wrapper = document.createElement("span");
    wrapper.className = "diagram-frame";
    wrapper.tabIndex = 0;
    wrapper.setAttribute("role", "region");
    wrapper.setAttribute("aria-label", t("diagramScroll", { label: image.alt || t("diagram") }));
    image.before(wrapper);
    wrapper.append(image);
    const source = document.createElement("a");
    source.className = "diagram-source no-print";
    source.href = image.getAttribute("src");
    source.target = "_blank";
    source.rel = "noopener";
    source.textContent = t("diagramSource");
    source.setAttribute("aria-label", t("diagramSourceLabel", { label: image.alt || t("diagram") }));
    wrapper.after(source);
  });

  document.addEventListener("keydown", (event) => {
    if (event.defaultPrevented) return;
    if (drawerOpen && !document.querySelector("dialog[open]")) {
      if (event.key === "Escape") { event.preventDefault(); closeDrawer(); return; }
      if (event.key === "Tab") {
        const items = focusableIn(sidebar);
        const first = items[0];
        const last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    }
    const typing = event.target instanceof Element && event.target.closest("input, textarea, select, [contenteditable]:not([contenteditable='false'])");
    if (typing || event.isComposing || document.querySelector("dialog[open]")) return;
    if (event.altKey && event.shiftKey && !event.ctrlKey && !event.metaKey && !drawerOpen && ["ArrowLeft", "ArrowRight"].includes(event.key)) {
      const index = chapters.indexOf(currentChapter);
      const target = chapters[index + (event.key === "ArrowRight" ? 1 : -1)];
      if (target) { event.preventDefault(); navigateToHeading(target.id); }
    }
  });
  function restorePrint() {
    if (!printState) return;
    printState.excluded.forEach((element) => element.classList.remove("print-excluded"));
    printState.links.forEach(({ link, href }) => link.setAttribute("href", href));
    printState.details.forEach((details) => { details.open = false; });
    printState = null;
    delete document.body.dataset.print;
    requestReadingUpdate();
  }

  function preparePrint(mode) {
    restorePrint();
    closeDrawer(false);
    printState = { excluded: [], links: [], details: [] };
    document.body.dataset.print = mode;
    const next = chapters[chapters.indexOf(currentChapter) + 1];
    let included = !currentChapter;
    Array.from(article.children).forEach((element) => {
      if (element === currentChapter?.heading) included = true;
      if (element === next?.heading) included = false;
      if (mode === "one" && !included) {
        element.classList.add("print-excluded");
        printState.excluded.push(element);
      }
    });
    $$("details:not([open])", article).forEach((details) => {
      printState.details.push(details);
      details.open = true;
    });
    $$("a[href]", article).forEach((link) => {
      const href = link.getAttribute("href");
      const fragment = idFromLink(link);
      const target = fragment ? document.getElementById(fragment) : null;
      if (target && article.contains(target) && !target.closest(".print-excluded")) return;
      const url = new URL(href, window.location.href);
      const local = ["localhost", "127.0.0.1", "[::1]", "0.0.0.0"].includes(url.hostname) || url.hostname.endsWith(".localhost");
      if (/^(?:https?:)?\/\//i.test(href) && ["http:", "https:"].includes(url.protocol) && !local) return;
      printState.links.push({ link, href });
      link.removeAttribute("href");
    });
  }

  function requestPrint(mode) {
    preparePrint(mode);
    try {
      window.print();
    } catch (error) {
      restorePrint();
      announce(t("printError"));
      console.error("Guide printing failed:", error);
    }
  }

  $("[data-print-one]").addEventListener("click", () => requestPrint("one"));
  $("[data-print-all]").addEventListener("click", () => requestPrint("all"));
  window.addEventListener("beforeprint", () => {
    if (!printState) preparePrint("one");
  });
  window.addEventListener("afterprint", restorePrint);

  document.documentElement.classList.add("js");
  menuToggle.hidden = false;
  menuClose.hidden = false;
  $("[data-print-one]").hidden = chapters.length === 0;
  $("[data-print-all]").hidden = false;
  $("[data-keyboard-help]").hidden = false;
  $("[data-progress-panel]").hidden = chapters.length === 0;
  $("[data-chapter-completion]").hidden = chapters.length === 0;
  $("[data-chapter-pagination]").hidden = chapters.length < 2;
  closeDrawer(false);
  if (currentChapter) updateChapter(currentChapter);
  updateProgress();
  requestReadingUpdate();
})();
