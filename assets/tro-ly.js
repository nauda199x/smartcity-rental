/* ================================================================
   TRỢ LÝ TÌM CĂN — timthuesmartcity.com
   Theo SPEC "Chat box trợ lý tìm căn" (26/08/2026).

   Không dùng LLM, không backend, không gọi mạng riêng: toàn bộ chạy
   trên mảng căn hộ mà index.html đã tải sẵn, nhận qua sự kiện
   "quy-can-san-sang" (index.html phát ra đúng 3 dòng trong init(),
   xem mục 5.1 của spec).

   Widget hoàn toàn tách rời: gỡ 2 dòng include ở cuối <body> và
   3 dòng dispatchEvent trong init() là hết dấu vết, không đụng
   logic lọc/phân trang/sắp xếp sẵn có của trang.
   ================================================================ */
(function () {
  "use strict";

  var ZALO_PHONE = "0977923284";
  var ZALO_URL = "https://zalo.me/" + ZALO_PHONE;
  var SITE_NAME = "timthuesmartcity.com";
  var SO_KET_QUA = 4;
  var SO_VONG_LAT_TRANG = 20;
  var KHOA_AN = "troLyAn";

  var LOAI = [
    { v: "Studio", t: "Studio" },
    { v: "1 Ngủ", t: "1 phòng ngủ" },
    { v: "1 Ngủ +", t: "1 phòng ngủ +" },
    { v: "2 Ngủ", t: "2 phòng ngủ" },
    { v: "2 Ngủ +", t: "2 phòng ngủ +" },
    { v: "3 Ngủ", t: "3 phòng ngủ" }
  ];
  /* Mốc giá PHẢI khớp bộ lọc chính của trang (biến priceFilters trong index.html):
     cận dưới không tính, cận trên có tính — "đúng 7,5 triệu" rơi vào "Dưới 7,5 triệu". */
  var GIA = [
    { t: "Dưới 7,5 triệu", test: function (tr) { return tr > 0 && tr <= 7.5; } },
    { t: "7,5 – 10 triệu", test: function (tr) { return tr > 7.5 && tr <= 10; } },
    { t: "10 – 12 triệu", test: function (tr) { return tr > 10 && tr <= 12; } },
    { t: "12 – 15 triệu", test: function (tr) { return tr > 12 && tr <= 15; } },
    { t: "Trên 15 triệu", test: function (tr) { return tr > 15; } }
  ];
  var NOITHAT = [
    { v: "Full nội thất", t: "Full nội thất" },
    { v: "Đồ Cơ bản", t: "Đồ cơ bản" },
    { v: "Nhà Nguyên Bản", t: "Nhà nguyên bản" }
  ];
  var LOI_CHOT = {
    gap: "Anh/chị cần vào ở ngay trong tuần thì nên xem nhà sớm ạ — căn đẹp thường chốt trong 2–3 ngày. Anh/chị nhắn Zalo, em sắp lịch dẫn xem luôn.",
    thang: "Trong tháng này thì còn thời gian chọn kỹ ạ. Anh/chị nhắn Zalo, em gửi thêm ảnh và video từng căn để xem trước.",
    xa: "Còn 1–2 tháng thì anh/chị cứ tham khảo dần ạ. Anh/chị lưu Zalo của em, sát ngày em cập nhật căn trống mới nhất.",
    xem: "Anh/chị cứ xem trước thoải mái ạ. Cần hỏi gì thêm hoặc muốn đi xem thực tế, nhắn Zalo em bất cứ lúc nào."
  };

  /* ---------------- Tiện ích chung ---------------- */
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function normVN(s) {
    return String(s)
      .toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d")
      .replace(/[^a-z0-9\s+]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }
  function slug(s) {
    return normVN(s).replace(/\+/g, "_plus").replace(/\s+/g, "_");
  }
  function cssAttrEscape(s) {
    return String(s).replace(/(["\\])/g, "\\$1");
  }
  function isMobile() {
    return window.matchMedia("(max-width:640px)").matches;
  }
  /* Định dạng giống hệt formatPrice() của index.html: chia 1.000.000,
     tròn 1 chữ số thập phân, dấu phẩy kiểu Việt, bỏ ",0" nếu tròn số. */
  function tienVN(giaVnd) {
    var tr = giaVnd / 1e6;
    var vi = Number.isInteger(tr) ? tr + " triệu" : tr.toFixed(1).replace(".", ",") + " triệu";
    return vi + "/tháng";
  }
  /* Chỉ hiện ngày vào ở khi có ngày thật, hợp lệ VÀ ở tương lai. Trống hoặc
     đã qua thì bỏ qua hẳn — không suy diễn "ở ngay" hay bất cứ điều gì khác. */
  function nhanNgayVao(s) {
    var m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(String(s || "").trim());
    if (!m) return "";
    var d = new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
    var now = new Date();
    now.setHours(0, 0, 0, 0);
    return d > now ? "Vào ở từ " + m[1] + "/" + m[2] : "";
  }
  /* Mô tả căn dùng chung cho dòng meta trên thẻ VÀ nội dung tin nhắn Zalo,
     để hai chỗ không bao giờ lệch nhau. */
  function moTaCan(u) {
    var phan = [];
    if (u.area) phan.push(u.area + "m²");
    phan.push(u.phanKhu ? u.phanKhu + " · " + u.tower : u.tower);
    if (u.interior) phan.push(u.interior);
    return phan.join(" · ");
  }
  function laMaChuan(id) {
    return /^CT\./i.test(String(id || ""));
  }
  function tinNhanZalo(u) {
    var giaVN = tienVN(u.price);
    var moTa = [];
    if (u.area) moTa.push(u.area + "m²");
    moTa.push(giaVN);
    if (laMaChuan(u.apartmentId)) {
      var noi = u.phanKhu ? u.phanKhu + " · " + u.tower : u.tower;
      return "Em quan tâm căn " + u.apartmentId + " (" + noi + ", " + moTa.join(", ") + ") trên " + SITE_NAME;
    }
    var tai = u.phanKhu ? u.phanKhu + " · " + u.tower : u.tower;
    return "Em quan tâm căn " + u.type + " tại " + tai + ", " + moTa.join(", ") + " trên " + SITE_NAME;
  }

  /* ---------------- Đo lường GA4 ---------------- */
  function guiSuKien(ten, thamSo) {
    try {
      if (typeof gtag === "function") gtag("event", ten, thamSo || {});
    } catch (e) { /* GA chặn/chưa nạp — im lặng bỏ qua, không được ảnh hưởng khách */ }
  }

  /* ---------------- Sao chép tin nhắn vào bộ nhớ tạm ----------------
     Zalo không hỗ trợ điền sẵn nội dung qua link, nên sao chép sẵn để
     khách dán — cùng cách trang chính đang làm với nút "Hỏi căn này"
     trên từng thẻ căn hộ. */
  function chepVaoBoNho(noiDung) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(noiDung).catch(function () { chepKieuCu(noiDung); });
        return;
      }
    } catch (e) { /* rơi xuống cách cũ */ }
    chepKieuCu(noiDung);
  }
  function chepKieuCu(noiDung) {
    try {
      var o = document.createElement("textarea");
      o.value = noiDung;
      o.setAttribute("readonly", "");
      o.style.cssText = "position:fixed;top:-1000px;opacity:0";
      document.body.appendChild(o);
      o.select();
      document.execCommand("copy");
      document.body.removeChild(o);
    } catch (e) { /* im lặng — khách vẫn mở được Zalo, chỉ không có sẵn tin nhắn */ }
  }

  /* ================================================================
     DỰNG WIDGET
     ================================================================ */
  var wrap = document.createElement("div");
  wrap.className = "tro-ly-wrap";
  wrap.id = "troLyWrap";
  wrap.innerHTML =
    '<div class="tro-ly-backdrop" id="troLyBackdrop"></div>' +
    '<div class="tro-ly-panel" role="dialog" aria-label="Trợ lý tìm căn">' +
      '<div class="tro-ly-grabber" id="troLyGrabber" aria-hidden="true"></div>' +
      '<div class="tro-ly-head">' +
        '<div class="tro-ly-av">TS</div>' +
        "<div><h3>Trợ lý tìm căn</h3><p><span class=\"tro-ly-dot\"></span> <span id=\"troLyHdSub\">Đang tải quỹ căn…</span></p></div>" +
        '<div class="tro-ly-acts">' +
          '<button class="tro-ly-ic" id="troLyMin" type="button" title="Thu nhỏ" aria-label="Thu nhỏ">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M5 12h14"/></svg></button>' +
          '<button class="tro-ly-ic" id="troLyHide" type="button" title="Ẩn trợ lý" aria-label="Ẩn trợ lý">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg></button>' +
        "</div>" +
      "</div>" +
      '<div class="tro-ly-body" id="troLyBody"></div>' +
      '<div class="tro-ly-foot">' +
        '<div class="tro-ly-input-row">' +
          '<input id="troLyInput" placeholder="Nhập tin nhắn…" autocomplete="off">' +
          '<button class="tro-ly-send" id="troLySend" type="button" aria-label="Gửi">' +
            '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/></svg></button>' +
        "</div>" +
        '<div class="tro-ly-hint">Muốn đi xem nhà, anh/chị chat Zalo trực tiếp nhé</div>' +
        '<button class="tro-ly-hide-link" id="troLyHideLink" type="button">Không cần trợ lý? Ẩn đi</button>' +
      "</div>" +
    "</div>" +
    '<button class="tro-ly-toggle" id="troLyToggle" type="button" aria-label="Mở trợ lý tìm căn">' +
      '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z"/></svg>' +
      '<span class="tro-ly-badge"></span></button>';

  var restoreBtn = document.createElement("button");
  restoreBtn.className = "tro-ly-restore";
  restoreBtn.id = "troLyRestore";
  restoreBtn.type = "button";
  restoreBtn.setAttribute("aria-label", "Hiện lại trợ lý");
  restoreBtn.innerHTML =
    '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z"/></svg> Trợ lý';

  var toastEl = document.createElement("div");
  toastEl.className = "tro-ly-toast";
  toastEl.id = "troLyToast";
  toastEl.setAttribute("role", "status");

  document.body.appendChild(wrap);
  document.body.appendChild(restoreBtn);
  document.body.appendChild(toastEl);

  var body = document.getElementById("troLyBody");
  var hdSub = document.getElementById("troLyHdSub");
  var inputEl = document.getElementById("troLyInput");

  /* ---------------- Trạng thái hội thoại ---------------- */
  var UNITS = [];
  var CAN_HOP_LE = [];
  var state = { loai: null, gia: null, nt: null, khi: null };
  var loaded = false, dataFailed = false, started = false, pendingStart = false;
  var hidden = false, missCount = 0, autoOpenDone = false;
  var thoiGianChoDuLieu = null;

  try {
    hidden = sessionStorage.getItem(KHOA_AN) === "1";
  } catch (e) { hidden = false; }
  if (hidden) {
    wrap.classList.add("tro-ly-gone");
    restoreBtn.classList.add("tro-ly-on");
  }

  /* ---------------- Lọc tập căn hợp lệ (khớp getFilteredApartments() cơ bản) ---------------- */
  function canHopLe(apartments) {
    return apartments.filter(function (a) {
      return a && a.show && a.price > 0 && a.type && a.tower;
    });
  }
  function loc(s) {
    return CAN_HOP_LE.filter(function (u) {
      return (!s.loai || u.type === s.loai) &&
        (!s.gia || s.gia.test(u.price / 1e6)) &&
        (!s.nt || u.interior === s.nt);
    });
  }
  function dem(s) { return loc(s).length; }

  /* ---------------- Giao diện: bong bóng, gõ, nút bấm ---------------- */
  function scrollBody() { body.scrollTop = body.scrollHeight; }
  function toast(t) {
    toastEl.textContent = t;
    toastEl.classList.add("tro-ly-on");
    clearTimeout(toastEl._h);
    toastEl._h = setTimeout(function () { toastEl.classList.remove("tro-ly-on"); }, 2600);
  }
  function bot(html, delay) {
    if (delay == null) delay = 420;
    var t = document.createElement("div");
    t.className = "tro-ly-typing";
    t.innerHTML = "<i></i><i></i><i></i>";
    body.appendChild(t);
    scrollBody();
    return new Promise(function (resolve) {
      setTimeout(function () {
        t.remove();
        var d = document.createElement("div");
        d.className = "tro-ly-msg tro-ly-msg-bot";
        d.innerHTML = html;
        body.appendChild(d);
        scrollBody();
        resolve();
      }, delay);
    });
  }
  function themTinKhach(t) {
    var d = document.createElement("div");
    d.className = "tro-ly-msg tro-ly-msg-user";
    d.textContent = t;
    body.appendChild(d);
    scrollBody();
  }
  function hienNut(list) {
    var w = document.createElement("div");
    w.className = "tro-ly-opts";
    list.forEach(function (o) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "tro-ly-opt" + (o.ghost ? " tro-ly-ghost" : "");
      b.innerHTML = esc(o.label) + (o.n != null ? " <i>" + o.n + "</i>" : "");
      b.onclick = function () {
        w.remove();
        themTinKhach(o.label);
        o.run();
      };
      w.appendChild(b);
    });
    body.appendChild(w);
    scrollBody();
  }
  /* Nút Zalo dùng chung: mở tab mới NGAY (target=_blank, không preventDefault,
     không hoãn điều hướng — khác với nút .ask ở thẻ căn hộ ngoài trang chính,
     nơi bản mobile cố tình đi cùng tab). Có nội dung thì chép sẵn vào bộ nhớ
     tạm để khách dán, không có thì chỉ mở Zalo. */
  function zaloBtn(label, noiDung, nguon) {
    var b = document.createElement("a");
    b.className = "tro-ly-zalo-cta";
    b.href = ZALO_URL;
    b.target = "_blank";
    b.rel = "noopener";
    b.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z"/></svg>' + esc(label);
    b.addEventListener("click", function () {
      if (noiDung) {
        chepVaoBoNho(noiDung);
        toast("Đã sao chép sẵn tin nhắn — dán vào khung chat Zalo giúp em nhé");
      }
      guiSuKien("troly_zalo", { nguon: nguon || "fallback" });
    });
    body.appendChild(b);
    scrollBody();
  }
  function napThe(el, ms) {
    el.classList.add("tro-ly-highlight");
    setTimeout(function () { el.classList.remove("tro-ly-highlight"); }, ms);
  }

  /* ---------------- Xem chi tiết: cuộn trang chính tới đúng thẻ căn ----------------
     Chỉ thao tác qua DOM công khai của trang (nút Xóa lọc, nút phân trang) —
     không đụng biến nội bộ (state/render) của index.html, để widget luôn
     tách rời khỏi cách trang chính cài đặt bên trong. */
  function timTheCan(id) {
    var grid = document.getElementById("listingGrid");
    if (!grid) return null;
    return grid.querySelector('[data-ma-noi-bo="' + cssAttrEscape(id) + '"]');
  }
  function xemChiTiet(id) {
    if (isMobile()) minimizeChat();
    var xoaBtn = document.getElementById("xoaBoLoc");
    if (xoaBtn) xoaBtn.click();

    var found = timTheCan(id);
    var vong = 0;
    while (!found && vong < SO_VONG_LAT_TRANG) {
      var pager = document.getElementById("pagination");
      var nutSau = pager ? pager.querySelector(".page-btn:last-child") : null;
      if (!nutSau || nutSau.disabled) break;
      nutSau.click();
      vong++;
      found = timTheCan(id);
    }

    if (found) {
      found.scrollIntoView({ behavior: "smooth", block: "center" });
      napThe(found, 2000);
    } else {
      bot("Anh/chị nhắn Zalo để em gửi trực tiếp căn này ạ.").then(function () {
        zaloBtn("Chat Zalo với em", null, "fallback");
      });
    }
  }
  function moBoLoc() {
    if (isMobile()) {
      minimizeChat();
      var nutMobile = document.getElementById("mobileFilterToggle");
      if (nutMobile) nutMobile.click();
      return;
    }
    var khoi = document.querySelector(".filter-card");
    if (!khoi) return;
    khoi.scrollIntoView({ behavior: "smooth", block: "center" });
    napThe(khoi, 1600);
  }

  /* ---------------- Mở / thu nhỏ / ẩn ---------------- */
  function moChat() {
    wrap.classList.add("tro-ly-open");
    if (isMobile()) document.body.classList.add("tro-ly-lock");
    scrollBody();
    guiSuKien("troly_mo", {});
    if (!started) {
      started = true;
      if (dataFailed) baoLoi();
      else if (loaded) chao();
      else pendingStart = true;
    }
  }
  function minimizeChat() {
    wrap.classList.remove("tro-ly-open");
    document.body.classList.remove("tro-ly-lock");
  }
  function anHan() {
    hidden = true;
    wrap.classList.remove("tro-ly-open");
    wrap.classList.add("tro-ly-gone");
    document.body.classList.remove("tro-ly-lock");
    restoreBtn.classList.add("tro-ly-on");
    try { sessionStorage.setItem(KHOA_AN, "1"); } catch (e) { /* trình duyệt chặn lưu — vẫn ẩn được trong phiên này */ }
    toast("Đã ẩn trợ lý. Bấm nút bên phải để hiện lại.");
    guiSuKien("troly_an", {});
  }
  function hienLai() {
    hidden = false;
    wrap.classList.remove("tro-ly-gone");
    restoreBtn.classList.remove("tro-ly-on");
    try { sessionStorage.removeItem(KHOA_AN); } catch (e) { /* im lặng */ }
    moChat();
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && wrap.classList.contains("tro-ly-open")) minimizeChat();
  });
  document.getElementById("troLyToggle").addEventListener("click", moChat);
  document.getElementById("troLyMin").addEventListener("click", minimizeChat);
  /* Ở mobile nút × chỉ còn một, nên nó đóng vai "thu nhỏ" (nút "–" bị ẩn đi
     bằng CSS) — ẩn hẳn (nhớ qua sessionStorage) chuyển sang dòng chữ nhỏ
     "Không cần trợ lý? Ẩn đi" cuối khung. Ở máy tính × vẫn ẩn hẳn như cũ. */
  document.getElementById("troLyHide").addEventListener("click", function () {
    if (isMobile()) minimizeChat(); else anHan();
  });
  document.getElementById("troLyHideLink").addEventListener("click", anHan);
  document.getElementById("troLyBackdrop").addEventListener("click", minimizeChat);
  restoreBtn.addEventListener("click", hienLai);

  /* ---------------- Vuốt header xuống để đóng (chỉ có tác dụng ở mobile,
     nơi panel là bottom sheet) ---------------- */
  (function ganVuotDeDong() {
    var headEl = wrap.querySelector(".tro-ly-head");
    var panelEl = wrap.querySelector(".tro-ly-panel");
    var NGUONG_DONG = 90;
    var startY = null, dy = 0, dragging = false;

    function onStart(e) {
      if (!isMobile() || !wrap.classList.contains("tro-ly-open")) return;
      startY = e.touches[0].clientY;
      dy = 0;
      dragging = true;
      panelEl.style.transition = "none";
    }
    function onMove(e) {
      if (!dragging) return;
      var raw = e.touches[0].clientY - startY;
      dy = raw > 0 ? raw : 0; // kéo lên không làm gì
      panelEl.style.transform = "translateY(" + dy + "px)";
    }
    function onEnd() {
      if (!dragging) return;
      dragging = false;
      panelEl.style.transition = "";
      if (dy > NGUONG_DONG) {
        panelEl.style.transform = "";
        minimizeChat();
      } else {
        // Chưa kéo đủ ngưỡng — bật lại về vị trí cũ, không đóng.
        panelEl.style.transform = "";
      }
      dy = 0;
    }
    headEl.addEventListener("touchstart", onStart, { passive: true });
    headEl.addEventListener("touchmove", onMove, { passive: true });
    headEl.addEventListener("touchend", onEnd);
    headEl.addEventListener("touchcancel", onEnd);
  })();

  /* ================================================================
     LUỒNG HỘI THOẠI
     ================================================================ */
  function chao() {
    return bot(
      "Chào anh/chị 👋 Em là trợ lý của <b>timthuesmartcity</b>.<br>Quỹ căn hiện có <b>" +
      CAN_HOP_LE.length + " căn</b> đang cho thuê tại Vinhomes Smart City ạ.", 250
    ).then(function () {
      hienNut([
        { label: "Tìm căn phù hợp", run: q1 },
        { label: "Chat Zalo luôn", ghost: true, run: function () {
          return bot("Anh/chị nhắn Zalo, em tư vấn trực tiếp ạ.").then(function () {
            zaloBtn("Chat Zalo với em", null, "fallback");
          });
        } }
      ]);
    });
  }
  function baoLoi() {
    return bot("Em chưa tải được quỹ căn lúc này ạ. Anh/chị nhắn Zalo để em tư vấn trực tiếp nhé.").then(function () {
      zaloBtn("Chat Zalo với em", null, "fallback");
    });
  }
  function q1() {
    state.loai = state.gia = state.nt = state.khi = null;
    return bot("Anh/chị cần thuê <b>loại căn nào</b> ạ?").then(function () {
      var list = LOAI
        .map(function (l) { return { l: l, n: dem({ loai: l.v }) }; })
        .filter(function (x) { return x.n > 0; })
        .map(function (x) { return { label: x.l.t, n: x.n, run: function () { state.loai = x.l.v; return q2(); } }; });
      hienNut(list);
    });
  }
  function q2() {
    return bot("Anh/chị cần mức nội thất nào ạ?").then(function () {
      var ds = NOITHAT
        .map(function (n) { return { n: n, c: dem({ loai: state.loai, nt: n.v }) }; })
        .filter(function (x) { return x.c > 0; });
      var list = ds.map(function (x) { return { label: x.n.t, n: x.c, run: function () { state.nt = x.n.v; return q3(); } }; });
      if (ds.length > 1) list.push({ label: "Loại nào cũng được", ghost: true, run: function () { state.nt = null; return q3(); } });
      hienNut(list);
    });
  }
  function q3() {
    return bot("Ngân sách của anh/chị khoảng bao nhiêu một tháng?").then(function () {
      var ds = GIA
        .map(function (g) { return { g: g, n: dem({ loai: state.loai, nt: state.nt, gia: g }) }; })
        .filter(function (x) { return x.n > 0; });
      var list = ds.map(function (x) { return { label: x.g.t, n: x.n, run: function () { state.gia = x.g; return q4(); } }; });
      if (ds.length > 1) list.push({ label: "Mức nào cũng được", ghost: true, run: function () { state.gia = null; return q4(); } });
      hienNut(list);
    });
  }
  function q4() {
    return bot("Anh/chị dự kiến <b>bao giờ vào ở</b> ạ?").then(function () {
      hienNut([
        { label: "Trong tuần này", run: function () { return show("gap"); } },
        { label: "Trong tháng này", run: function () { return show("thang"); } },
        { label: "1–2 tháng nữa", run: function () { return show("xa"); } },
        { label: "Chưa rõ, xem trước", ghost: true, run: function () { return show("xem"); } }
      ]);
    });
  }

  function veTheCan(u) {
    var d = document.createElement("div");
    d.className = "tro-ly-unit";
    var maChuan = laMaChuan(u.apartmentId);
    var nhan = maChuan ? esc(u.apartmentId) : "Căn " + esc(u.type);
    var when = nhanNgayVao(u.availableDate);
    var nutXemChiTiet = maChuan
      ? '<button class="tro-ly-btn-detail" type="button">Xem chi tiết</button>'
      : "";
    d.innerHTML =
      '<div class="tro-ly-unit-top">' +
        '<span class="tro-ly-unit-code' + (maChuan ? "" : " tro-ly-nomark") + '">' + nhan + "</span>" +
        '<span class="tro-ly-unit-price">' + esc(tienVN(u.price)) + "</span>" +
      "</div>" +
      '<div class="tro-ly-unit-meta">' + esc(moTaCan(u)) + "</div>" +
      (when ? '<div class="tro-ly-unit-when">' + esc(when) + "</div>" : "") +
      '<div class="tro-ly-unit-acts">' + nutXemChiTiet +
        '<a class="tro-ly-btn-zalo" href="' + ZALO_URL + '" target="_blank" rel="noopener">Hỏi căn này</a></div>';
    if (maChuan) {
      d.querySelector(".tro-ly-btn-detail").addEventListener("click", function () { xemChiTiet(u.apartmentId); });
    }
    d.querySelector(".tro-ly-btn-zalo").addEventListener("click", function () {
      chepVaoBoNho(tinNhanZalo(u));
      toast("Đã sao chép sẵn tin nhắn — dán vào khung chat Zalo giúp em nhé");
      guiSuKien("troly_zalo", { nguon: "the-can" });
    });
    body.appendChild(d);
    scrollBody();
  }

  function show(khi) {
    state.khi = khi;
    var found = loc(state).slice().sort(function (a, b) { return a.price - b.price; });
    var list = found.slice(0, SO_KET_QUA);

    guiSuKien("troly_hoan_thanh", {
      loai: state.loai ? slug(state.loai) : "tat_ca",
      khoang_gia: state.gia ? slug(state.gia.t) : "tat_ca",
      noi_that: state.nt ? slug(state.nt) : "tat_ca",
      so_can: found.length
    });

    if (!list.length) {
      return bot(
        "Hiện <b>chưa có căn nào</b> khớp đúng tiêu chí này ạ. Em không gợi ý căn lệch tiêu chí để anh/chị khỏi mất công xem.<br><br>Anh/chị nhắn Zalo, có căn mới về em báo ngay."
      ).then(function () {
        zaloBtn("Chat Zalo với em", null, "fallback");
        hienNut([{ label: "Tìm lại từ đầu", ghost: true, run: q1 }]);
      });
    }

    var du = found.length - list.length;
    return bot("Em có <b>" + found.length + " căn</b> phù hợp ạ. Em gửi anh/chị " + list.length + " căn giá tốt nhất:")
      .then(function () {
        var chain = Promise.resolve();
        list.forEach(function (u) {
          chain = chain.then(function () {
            return new Promise(function (r) { setTimeout(r, 160); }).then(function () { veTheCan(u); });
          });
        });
        return chain;
      })
      .then(function () {
        if (du > 0) return bot("Còn <b>" + du + " căn</b> nữa cùng tiêu chí ạ. Anh/chị xem thêm ở bộ lọc đầu trang, hoặc nhắn Zalo để em gửi hết.");
      })
      .then(function () { return bot(LOI_CHOT[khi]); })
      .then(function () {
        zaloBtn("Chat Zalo với em", null, "chot-cuoi");
        hienNut([
          { label: "Mở bộ lọc", run: function () {
            moBoLoc();
            return bot("Bộ lọc ở ngay đầu trang ạ, anh/chị chọn tiêu chí là danh sách tự cập nhật.");
          } },
          { label: "Tìm loại căn khác", ghost: true, run: q1 }
        ]);
      });
  }

  /* ---------------- Gõ tự do ---------------- */
  var RE_TIM_CAN = /(studio|\d ?ngu|\d ?pn|phong ngu|can ho|thue|tim can|noi that|gia|trieu)/;
  function guiTinNhan() {
    var raw = inputEl.value.trim();
    if (!raw) return;
    inputEl.value = "";
    themTinKhach(raw);

    if (!loaded) {
      if (dataFailed) { baoLoi(); return; }
      bot("Em đang tải quỹ căn, anh/chị đợi một chút ạ.");
      return;
    }
    var q = normVN(raw);
    if (RE_TIM_CAN.test(q)) {
      missCount = 0;
      bot("Để em hỏi vài câu rồi gợi ý căn cho nhanh ạ.").then(q1);
      return;
    }
    missCount++;
    if (missCount >= 2) {
      bot("Câu này em nhắn Zalo trao đổi với anh/chị cho tiện ạ.").then(function () {
        zaloBtn("Chat Zalo với em", null, "fallback");
      });
      missCount = 0;
    } else {
      bot("Em hỗ trợ <b>tìm căn hộ cho thuê</b> tại Vinhomes Smart City ạ. Các câu hỏi khác anh/chị nhắn Zalo em trả lời trực tiếp nhé.").then(function () {
        hienNut([{ label: "Bắt đầu tìm căn", run: q1 }]);
      });
    }
  }
  document.getElementById("troLySend").addEventListener("click", guiTinNhan);
  inputEl.addEventListener("keydown", function (e) { if (e.key === "Enter") guiTinNhan(); });

  /* ================================================================
     NHẬN DỮ LIỆU SỐNG TỪ TRANG CHÍNH
     ================================================================ */
  function tuMoNeuHopLe() {
    if (autoOpenDone || isMobile() || hidden) return;
    autoOpenDone = true;
    setTimeout(function () {
      if (!hidden && !wrap.classList.contains("tro-ly-open")) moChat();
    }, 2000);
  }

  document.addEventListener("quy-can-san-sang", function (e) {
    clearTimeout(thoiGianChoDuLieu);
    var apartments = (e.detail && e.detail.apartments) || [];
    UNITS = apartments;
    CAN_HOP_LE = canHopLe(UNITS);
    loaded = true;
    dataFailed = false;
    hdSub.textContent = "Đang hoạt động";
    if (pendingStart) { pendingStart = false; chao(); }
    tuMoNeuHopLe();
  });

  /* index.html có thể chưa từng phát sự kiện (lỗi mạng khi tải data.json,
     hoặc trang cũ chưa kịp thêm 3 dòng dispatchEvent) — sau 12 giây coi như
     không tải được, báo lỗi rõ ràng thay vì treo vòng xoay mãi mãi. */
  thoiGianChoDuLieu = setTimeout(function () {
    if (loaded) return;
    dataFailed = true;
    hdSub.textContent = "Chưa tải được dữ liệu";
    if (pendingStart) { pendingStart = false; baoLoi(); }
    tuMoNeuHopLe();
  }, 12000);
})();
