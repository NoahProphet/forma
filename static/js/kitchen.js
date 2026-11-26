(() => {
  "use strict";
  const root = document.getElementById("home-03");
  if (!root) return;
  const scene = JSON.parse(root.querySelector("#kitchen-data").textContent);
  const entries = Object.entries(scene.slots).filter(([, slot]) => slot.models.length);
  const views = Object.keys(scene.views);
  const storageKey = "forma.kitchen." + scene.id;
  const find = (selector) => root.querySelector(selector);
  const viewport = find(".k-viewport");
  const plane = find(".k-plane");
  const status = find(".k-status");
  const retry = find(".k-retry");
  const picker = find(".k-options");
  const cache = new Map();
  const layers = document.createElement("div");
  const hitLayer = document.createElement("div");
  layers.className = "k-layer-stack";
  hitLayer.className = "k-hit-layer";
  plane.append(layers, hitLayer);

  function selection(saved = {}) {
    const slots = {};
    for (const [key, slot] of entries) {
      const model = slot.models.find(m => m.id === saved?.[key]?.model) || slot.models[0];
      const variant = model.variants.find(v => v.id === saved?.[key]?.finish) || model.variants[0];
      slots[key] = {model:model.id, finish:variant.id};
    }
    return slots;
  }
  function loadSelection() {
    try { return selection(JSON.parse(sessionStorage.getItem(storageKey))); }
    catch { return selection(); }
  }
  let desired = {camera:views[0], slots:loadSelection()};
  let displayed = null;
  let active = entries[0][0];
  let revision = 0;
  let zoom = 1;
  let offset = {x:0,y:0};
  let drag = null;
  let started = false;
  let suppressClick = false;
  const hits = new Map();

  function parts(state, key) {
    const choice = state.slots[key];
    const model = scene.slots[key].models.find(m => m.id === choice.model);
    return {model, variant:model.variants.find(v => v.id === choice.finish)};
  }
  function element(tag, cls, label) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (label) node.textContent = label;
    return node;
  }
  function button(label, group, value, selected) {
    const b = element("button", "", label);
    b.type = "button";
    b.dataset[group] = value;
    b.setAttribute("aria-pressed", String(selected));
    return b;
  }
  function paintOptions() {
    if (!displayed) return;
    const focus = picker.contains(document.activeElement) ? document.activeElement.dataset : null;
    const {model, variant} = parts(displayed, active);
    const slot = scene.slots[active];
    const models = element("div", "k-models");
    models.setAttribute("role","group");
    models.setAttribute("aria-label","مدل‌های "+slot.name);
    for (const option of slot.models) {
      const choice = button("", "model", option.id, model.id === option.id);
      const photo = element("img");
      photo.alt = "";
      photo.src = (option.id === model.id ? variant : option.variants[0]).thumb;
      choice.className = "k-model";
      choice.append(photo, element("span","",option.name));
      models.append(choice);
    }
    const fieldset = element("fieldset");
    fieldset.append(element("legend","","رنگ و پرداخت"));
    const finishes = element("div","k-finishes");
    for (const v of model.variants) {
      const choice = button("", "finish",v.id,v.id === variant.id);
      const chip = element("span","k-swatch");
      chip.style.setProperty("--color",v.color || "transparent");
      choice.append(chip,document.createTextNode(v.name));
      finishes.append(choice);
    }
    fieldset.append(finishes);
    const footer = element("div","k-selection");
    const link = element("a","button","مشاهده محصول");
    link.href = variant.url;
    footer.append(element("span","k-stock",(scene.demo ? "موجودی نمایشی: " : "")+variant.availability),link);
    picker.replaceChildren(element("h3","",slot.name),models,fieldset,footer);
    if (focus?.model || focus?.finish) {
      Array.from(picker.querySelectorAll("button")).find(b =>
        (focus.model && b.dataset.model === focus.model) || (focus.finish && b.dataset.finish === focus.finish)
      )?.focus({preventScroll:true});
    }
    root.querySelectorAll("[data-category]").forEach(b => b.setAttribute("aria-pressed",String(b.dataset.category === active)));
    for (const [key,hit] of hits) hit.setAttribute("aria-pressed",String(key === active));
  }
  function rect(node, box, size) {
    const [w,h] = size;
    node.style.left = 100*box[0]/w+"%";
    node.style.top = 100*box[1]/h+"%";
    node.style.width = 100*(box[2]-box[0])/w+"%";
    node.style.height = 100*(box[3]-box[1])/h+"%";
  }
  function image(url) {
    if (!cache.has(url)) {
      const img = new Image();
      img.src = scene.assetRoot + url;
      const decoded = img.decode().then(() => img).catch(error => {cache.delete(url); throw error;});
      cache.set(url, decoded);
      if (cache.size > 18) cache.delete(cache.keys().next().value);
    }
    return cache.get(url);
  }
  function applyTransform() {
    offset.x = Math.max(viewport.clientWidth*(1-zoom),Math.min(0,offset.x));
    offset.y = Math.max(viewport.clientHeight*(1-zoom),Math.min(0,offset.y));
    plane.style.transform = "translate("+offset.x+"px,"+offset.y+"px) scale("+zoom+")";
    plane.style.setProperty("--pin-scale",1/zoom);
    viewport.toggleAttribute("data-zoomed",zoom>1);
    find("[data-minus]").disabled = zoom <= 1;
    find("[data-plus]").disabled = zoom >= 3;
    find(".k-zoom output").textContent = new Intl.NumberFormat("fa-IR").format(zoom)+"×";
  }
  function centerOnSelection() {
    if (!displayed) return;
    const view = scene.views[displayed.camera];
    const pick = displayed.slots[active];
    const box = view.hits[active][pick.model+"."+pick.finish];
    offset.x = viewport.clientWidth*(.5-zoom*(box[0]+box[2])/(2*view.size[0]));
    offset.y = viewport.clientHeight*(.5-zoom*(box[1]+box[3])/(2*view.size[1]));
    applyTransform();
  }
  async function draw(announce = true, reset = false) {
    const ticket = ++revision;
    const state = desired;
    const view = scene.views[state.camera];
    const large = viewport.clientWidth * Math.min(devicePixelRatio,2)*zoom > 896;
    const sources = [{url:state.camera+"-"+(large ? "large" : "small")+".webp"}];
    for (const [group, keys] of Object.entries(scene.groups)) {
      const indices = keys.map(key => state.slots[key] ? parts(state,key).variant.index : 0);
      if (indices.some(Boolean)) sources.push({url:state.camera+"-"+group+"-"+indices.join("-")+".webp",box:view.groups[group]});
    }
    root.setAttribute("aria-busy","true");
    retry.hidden = true;
    const timer = setTimeout(() => { if (ticket === revision) status.textContent = "در حال آماده‌سازی تصویر…"; },160);
    try {
      const decoded = await Promise.all(sources.map(source => image(source.url)));
      if (ticket !== revision) return;
      const fragment = document.createDocumentFragment();
      for (const [i,img] of decoded.entries()) {
        img.alt = i ? "" : "آشپزخانه فرما، "+view.name;
        img.draggable = false;
        if (i) rect(img,sources[i].box,view.size);
        else img.className = "k-base";
        fragment.append(img);
      }
      layers.replaceChildren(fragment);
      const cameraChanged = displayed?.camera !== state.camera;
      displayed = state;
      for (const [key,slot] of entries) {
        let hit = hits.get(key);
        if (!hit) {
          hit = button("", "slot",key,key===active);
          hit.className = "k-hit";
          hit.setAttribute("aria-label","انتخاب "+slot.name);
          const pin = element("span","k-pin");
          pin.append(element("span","k-label",slot.name));
          hit.append(pin);
          hitLayer.append(hit);
          hits.set(key,hit);
        }
        const pick = state.slots[key];
        rect(hit,view.hits[key][pick.model+"."+pick.finish],view.size);
      }
      root.querySelectorAll("[data-camera]").forEach(b => b.setAttribute("aria-pressed",String(b.dataset.camera===state.camera)));
      if (cameraChanged || reset) centerOnSelection();
      else applyTransform();
      find(".k-tools").hidden = false;
      find(".k-categories").hidden = false;
      find(".k-reset").hidden = false;
      paintOptions();
      const {model,variant} = parts(state,active);
      status.textContent = reset ? "چیدمان اولیه بازیابی شد." : announce ? view.name+" · "+model.name+" · "+variant.name : "";
      try {
        if (reset) sessionStorage.removeItem(storageKey);
        else sessionStorage.setItem(storageKey,JSON.stringify(state.slots));
      } catch { /* Storage can be disabled in private browsing. */ }
    } catch {
      if (ticket !== revision) return;
      status.textContent = "تصویر بارگذاری نشد. اتصال را بررسی کنید و دوباره تلاش کنید.";
      retry.hidden = false;
    } finally {
      clearTimeout(timer);
      if (ticket === revision) root.removeAttribute("aria-busy");
    }
  }
  function start() {
    if (!started) {started = true; draw(false);}
  }
  root.addEventListener("click", event => {
    const b = event.target.closest("button");
    if (!b || suppressClick) return;
    if (b===retry) {draw(); return;}
    const key = b.dataset.category || b.dataset.slot;
    if (key) {
      active = key;
      start();
      paintOptions();
      if (zoom>1) centerOnSelection();
      if (b.dataset.slot && event.detail===0) picker.querySelector('[data-model][aria-pressed="true"]')?.focus();
    } else if (b.dataset.camera) {
      desired = {...desired, camera:b.dataset.camera};
      draw();
    } else if (b.dataset.model || b.dataset.finish) {
      const current = desired.slots[active];
      const model = scene.slots[active].models.find(m => m.id === (b.dataset.model || current.model));
      const variant = model.variants.find(v => v.id === (b.dataset.finish || current.finish)) || model.variants[0];
      desired = {...desired,slots:{...desired.slots,[active]:{model:model.id,finish:variant.id}}};
      draw();
    } else if (b.matches("[data-plus],[data-minus]")) {
      zoom = Math.max(1,Math.min(3,zoom+(b.hasAttribute("data-plus") ? 1 : -1)));
      centerOnSelection();
      draw(false);
    } else if (b.matches(".k-reset")) {
      desired = {camera:views[0],slots:selection()};
      active = entries[0][0]; zoom = 1;
      draw(true,true);
    }
  });
  viewport.addEventListener("pointerdown",event => {
    if (zoom===1 || event.button!==0) return;
    drag = {id:event.pointerId,x:event.clientX,y:event.clientY,origin:{...offset}};
  });
  viewport.addEventListener("pointermove",event => {
    if (!drag || event.pointerId!==drag.id) return;
    const dx = event.clientX-drag.x,dy = event.clientY-drag.y;
    if (!suppressClick && Math.hypot(dx,dy)<5) return;
    suppressClick = true;
    viewport.setPointerCapture(event.pointerId);
    viewport.setAttribute("data-dragging","");
    offset = {x:drag.origin.x+dx,y:drag.origin.y+dy};
    applyTransform();
  });
  function endDrag() {
    drag = null;
    viewport.removeAttribute("data-dragging");
    setTimeout(() => {suppressClick=false;},0);
  }
  window.addEventListener("pointerup",endDrag);
  window.addEventListener("pointercancel",endDrag);
  viewport.addEventListener("keydown",event => {
    if (zoom<=1) return;
    if (event.key==="Escape") {zoom=1; centerOnSelection(); return;}
    const amount = {ArrowRight:[-45,0],ArrowLeft:[45,0],ArrowDown:[0,-45],ArrowUp:[0,45]}[event.key];
    if (amount) {event.preventDefault(); offset.x+=amount[0]; offset.y+=amount[1]; applyTransform();}
  });
  let resizeTimer;
  window.addEventListener("resize",() => {
    clearTimeout(resizeTimer);
    resizeTimer=setTimeout(() => {if (displayed) {centerOnSelection(); draw(false);}},150);
  });
  if (location.hash === "#" + root.id) {
    start();
  } else if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {observer.disconnect();start();}
    },{rootMargin:"96px"});
    observer.observe(root);
  } else start();
})();
