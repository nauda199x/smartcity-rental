/*!
 * gallery.js — Xem ảnh toàn màn hình, kiểu Airbnb / Booking / Ảnh trên iPhone
 * timthuesmartcity.com — thêm 01/08/2026
 *
 * VÌ SAO CÓ FILE NÀY: trước đây trang chủ và 25 trang danh mục dùng HAI cơ chế
 * xem ảnh khác nhau, sửa một chỗ không ảnh hưởng chỗ kia. Nay gộp về một.
 *
 * ĐÚNG YÊU CẦU, KHÔNG THÊM GÌ KHÁC:
 *   - Nền đen, ảnh chiếm trọn màn hình
 *   - Nút ✕ góc trên TRÁI, số thứ tự "1/12" góc trên PHẢI
 *   - Vuốt ngang đổi ảnh, chụm hai ngón để phóng, kéo ảnh khi đã phóng
 *   - KHÔNG hiện giá, mô tả, nút Zalo hay bất kỳ thông tin nào khác
 *   - Đóng lại về ĐÚNG vị trí cũ trên trang, không tải lại trang
 *
 * BA ĐIỂM KỸ THUẬT QUAN TRỌNG:
 *   1. Vuốt ngang dùng scroll-snap gốc của trình duyệt nên mượt như app thật,
 *      không phải mô phỏng bằng JS và không nạp thư viện ngoài.
 *   2. Nút Back của Android và vuốt-back của iOS ĐÓNG GALLERY chứ không rời
 *      trang. Thiếu phần này thì khách bấm back một phát là văng khỏi web.
 *   3. Ảnh Drive trên thẻ tải bản w1000 cho nhẹ; vào gallery mới đổi sang
 *      w1600 để phóng to không bị vỡ. Chỉ tải ảnh liền kề, không tải cả album.
 */
