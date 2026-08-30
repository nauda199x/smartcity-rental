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
    if (/bang-gia|so-sanh-gia|gia-thue-studio/.test(p)) return "bang-gia";
    if (/cam-nang|kinh-nghiem|luu-y|phi-dich-vu|tien-ich/.test(p)) return "cam-nang";
    return "";
  }

  var IC = {
    nha: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 10.5 12 4l8.5 6.5V19a1 1 0 0 1-1 1h-5v-6h-5v6h-5a1 1 0 0 1-1-1Z"/></svg>',
    sach: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H10a2 2 0 0 1 2 2v13a2 2 0 0 0-2-2H5.5A1.5 1.5 0 0 1 4 15.5Z"/><path d="M20 5.5A1.5 1.5 0 0 0 18.5 4H14a2 2 0 0 0-2 2v13a2 2 0 0 1 2-2h4.5a1.5 1.5 0 0 0 1.5-1.5Z"/></svg>',
    kygui: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 10.5 12 4l8.5 6.5V19a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1Z"/><path d="M12 16v-5M9.6 13.2 12 10.8l2.4 2.4" stroke-linecap="round"/></svg>',
    timmua: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M3.5 10.5 12 4l8.5 6.5V19a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1Z"/><path d="M12 10.5v6M10.2 12.2h2.6a1.3 1.3 0 0 1 0 2.6h-1.6a1.3 1.3 0 0 0 0 2.6h2.6" stroke-linecap="round"/></svg>',
    gia: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M4 7.5A2.5 2.5 0 0 1 6.5 5h11A2.5 2.5 0 0 1 20 7.5v9a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5Z"/><path d="M8 9.5h8M8 13h5M8 16.5h3"/></svg>',
    menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none"/></svg>'
  };

  /* Các mục trong bảng Menu — TOÀN BỘ đều là trang đã có thật trên site,
     không tạo link tới trang chưa tồn tại. */
  /* "k" là khoá tra bản dịch (assets/ngon-ngu.js). "so" là số điện thoại tách
     riêng khỏi phần chữ để dịch không nuốt mất số. */
  var MENU = [
    { nhom: "Tìm căn hộ", k: "sh.findRent" },
    { ten: "Tất cả căn đang thuê", k: "sh.allRent", href: "/" },
    { ten: "Studio", href: "/studio/" },
    { ten: "1 phòng ngủ", href: "/1pn/" },
    { ten: "1 phòng ngủ +", href: "/1pn-plus/" },
    { ten: "2 phòng ngủ", href: "/2pn/" },
    { ten: "2 phòng ngủ +", href: "/2pn-plus/" },
    { ten: "3 phòng ngủ", href: "/3pn/" },

    { nhom: "Phân khu", k: "sh.zones" },
    { ten: "Sapphire", href: "/sapphire/" },
    { ten: "Masteri West Heights", href: "/masteri/" },
    { ten: "The Miami", href: "/miami/" },
    { ten: "Sakura", href: "/sakura/" },
    { ten: "Imperia Smart City", href: "/imperia/" },
    { ten: "The Canopy Residences", href: "/canopy/" },
    { ten: "Lumiere Evergreen", href: "/lumiere/" },
    { ten: "The Tonkin", href: "/tonkin/" },

    { nhom: "Giá thuê & cẩm nang", k: "sh.priceGuide" },
    { ten: "Bảng giá thuê Vinhomes Smart City", k: "sh.priceTable", href: "/bang-gia-thue-vinhomes-smart-city.html" },
    { ten: "So sánh giá thuê các phân khu", k: "sh.priceCompare", href: "/so-sanh-gia-thue-cac-phan-khu-smart-city.html" },
    { ten: "Cẩm nang thuê nhà", k: "sh.guideFull", href: "/cam-nang-thue-nha.html" },
    { ten: "Kinh nghiệm thuê chung cư Smart City", k: "sh.exp", href: "/kinh-nghiem-thue-chung-cu-smart-city.html" },
    { ten: "Phí dịch vụ, gửi xe, thú cưng", k: "sh.fees", href: "/phi-dich-vu-vinhomes-smart-city.html" },

    { nhom: "Liên hệ", k: "sh.contact" },
    { ten: "Ký gửi căn cho thuê", k: "nav.consign", href: "/gui-thue/" },
    { ten: "Nhắn Zalo", so: SDT, k: "nav.zalo", href: "https://zalo.me/" + SDT, ngoai: true, zalo: true },
    { ten: "Gọi", so: SDT, k: "ft.call", href: "tel:" + SDT },

    { nhom: "Khác", k: "sh.other" },
    { ten: "Tìm mua căn hộ Smart City", k: "sh.buyLink", href: "https://timmuasmartcity.com", ngoai: true },
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
         + '><span' + (m.k ? ' data-i18n="' + m.k + '"' : '') + '>' + m.ten + '</span>'
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
        '<a href="/"' + lop("trang-chu") + '>' + IC.nha + '<span data-i18n="sh.rent">Căn thuê</span></a>'
      + '<a href="https://timmuasmartcity.com" target="_blank" rel="noopener">'
        + IC.timmua + '<span data-i18n="sh.buy">Tìm mua</span></a>'
      + '<a href="/gui-thue/"' + lop("ky-gui") + '>' + IC.kygui + '<span data-i18n="sh.consign">Ký gửi</span></a>'
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
     NAVIGATION V4 — một kiến trúc điều hướng cho toàn site
     ------------------------------------------------------------------
     HTML tĩnh cũ vẫn giữ link để crawler đọc. Sau DOMContentLoaded, khối này
     chuẩn hóa phần nhìn thành menu theo ý định thuê: Thuê căn hộ / Phân khu /
     Loại căn / Bảng giá / Cẩm nang / Tìm mua / Ký gửi.
     ================================================================ */
  var NHOM_PHAN_KHU = [
    ["Sapphire", "/sapphire/"],
    ["Masteri West Heights", "/masteri/"],
    ["The Miami", "/miami/"],
    ["Sakura", "/sakura/"],
    ["Imperia Smart City", "/imperia/"],
    ["The Canopy Residences", "/canopy/"],
    ["Lumiere Evergreen", "/lumiere/"],
    ["The Tonkin", "/tonkin/"]
  ];

  var NHOM_LOAI_CAN = [
    ["Studio", "/studio/"],
    ["1 phòng ngủ", "/1pn/"],
    ["1 phòng ngủ +", "/1pn-plus/"],
    ["2 phòng ngủ", "/2pn/"],
    ["2 phòng ngủ +", "/2pn-plus/"],
    ["3 phòng ngủ", "/3pn/"]
  ];

  function navLink(label, href, cls, key) {
    var current = duongDan();
    var active = href === "/"
      ? (current === "/" || current === "")
      : current.indexOf(href.replace(/\/$/, "")) === 0;
    return '<a class="nav-v4-link' + (cls ? " " + cls : "") + (active ? " active" : "") + '" href="' + href + '"'
      + (active ? ' aria-current="page"' : "")
      + (key ? ' data-i18n="' + key + '"' : "") + '>' + label + '</a>';
  }

  function navNhom(label, items, active, key) {
    var html = '<div class="nav-v4-group' + (active ? " active" : "") + '">'
      + '<button class="nav-v4-trigger" type="button" aria-expanded="false"'
      + (key ? ' data-i18n="' + key + '"' : "") + '>' + label
      + '<span class="nav-v4-chevron" aria-hidden="true"></span></button>'
      + '<div class="nav-v4-panel">';
    for (var i = 0; i < items.length; i++) {
      html += '<a href="' + items[i][1] + '">' + items[i][0] + '</a>';
    }
    html += '</div></div>';
    return html;
  }

  function nhomNavDangMo() {
    var p = duongDan();
    var zone = /\/(sapphire|masteri|miami|sakura|imperia|canopy|lumiere|tonkin)\/?/.test(p);
    var type = /\/(studio|1pn|1pn-plus|2pn|2pn-plus|3pn)\/?/.test(p);

    /* Trang chi tiết dùng slug căn chứ không dùng slug danh mục, nên đọc thêm
       breadcrumb để vẫn tô đúng nhóm Phân khu / Loại căn. */
    var bcLinks = document.querySelectorAll(".bc a");
    for (var i = 0; i < bcLinks.length; i++) {
      var href = bcLinks[i].getAttribute("href") || "";
      if (/^\/(sapphire|masteri|miami|sakura|imperia|canopy|lumiere|tonkin)\/?$/.test(href)) zone = true;
      if (/^\/(studio|1pn|1pn-plus|2pn|2pn-plus|3pn)\/?$/.test(href)) type = true;
    }

    return {
      zone: zone,
      type: type,
      price: /bang-gia|so-sanh-gia|gia-thue-studio/.test(p),
      guide: /cam-nang|kinh-nghiem|luu-y|phi-dich-vu|tien-ich/.test(p),
      consign: p.indexOf("/gui-thue") === 0
    };
  }

  function dongTatCaDropdown(ngoaiTru) {
    var ds = document.querySelectorAll(".nav-v4-group.open");
    for (var i = 0; i < ds.length; i++) {
      if (ngoaiTru && ds[i] === ngoaiTru) continue;
      ds[i].classList.remove("open");
      var b = ds[i].querySelector(".nav-v4-trigger");
      if (b) b.setAttribute("aria-expanded", "false");
    }
  }

  function nangCapNavigation() {
    var header = document.querySelector("header.topbar, header.top");
    if (!header) return;
    var nav = header.querySelector("nav.topnav") || header.querySelector("nav");
    if (!nav || nav.classList.contains("site-nav-v4")) return;

    var active = nhomNavDangMo();
    var brand = header.querySelector("a.brand, a.hieu");
    if (brand && (!brand.getAttribute("href") || brand.getAttribute("href") === "#")) brand.href = "/";
    nav.className = "topnav site-nav-v4";
    nav.setAttribute("aria-label", "Điều hướng chính");
    nav.setAttribute("data-i18n-al", "nav.main");
    nav.innerHTML =
        navLink("Thuê căn hộ", "/", "nav-v4-rent", "nav.rent")
      + navNhom("Phân khu", NHOM_PHAN_KHU, active.zone, "nav.zone")
      + navNhom("Loại căn", NHOM_LOAI_CAN, active.type, "nav.type")
      + navLink("Bảng giá", "/bang-gia-thue-vinhomes-smart-city.html", active.price ? "active" : "", "nav.price")
      + navLink("Cẩm nang", "/cam-nang-thue-nha.html", active.guide ? "active" : "", "nav.guideShort")
      + '<a class="nav-v4-link nav-v4-buy" href="https://timmuasmartcity.com" target="_blank" rel="noopener" data-i18n="sh.buy">Tìm mua</a>'
      + navLink("Ký gửi", "/gui-thue/", active.consign ? "active" : "", "nav.consignShort");

    var shell = header.querySelector(".shell, .khung");
    if (shell) {
      shell.classList.add("site-nav-shell");
      if (shell.querySelector(".search")) shell.classList.add("has-site-search");
    }

    var triggers = nav.querySelectorAll(".nav-v4-trigger");
    for (var i = 0; i < triggers.length; i++) {
      triggers[i].addEventListener("click", function (e) {
        e.stopPropagation();
        var group = this.closest(".nav-v4-group");
        var mo = !group.classList.contains("open");
        dongTatCaDropdown(group);
        group.classList.toggle("open", mo);
        this.setAttribute("aria-expanded", mo ? "true" : "false");
      });
    }

    document.addEventListener("click", function (e) {
      if (!e.target.closest(".site-nav-v4")) dongTatCaDropdown();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") dongTatCaDropdown();
    });

    nhoDich(nav);
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

  /* ================================================================
     TRANG CHI TIẾT CĂN HỘ — nạp gallery + UX riêng chỉ ở /can-ho/<slug>/
     ------------------------------------------------------------------
     Trang căn được generator sinh lại nhiều lần trong ngày. Nạp từ app-shell
     giúp cả trang cũ lẫn trang mới nhận UX mới mà không cần sửa tay 60+ file.
     ================================================================ */
  function laTrangChiTietCan() {
    var p = duongDan();
    return /^\/can-ho\/[^/]+\/?$/.test(p);
  }

  function napScriptMotLan(id, src, xong) {
    var cu = document.getElementById(id);
    if (cu) {
      if (cu.dataset.daTai === "1") { if (xong) xong(); }
      else if (xong) cu.addEventListener("load", xong, { once: true });
      return;
    }
    var s = document.createElement("script");
    s.id = id;
    s.src = src;
    s.defer = true;
    s.addEventListener("load", function () {
      s.dataset.daTai = "1";
      if (xong) xong();
    }, { once: true });
    document.head.appendChild(s);
  }

  function napUxChiTietCan() {
    if (!laTrangChiTietCan()) return;
    function napDetail() {
      napScriptMotLan("ct-detail-js", "/assets/can-ho-detail.js");
    }
    if (typeof window.MoGallery === "function") napDetail();
    else napScriptMotLan("ct-gallery-js", "/assets/gallery.js", napDetail);
  }

  function khoiDong() {
    try {
      nangCapNavigation();              // header/menu desktop dong bo toan site
      boSungDanhTinhWebsite();          // disclaimer + link gioi thieu tren toan site
      napUxChiTietCan();                // gallery + UX rieng cho trang can
      if (laDienThoai() && !laTrangChiTietCan()) dung(); // trang can dung CTA lien he rieng
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