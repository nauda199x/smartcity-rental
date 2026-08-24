/*!
 * app-shell.js — Thanh tab dưới đáy cho bản điện thoại
 *
 * SỬA 24/08/2026 — bổ sung thông tin minh bạch ở footer và đường dẫn
 * "Giới thiệu & Liên hệ" trên toàn site để làm rõ TimThueSmartCity.com
 * là nền tảng/môi giới độc lập, không phải website chính thức của
 * Vinhomes/Vingroup.
 *
 * SỬA 03/08/2026 — tab thứ 2 đổi từ "Cẩm nang" thành "Tìm mua",
 * trỏ sang timmuasmartcity.com. Khách đang xem thuê mà muốn mua thì
 * sang thẳng, không phải rời site tìm lại. Cẩm nang chuyển vào Menu
 * (vốn đã có sẵn ở đó, nên không mất đường vào).
 * timthuesmartcity.com — thêm 01/08/2026
 *
 * VÌ SAO DỰNG BẰNG JS THAY VÌ DÁN HTML VÀO 39 TRANG:
 *   - Sửa một file là cả site đổi theo, không phải mở lại 39 file mỗi lần
 *     đổi nhãn tab hay thêm mục trong Menu.
 *   - Các đường link trong thanh tab ĐỀU ĐÃ CÓ SẴN trong header/footer HTML
 *     tĩnh của từng trang, nên Google vẫn đọc đủ liên kết nội bộ. Thanh tab
 *     chỉ là lối đi tắt cho người dùng, không phải nguồn liên kết duy nhất.
 *   - Chỉ chèn thêm phần tử, KHÔNG đụng vào nội dung đang có.
 *
 * An toàn: bọc try/catch, lỗi ở đây tuyệt đối không được làm chết trang.
 */
