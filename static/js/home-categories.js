(() => {
  const browser = document.querySelector(".home-category-browser");
  if (!browser) return;

  const tabList = browser.querySelector(".home-category-tabs");
  const tabs = [...tabList.querySelectorAll("button")];
  const panels = [...browser.querySelectorAll(".home-category-panel")];
  if (tabs.length < 2) return;

  const compactLayout = window.matchMedia("(max-width: 959px), (hover: none)");
  let selected = 0;

  function render() {
    const compact = compactLayout.matches;
    browser.classList.toggle("has-category-tabs", compact);
    tabList.hidden = !compact;
    panels.forEach((panel, index) => {
      const active = index === selected;
      tabs[index].setAttribute("aria-selected", String(active));
      tabs[index].tabIndex = active ? 0 : -1;
      panel.hidden = compact && !active;
      if (compact) {
        panel.setAttribute("role", "tabpanel");
        panel.setAttribute("aria-labelledby", tabs[index].id);
      } else {
        panel.removeAttribute("role");
        panel.removeAttribute("aria-labelledby");
      }
    });
  }

  tabList.addEventListener("click", (event) => {
    const index = tabs.indexOf(event.target.closest("button"));
    if (index < 0) return;
    selected = index;
    render();
  });
  tabList.addEventListener("keydown", (event) => {
    const last = tabs.length - 1;
    const options = {
      ArrowDown: (selected + 1) % tabs.length,
      ArrowUp: (selected + last) % tabs.length,
      Home: 0,
      End: last,
    };
    if (!Object.hasOwn(options, event.key)) return;
    event.preventDefault();
    selected = options[event.key];
    render();
    tabs[selected].focus();
  });
  compactLayout.addEventListener("change", () => {
    const active = document.activeElement;
    const focusedPanel = panels.findIndex((panel) => panel.contains(active));
    if (focusedPanel >= 0) selected = focusedPanel;
    render();
    if (!compactLayout.matches && tabs.includes(active)) {
      panels[selected].querySelector("a").focus();
    }
  });
  render();
})();