(function () {
  "use strict";

  var ID = "gallery-toan-man-hinh";
  var CSS_ID = "gallery-css";

  /* ---------- 0. Đổi ngôn ngữ (thêm 11/08/2026) ----------------------
     assets/ngon-ngu.js CHỈ được nạp ở index.html. Trên 41 trang còn lại
     window.NGON_NGU_APDUNG không tồn tại nên file này hiện đúng tiếng Việt
     như hôm nay — đây là hành vi mong muốn, không phải lỗi.

     Khung gallery được dựng bằng CHỮ TIẾNG VIỆT kèm data-i18n-al rồi mới
     nhờ bộ máy dịch, thay vì dịch sẵn lúc dựng: có vậy bộ máy mới ghi nhớ
     được đúng bản gốc và trả lại nguyên văn khi khách bấm VI. */
  function nhoDich(el) {
    try {
      if (typeof window.NGON_NGU_APDUNG === "function") window.NGON_NGU_APDUNG(el);
    } catch (e) { /* im lặng — hỏng ở đây không được kéo sập gallery */ }
  }
  var khung = null, track = null, oDem = null;
  var danhSach = [], viTri = 0, doCuonCu = 0, dangMo = false, daDayLichSu = false;

  /* ---------- 1. CSS tự chèn: file này chạy độc lập, không phụ thuộc v3.css ---------- */
  function chenCss() {
    if (document.getElementById(CSS_ID)) return;
    var s = document.createElement("style");
    s.id = CSS_ID;
    s.textContent = [
      "#" + ID + "{position:fixed;inset:0;z-index:9999;background:#000;display:none;",
      "  -webkit-user-select:none;user-select:none;overscroll-behavior:contain}",
      "#" + ID + ".mo{display:block}",
      "#" + ID + " .gl-track{position:absolute;inset:0;display:flex;overflow-x:auto;overflow-y:hidden;",
      "  scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;scrollbar-width:none}",
      "#" + ID + " .gl-track::-webkit-scrollbar{display:none}",
      "#" + ID + " .gl-slide{flex:0 0 100%;width:100%;height:100%;scroll-snap-align:center;",
      "  scroll-snap-stop:always;display:flex;align-items:center;justify-content:center;",
      "  overflow:hidden;touch-action:pan-x}",
      "#" + ID + " .gl-slide.phong{touch-action:none}",
      "#" + ID + " .gl-slide img,#" + ID + " .gl-slide video{max-width:100%;max-height:100%;",
      "  display:block;object-fit:contain;transform-origin:center center;will-change:transform}",
      "#" + ID + " .gl-slide img{cursor:zoom-in}",
      /* Thanh trên: chỉ có ✕ và số thứ tự. Nền chuyển đen mờ để hai thứ đó
         luôn đọc được kể cả khi ảnh phía sau sáng trắng. */
      "#" + ID + " .gl-top{position:absolute;left:0;right:0;top:0;z-index:3;",
      "  display:flex;align-items:center;justify-content:space-between;",
      "  padding:calc(10px + env(safe-area-inset-top)) 14px 26px;",
      "  background:linear-gradient(180deg,rgba(0,0,0,.55),rgba(0,0,0,0));pointer-events:none}",
      "#" + ID + " .gl-x{pointer-events:auto;width:38px;height:38px;border:0;border-radius:50%;",
      "  background:rgba(0,0,0,.42);color:#fff;font-size:22px;line-height:1;display:grid;",
      "  place-items:center;cursor:pointer;-webkit-tap-highlight-color:transparent}",
      "#" + ID + " .gl-dem{pointer-events:none;color:#fff;font-size:14px;font-weight:600;",
      "  background:rgba(0,0,0,.42);border-radius:99px;padding:6px 13px;",
      "  font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;font-variant-numeric:tabular-nums}",
      "#" + ID + " .gl-nut{display:none}",
      /* Máy tính: thêm hai nút mũi tên. Trên điện thoại vuốt là đủ, hiện nút chỉ che ảnh. */
      "@media (min-width:860px) and (pointer:fine){",
      "#" + ID + " .gl-nut{display:grid;place-items:center;position:absolute;top:50%;z-index:3;",
      "  transform:translateY(-50%);width:44px;height:44px;border:0;border-radius:50%;",
      "  background:rgba(0,0,0,.42);color:#fff;font-size:24px;cursor:pointer}",
      "#" + ID + " .gl-truoc{left:16px}#" + ID + " .gl-sau{right:16px}}"
    ].join("");
    document.head.appendChild(s);
  }

  /* ---------- 2. Ảnh Drive: đổi sang bản to hơn khi xem toàn màn hình ---------- */
  function anhToHon(url) {
    if (url.indexOf("drive.google.com") === -1) return url;
    return url.replace(/([?&]sz=)w\d+/, "$1w1600");
  }
  function laVideo(url) { return /\.(mp4|mov|m4v|webm)(\?|$)/i.test(url); }

  /* ---------- 3. Dựng khung một lần rồi dùng lại ---------- */
  function taoKhung() {
    if (khung) return;
    chenCss();
    khung = document.createElement("div");
    khung.id = ID;
    khung.setAttribute("role", "dialog");
    khung.setAttribute("aria-modal", "true");
    khung.setAttribute("aria-label", "Xem ảnh căn hộ");
    khung.setAttribute("data-i18n-al", "g.open");
    khung.innerHTML =
        '<div class="gl-track"></div>'
      + '<div class="gl-top"><button class="gl-x" type="button" aria-label="Đóng" data-i18n-al="g.close">&times;</button>'
      + '<span class="gl-dem" aria-live="polite"></span></div>'
      + '<button class="gl-nut gl-truoc" type="button" aria-label="Ảnh trước" data-i18n-al="g.prev">&#8249;</button>'
      + '<button class="gl-nut gl-sau" type="button" aria-label="Ảnh sau" data-i18n-al="g.next">&#8250;</button>';
    document.body.appendChild(khung);
    nhoDich(khung);

    track = khung.querySelector(".gl-track");
    oDem = khung.querySelector(".gl-dem");

    khung.querySelector(".gl-x").addEventListener("click", nguoiDungDong);
    khung.querySelector(".gl-truoc").addEventListener("click", function () { nhay(viTri - 1); });
    khung.querySelector(".gl-sau").addEventListener("click", function () { nhay(viTri + 1); });

    /* Đang cuộn thì tính lại số thứ tự. Dùng hẹn giờ ngắn thay vì tính mỗi
       khung hình — cuộn trên điện thoại bắn ra rất nhiều sự kiện. */
    var hen = null;
    track.addEventListener("scroll", function () {
      clearTimeout(hen);
      hen = setTimeout(function () {
        var moi = Math.round(track.scrollLeft / track.clientWidth);
        if (moi !== viTri && moi >= 0 && moi < danhSach.length) {
          datLai(viTri);          // ảnh vừa rời đi: trả về tỉ lệ 1x
          viTri = moi;
          veDem();
          taiQuanh(viTri);
        }
      }, 90);
    }, { passive: true });

    document.addEventListener("keydown", function (e) {
      if (!dangMo) return;
      if (e.key === "Escape") { nguoiDungDong(); }
      else if (e.key === "ArrowRight") { nhay(viTri + 1); }
      else if (e.key === "ArrowLeft") { nhay(viTri - 1); }
    });

    ganCuChi();
  }

  function veDem() {
    oDem.textContent = (viTri + 1) + "/" + danhSach.length;
  }

  function nhay(i) {
    if (i < 0 || i >= danhSach.length) return;
    datLai(viTri);
    track.scrollTo({ left: i * track.clientWidth, behavior: "smooth" });
  }

  /* ---------- 4. Chỉ tải ảnh liền kề ---------- */
  function taiQuanh(i) {
    var cac = track.children;
    for (var k = Math.max(0, i - 1); k <= Math.min(cac.length - 1, i + 1); k++) {
      var m = cac[k].querySelector("img,video");
      if (m && m.dataset.src) { m.src = m.dataset.src; delete m.dataset.src; }
    }
  }

  /* ---------- 5. Phóng to, kéo ảnh ---------- */
  var scale = 1, tx = 0, ty = 0;
  var batDauKC = 0, batDauScale = 1, batDauX = 0, batDauY = 0, batDauTx = 0, batDauTy = 0;
  var soNgon = 0, lanChamCuoi = 0;

  function anhHienTai() {
    var s = track.children[viTri];
    return s ? s.querySelector("img") : null;
  }
  function apDung(img) {
    if (!img) return;
    img.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + scale + ")";
  }
  function datLai(i) {
    var s = track.children[i];
    if (!s) return;
    var img = s.querySelector("img");
    scale = 1; tx = 0; ty = 0;
    if (img) { img.style.transition = "transform .2s"; img.style.transform = ""; }
    s.classList.remove("phong");
  }
  /* Không cho kéo ảnh ra ngoài khung — kéo tự do sẽ để lại nền đen trống bên cạnh */
  function ghim(img) {
    if (!img) return;
    var gioiHanX = Math.max(0, (img.clientWidth * scale - track.clientWidth) / 2);
    var gioiHanY = Math.max(0, (img.clientHeight * scale - track.clientHeight) / 2);
    tx = Math.min(gioiHanX, Math.max(-gioiHanX, tx));
    ty = Math.min(gioiHanY, Math.max(-gioiHanY, ty));
  }
  function khoangCach(t) {
    var dx = t[0].clientX - t[1].clientX, dy = t[0].clientY - t[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function ganCuChi() {
    track.addEventListener("touchstart", function (e) {
      var s = track.children[viTri];
      var img = anhHienTai();
      if (!img) return;
      soNgon = e.touches.length;
      img.style.transition = "none";

      if (soNgon === 2) {
        // Hai ngón: chuyển sang chế độ tự xử lý, khoá vuốt ngang của trình duyệt
        s.classList.add("phong");
        batDauKC = khoangCach(e.touches);
        batDauScale = scale;
      } else if (soNgon === 1) {
        if (scale > 1) {
          batDauX = e.touches[0].clientX; batDauY = e.touches[0].clientY;
          batDauTx = tx; batDauTy = ty;
        } else {
          // Chạm hai lần nhanh: phóng thẳng lên 2,5x
          var gio = Date.now();
          if (gio - lanChamCuoi < 300) {
            s.classList.add("phong");
            img.style.transition = "transform .22s";
            scale = 2.5; tx = 0; ty = 0;
            apDung(img);
          }
          lanChamCuoi = gio;
        }
      }
    }, { passive: true });

    track.addEventListener("touchmove", function (e) {
      var img = anhHienTai();
      if (!img) return;
      if (e.touches.length === 2) {
        e.preventDefault();
        var tyLe = khoangCach(e.touches) / (batDauKC || 1);
        scale = Math.min(4, Math.max(1, batDauScale * tyLe));
        ghim(img); apDung(img);
      } else if (e.touches.length === 1 && scale > 1) {
        e.preventDefault();
        tx = batDauTx + (e.touches[0].clientX - batDauX);
        ty = batDauTy + (e.touches[0].clientY - batDauY);
        ghim(img); apDung(img);
      }
    }, { passive: false });

    track.addEventListener("touchend", function () {
      var s = track.children[viTri];
      var img = anhHienTai();
      if (!img || !s) return;
      if (scale <= 1.02) {
        // Về đúng 1x thì trả quyền vuốt ngang lại cho trình duyệt
        scale = 1; tx = 0; ty = 0;
        img.style.transition = "transform .2s";
        img.style.transform = "";
        s.classList.remove("phong");
      }
    }, { passive: true });

    // Máy tính: bấm vào ảnh để phóng / thu
    track.addEventListener("dblclick", function () {
      var s = track.children[viTri];
      var img = anhHienTai();
      if (!img || !s) return;
      img.style.transition = "transform .22s";
      if (scale > 1) { scale = 1; tx = 0; ty = 0; s.classList.remove("phong"); img.style.transform = ""; }
      else { scale = 2.5; tx = 0; ty = 0; s.classList.add("phong"); apDung(img); }
    });
  }

  /* ---------- 6. Mở / đóng ---------- */
  function mo(media, batDauTai) {
    if (!media || !media.length) return;
    taoKhung();
    danhSach = media.slice();
    viTri = Math.min(Math.max(0, batDauTai || 0), danhSach.length - 1);

    track.innerHTML = danhSach.map(function (url) {
      var to = anhToHon(url);
      return laVideo(url)
        ? '<div class="gl-slide"><video data-src="' + url + '" controls playsinline preload="none"></video></div>'
        : '<div class="gl-slide"><img data-src="' + to + '" alt=""></div>';
    }).join("");

    /* Khoá trang nền BẰNG CÁCH ghim đúng vị trí đang đứng. Chỉ dùng
       overflow:hidden thì Safari trên iPhone vẫn nhảy về đầu trang khi đóng. */
    doCuonCu = window.scrollY || document.documentElement.scrollTop || 0;
    document.body.style.position = "fixed";
    document.body.style.top = (-doCuonCu) + "px";
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";

    khung.classList.add("mo");
    dangMo = true;
    veDem();
    taiQuanh(viTri);
    // Nhảy tới đúng ảnh khách vừa bấm, không hiệu ứng trượt
    requestAnimationFrame(function () {
      track.scrollLeft = viTri * track.clientWidth;
    });

    /* Nút Back của máy = đóng gallery, không rời khỏi trang */
    try {
      history.pushState({ gallery: 1 }, "");
      daDayLichSu = true;
    } catch (e) { daDayLichSu = false; }

    khung.querySelector(".gl-x").focus();
  }

  function dong() {
    if (!dangMo) return;
    dangMo = false;
    khung.classList.remove("mo");
    track.innerHTML = "";

    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    window.scrollTo(0, doCuonCu);
  }

  /* Khách bấm ✕: lùi lịch sử một bước để trạng thái trình duyệt sạch sẽ,
     phần đóng thật do popstate lo. */
  function nguoiDungDong() {
    if (daDayLichSu) { daDayLichSu = false; history.back(); }
    else { dong(); }
  }

  window.addEventListener("popstate", function () {
    if (dangMo) { daDayLichSu = false; dong(); }
  });

  /* ---------- 7. Cửa dùng chung cho trang chủ và trang danh mục ---------- */
  window.MoGallery = mo;
})();