(function () {
  "use strict";

  var SDT = "0977923284";

  /* ---------- Đổi ngôn ngữ (thêm 11/08/2026) -------------------------
     assets/ngon-ngu.js CHỈ được nạp ở index.html. Trên 41 trang còn lại
     window.NGON_NGU_APDUNG không tồn tại nên thanh tab và Menu hiện đúng
     tiếng Việt như hôm nay — đây là hành vi mong muốn, không phải lỗi.

     Dựng bằng CHỮ TIẾNG VIỆT kèm data-i18n rồi mới nhờ bộ máy dịch, thay vì
     dịch sẵn lúc dựng: có vậy bộ máy mới ghi nhớ được đúng bản gốc và trả
     lại nguyên văn khi khách bấm VI. */
  function nhoDich(el) {
    try {
      if (typeof window.NGON_NGU_APDUNG === "function") window.NGON_NGU_APDUNG(el);
    } catch (e) { /* im lặng — hỏng ở đây không được kéo sập cả trang */ }
  }

  /* Chỉ dựng trên màn hình hẹp. Khách xoay ngang máy tính bảng thì CSS tự ẩn,
     không cần dựng lại DOM. */
  function laDienThoai() {
    return window.matchMedia("(max-width:640px)").matches;
  }

  function duongDan() {
    var p = location.pathname.replace(/index\.html$/, "");
    if (p.length > 1 && p.charAt(p.length - 1) !== "/") return p;
    return p;
  }

  /* Tab nào đang mở: dùng để tô đậm đúng một mục */
  function tabDangMo() {
    var p = duongDan();
    if (p === "/" || p === "") return "trang-chu";
    if (p.indexOf("/gui-thue") === 0) return "ky-gui";
    if (/cam-nang|kinh-nghiem|luu-y|phi-dich-vu|tien-ich|bang-gia|so-sanh|gia-thue-studio/.test(p)) return "cam-nang";
    return "";
  }

  var IC = {
    nha: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 10.5 12 4l8.5 6.5V19a1 1 0 0 1-1 1h-5v-6h-5v6h-5a1 1 0 0 1-1-1Z"/></svg>',
    sach: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H10a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H5.5A1.5 1.5 0 0 1 4 15.5Z"/><path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H14a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h4.5a1.5 1.5 0 0 0 1.5-1.5Z"/></svg>',
    kygui: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 10.5 12 4l8.5 6.5V19a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1Z"/><path d="M12 16v-5M9.6 13.2 12 10.8l2.4 2.4" stroke-linecap="round"/></svg>',
    timmua: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 10.5 12 4l8.5 6.5V19a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1Z"/><path d="M12 10.5v6M10.2 12.2h2.6a1.3 1.3 0 0 1 0 2.6h-1.6a1.3 1.3 0 0 0 0 2.6h2.6" stroke-linecap="round"/></svg>',
    menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none"/></svg>'
  };

  /* Các mục trong bảng Menu — TOÀN BỘ đều là trang đã có thật trên site,
     không tạo link tới trang chưa tồn tại. */
  /* "k" là khoá tra bản dịch (assets/ngon-ngu.js). "so" là số điện thoại tách
     riêng khỏi phần chữ để dịch không nuốt mất số. */
  var MENU = [
    { nhom: "Liên hệ", k: "sh.contact" },
    { ten: "Nhắn Zalo", so: SDT, k: "nav.zalo", href: "https://zalo.me/" + SDT, ngoai: true, zalo: true },
    { ten: "Gọi", so: SDT, k: "ft.call", href: "tel:" + SDT },
    { nhom: "Tra cứu giá", k: "sh.priceLookup" },
    { ten: "Bảng giá thuê Vinhomes Smart City", k: "sh.priceTable", href: "/bang-gia-thue-vinhomes-smart-city.html" },
    { ten: "So sánh giá thuê các phân khu", k: "sh.priceCompare", href: "/so-sanh-gia-thue-cac-phan-khu-smart-city.html" },
    { ten: "Giá thuê căn Studio", k: "sh.priceStudio", href: "/gia-thue-studio-smart-city.html" },
    { nhom: "Tìm hiểu trước khi thuê", k: "sh.before" },
    { ten: "Cẩm nang thuê nhà", k: "sh.guideFull", href: "/cam-nang-thue-nha.html" },
    { ten: "Kinh nghiệm thuê chung cư Smart City", k: "sh.exp", href: "/kinh-nghiem-thue-chung-cu-smart-city.html" },
    { ten: "Tiện ích nội khu", k: "sh.amen", href: "/tien-ich-vinhomes-smart-city.html" },
    { ten: "Phí dịch vụ, gửi xe, thú cưng", k: "sh.fees", href: "/phi-dich-vu-vinhomes-smart-city.html" },
    { nhom: "Muốn mua thay vì thuê?", k: "sh.buyTitle" },
    { ten: "Xem căn đang bán tại Smart City", k: "sh.buyLink", href: "https://timmuasmartcity.com", ngoai: true },
    { nhom: "Khác", k: "sh.other" },
    { ten: "Danh mục căn hộ theo phân khu", k: "sh.cat", href: "/#mucLucKhoDuLieu" },
    { ten: "Giới thiệu & Liên hệ", k: "sh.about", href: "/gioi-thieu-lien-he.html" },
    { ten: "Chính sách quyền riêng tư", k: "sh.privacy", href: "/chinh-sach-quyen-rieng-tu.html" }
  ];

  function dungMenuHtml() {
    var h = '<div class="tbs-head"><strong data-i18n="sh.menu">Menu</strong>'
          + '<button type="button" id="tbsDong" aria-label="Đóng" data-i18n-al="sh.close">&times;</button></div>';
    for (var i = 0; i < MENU.length; i++) {
      var m = MENU[i];
      if (m.nhom) {
        h += '<div class="tbs-nhom" data-i18n="' + m.k + '">' + m.nhom + '</div>';
        continue;
      }
      h += '<a href="' + m.href + '"'
         + (m.ngoai ? ' target="_blank" rel="noopener"' : '')
         + (m.zalo ? ' class="tbs-zalo"' : '')
         + '><span data-i18n="' + m.k + '">' + m.ten + '</span>'
         + (m.so ? " " + m.so : "") + '</a>';
    }
    return h;
  }

  function dung() {
    if (document.querySelector(".tabbar")) return;

    var mo = tabDangMo();
    function lop(k) { return mo === k ? ' class="dang-o-day"' : ''; }

    var bar = document.createElement("nav");
    bar.className = "tabbar";
    bar.setAttribute("aria-label", "Điều hướng nhanh");
    bar.setAttribute("data-i18n-al", "sh.navAl");
    bar.innerHTML =
        '<a href="/"' + lop("trang-chu") + '>' + IC.nha + '<span data-i18n="sh.home">Trang chủ</span></a>'
      + '<a href="https://timmuasmartcity.com" target="_blank" rel="noopener">'
        + IC.timmua + '<span data-i18n="sh.buy">Tìm mua</span></a>'
      + '<a href="/gui-thue/"' + lop("ky-gui") + '>' + IC.kygui + '<span data-i18n="sh.consign">Ký gửi thuê</span></a>'
      + '<button type="button" id="tabMenu" aria-haspopup="dialog">' + IC.menu + '<span data-i18n="sh.menu">Menu</span></button>';

    var nen = document.createElement("div");
    nen.className = "tabbar-backdrop";

    var sheet = document.createElement("div");
    sheet.className = "tabbar-sheet";
    sheet.setAttribute("role", "dialog");
    sheet.setAttribute("aria-label", "Menu");
    sheet.innerHTML = dungMenuHtml();

    document.body.appendChild(nen);
    document.body.appendChild(sheet);
    document.body.appendChild(bar);
    nhoDich(sheet);
    nhoDich(bar);

    function moMenu() { sheet.classList.add("open"); nen.classList.add("open"); }
    function dongMenu() { sheet.classList.remove("open"); nen.classList.remove("open"); }

    document.getElementById("tabMenu").addEventListener("click", moMenu);
    document.getElementById("tbsDong").addEventListener("click", dongMenu);
    nen.addEventListener("click", dongMenu);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") dongMenu();
    });
    sheet.addEventListener("click", function (e) {
      if (e.target.closest("a")) dongMenu();
    });
  }

  /* ================================================================
     CHEN LINK "TIM MUA" VAO MENU DESKTOP  (them 03/08/2026)
     ----------------------------------------------------------------
     VI SAO LAM BANG JS:
       Menu desktop nam trong <nav class="topnav"> cua TUNG file HTML —
       ben nay co 39 trang. Sua tay 39 file cho mot lien ket la khong
       thuc te, va lan sau doi chu lai phai sua lai tu dau.
       File nay da duoc nap tren moi trang nen chen o day la ca site co.

     KHAC voi thanh tab duoi: thanh tab CHI dung tren dien thoai, con
     ham nay chay o MOI kich thuoc man hinh.

     An toan: khong tim thay <nav class="topnav"> thi lang le bo qua.
     ================================================================ */
  function chenLinkTimMua() {
    var nav = document.querySelector("nav.topnav");
    if (!nav) return;
    if (nav.querySelector('a[href*="timmuasmartcity.com"]')) return;  // da co roi

    var a = document.createElement("a");
    a.href = "https://timmuasmartcity.com";
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "Tìm mua";
    a.setAttribute("data-i18n", "sh.buy");

    /* Đặt ngay sau "Trang chủ" — mục "Danh mục căn" (mốc cũ) đã gỡ ngày 08/08/2026. */
    nav.insertBefore(a, nav.children[1] || null);
    nhoDich(a);
  }

  /* ================================================================
     THONG TIN MINH BACH / DISCLAIMER  (them 24/08/2026)
     ----------------------------------------------------------------
     Dùng chung cho tất cả trang đang nạp app-shell.js. Nội dung được đặt
     ngay trong footer, rõ ràng nhưng không làm cản trở luồng tìm căn.
     Trang /gioi-thieu-lien-he.html chứa bản đầy đủ và tĩnh trong HTML.
     ================================================================ */
  function boSungDanhTinhWebsite() {
    var footer = document.querySelector("footer");
    if (!footer) return;
    if (footer.querySelector('[data-site-identity="true"]')) return;

    var box = document.createElement("div");
    box.className = "shell";
    box.setAttribute("data-site-identity", "true");
    box.style.cssText = "padding-top:14px;padding-bottom:8px;color:var(--muted,#667085);font-size:13px;line-height:1.65";
    box.innerHTML = '<p style="margin:0"><strong style="color:inherit">Thông tin minh bạch:</strong> '
      + '<strong>TimThueSmartCity.com</strong> là nền tảng/môi giới cho thuê căn hộ độc lập, '
      + 'không phải website chính thức và không đại diện cho Vinhomes/Vingroup. '
      + '<a href="/gioi-thieu-lien-he.html" style="font-weight:700">Giới thiệu &amp; Liên hệ</a>.</p>';

    footer.insertBefore(box, footer.firstChild);
  }

  function khoiDong() {
    try {
      chenLinkTimMua();                 // chay o MOI kich thuoc man hinh
      boSungDanhTinhWebsite();          // disclaimer + link gioi thieu tren toan site
      if (laDienThoai()) dung();        // thanh tab duoi CHI tren dien thoai
    } catch (e) { /* im lặng — hỏng ở đây không được kéo sập cả trang */ }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", khoiDong);
  } else {
    khoiDong();
  }
  /* Xoay ngang / đổi kích thước cửa sổ: dựng bù nếu lúc tải là màn rộng */
  window.addEventListener("resize", khoiDong);
})();