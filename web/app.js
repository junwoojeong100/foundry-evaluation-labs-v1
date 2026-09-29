(() => {
  "use strict";

  const article = document.getElementById("guide-start");
  if (!article) return;

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const cleanText = (text) => text.normalize("NFC").replace(/\s+/g, " ").trim();
  const lower = (text) => cleanText(text).toLocaleLowerCase("ko-KR");
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

  function idFromLink(link) {
    const value = link.getAttribute("href") || "";
    if (!value.startsWith("#")) return null;
    try { return decodeURIComponent(value.slice(1)); } catch { return value.slice(1); }
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
    menuToggle.setAttribute("aria-label", "학습 목차 열기");
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
    menuToggle.setAttribute("aria-label", "학습 목차 닫기");
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
    let destinationChapter = chapters[0];
    for (const chapter of chapters) {
      if (chapter.heading === heading || (chapter.heading.compareDocumentPosition(heading) & Node.DOCUMENT_POSITION_FOLLOWING)) {
        destinationChapter = chapter;
      }
    }
    if (destinationChapter) updateChapter(destinationChapter);
    heading.scrollIntoView({ block: "start", behavior: reducedMotion.matches ? "auto" : "smooth" });
    requestReadingUpdate();
  }

  menuToggle.addEventListener("click", () => drawerOpen ? closeDrawer() : openDrawer());
  menuClose.addEventListener("click", () => closeDrawer());
  backdrop.addEventListener("click", () => closeDrawer());
  mobile.addEventListener("change", () => closeDrawer(false));
  window.addEventListener("beforeprint", () => closeDrawer(false));

  // Capture only authored text, before adding copy controls or chapter links.
  const ancestors = [];
  const searchIndex = headings.map((heading, index) => {
    const level = Number(heading.tagName.slice(1));
    while (ancestors.length && ancestors[ancestors.length - 1].level >= level) ancestors.pop();
    const label = cleanText(heading.textContent);
    const trail = ancestors.map((ancestor) => ancestor.label).join(" › ");
    const range = document.createRange();
    range.setStartAfter(heading);
    if (headings[index + 1]) range.setEndBefore(headings[index + 1]);
    else range.setEnd(article, article.childNodes.length);
    const body = cleanText(range.toString());
    ancestors.push({ level, label });
    return { id: heading.id, label, trail, body, titleText: lower(label), text: lower(`${trail} ${label} ${body}`), order: index };
  });

  const searchDialog = $("#search-dialog");
  const searchInput = $("#search-input");
  const searchResults = $("#search-results");
  const searchStatus = $("#search-status");
  const searchOpen = $("[data-search-open]");
  const supportsDialog = typeof searchDialog.showModal === "function";
  let searchTimer;
  let composing = false;

  function appendHighlighted(element, text, terms) {
    const comparable = lower(text);
    let cursor = 0;
    while (cursor < text.length) {
      let nextIndex = -1;
      let nextTerm = "";
      terms.forEach((term) => {
        const index = comparable.indexOf(term, cursor);
        if (index !== -1 && (nextIndex === -1 || index < nextIndex || (index === nextIndex && term.length > nextTerm.length))) {
          nextIndex = index;
          nextTerm = term;
        }
      });
      if (nextIndex === -1) {
        element.append(document.createTextNode(text.slice(cursor)));
        break;
      }
      element.append(document.createTextNode(text.slice(cursor, nextIndex)));
      const mark = document.createElement("mark");
      mark.textContent = text.slice(nextIndex, nextIndex + nextTerm.length);
      element.append(mark);
      cursor = nextIndex + nextTerm.length;
    }
  }

  function excerptFor(entry, terms) {
    if (!entry.body) return "이 제목으로 이동합니다.";
    const comparable = lower(entry.body);
    const matches = terms.map((term) => comparable.indexOf(term)).filter((index) => index >= 0);
    const firstMatch = matches.length ? Math.min(...matches) : 0;
    const start = Math.max(0, firstMatch - 38);
    const end = Math.min(entry.body.length, start + 180);
    return `${start ? "…" : ""}${entry.body.slice(start, end)}${end < entry.body.length ? "…" : ""}`;
  }

  function renderSearch() {
    window.clearTimeout(searchTimer);
    const query = lower(searchInput.value);
    searchResults.replaceChildren();
    if (!query) {
      searchStatus.textContent = "검색어를 입력하세요. 제목뿐 아니라 본문·표·코드도 검색합니다.";
      return;
    }
    const terms = [...new Set(query.split(" ").filter(Boolean))];
    const matches = searchIndex.filter((entry) => terms.every((term) => entry.text.includes(term)));
    const score = (entry) => (entry.titleText.includes(query) ? 20 : 0)
      + terms.reduce((total, term) => total + (entry.titleText.includes(term) ? 4 : 0), 0);
    matches.sort((a, b) => score(b) - score(a) || a.order - b.order);
    if (!matches.length) {
      searchStatus.textContent = "검색 결과가 없습니다. 짧은 단어나 다른 표현으로 검색해 보세요.";
      return;
    }
    const limit = 30;
    searchStatus.textContent = `${matches.length}개 위치를 찾았습니다.${matches.length > limit ? ` 앞의 ${limit}개를 표시합니다. 검색어를 더해 범위를 좁혀 보세요.` : ""}`;
    matches.slice(0, limit).forEach((entry) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.className = "search-result";
      link.href = `#${encodeURIComponent(entry.id)}`;
      if (entry.trail) {
        const trail = document.createElement("span");
        trail.className = "result-trail";
        trail.textContent = entry.trail;
        link.append(trail);
      }
      const title = document.createElement("strong");
      appendHighlighted(title, entry.label, terms);
      const excerpt = document.createElement("span");
      excerpt.className = "result-excerpt";
      appendHighlighted(excerpt, excerptFor(entry, terms), terms);
      link.append(title, excerpt);
      item.append(link);
      searchResults.append(item);
    });
  }

  function openSearch() {
    if (!supportsDialog) return;
    closeDrawer();
    if (!searchDialog.open) searchDialog.showModal();
    renderSearch();
    searchInput.focus();
    searchInput.select();
  }

  searchOpen.addEventListener("click", openSearch);
  $("[data-search-close]").addEventListener("click", () => searchDialog.close());
  searchDialog.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !event.isComposing && !composing) {
      event.preventDefault();
      searchDialog.close();
    }
  });
  searchInput.addEventListener("compositionstart", () => { composing = true; });
  searchInput.addEventListener("compositionend", () => { composing = false; renderSearch(); });
  searchInput.addEventListener("input", (event) => {
    if (composing || event.isComposing) return;
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(renderSearch, 120);
  });
  $("#guide-search-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!composing) renderSearch();
  });
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" && !composing) {
      const firstResult = $("a", searchResults);
      if (firstResult) { event.preventDefault(); firstResult.focus(); }
    }
  });
  searchResults.addEventListener("keydown", (event) => {
    if (!["ArrowDown", "ArrowUp"].includes(event.key)) return;
    const results = $$("a", searchResults);
    const index = results.indexOf(document.activeElement);
    if (index < 0) return;
    event.preventDefault();
    if (event.key === "ArrowUp" && index === 0) searchInput.focus();
    else results[Math.min(results.length - 1, index + (event.key === "ArrowDown" ? 1 : -1))].focus();
  });
  searchResults.addEventListener("click", (event) => {
    const link = event.target.closest("a");
    if (!link || !isPlainClick(event)) return;
    event.preventDefault();
    const id = idFromLink(link);
    searchDialog.close();
    navigateToHeading(id);
  });
  $$("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
    });
  });

  const documentId = document.body.dataset.documentId || window.location.pathname.split("/").pop() || "index.html";
  const storageKey = `foundry-evaluation-guide:progress:v2:${encodeURIComponent(documentId)}`;
  const storageFeedback = $("#storage-feedback");
  let completed = new Set();
  try {
    let stored = window.localStorage.getItem(storageKey);
    if (stored === null && documentId === "index.html") {
      stored = window.localStorage.getItem("foundry-evaluation-guide:progress:v1");
    }
    if (stored) {
      const record = JSON.parse(stored);
      if (record.version !== 1 || !Array.isArray(record.completed) || !record.completed.every((id) => typeof id === "string")) {
        throw new Error("Invalid progress record");
      }
      completed = new Set(record.completed.filter((id) => chapterIds.has(id)));
    }
  } catch {
    storageFeedback.textContent = "저장된 기록을 읽을 수 없습니다. 이 창에서는 계속 완료 표시를 사용할 수 있습니다.";
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
      storageFeedback.textContent = "이 문서의 완료 표시는 이 브라우저에만 저장됩니다.";
      storageFeedback.classList.remove("is-warning");
      return true;
    } catch {
      storageFeedback.textContent = "저장할 수 없어 현재 창에만 기록합니다. 창을 닫으면 이번 변경 사항이 사라집니다.";
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
    const summary = `완료 ${completed.size} / ${chapters.length}개 장`;
    if ($("#progress-summary").textContent !== summary) $("#progress-summary").textContent = summary;
    progressInputs.forEach((input, id) => { input.checked = completed.has(id); });
    tocLinks.forEach(({ link, id }) => link.classList.toggle("is-complete", completed.has(id)));
    resetButton.disabled = completed.size === 0;
    if (currentChapter) {
      const done = completed.has(currentChapter.id);
      markChapter.setAttribute("aria-pressed", String(done));
      markChapter.textContent = done ? "완료 표시 취소" : "이 장 완료 표시";
      markChapter.setAttribute("aria-label", `${currentChapter.label}: ${done ? "완료 표시 취소" : "완료 표시"}`);
    }
  }

  function setComplete(chapter, isComplete) {
    if (isComplete) completed.add(chapter.id);
    else completed.delete(chapter.id);
    const saved = saveProgress();
    updateProgress();
    announce(`${chapter.label}: ${isComplete ? "완료로 표시했습니다." : "완료 표시를 취소했습니다."}${saved ? "" : " 브라우저 저장이 불가능하여 현재 창에만 적용됩니다."}`);
  }

  function resetProgress() {
    completed.clear();
    const saved = saveProgress();
    updateProgress();
    announce(saved ? "모든 장의 완료 표시를 초기화했습니다." : "현재 창의 완료 표시를 초기화했습니다. 저장된 기록은 지우지 못했습니다.");
    $(".progress-details summary").focus({ preventScroll: true });
  }

  markChapter.addEventListener("click", () => {
    if (currentChapter) setComplete(currentChapter, !completed.has(currentChapter.id));
  });
  resetButton.addEventListener("click", () => {
    if (typeof resetDialog.showModal === "function") {
      resetDialog.returnValue = "";
      resetDialog.showModal();
    } else if (window.confirm("이 문서의 모든 장 완료 표시를 초기화할까요?")) resetProgress();
  });
  resetDialog.addEventListener("close", () => {
    if (resetDialog.returnValue === "reset") resetProgress();
  });

  const previousChapter = $("[data-previous-chapter]");
  const nextChapter = $("[data-next-chapter]");
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
    updateProgress();
  }

  // Native links at chapter boundaries keep long, continuous chapters navigable.
  chapters.forEach((chapter, index) => {
    const next = chapters[index + 1];
    if (!next || next.heading.parentElement !== article) return;
    const nav = document.createElement("nav");
    nav.className = "section-pagination no-print";
    nav.setAttribute("aria-label", `${chapter.label} — 장 이동`);
    [chapters[index - 1], next].forEach((target, direction) => {
      if (!target) return;
      const link = document.createElement("a");
      link.href = `#${encodeURIComponent(target.id)}`;
      link.rel = direction ? "next" : "prev";
      link.textContent = direction ? `다음 장: ${target.label} →` : `← 이전 장: ${target.label}`;
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

  $$("pre", article).forEach((pre, index) => {
    const code = $("code", pre);
    if (!code) return;
    const wrapper = document.createElement("div");
    wrapper.className = "code-block";
    const toolbar = document.createElement("div");
    toolbar.className = "code-toolbar no-print";
    const language = document.createElement("span");
    language.className = "code-language";
    language.textContent = (Array.from(code.classList).find((name) => name.startsWith("language-")) || "language-code").slice(9);
    const button = document.createElement("button");
    button.className = "copy-button";
    button.type = "button";
    button.textContent = "코드 복사";
    button.setAttribute("aria-label", `${index + 1}번째 ${language.textContent} 코드 복사`);
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
    pre.setAttribute("aria-label", `${language.textContent} 코드. 긴 줄은 가로로 스크롤할 수 있습니다.`);
    let feedbackTimer;
    button.addEventListener("click", async () => {
      if (button.getAttribute("aria-busy") === "true") return;
      window.clearTimeout(feedbackTimer);
      button.setAttribute("aria-busy", "true");
      feedback.textContent = "";
      const success = await copyText(code.textContent);
      button.removeAttribute("aria-busy");
      button.dataset.copyState = success ? "success" : "error";
      button.textContent = success ? "복사됨 ✓" : "복사 실패";
      feedback.textContent = success ? "코드를 클립보드에 복사했습니다." : "자동 복사가 지원되지 않습니다. 코드를 선택한 뒤 직접 복사하세요.";
      if (success) {
        feedbackTimer = window.setTimeout(() => {
          button.textContent = "코드 복사";
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
    wrapper.setAttribute("aria-label", `${caption ? cleanText(caption.textContent) : `${index + 1}번째 표`}. 넓은 표는 가로로 스크롤할 수 있습니다.`);
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
    wrapper.setAttribute("aria-label", `${image.alt || "도식"}. 가로로 스크롤하여 볼 수 있습니다.`);
    image.before(wrapper);
    wrapper.append(image);
    const source = document.createElement("a");
    source.className = "diagram-source no-print";
    source.href = image.getAttribute("src");
    source.target = "_blank";
    source.rel = "noopener";
    source.textContent = "도식 원본 보기 ↗";
    source.setAttribute("aria-label", `${image.alt || "도식"} 원본 보기 (새 탭)`);
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
    if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey && supportsDialog) {
      event.preventDefault();
      openSearch();
    }
    if (event.altKey && event.shiftKey && !event.ctrlKey && !event.metaKey && !drawerOpen && ["ArrowLeft", "ArrowRight"].includes(event.key)) {
      const index = chapters.indexOf(currentChapter);
      const target = chapters[index + (event.key === "ArrowRight" ? 1 : -1)];
      if (target) { event.preventDefault(); navigateToHeading(target.id); }
    }
  });
  $("[data-print]").addEventListener("click", () => window.print());

  document.documentElement.classList.add("js");
  menuToggle.hidden = false;
  menuClose.hidden = false;
  searchOpen.hidden = !supportsDialog;
  $("[data-print]").hidden = false;
  $("[data-keyboard-help]").hidden = false;
  $("[data-progress-panel]").hidden = chapters.length === 0;
  $("[data-chapter-completion]").hidden = chapters.length === 0;
  $("[data-chapter-pagination]").hidden = chapters.length < 2;
  closeDrawer(false);
  if (currentChapter) updateChapter(currentChapter);
  updateProgress();
  requestReadingUpdate();
})();
