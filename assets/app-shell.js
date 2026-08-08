/*!
 * app-shell.js — Thanh tab dưới đáy cho bản điện thoại
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
  var MENU = [
    { nhom: "Liên hệ" },
    { ten: "Nhắn Zalo " + SDT, href: "https://zalo.me/" + SDT, ngoai: true, zalo: true },
    { ten: "Gọi " + SDT, href: "tel:" + SDT },
    { nhom: "Tra cứu giá" },
    { ten: "Bảng giá thuê Vinhomes Smart City", href: "/bang-gia-thue-vinhomes-smart-city.html" },
    { ten: "So sánh giá thuê các phân khu", href: "/so-sanh-gia-thue-cac-phan-khu-smart-city.html" },
    { ten: "Giá thuê căn Studio", href: "/gia-thue-studio-smart-city.html" },
    { nhom: "Tìm hiểu trước khi thuê" },
    { ten: "Cẩm nang thuê nhà", href: "/cam-nang-thue-nha.html" },
    { ten: "Kinh nghiệm thuê chung cư Smart City", href: "/kinh-nghiem-thue-chung-cu-smart-city.html" },
    { ten: "Tiện ích nội khu", href: "/tien-ich-vinhomes-smart-city.html" },
    { ten: "Phí dịch vụ, gửi xe, thú cưng", href: "/phi-dich-vu-vinhomes-smart-city.html" },
    { nhom: "Muốn mua thay vì thuê?" },
    { ten: "Xem căn đang bán tại Smart City", href: "https://timmuasmartcity.com", ngoai: true },
    { nhom: "Khác" },
    { ten: "Danh mục căn hộ theo phân khu", href: "/#mucLucKhoDuLieu" },
    { ten: "Chính sách quyền riêng tư", href: "/chinh-sach-quyen-rieng-tu.html" }
  ];

  function dungMenuHtml() {
    var h = '<div class="tbs-head"><strong>Menu</strong>'
          + '<button type="button" id="tbsDong" aria-label="Đóng">&times;</button></div>';
    for (var i = 0; i < MENU.length; i++) {
      var m = MENU[i];
      if (m.nhom) { h += '<div class="tbs-nhom">' + m.nhom + '</div>'; continue; }
      h += '<a href="' + m.href + '"'
         + (m.ngoai ? ' target="_blank" rel="noopener"' : '')
         + (m.zalo ? ' class="tbs-zalo"' : '')
         + '>' + m.ten + '</a>';
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
    bar.innerHTML =
        '<a href="/"' + lop("trang-chu") + '>' + IC.nha + '<span>Trang chủ</span></a>'
      + '<a href="https://timmuasmartcity.com" target="_blank" rel="noopener">'
        + IC.timmua + '<span>Tìm mua</span></a>'
      + '<a href="/gui-thue/"' + lop("ky-gui") + '>' + IC.kygui + '<span>Ký gửi thuê</span></a>'
      + '<button type="button" id="tabMenu" aria-haspopup="dialog">' + IC.menu + '<span>Menu</span></button>';

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

    /* Đặt ngay sau "Trang chủ" — mục "Danh mục căn" (mốc cũ) đã gỡ ngày 08/08/2026. */
    nav.insertBefore(a, nav.children[1] || null);
  }

  function khoiDong() {
    try {
      chenLinkTimMua();                 // chay o MOI kich thuoc man hinh
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
