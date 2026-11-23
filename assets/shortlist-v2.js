/* Saved apartments / side-by-side comparison. Stored on this device only. */
(function () {
  "use strict";
  const KEY = "smartcity-shortlist-v2";
  const DETAIL = /^\/can-ho\/[^/]+\/?$/;
  const lang = () => document.documentElement.lang || "vi";
  const tr = (vi, en, ko) => lang().startsWith("en") ? en : lang().startsWith("ko") ? ko : vi;
  const clean = v => String(v || "").trim().slice(0, 250);
  const value = (root, sel) => clean(root.querySelector(sel)?.textContent);
  const pathFor = href => {
    try { const u = new URL(href, location.origin); return u.origin === location.origin && DETAIL.test(u.pathname) ? u.pathname.replace(/\/?$/, "/") : ""; }
    catch { return ""; }
  };
  function safeImage(v) {
    try { const u = new URL(v, location.origin); return ["http:","https:"].includes(u.protocol) ? u.href : ""; } catch { return ""; }
  }
  function normalize(item) {
    if (!item || !pathFor(item.path)) return null;
    return {path:pathFor(item.path), title:clean(item.title), price:clean(item.price),
      tower:clean(item.tower), interior:clean(item.interior), status:clean(item.status),
      image:item.image ? safeImage(item.image) : ""};
  }
  let saved = [];
  try { const list = JSON.parse(localStorage.getItem(KEY) || "[]"); if (Array.isArray(list)) saved = list.map(normalize).filter(Boolean).slice(0, 30); } catch {}
  let selected = new Set(saved.slice(0,3).map(x => x.path));
  let trigger, dialog, count, body, feedback;
  const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch {} };
  const isSaved = path => saved.some(x => x.path === path);
  function element(tag, cls, txt) {
    const el = document.createElement(tag); if (cls) el.className = cls; if (txt) el.textContent = txt; return el;
  }
  function updateButtons() {
    document.querySelectorAll(".sc-save[data-path]").forEach(button => {
      const on = isSaved(button.dataset.path);
      button.setAttribute("aria-pressed", String(on));
      const label = on ? tr("Bỏ lưu căn", "Remove saved apartment", "저장 취소") : tr("Lưu căn", "Save apartment", "저장");
      button.title = label; button.setAttribute("aria-label", label);
      button.textContent = button.classList.contains("sc-save-inline") ? (on ? "♥ " : "♡ ") + label : on ? "♥" : "♡";
    });
    if (count) count.textContent = String(saved.length);
    if (trigger) trigger.hidden = !saved.length && !trigger.classList.contains("sc-shortlist-in-list");
  }
  function toggle(item) {
    if (isSaved(item.path)) {
      saved = saved.filter(x => x.path !== item.path); selected.delete(item.path);
    } else {
      if (saved.length >= 30) { openDialog(); feedback.textContent = tr("Anh/chị có thể lưu tối đa 30 căn. Bỏ lưu một căn để tiếp tục.", "You can save up to 30 apartments.", "최대 30개까지 저장할 수 있습니다."); return; }
      saved.unshift(item); if (selected.size < 3) selected.add(item.path);
    }
    persist(); updateButtons(); if (dialog?.open) render();
  }
  function attach(root, data, place, inline) {
    if (!data || !place || root.querySelector(".sc-save")) return;
    if (isSaved(data.path)) {
      const i = saved.findIndex(x => x.path === data.path);
      if (JSON.stringify(saved[i]) !== JSON.stringify(data)) { saved[i] = data; persist(); }
    }
    const b = element("button", "sc-save" + (inline ? " sc-save-inline" : ""));
    b.type = "button"; b.dataset.path = data.path;
    b.addEventListener("click", e => { e.preventDefault(); e.stopPropagation(); toggle(data); });
    place.appendChild(b);
  }
  function enhance() {
    document.querySelectorAll("article.card, article.the").forEach(card => {
      if (card.querySelector(".sc-save")) return;
      const path = pathFor(card.querySelector('a[href^="/can-ho/"]')?.href || "");
      if (!path) return;
      const img = card.querySelector(".media img,.the-anh img");
      const data = normalize({path, title:value(card,"h3"), price:value(card,".price,.gia"),
        tower:value(card,".tower,.vi-tri"), interior:value(card,".cc-nt,.badge-nt"),
        status:value(card,".badge,.tinh-trang"), image:img?.getAttribute("src")});
      // Media may itself be a gallery <button>; controls must be siblings.
      attach(card, data, card, false);
    });
    const main = document.querySelector("main");
    if (DETAIL.test(location.pathname) && main && !main.querySelector(".sc-save") && !/noindex/i.test(document.querySelector('meta[name="robots"]')?.content || "")) {
      const rows = [...main.querySelectorAll(".bang tr")].map(r => Array.from(r.cells).map(c => clean(c.textContent)));
      if (rows.length) {
        const get = label => rows.find(r => r[0] === label)?.[1] || "";
        const data = normalize({path:location.pathname, title:[get("Loại"), get("Diện tích")].filter(Boolean).join(" · "),
          price:get("Giá thuê"), tower:[get("Phân khu"), get("Tòa")].filter(Boolean).join(" · "), interior:get("Nội thất"), status:get("Ngày vào ở"),
          image:main.querySelector(".gallery img")?.getAttribute("src")});
        const place = element("div", "sc-detail-actions"); main.querySelector("h1")?.insertAdjacentElement("afterend", place);
        attach(main, data, place, true);
      }
    }
    updateButtons();
  }
  function render() {
    body.replaceChildren(); feedback.textContent = "";
    const desc = element("p", "sc-shortlist-note", tr("Chọn tối đa 3 căn để so sánh. Giá và tình trạng là thông tin tại lần xem gần nhất; mở chi tiết để kiểm tra lại.", "Choose up to 3 apartments to compare. Open each listing to verify current availability and price.", "최대 3개를 비교하세요. 최신 정보는 상세 페이지에서 확인하세요."));
    body.append(desc);
    const choices = element("div", "sc-actions");
    saved.forEach(item => {
      const b = element("button", "", `${selected.has(item.path) ? "✓ " : "+ "}${item.title} · ${item.price}`);
      b.type = "button"; b.setAttribute("aria-pressed", String(selected.has(item.path)));
      b.addEventListener("click", () => {
        if (selected.has(item.path)) selected.delete(item.path);
        else if (selected.size < 3) selected.add(item.path);
        else { feedback.textContent = tr("Chỉ so sánh tối đa 3 căn.", "Compare up to 3 apartments.", "최대 3개까지 비교할 수 있습니다."); return; }
        render();
      }); choices.append(b);
    });
    body.append(choices);
    const grid = element("div", "sc-shortlist-table");
    const compare = saved.filter(item => selected.has(item.path));
    compare.forEach(item => {
      const card = element("section", "sc-shortlist-item");
      if (item.image) { const img = element("img"); img.src = item.image; img.alt = item.title; img.loading = "lazy"; card.append(img); }
      card.append(element("b", "", item.price), element("strong", "", item.title), element("p", "", item.tower), element("p", "", item.interior), element("p", "", item.status));
      const a = element("a", "", tr("Xem chi tiết →", "View details →", "상세 보기 →")); a.href = item.path; card.append(a);
      const remove = element("button", "", tr("Bỏ lưu", "Remove", "삭제")); remove.type = "button"; remove.addEventListener("click", () => toggle(item)); card.append(remove); grid.append(card);
    });
    if (!saved.length) body.append(element("p", "", tr("Chưa lưu căn nào.", "No saved apartments.", "저장된 아파트가 없습니다.")));
    if (compare.length) {
      body.append(grid);
      const share = element("button", "sc-primary", tr("Sao chép danh sách", "Copy comparison", "목록 복사")); share.type = "button";
      share.addEventListener("click", async () => {
        const text = compare.map(x => `${x.title} | ${x.tower} | ${x.price}\n${location.origin}${x.path}`).join("\n\n");
        try { await navigator.clipboard.writeText(text); feedback.textContent = tr("Đã sao chép — anh/chị có thể dán vào Zalo.", "Copied. You can paste it into a message.", "복사했습니다."); }
        catch { const t = element("textarea"); t.value = text; t.readOnly = true; t.rows = 6; body.append(t); t.select(); feedback.textContent = tr("Chọn và sao chép nội dung bên dưới.", "Select and copy the text below.", "아래 내용을 복사하세요."); }
      });
      const zalo = element("a", "sc-primary", tr("Mở Zalo tư vấn", "Contact on Zalo", "Zalo 문의")); zalo.href = "https://zalo.me/0977923284"; zalo.target = "_blank"; zalo.rel = "noopener noreferrer";
      const actions = element("div", "sc-actions"); actions.append(share,zalo); body.append(actions);
    }
  }
  function openDialog() { render(); if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", ""); }
  function init() {
    if (!document.querySelector("main") || document.querySelector(".sc-shortlist-trigger")) return;
    trigger = element("button", "sc-shortlist-trigger", tr("Căn đã lưu", "Saved homes", "저장 목록")); trigger.type = "button";
    count = element("span", "sc-shortlist-count", "0"); trigger.append(count); trigger.hidden = true;
    dialog = element("dialog", "sc-shortlist"); dialog.setAttribute("aria-labelledby", "sc-shortlist-title");
    const head = element("div", "sc-shortlist-head"); const title = element("h2", "", tr("Căn đã lưu & so sánh", "Saved homes & comparison", "저장 및 비교")); title.id = "sc-shortlist-title";
    const close = element("button", "", tr("Đóng", "Close", "닫기")); close.type = "button"; close.addEventListener("click", () => { if (typeof dialog.close === "function") dialog.close(); else dialog.removeAttribute("open"); });
    head.append(title,close); body = element("div"); feedback = element("p", "sc-shortlist-note"); feedback.setAttribute("role", "status"); dialog.append(head,body,feedback);
    trigger.addEventListener("click", openDialog);
    const listHead = document.querySelector("#listingGrid") && document.querySelector(".list-head");
    if (listHead) {
      trigger.classList.add("sc-shortlist-in-list");
      listHead.insertBefore(trigger, listHead.querySelector("#sortSelect"));
    } else document.body.append(trigger);
    document.body.append(dialog);
    enhance();
    const container = document.querySelector("#listingGrid, .luoi, main");
    let pending = false;
    new MutationObserver(records => {
      if (pending || !records.some(r => [...r.addedNodes].some(n => n.nodeType === 1 && (n.matches?.("article.card, article.the") || n.querySelector?.("article.card, article.the"))))) return;
      pending = true; requestAnimationFrame(() => { pending = false; enhance(); });
    }).observe(container, {childList:true,subtree:true});
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, {once:true}); else init();
})();
