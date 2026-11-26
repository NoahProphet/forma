const shopPrice = new Intl.NumberFormat("fa-IR");
const priceTimers = new WeakMap();
const addedTimers = new WeakMap();

// Prices in the text fields stay authoritative for exact entries and no-JS submissions.
function readPrice(value) {
  const normalized = value.trim().replace(/[۰-۹٠-٩]/g, (digit) => (
    String(digit.charCodeAt(0) - (digit >= "۰" ? 1776 : 1632))
  )).replace(/[٬,]/g, "");
  return /^\d{1,10}$/.test(normalized) ? Number(normalized) : null;
}

function priceStep(span) {
  if (span >= 10_000_000) return 100_000;
  if (span >= 2_000_000) return 50_000;
  if (span >= 500_000) return 20_000;
  return 10_000;
}

function preparePriceRange() {
  const range = document.querySelector("[data-price-range][hidden]");
  if (!range) return;

  const form = range.closest("form");
  const [low, high] = range.querySelectorAll("input");
  const [lowLabel, highLabel] = range.querySelectorAll("output");
  const [lowField, highField] = [form.elements.low, form.elements.high];
  const boundLow = Number(range.dataset.min);
  const boundHigh = Number(range.dataset.max);
  const step = priceStep(boundHigh - boundLow);
  const min = Math.floor(boundLow / step) * step;
  const max = Math.ceil(boundHigh / step) * step;
  const track = range.querySelector(".shop-range-track");

  function paint() {
    const start = low.valueAsNumber;
    const end = high.valueAsNumber;
    track.style.setProperty("--range-start", `${100 * (start - min) / (max - min)}%`);
    track.style.setProperty("--range-end", `${100 * (end - min) / (max - min)}%`);
    lowLabel.textContent = shopPrice.format(start);
    highLabel.textContent = shopPrice.format(end);
    low.setAttribute("aria-valuetext", `${lowLabel.textContent} تومان`);
    high.setAttribute("aria-valuetext", `${highLabel.textContent} تومان`);
    track.classList.toggle("raise-low", end >= max);
  }

  for (const [handle, field, fallback] of [[low, lowField, min], [high, highField, max]]) {
    handle.min = min;
    handle.max = max;
    handle.step = step;
    handle.value = readPrice(field.value) ?? fallback;
    handle.addEventListener("input", () => {
      if (low.valueAsNumber > high.valueAsNumber) {
        handle.value = (handle === low ? high : low).value;
      }
      paint();
    });
    handle.addEventListener("change", () => {
      field.value = handle.valueAsNumber === fallback ? "" : String(handle.valueAsNumber);
      clearTimeout(priceTimers.get(form));
      priceTimers.set(form, setTimeout(() => {
        if (form.isConnected) form.requestSubmit();
      }, 250));
    });
  }
  track.addEventListener("pointerup", (event) => {
    if (event.target !== track || event.button !== 0) return;
    const box = track.getBoundingClientRect();
    const fraction = (event.clientX - box.left - 11) / (box.width - 22);
    const value = Math.min(max, Math.max(min, min + Math.round(fraction * (max - min) / step) * step));
    const handle = Math.abs(value - low.valueAsNumber) <= Math.abs(value - high.valueAsNumber) ? low : high;
    handle.value = value;
    handle.focus({ preventScroll: true });
    handle.dispatchEvent(new Event("input"));
    handle.dispatchEvent(new Event("change"));
  });
  if (low.valueAsNumber > high.valueAsNumber) low.value = high.value;
  paint();
  range.hidden = false;
}

document.body.addEventListener("change", ({ target }) => {
  if (target.matches("#filters-form [data-shop-auto]")) target.form.requestSubmit();
});
document.body.addEventListener("submit", ({ target }) => {
  if (target.id !== "filters-form") return;
  clearTimeout(priceTimers.get(target));
});
document.body.addEventListener("htmx:afterSwap", preparePriceRange);
document.body.addEventListener("htmx:historyRestore", preparePriceRange);
document.body.addEventListener("htmx:afterSwap", ({ detail }) => {
  const status = detail.target;
  if (!status?.matches(".shop-add-status")) return;
  const button = status.closest(".shop-purchase")?.querySelector(".shop-buy");
  if (!button) return;
  clearTimeout(addedTimers.get(button));
  const added = Boolean(status.querySelector("[data-added]"));
  button.classList.toggle("is-added", added);
  if (added) {
    addedTimers.set(button, setTimeout(() => button.classList.remove("is-added"), 1600));
  }
});

preparePriceRange();
