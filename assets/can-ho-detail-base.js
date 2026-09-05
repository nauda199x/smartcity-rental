/*!
 * can-ho-detail.js — UX marketplace cho trang chi tiết căn hộ
 * Chỉ chạy trên /can-ho/<slug>/; HTML tĩnh và schema giữ nguyên cho crawler.
 */
(function () {
  "use strict";

  var SDT = "0977923284";
  var MEDIA_API = "https://script.google.com/macros/s/AKfycbxP2LYjIwPnf9VPofUtKjyIETqo9lGjAmv-AT0txsh0NXcTZhdZLkpHcDDssGQtjEWs/exec";
  var MEDIA_CACHE_KEY = "ct-detail-video-map-v1";
  var MEDIA_CACHE_TTL = 10 * 60 * 1000;

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

  /* =====================================================================
     VIDEO CĂN HỘ
     - Bảng hàng An Việt Land đã có sẵn Danh sách video từ Google Drive.
     - Trang chi tiết chỉ lấy 3 trường an toàn: id, videoCover, videoList.
     - JSONP để chạy ổn cả khi Apps Script không trả CORS header.
     - Desktop: phát ngay trong mosaic.
     - Mobile: mở player toàn màn hình riêng để control Google Drive không
       đè lên gallery/CTA và người dùng đóng quay lại đúng vị trí đang xem.
     ===================================================================== */
  function tachDanhSachVideo(v) {
    if (Array.isArray(v)) return v.map(String).map(function (s) { return s.trim(); }).filter(Boolean);
    return String(v || "").split(/\r?\n/).map(function (s) { return s.trim(); }).filter(Boolean);
  }

  function laUrlVideoAnToan(url) {
    return /^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]+\/preview(?:[?#].*)?$/i.test(String(url || ""));
  }

  function docMediaCache() {
    try {
      var raw = sessionStorage.getItem(MEDIA_CACHE_KEY);
      if (!raw) return null;
      var x = JSON.parse(raw);
      if (!x || !x.at || !x.map || Date.now() - x.at > MEDIA_CACHE_TTL) return null;
      return x.map;
    } catch (e) { return null; }
  }

  function luuMediaCache(items) {
    var map = {};
    (Array.isArray(items) ? items : []).forEach(function (item) {
      var id = String(item && item.id || "").trim();
      var videos = tachDanhSachVideo(item && item.videoList).filter(laUrlVideoAnToan);
      if (!id || !videos.length) return;
      map[id] = {
        videos: videos,
        cover: String(item.videoCover || "").trim()
      };
    });
    try {
      sessionStorage.setItem(MEDIA_CACHE_KEY, JSON.stringify({ at: Date.now(), map: map }));
    } catch (e) {}
    return map;
  }

  function napInventoryJsonp(done) {
    var cb = "__ctVideoCb" + Date.now() + Math.floor(Math.random() * 100000);
    var script = document.createElement("script");
    var xong = false;
    var hen;

    function don() {
      if (hen) clearTimeout(hen);
      try { delete window[cb]; } catch (e) { window[cb] = undefined; }
      if (script.parentNode) script.parentNode.removeChild(script);
    }

    window[cb] = function (payload) {
      if (xong) return;
      xong = true;
      don();
      var items = payload && Array.isArray(payload.items) ? payload.items : [];
      done(null, luuMediaCache(items));
    };

    script.async = true;
    script.src = MEDIA_API + "?action=inventory&callback=" + encodeURIComponent(cb) + "&_=" + Date.now();
    script.onerror = function () {
      if (xong) return;
      xong = true;
      don();
      done(new Error("Không tải được dữ liệu video"), null);
    };
    hen = setTimeout(function () {
      if (xong) return;
      xong = true;
      don();
      done(new Error("Quá thời gian tải video"), null);
    }, 9000);
    document.head.appendChild(script);
  }

  function layVideoTheoMa(ma, done) {
    ma = String(ma || "").trim();
    if (!ma) return done(null);

    var cache = docMediaCache();
    if (cache) return done(cache[ma] || null);

    napInventoryJsonp(function (err, map) {
      if (err || !map) return done(null);
      done(map[ma] || null);
    });
  }

  function chenCssVideo() {
    if (q("#ctDetailVideoStyle")) return;
    var st = tao("style");
    st.id = "ctDetailVideoStyle";
    st.textContent = [
      ".trang-chi-tiet-can .ct-gallery.ct-has-video>.ct-video-media{grid-column:1;grid-row:1/3;position:relative;z-index:2;min-width:0;min-height:0;overflow:hidden;background:#0b1220}",
      ".trang-chi-tiet-can .ct-gallery.ct-has-video>img:nth-of-type(1){grid-column:2;grid-row:1;display:block}",
      ".trang-chi-tiet-can .ct-gallery.ct-has-video>img:nth-of-type(2){grid-column:2;grid-row:2;display:block}",
      ".trang-chi-tiet-can .ct-gallery.ct-has-video>img:nth-of-type(n+3){display:none}",
      ".trang-chi-tiet-can .ct-gallery.ct-has-video.ct-video-one-image>img:nth-of-type(1){grid-row:1/3}",
      ".ct-video-launch,.ct-video-frame{width:100%;height:100%;border:0;display:block}",
      ".ct-video-launch{position:relative;padding:0;background:#0b1220;overflow:hidden;color:#fff;text-align:left;touch-action:pan-x}",
      ".ct-video-launch>img{width:100%;height:100%;object-fit:cover;display:block;opacity:.96;transition:transform .25s ease,filter .25s ease}",
      ".ct-video-launch:after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,12,24,.02) 38%,rgba(4,12,24,.56) 100%);pointer-events:none}",
      ".ct-video-launch:hover>img{transform:scale(1.012);filter:brightness(.96)}",
      ".ct-video-play{position:absolute;left:50%;top:50%;z-index:3;transform:translate(-50%,-50%);width:68px;height:68px;border-radius:999px;background:rgba(15,23,42,.88);border:1px solid rgba(255,255,255,.38);box-shadow:0 12px 35px rgba(0,0,0,.28);display:grid;place-items:center;font-size:27px;line-height:1;padding-left:4px;color:#fff}",
      ".ct-video-label{position:absolute;left:14px;bottom:14px;z-index:3;display:inline-flex;align-items:center;gap:7px;padding:8px 11px;border-radius:9px;background:rgba(15,23,42,.82);color:#fff;font-size:.78rem;font-weight:700;box-shadow:0 7px 22px rgba(0,0,0,.18)}",
      ".ct-video-count{position:absolute;left:14px;top:14px;z-index:3;padding:6px 9px;border-radius:8px;background:rgba(15,23,42,.76);color:#fff;font-size:.7rem;font-weight:700}",
      ".ct-video-frame{background:#0b1220}",
      ".ct-video-modal{position:fixed;inset:0;z-index:10000;background:#03060b;display:flex;flex-direction:column;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}",
      ".ct-video-modal-head{height:58px;flex:none;display:flex;align-items:center;justify-content:space-between;padding:0 14px;color:#fff;background:#080d16;border-bottom:1px solid rgba(255,255,255,.09)}",
      ".ct-video-modal-head strong{font-family:var(--font-tieu-de);font-size:.93rem;letter-spacing:-.01em}",
      ".ct-video-modal-close{width:40px;height:40px;border:1px solid rgba(255,255,255,.15);border-radius:12px;background:rgba(255,255,255,.08);color:#fff;font-size:27px;line-height:1;display:grid;place-items:center;padding:0}",
      ".ct-video-modal-body{position:relative;flex:1;min-height:0;background:#000;display:flex;align-items:stretch;justify-content:stretch}",
      ".ct-video-modal-body iframe{width:100%;height:100%;border:0;background:#000;display:block}",
      "body.ct-video-modal-open{overflow:hidden!important;touch-action:none}",
      "@media(max-width:640px){.trang-chi-tiet-can .ct-gallery.ct-has-video>.ct-video-media{display:block;flex:0 0 100%;width:100%;height:100%;scroll-snap-align:center;scroll-snap-stop:always}.ct-video-play{width:58px;height:58px;font-size:23px;background:rgba(9,20,38,.9);box-shadow:0 10px 30px rgba(0,0,0,.3)}.ct-video-label{left:10px;bottom:10px;padding:7px 9px;font-size:.7rem;border-radius:8px}.ct-video-count{left:10px;top:10px}.trang-chi-tiet-can .ct-gallery.ct-has-video>img,.trang-chi-tiet-can .ct-gallery.ct-has-video>img:nth-of-type(n+3){display:block;flex:0 0 100%;width:100%;height:100%;object-fit:cover;scroll-snap-align:center;scroll-snap-stop:always}.trang-chi-tiet-can .ct-gallery.ct-has-video>.ct-gallery-all{right:10px;top:10px;bottom:auto;min-height:32px;padding:0 10px;background:rgba(255,255,255,.94);border-radius:9px;font-size:.7rem}.ct-video-modal-head{height:54px;padding:0 10px 0 14px}.ct-video-modal-close{width:38px;height:38px;border-radius:11px}.ct-video-modal-body{min-height:0}.trang-chi-tiet-can .bc{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}"
    ].join("\n");
    document.head.appendChild(st);
  }

  function moVideoModal(url, ma) {
    if (!laUrlVideoAnToan(url)) return;
    var cu = q("#ctVideoModal");
    if (cu) cu.remove();

    var modal = tao("div", "ct-video-modal");
    modal.id = "ctVideoModal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "Video thực tế căn hộ");

    var head = tao("div", "ct-video-modal-head");
    head.appendChild(tao("strong", "", ma ? "Video thực tế · " + ma : "Video thực tế căn hộ"));
    var dong = tao("button", "ct-video-modal-close", "×");
    dong.type = "button";
    dong.setAttribute("aria-label", "Đóng video");
    head.appendChild(dong);

    var body = tao("div", "ct-video-modal-body");
    var frame = tao("iframe");
    frame.src = url;
    frame.title = ma ? "Video thực tế căn " + ma : "Video thực tế căn hộ";
    frame.loading = "eager";
    frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    frame.setAttribute("allowfullscreen", "");
    frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
    body.appendChild(frame);

    modal.appendChild(head);
    modal.appendChild(body);
    document.body.appendChild(modal);
    document.body.classList.add("ct-video-modal-open");

    function tat() {
      document.body.classList.remove("ct-video-modal-open");
      if (modal.parentNode) modal.parentNode.removeChild(modal);
      document.removeEventListener("keydown", phim);
    }
    function phim(e) { if (e.key === "Escape") tat(); }
    dong.addEventListener("click", tat);
    document.addEventListener("keydown", phim);
    setTimeout(function () { try { dong.focus(); } catch (e) {} }, 0);
  }

  function themVideoVaoGallery(gallery, media, soAnh, ma) {
    if (!gallery || !media || !media.videos || !media.videos.length || q(".ct-video-media", gallery)) return;
    var videos = media.videos.filter(laUrlVideoAnToan);
    if (!videos.length) return;

    chenCssVideo();
    gallery.classList.add("ct-has-video");
    if (soAnh === 1) gallery.classList.add("ct-video-one-image");

    var wrap = tao("div", "ct-video-media");
    var launch = tao("button", "ct-video-launch");
    launch.type = "button";
    launch.setAttribute("aria-label", "Xem video thực tế căn hộ");

    var poster = tao("img");
    var anhDau = q("img", gallery);
    poster.src = media.cover || (anhDau ? (anhDau.currentSrc || anhDau.src) : "");
    poster.alt = "Video thực tế căn hộ";
    poster.loading = "eager";
    poster.decoding = "async";
    launch.appendChild(poster);

    var play = tao("span", "ct-video-play", "▶");
    play.setAttribute("aria-hidden", "true");
    launch.appendChild(play);
    launch.appendChild(tao("span", "ct-video-label", "Video thực tế · Bấm để xem"));
    if (videos.length > 1) launch.appendChild(tao("span", "ct-video-count", videos.length + " video"));

    launch.addEventListener("click", function () {
      if (window.matchMedia("(max-width:640px)").matches) {
        moVideoModal(videos[0], ma);
        return;
      }
      var frame = tao("iframe", "ct-video-frame");
      frame.src = videos[0];
      frame.title = ma ? "Video thực tế căn " + ma : "Video thực tế căn hộ";
      frame.loading = "eager";
      frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      frame.setAttribute("allowfullscreen", "");
      frame.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
      wrap.replaceChildren(frame);
    });

    wrap.appendChild(launch);
    gallery.insertBefore(wrap, gallery.firstChild);

    /* Trên mobile nút cũ “Xem tất cả N ảnh” hơi dài và đè lên video.
       Thu gọn thành “N ảnh”; desktop vẫn giữ nguyên câu đầy đủ. */
    var nutAnh = q(".ct-gallery-all", gallery);
    if (nutAnh && window.matchMedia("(max-width:640px)").matches) {
      nutAnh.textContent = soAnh + " ảnh";
      nutAnh.setAttribute("aria-label", "Xem toàn bộ " + soAnh + " ảnh căn hộ");
    }
  }

  function napVideoChoGallery(gallery, ma, soAnh) {
    layVideoTheoMa(ma, function (media) {
      if (!media) return;
      themVideoVaoGallery(gallery, media, soAnh, ma);
    });
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
      var xemAnh = tao("button", "ct-gallery-all", typeof window.CT_DETAIL_T === "function"
        ? window.CT_DETAIL_T("gallery.all", "Xem tất cả {N} ảnh", { N: imgs.length })
        : "Xem tất cả " + imgs.length + " ảnh");
      xemAnh.type = "button";
      xemAnh.setAttribute("aria-label", "Xem toàn bộ " + imgs.length + " ảnh căn hộ");
      xemAnh.addEventListener("click", function () {
        if (typeof window.MoGallery === "function") window.MoGallery(media, hienTai);
      });
      gallery.appendChild(xemAnh);

      var hen = 0;
      gallery.addEventListener("scroll", function () {
        if (gallery.classList.contains("ct-has-video")) return;
        if (hen) return;
        hen = requestAnimationFrame(function () {
          hen = 0;
          if (gallery.clientWidth) {
            hienTai = Math.max(0, Math.min(imgs.length - 1, Math.round(gallery.scrollLeft / gallery.clientWidth)));
            if (window.matchMedia("(max-width:640px)").matches) {
              xemAnh.textContent = typeof window.CT_DETAIL_T === "function"
                ? window.CT_DETAIL_T("gallery.count", "{I}/{N} ảnh", { I: hienTai + 1, N: imgs.length })
                : (hienTai + 1) + "/" + imgs.length + " ảnh";
            }
          }
        });
      }, { passive: true });
    }

    /* Video lấy từ cùng nguồn đang cấp cho bảng hàng. Chạy bất đồng bộ để
       HTML/ảnh hiển thị ngay; lỗi API không ảnh hưởng phần còn lại của trang. */
    napVideoChoGallery(gallery, ma, imgs.length);

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