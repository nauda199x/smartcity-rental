/*!
 * can-ho-detail.js — UX marketplace cho trang chi tiết căn hộ
 * Chỉ chạy trên /can-ho/<slug>/; HTML tĩnh và schema giữ nguyên cho crawler.
 */
(function () {
  "use strict";

  var SDT = "0977923284";

  function q(sel, root) { return (root || document).querySelector(sel); }
  function qa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  function tao(tag, cls, chu) {
    var el = document.createElement(tag);
    if (cls) el.className = cls;
    if (chu !== undefined && chu !== null) el.textContent = chu;
    return el;
  }

  function laTrangChiTiet() {
    var p = location.pathname.replace(/index\.html$/, "");
    return /^\/can-ho\/[^/]+\/?$/.test(p);
  }

  function docBang(bang) {
    var ra = {};
    if (!bang) return ra;
    qa("tr", bang).forEach(function (tr) {
      var td = qa("td", tr);
      if (td.length >= 2) ra[td[0].textContent.trim()] = td[1].textContent.trim();
    });
    return ra;
  }

  function tinhTrang(giaTri) {
    var s = String(giaTri || "").trim();
    if (!s || /vào ngay|o ngay|luôn|ngay/i.test(s)) return "Vào ngay";
    return "Trống từ " + s;
  }

  function nutLienHe(cls, href, chu, ngoai) {
    var a = tao("a", cls, chu);
    a.href = href;
    if (ngoai) {
      a.target = "_blank";
      a.rel = "noopener";
    }
    return a;
  }

  function saoChepDatLich(ma) {
    var noiDung = "Mình muốn đặt lịch xem căn " + (ma || "") + " tại Vinhomes Smart City. Nhờ bạn tư vấn giúp mình thời gian xem căn phù hợp.";
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(noiDung).catch(function () {});
        return;
      }
    } catch (e) {}

    try {
      var ta = document.createElement("textarea");
      ta.value = noiDung;
      ta.setAttribute("readonly", "");
      ta.style.cssText = "position:fixed;left:-9999px;top:0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    } catch (e2) {}
  }

  function ganNutDatLich(a, ma) {
    if (!a) return;
    a.addEventListener("click", function () {
      saoChepDatLich(ma);
      var toast = q("#ctDetailToast");
      if (toast) {
        toast.classList.add("show");
        clearTimeout(window.__ctToast);
        window.__ctToast = setTimeout(function () { toast.classList.remove("show"); }, 1800);
      }
    });
  }

  function taoToast() {
    if (q("#ctDetailToast")) return;
    var t = tao("div", "ct-detail-toast", "Đã sao chép nội dung đặt lịch — mở Zalo và dán để gửi nhanh.");
    t.id = "ctDetailToast";
    t.setAttribute("role", "status");
    t.setAttribute("aria-live", "polite");
    document.body.appendChild(t);
  }

  function nangTrangDaThue(main) {
    document.body.classList.add("trang-chi-tiet-can", "trang-chi-tiet-da-thue");
    var bai = q(".bai", main);
    if (bai) bai.classList.add("ct-rented-note");

    var h2s = qa("h2", main);
    h2s.forEach(function (h) {
      var next = h.nextElementSibling;
      if (/căn còn trống tương tự/i.test(h.textContent) && next) next.classList.add("ct-related");
      if (/xem thêm/i.test(h.textContent) && next) next.classList.add("ct-more-links");
    });

    if (!q(".ct-mobile-actions")) {
      var bar = tao("nav", "ct-mobile-actions ct-mobile-occupied");
      bar.setAttribute("aria-label", "Hành động nhanh");
      bar.appendChild(nutLienHe("ct-ma-secondary", "/", "Xem căn trống", false));
      bar.appendChild(nutLienHe("ct-ma-primary", "https://zalo.me/" + SDT, "Nhắn Zalo", true));
      document.body.appendChild(bar);
    }
  }

  function khoiDong() {
    if (!laTrangChiTiet()) return;

    var main = q("main.khung");
    if (!main || document.body.classList.contains("trang-chi-tiet-can")) return;

    var h1 = q("h1", main);
    var gallery = q("section.gallery", main);
    var bang = q("table.bang", main);

    if (!gallery) {
      nangTrangDaThue(main);
      return;
    }

    document.body.classList.add("trang-chi-tiet-can");
    main.classList.add("ct-detail-page");

    var duLieu = docBang(bang);
    var ma = duLieu["Mã căn"] || "";
    var gia = duLieu["Giá thuê"] || "";
    var vaoO = tinhTrang(duLieu["Ngày vào ở"]);
    var tt = h1 ? h1.nextElementSibling : null;

    /* ----- Dòng giá + trạng thái ngay dưới tiêu đề ----- */
    if (h1 && !q(".ct-title-meta", main)) {
      var titleMeta = tao("div", "ct-title-meta");
      var price = tao("strong", "ct-title-price", gia || "Liên hệ giá thuê");
      var status = tao("span", "ct-title-status", vaoO);
      titleMeta.appendChild(price);
      titleMeta.appendChild(status);
      h1.insertAdjacentElement("afterend", titleMeta);
      if (tt && tt.classList && tt.classList.contains("tt")) tt.classList.add("ct-detail-lead");
    }

    /* ----- Gallery: desktop mosaic, mobile swipe; bấm mở fullscreen ----- */
    gallery.classList.add("ct-gallery");
    var imgs = qa("img", gallery);
    var media = imgs.map(function (img) { return img.currentSrc || img.src; }).filter(Boolean);
    var hienTai = 0;

    imgs.forEach(function (img, i) {
      img.dataset.ctIndex = String(i);
      img.setAttribute("role", "button");
      img.setAttribute("tabindex", "0");
      img.setAttribute("aria-label", "Mở ảnh " + (i + 1) + " trên " + imgs.length);
      function mo() {
        if (typeof window.MoGallery === "function") window.MoGallery(media, i);
      }
      img.addEventListener("click", mo);
      img.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); mo(); }
      });
    });

    if (imgs.length) {
      var xemAnh = tao("button", "ct-gallery-all", "Xem tất cả " + imgs.length + " ảnh");
      xemAnh.type = "button";
      xemAnh.setAttribute("aria-label", "Xem toàn bộ " + imgs.length + " ảnh căn hộ");
      xemAnh.addEventListener("click", function () {
        if (typeof window.MoGallery === "function") window.MoGallery(media, hienTai);
      });
      gallery.appendChild(xemAnh);

      var hen = 0;
      gallery.addEventListener("scroll", function () {
        if (hen) return;
        hen = requestAnimationFrame(function () {
          hen = 0;
          if (gallery.clientWidth) {
            hienTai = Math.max(0, Math.min(imgs.length - 1, Math.round(gallery.scrollLeft / gallery.clientWidth)));
            if (window.matchMedia("(max-width:640px)").matches) {
              xemAnh.textContent = (hienTai + 1) + "/" + imgs.length + " ảnh";
            }
          }
        });
      }, { passive: true });
    }

    /* ----- Hai cột: nội dung + card liên hệ sticky ----- */
    var cacSauGallery = [];
    var node = gallery.nextElementSibling;
    while (node) {
      cacSauGallery.push(node);
      node = node.nextElementSibling;
    }

    var layout = tao("div", "ct-detail-layout");
    var content = tao("section", "ct-detail-content");
    var aside = tao("aside", "ct-detail-aside");
    aside.setAttribute("aria-label", "Thông tin thuê và liên hệ");
    layout.appendChild(content);
    layout.appendChild(aside);
    gallery.insertAdjacentElement("afterend", layout);
    cacSauGallery.forEach(function (el) { content.appendChild(el); });

    var stats = q(".sl", content);
    if (stats) stats.classList.add("ct-facts");
    if (bang) bang.classList.add("ct-detail-table");

    /* Nút cũ vẫn tồn tại trong HTML cho fallback/SEO; JS chỉ ẩn bản nhìn để tránh lặp. */
    var ctaCu = q("a.cta-loc", content);
    if (ctaCu && ctaCu.parentElement) ctaCu.parentElement.classList.add("ct-original-actions");

    qa("h2", content).forEach(function (h) {
      var next = h.nextElementSibling;
      if (/căn tương tự/i.test(h.textContent) && next) next.classList.add("ct-related");
      if (/xem thêm/i.test(h.textContent) && next) next.classList.add("ct-more-links");
    });

    /* ----- Sticky card desktop/tablet ----- */
    var card = tao("div", "ct-aside-card");
    var badge = tao("span", "ct-live-badge", vaoO === "Vào ngay" ? "Có thể vào ở ngay" : vaoO);
    var priceAside = tao("strong", "ct-aside-price", gia || "Liên hệ");
    var sub = tao("span", "ct-aside-sub", "Giá thuê căn hộ");
    card.appendChild(badge);
    card.appendChild(priceAside);
    card.appendChild(sub);

    var facts = tao("div", "ct-aside-facts");
    [
      ["Loại căn", duLieu["Loại"]],
      ["Diện tích", duLieu["Diện tích"]],
      ["Tòa", duLieu["Tòa"]],
      ["Nội thất", duLieu["Nội thất"]]
    ].forEach(function (item) {
      if (!item[1]) return;
      var row = tao("div", "ct-aside-fact");
      row.appendChild(tao("span", "", item[0]));
      row.appendChild(tao("b", "", item[1]));
      facts.appendChild(row);
    });
    card.appendChild(facts);

    var actions = tao("div", "ct-aside-actions");
    var datLich = nutLienHe("ct-action ct-action-primary", "https://zalo.me/" + SDT, "Đặt lịch xem căn", true);
    var zalo = nutLienHe("ct-action ct-action-zalo", "https://zalo.me/" + SDT, "Nhắn Zalo", true);
    var call = nutLienHe("ct-action ct-action-call", "tel:" + SDT, "Gọi 0977 923 284", false);
    actions.appendChild(datLich);
    actions.appendChild(zalo);
    actions.appendChild(call);
    card.appendChild(actions);

    if (ma) card.appendChild(tao("small", "ct-aside-code", "Mã căn: " + ma));
    card.appendChild(tao("p", "ct-aside-note", "Thông tin căn được đồng bộ từ quỹ căn đang hiển thị trên website."));
    aside.appendChild(card);

    /* ----- Thanh hành động cố định mobile ----- */
    var mobile = tao("nav", "ct-mobile-actions");
    mobile.setAttribute("aria-label", "Liên hệ căn hộ");
    var mCall = nutLienHe("ct-ma-call", "tel:" + SDT, "Gọi", false);
    var mZalo = nutLienHe("ct-ma-zalo", "https://zalo.me/" + SDT, "Zalo", true);
    var mBook = nutLienHe("ct-ma-primary", "https://zalo.me/" + SDT, "Đặt lịch xem", true);
    mobile.appendChild(mCall);
    mobile.appendChild(mZalo);
    mobile.appendChild(mBook);
    document.body.appendChild(mobile);

    ganNutDatLich(datLich, ma);
    ganNutDatLich(mBook, ma);
    taoToast();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", khoiDong);
  } else {
    khoiDong();
  }
})();