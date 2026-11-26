const mobileCatalog = window.matchMedia("(max-width: 1023px)");
const focusBeforeSwap = new WeakMap();

if (navigator.clipboard?.writeText) {
  document.documentElement.classList.add("clipboard-ready");
  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".copy-sku");
    if (!button) return;
    const reference = button.closest(".sku-reference");
    const sku = reference.querySelector("[data-sku]");
    const feedback = reference.querySelector(".sku-feedback");
    try {
      await navigator.clipboard.writeText(sku.textContent);
      feedback.textContent = "شناسه کپی شد.";
    } catch {
      const range = document.createRange();
      range.selectNodeContents(sku);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      feedback.textContent = "شناسه انتخاب شد. از فرمان «کپی» دستگاه استفاده کنید.";
    }
  });
}

function prepareFilters(restore) {
  const panel = document.getElementById("catalog-panel");
  if (!panel || panel.dataset.filtersReady || typeof HTMLDialogElement === "undefined") return;

  const opener = panel.querySelector("#open-filters");
  const host = panel.querySelector("#filter-host");
  const dialog = panel.querySelector("#filter-dialog");
  const form = host.querySelector("form");
  const content = dialog.querySelector("#filter-drawer-content");
  panel.dataset.filtersReady = "true";
  opener.hidden = false;
  host.dataset.filterReady = "true";

  function openFilters() {
    content.append(form);
    dialog.showModal();
    dialog.querySelector("#close-filters").focus();
  }
  function closeFilters() {
    if (dialog.dataset.closing !== undefined) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !dialog.animate) {
      dialog.close();
      return;
    }
    dialog.dataset.closing = "";
    dialog.animate(
      [{ transform: getComputedStyle(dialog).transform }, { transform: "translateY(100%)" }],
      { duration: 220, easing: "cubic-bezier(.22,.68,.34,1)", fill: "forwards" },
    ).finished.then(() => {
      if (dialog.open) dialog.close();
    }, () => { /* A resize or a form submit can close the sheet first. */ });
  }
  opener.addEventListener("click", openFilters);
  dialog.querySelector("#close-filters").addEventListener("click", closeFilters);
  dialog.querySelector("#show-results").addEventListener("click", closeFilters);
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeFilters();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog && event.clientY < dialog.getBoundingClientRect().top) closeFilters();
  });
  dialog.addEventListener("close", () => {
    delete dialog.dataset.restored;
    delete dialog.dataset.closing;
    dialog.getAnimations?.().forEach((animation) => animation.cancel());
    host.append(form);
    if (mobileCatalog.matches) opener.focus();
  });
  if (restore?.drawer && mobileCatalog.matches) {
    dialog.dataset.restored = "";
    openFilters();
    document.getElementById(restore.id)?.focus({ preventScroll: true });
    dialog.scrollTop = restore.scroll;
  }
}

mobileCatalog.addEventListener("change", (event) => {
  const dialog = document.getElementById("filter-dialog");
  if (!event.matches && dialog?.open) dialog.close();
});

document.addEventListener("toggle", ({ target: details }) => {
  if (!(details instanceof HTMLDetailsElement) || !details.matches("[data-disclosure][open]")) return;
  document.querySelectorAll("[data-disclosure][open]").forEach((other) => {
    if (other !== details) other.open = false;
  });
  details.querySelector("input")?.focus();
}, true);
document.addEventListener("keydown", (event) => {
  const details = event.target.closest("[data-disclosure][open]");
  if (event.key !== "Escape" || !details) return;
  details.open = false;
  details.querySelector("summary").focus();
});
document.addEventListener("pointerdown", (event) => {
  document.querySelectorAll("[data-disclosure][open]").forEach((details) => {
    if (!details.contains(event.target)) details.open = false;
  });
});

document.body.addEventListener("htmx:beforeRequest", ({ detail }) => {
  document.querySelectorAll("[data-network-status]").forEach((status) => { status.hidden = true; });
  const target = detail.target;
  if (target && target.id !== "add-status") target.setAttribute("aria-busy", "true");
});
document.body.addEventListener("htmx:beforeSwap", ({ detail }) => {
  if (!detail.shouldSwap) return;
  const active = document.activeElement;
  const dialog = detail.target?.id === "catalog-panel" && detail.target.querySelector("#filter-dialog[open]");
  if (dialog && dialog.dataset.closing === undefined) {
    focusBeforeSwap.set(detail.xhr, {
      id: active.id,
      target: detail.target.id,
      drawer: true,
      scroll: dialog.scrollTop,
    });
    return;
  }
  if (detail.target?.contains(active)) {
    focusBeforeSwap.set(detail.xhr, {
      id: active.closest("dialog") ? "" : active.id,
      target: detail.target.id,
    });
  }
});
document.body.addEventListener("htmx:afterSettle", ({ detail }) => {
  const previous = focusBeforeSwap.get(detail.xhr);
  prepareFilters(previous);
  if (!previous) return;
  focusBeforeSwap.delete(detail.xhr);
  const fallback = { "catalog-panel": "results-count", "cart-content": "order-heading" };
  const element = document.getElementById(previous.id) || document.getElementById(fallback[previous.target]);
  const active = document.activeElement;
  if (active === document.body || active === document.documentElement || !active?.getClientRects().length) {
    element?.focus();
  }
});
document.body.addEventListener("htmx:afterRequest", ({ detail }) => {
  detail.target?.removeAttribute("aria-busy");
});
["htmx:responseError", "htmx:sendError", "htmx:timeout"].forEach((event) => {
  document.body.addEventListener(event, ({ detail }) => {
    const status = document.querySelector("dialog[open] [data-network-status]")
      || document.getElementById("network-status");
    status.textContent = detail.xhr?.status === 403
      ? "درخواست قابل تأیید نبود. صفحه را تازه‌سازی کنید و دوباره تلاش کنید."
      : "ارتباط با فروشگاه برقرار نشد. دوباره تلاش کنید.";
    status.hidden = false;
    status.focus();
  });
});
document.body.addEventListener("htmx:historyRestore", () => prepareFilters());

prepareFilters();
