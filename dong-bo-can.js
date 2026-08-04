/*!
 * dong-bo-can.js  v3 — Đồng bộ HAI CHIỀU cho 25 trang danh mục tĩnh
 * timthuesmartcity.com
 *
 * v1 chỉ ẩn căn đã thuê. v2 dựng lại toàn bộ lưới căn từ data.json:
 *   - Căn đã tắt "Hiển thị trên Web"  -> biến mất
 *   - Căn mới nhập vào Sheet          -> tự xuất hiện
 *   - Giá / diện tích / nội thất đổi  -> tự cập nhật theo dữ liệu mới
 * v3 thêm album ảnh: thẻ căn hộ nào có ảnh trong "Danh sách ảnh" thì bấm
 *   được để xem toàn bộ ảnh, giống hệt trang chủ. Trước đây trang danh mục
 *   chỉ hiện 1 ảnh bìa và không bấm được gì.
 *
 * AN TOÀN: nếu tải data.json thất bại hoặc trang không khai báo bộ lọc
 * -> KHÔNG đụng gì vào trang, giữ nguyên 100% nội dung tĩnh.
 *
 * Mỗi trang khai báo điều kiện lọc riêng trong thẻ:
 *   <script type="application/json" id="bo-loc-trang">{...}</script>
 * Các khóa hỗ trợ: loai, phanKhu, noiThat, giaTren (lớn hơn), giaMax (nhỏ hơn hoặc bằng)
 */
(function () {
  "use strict";

  var NGUON = "/data.json";
  var NGUON_ANH = "/anh-can-ho/anh-map.json";
  var SDT = "0977923284";

  /* Bảng tra ảnh đã di dời về repo: drive_id -> đường dẫn ảnh trong repo.
     Nạp một lần lúc script khởi động. Nếu nạp lỗi thì để rỗng — site vẫn chạy
     bình thường với ảnh Drive như trước. */
  var anhTrongRepo = {};

  /* Luôn resolve, kể cả khi file không tồn tại hoặc hỏng: lưới căn phải được
     dựng trong mọi trường hợp. */
  function napBanDoAnh() {
    return fetch(NGUON_ANH, { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && typeof d === "object") anhTrongRepo = d; })
      .catch(function () { /* giữ nguyên map rỗng -> dùng ảnh Drive */ });
  }

  function chuan(v) { return String(v == null ? "" : v).trim(); }
  function khoa(v) { return chuan(v).toLowerCase(); }
  function esc(v) {
    return chuan(v).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function laCanHopLe(r) {
    var v = khoa(r["Hiển thị trên Web"] || r["Hiển thị trên web"] || r["Hiển thị"]);
    return v === "có" || v === "co" || v === "yes" || v === "true";
  }

  function soTien(v) {
    if (typeof v === "number") return v;
    return Number(chuan(v).replace(/[^\d]/g, "") || 0);
  }

  function dienTich(v) {
    if (typeof v === "number") return v;
    return parseFloat(chuan(v).replace(",", ".").replace(/[^\d.]/g, "")) || 0;
  }

  function dinhDangGia(p) {
    if (!p) return "Liên hệ";
    if (p % 1000000 === 0) return (p / 1000000) + " triệu";
    return String(Math.round(p / 100000) / 10).replace(".", ",") + " triệu";
  }

  /* ---------- Tách & chuẩn hoá link ảnh/video (giống hệt logic trang chủ) ---------- */
  function splitLinks(v) {
    if (Array.isArray(v)) {
      var raMang = [];
      for (var j = 0; j < v.length; j++) if (v[j]) raMang.push(v[j]);
      return raMang;
    }
    var s = chuan(v);
    if (!s) return [];
    var mieng = s.split(/[\n,;]+/);
    var ra = [];
    for (var i = 0; i < mieng.length; i++) {
      var p = String(mieng[i]).trim();
      if (p) ra.push(p);
    }
    return ra;
  }

  /* Ảnh trên Google Drive không xem trực tiếp được -> đổi sang dạng thumbnail xem được.
     Mọi nơi cần link ảnh PHẢI đi qua hàm này, không được ghép cứng tên miền Drive,
     để sau này chuyển ảnh về host riêng chỉ cần sửa một chỗ.
     Ảnh nào đã di dời về repo (có trong anh-map.json) thì trả về đường dẫn repo —
     Drive chặn crawler nên ảnh host ở đó không bao giờ được Google Images index. */
  function driveUrlToViewUrl(v) {
    var text = chuan(v);
    if (!text) return "";
    var m = text.match(/\/file\/d\/([^/]+)/) || text.match(/[?&]id=([^&]+)/);
    if (m) {
      var trongRepo = anhTrongRepo[m[1]];
      if (trongRepo) return trongRepo;
      return "https://drive.google.com/thumbnail?id=" + m[1] + "&sz=w1000";
    }
    return text;
  }

  function laVideo(url) {
    return /\.(mp4|mov|m4v|webm)(\?|$)/i.test(chuan(url));
  }

  /* Ghép "Ảnh đại diện" + "Danh sách ảnh" thành một danh sách không trùng lặp,
     tách riêng "Video". Đây là toàn bộ media của một căn hộ dùng cho album. */
  function danhSachMedia(r) {
    var daThay = {};
    var anh = [];
    function themAnh(u) {
      var v = driveUrlToViewUrl(u);
      if (!v || daThay[v]) return;
      daThay[v] = true;
      anh.push(v);
    }
    themAnh(r["Ảnh đại diện"]);
    var dsAnhTho = splitLinks(r["Danh sách ảnh"]);
    for (var i = 0; i < dsAnhTho.length; i++) themAnh(dsAnhTho[i]);

    var video = [];
    var dsVideoTho = splitLinks(r["Video"]);
    for (var k = 0; k < dsVideoTho.length; k++) {
      var vv = driveUrlToViewUrl(dsVideoTho[k]);
      if (vv) video.push(vv);
    }
    return { anh: anh, video: video };
  }

  /* Ánh xạ mã tòa -> tên phân khu (giống hệt trang chủ, tiền tố dài đứng trước) */
  function tenPhanKhu(toa) {
    var t = chuan(toa).toUpperCase().replace(/[\s.\-_]/g, "");
    if (!t) return "";
    if (t.indexOf("MAS") === 0 || t.indexOf("WEST") === 0) return "Masteri";
    if (t.indexOf("SA") === 0) return "Sakura";
    if (t.indexOf("GS") === 0) return "Miami";
    if (t.indexOf("TC") === 0) return "Canopy";
    if (t.indexOf("TK") === 0) return "Tonkin";
    if (/^I\d/.test(t)) return "Imperia";
    if (/^A\d/.test(t)) return "Lumiere";
    if (/^V\d/.test(t)) return "Victoria";
    if (/^S\d/.test(t)) return "Sapphire";
    if (/^G\d/.test(t)) return "Sola Park";
    return "";
  }

  function laNgayDaQua(s) {
    var m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(chuan(s));
    if (!m) return false;
    var d = new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
    var nay = new Date(); nay.setHours(0, 0, 0, 0);
    return d <= nay;
  }

  function vaoONgay(r) {
    var s = chuan(r["Ngày vào ở"]);
    if (!s) return true;
    if (["luôn", "ở ngay", "o ngay", "ngay"].indexOf(khoa(s)) !== -1) return true;
    return laNgayDaQua(s);
  }

  /* Căn vừa được nhập trong 72 tiếng - giống hệt ngưỡng "Mới" của trang chủ */
  function laCanMoi(r) {
    var s = chuan(r["Ngày thêm vào hệ thống"]);
    if (!s) return false;
    var moc = NaN;
    if (/^\d{4}-\d{2}-\d{2}/.test(s)) {
      moc = Date.parse(s);
    } else {
      var m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})/.exec(s);
      if (m) moc = new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1])).getTime();
    }
    return !isNaN(moc) && (Date.now() - moc) < 72 * 60 * 60 * 1000;
  }

  /* Rút ngày còn ngày/tháng - năm là thông tin thừa trong khuôn khổ một thẻ */
  function ngayNganGon(s) {
    var m = /^(\d{1,2})\/(\d{1,2})/.exec(chuan(s));
    return m ? m[1] + "/" + m[2] : chuan(s);
  }

  /* Chữ trên huy hiệu tình trạng. Mỗi thẻ chỉ hiện ĐÚNG MỘT huy hiệu: căn vừa
     về ưu tiên nhãn "Mới", còn lại hiện tình trạng trống. Luôn kèm nhãn -
     con số ngày đứng trần rất dễ bị hiểu nhầm. */
  function nhanTinhTrang(r) {
    if (laCanMoi(r)) return "✨ Mới";
    if (vaoONgay(r)) return "Vào ngay";
    return "Trống từ " + ngayNganGon(r["Ngày vào ở"]);
  }

  /* Giá trị trong data.json là URL Drive thô, phải đi qua driveUrlToViewUrl thì
     ảnh bìa mới được áp bảng tra ảnh repo (và mới xem trực tiếp được). */
  function anhBia(r) {
    var a = chuan(r["Ảnh đại diện"]);
    if (!a) {
      var ds = chuan(r["Danh sách ảnh"]).split(/\s*\n\s*/);
      a = ds[0] || "";
    }
    return driveUrlToViewUrl(a);
  }

  function homNay() {
    var d = new Date(), h = function (n) { return (n < 10 ? "0" : "") + n; };
    return h(d.getDate()) + "/" + h(d.getMonth() + 1) + "/" + d.getFullYear();
  }

  /* =====================================================================
   * ALBUM ẢNH (lightbox) — toàn bộ CSS + HTML do script này tự tạo ra,
   * tiền tố "dbc-" để không đụng độ với CSS sẵn có của 25 trang tĩnh.
   * ===================================================================== */

  var dbcTrang = {
    media: [],       // danh sách url ảnh/video của căn đang xem
    chiSo: 0,        // ảnh đang xem, 0-based
    dangMo: false,
    cuonTruoc: "",   // overflow cũ của <body>, để khôi phục khi đóng
    phanTuTruoc: null // phần tử đang có focus trước khi mở album, để trả focus lại
  };

  var dbcDom = null; // cache tham chiếu DOM sau khi dựng lần đầu

  function dbcChenCss() {
    if (document.getElementById("dbc-style")) return;
    var css =
      /* Dáng của .dbc-xem-duoc, .dbc-huy-hieu, .the-anh và hiệu ứng phóng ảnh
         khi rê chuột đã chuyển hẳn sang /assets/v3.css. Để lại ở đây thì khối
         style chèn lúc chạy sẽ đè lên file dùng chung và thẻ căn trên trang
         danh mục lệch khỏi thẻ căn trang chủ. Chỉ giữ phần album ảnh. */
      ".dbc-huy-hieu{pointer-events:none}" +
      ".dbc-nen{position:fixed;inset:0;z-index:9999;background:rgba(15,23,42,.92);" +
        "display:none;align-items:center;justify-content:center;padding:0}" +
      ".dbc-nen.dbc-mo{display:flex}" +
      ".dbc-hop{width:100%;height:100%;max-width:960px;max-height:100vh;display:flex;" +
        "flex-direction:column;background:transparent}" +
      "@media(min-width:760px){.dbc-hop{height:92vh;margin:4vh auto}}" +
      ".dbc-dau{display:flex;align-items:center;gap:10px;padding:12px 14px;color:#fff;" +
        "font-family:inherit}" +
      ".dbc-dem{font-size:13px;font-weight:700;background:rgba(255,255,255,.15);" +
        "border-radius:999px;padding:3px 10px;flex:0 0 auto}" +
      ".dbc-ten{flex:1;font-size:14px;font-weight:600;overflow:hidden;text-overflow:ellipsis;" +
        "white-space:nowrap}" +
      ".dbc-dong{flex:0 0 auto;width:44px;height:44px;border:0;background:rgba(255,255,255,.12);" +
        "color:#fff;border-radius:999px;font-size:22px;line-height:1;cursor:pointer}" +
      ".dbc-dong:hover{background:rgba(255,255,255,.24)}" +
      ".dbc-than{position:relative;flex:1;display:flex;align-items:center;justify-content:center;" +
        "min-height:0;touch-action:pan-y}" +
      ".dbc-khung-anh{width:100%;height:100%;display:flex;align-items:center;justify-content:center;" +
        "min-height:0}" +
      ".dbc-media{max-width:100%;max-height:100%;-o-object-fit:contain;object-fit:contain;display:block}" +
      ".dbc-loi{color:#e5e7eb;background:#1f2937;border-radius:8px;padding:26px 20px;" +
        "font-size:14px;text-align:center}" +
      ".dbc-truoc,.dbc-sau{position:absolute;top:50%;margin-top:-22px;width:44px;height:44px;" +
        "border:0;border-radius:999px;background:rgba(255,255,255,.14);color:#fff;font-size:22px;" +
        "cursor:pointer;z-index:2}" +
      ".dbc-truoc{left:8px}.dbc-sau{right:8px}" +
      ".dbc-truoc:hover,.dbc-sau:hover{background:rgba(255,255,255,.28)}" +
      "@media(max-width:539px){.dbc-truoc,.dbc-sau{display:none}}" +
      ".dbc-chan{padding:14px;text-align:center}" +
      ".dbc-zalo{display:inline-flex;align-items:center;justify-content:center;height:44px;" +
        "padding:0 22px;border-radius:999px;background:#2563eb;color:#fff;font-weight:700;" +
        "font-size:14.5px;text-decoration:none}" +
      ".dbc-zalo:hover{background:#1e3a8a}";
    var st = document.createElement("style");
    st.id = "dbc-style";
    st.appendChild(document.createTextNode(css));
    document.head.appendChild(st);
  }

  function dbcTaoKhung() {
    if (dbcDom) return dbcDom;
    dbcChenCss();

    var nen = document.createElement("div");
    nen.className = "dbc-nen";

    var hop = document.createElement("div");
    hop.className = "dbc-hop";
    hop.setAttribute("role", "dialog");
    hop.setAttribute("aria-modal", "true");

    var dau = document.createElement("div");
    dau.className = "dbc-dau";
    var dem = document.createElement("span");
    dem.className = "dbc-dem";
    var ten = document.createElement("span");
    ten.className = "dbc-ten";
    var dong = document.createElement("button");
    dong.type = "button";
    dong.className = "dbc-dong";
    dong.setAttribute("aria-label", "Đóng album ảnh");
    dong.innerHTML = "&times;";
    dau.appendChild(dem);
    dau.appendChild(ten);
    dau.appendChild(dong);

    var than = document.createElement("div");
    than.className = "dbc-than";
    var truoc = document.createElement("button");
    truoc.type = "button";
    truoc.className = "dbc-truoc";
    truoc.setAttribute("aria-label", "Ảnh trước");
    truoc.innerHTML = "&lsaquo;";
    var khungAnh = document.createElement("div");
    khungAnh.className = "dbc-khung-anh";
    var sau = document.createElement("button");
    sau.type = "button";
    sau.className = "dbc-sau";
    sau.setAttribute("aria-label", "Ảnh sau");
    sau.innerHTML = "&rsaquo;";
    than.appendChild(truoc);
    than.appendChild(khungAnh);
    than.appendChild(sau);

    var chan = document.createElement("div");
    chan.className = "dbc-chan";
    var zalo = document.createElement("a");
    zalo.className = "dbc-zalo";
    zalo.href = "https://zalo.me/" + SDT;
    zalo.target = "_blank";
    zalo.rel = "noopener";
    zalo.textContent = "Nhắn Zalo về căn này";
    chan.appendChild(zalo);

    hop.appendChild(dau);
    hop.appendChild(than);
    hop.appendChild(chan);
    nen.appendChild(hop);
    document.body.appendChild(nen);

    dong.addEventListener("click", dbcDong);
    truoc.addEventListener("click", function () { dbcHien(dbcTrang.chiSo - 1); });
    sau.addEventListener("click", function () { dbcHien(dbcTrang.chiSo + 1); });
    nen.addEventListener("click", function (ev) {
      if (ev.target === nen) dbcDong();
    });

    /* Vuốt trái/phải trên điện thoại để chuyển ảnh */
    var chamX = 0, chamY = 0;
    than.addEventListener("touchstart", function (ev) {
      if (!ev.touches || !ev.touches.length) return;
      chamX = ev.touches[0].clientX;
      chamY = ev.touches[0].clientY;
    }, { passive: true });
    than.addEventListener("touchend", function (ev) {
      if (!ev.changedTouches || !ev.changedTouches.length) return;
      var dx = ev.changedTouches[0].clientX - chamX;
      var dy = ev.changedTouches[0].clientY - chamY;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
        if (dx < 0) dbcHien(dbcTrang.chiSo + 1); else dbcHien(dbcTrang.chiSo - 1);
      }
    }, { passive: true });

    document.addEventListener("keydown", function (ev) {
      if (!dbcTrang.dangMo) return;
      var phim = ev.key;
      if (phim === "Escape" || phim === "Esc") { dbcDong(); }
      else if (phim === "ArrowLeft") { dbcHien(dbcTrang.chiSo - 1); }
      else if (phim === "ArrowRight") { dbcHien(dbcTrang.chiSo + 1); }
    });

    dbcDom = { nen: nen, dem: dem, ten: ten, khungAnh: khungAnh };
    return dbcDom;
  }

  /* Chỉ tải ảnh đang xem + 1 ảnh kế tiếp, không tải cả album cùng lúc */
  function dbcTaiTruoc(url) {
    if (!url || laVideo(url)) return;
    var im = new Image();
    im.src = url;
  }

  function dbcHien(chiSoMoi) {
    var tong = dbcTrang.media.length;
    if (!tong) return;
    var i = ((chiSoMoi % tong) + tong) % tong; // vòng tròn, kể cả số âm
    dbcTrang.chiSo = i;
    var url = dbcTrang.media[i];
    var d = dbcDom;

    d.khungAnh.innerHTML = "";
    if (laVideo(url)) {
      var v = document.createElement("video");
      v.className = "dbc-media";
      v.src = url;
      v.controls = true;
      v.setAttribute("playsinline", "");
      d.khungAnh.appendChild(v);
    } else {
      var img = document.createElement("img");
      img.className = "dbc-media";
      img.alt = dbcTrang.tieuDe || "Ảnh căn hộ";
      img.onerror = function () {
        d.khungAnh.innerHTML = '<div class="dbc-loi">Ảnh không tải được</div>';
      };
      img.src = url;
      d.khungAnh.appendChild(img);
    }

    dbcTaiTruoc(dbcTrang.media[(i + 1) % tong]);
    d.dem.textContent = (i + 1) + " / " + tong;
  }

  function dbcMo(media, tieuDe, gia, chiSoBatDau) {
    if (!media || !media.length) return;
    /* Gallery toàn màn hình dùng chung (assets/gallery.js). Khung xem ảnh cũ
       của riêng trang danh mục giữ nguyên bên dưới làm phương án dự phòng. */
    if (typeof window.MoGallery === "function") {
      window.MoGallery(media, chiSoBatDau || 0);
      return;
    }
    var d = dbcTaoKhung();
    dbcTrang.media = media;
    dbcTrang.tieuDe = tieuDe;
    dbcTrang.dangMo = true;
    dbcTrang.phanTuTruoc = document.activeElement;
    dbcTrang.cuonTruoc = document.body.style.overflow;

    d.ten.textContent = gia ? (tieuDe + " — " + gia + "/tháng") : tieuDe;
    dbcHien(chiSoBatDau || 0);

    d.nen.className = "dbc-nen dbc-mo";
    document.body.style.overflow = "hidden";
  }

  function dbcDong() {
    if (!dbcTrang.dangMo || !dbcDom) return;
    dbcTrang.dangMo = false;
    dbcDom.nen.className = "dbc-nen";
    document.body.style.overflow = dbcTrang.cuonTruoc || "";
    if (dbcTrang.phanTuTruoc && typeof dbcTrang.phanTuTruoc.focus === "function") {
      dbcTrang.phanTuTruoc.focus();
    }
  }

  /* ---------- Dựng thẻ căn hộ, đúng markup sẵn có của trang tĩnh ---------- */
  function dungThe(r) {
    var ma = chuan(r["Mã nội bộ"]);
    var toa = chuan(r["Tòa"]);
    var loai = chuan(r["Loại"]);
    var dt = dienTich(r["Diện tích"]);
    var noiThat = chuan(r["Nội thất"]);
    var pk = tenPhanKhu(toa);
    var anh = anhBia(r);
    var huyHieuTinhTrang = '<span class="tinh-trang">' + esc(nhanTinhTrang(r)) + "</span>";

    /* Thứ tự thông tin theo đúng cái khách thuê cân nhắc: loại căn + diện tích
       nổi nhất, mã tòa hạ xuống dòng phụ đi kèm phân khu. */
    var tenHtml = esc(loai) + (dt ? " · " + Math.round(dt) + " m²" : "");
    var viTri = pk ? pk + " · " + toa : toa;

    var media = danhSachMedia(r);
    var toanBoMedia = media.anh.concat(media.video);
    var soMedia = toanBoMedia.length;

    var alt = "Cho thuê " + loai + " " + toa + " Vinhomes Smart City" + (dt ? " " + Math.round(dt) + "m2" : "");

    /* Giao diện v3: nhãn nội thất là huy hiệu nằm trên ảnh, ngay dưới huy hiệu
       tình trạng. Chỉ "Full nội thất" được tô xanh dương — căn cơ bản hay
       nguyên bản dùng màu trung tính để huy hiệu không hứa quá thực tế. */
    var huyHieuNoiThat = noiThat
      ? '<span class="badge-nt' + (khoa(noiThat) === "full nội thất" ? "" : " thuong") + '">' +
        esc(noiThat) + "</span>"
      : "";

    var khungAnh;
    if (anh) {
      /* Số ảnh: icon do CSS vẽ bằng mask, nên chuỗi chỉ còn con số + chữ "ảnh". */
      var huyHieu = soMedia > 0
        ? '<span class="dbc-huy-hieu">' + soMedia + ' ảnh</span>'
        : "";
      khungAnh = '<div class="the-anh"><img src="' + esc(anh) + '" alt="' + esc(alt) + '" loading="lazy" ' +
        'decoding="async" width="400" height="300" ' +
        "onerror=\"this.closest('.the').classList.add('khong-anh');" +
        "var b=this.parentNode.querySelector('.dbc-huy-hieu');if(b)b.parentNode.removeChild(b);" +
        "this.remove()\">" + huyHieu + huyHieuTinhTrang + huyHieuNoiThat + "</div>";
    } else {
      khungAnh = '<div class="the-anh">' + huyHieuTinhTrang + huyHieuNoiThat + "</div>";
    }

    var el = document.createElement("article");
    el.className = anh ? "the" : "the khong-anh";
    el.setAttribute("data-ma-noi-bo", ma);
    el.innerHTML =
      khungAnh +
      '<div class="than">' +
        '<h3 class="ten">' + tenHtml + "</h3>" +
        '<p class="vi-tri">' + esc(viTri) + "</p>" +
        '<div class="card-chips">' +
          (noiThat
            ? '<span class="cc-nt' + (khoa(noiThat) === "full nội thất" ? "" : " thuong") + '">' + esc(noiThat) + "</span>"
            : "") +
          (ma ? '<span class="cc-ma">' + esc(ma) + "</span>" : "") +
        "</div>" +
        '<div class="chan-the">' +
          '<div class="gia">' + esc(dinhDangGia(soTien(r["Giá thuê"]))) + "<small>/tháng</small></div>" +
          '<a class="zalo" href="https://zalo.me/' + SDT + '" target="_blank" rel="noopener">Nhắn Zalo</a>' +
        "</div>" +
        /* Căn chưa có mã nội bộ thì ẩn hẳn dòng này, không hiện nhãn rỗng. */
        (ma ? '<p class="ma-can">Mã căn: <b>' + esc(ma) + "</b></p>" : "") +
      "</div>";

    /* Thẻ bấm được để mở album — chỉ khi có ít nhất 1 ảnh/video.
       Bỏ qua khi bấm vào nút Zalo để nút đó vẫn hoạt động bình thường. */
    if (soMedia > 0) {
      el.classList.add("dbc-xem-duoc");
      el.setAttribute("tabindex", "0");
      el.setAttribute("role", "button");
      el.setAttribute("aria-label", "Xem " + soMedia + " ảnh căn " + loai + " " + toa);

      var giaHienThi = dinhDangGia(soTien(r["Giá thuê"]));
      var tieuDeAlbum = (loai + " · " + toa);
      el.addEventListener("click", function (ev) {
        if (ev.target.closest("a")) return;
        dbcMo(toanBoMedia, tieuDeAlbum, giaHienThi, 0);
      });
      el.addEventListener("keydown", function (ev) {
        if (ev.target.closest("a")) return;
        if (ev.key === "Enter" || ev.key === " " || ev.key === "Spacebar") {
          ev.preventDefault();
          dbcMo(toanBoMedia, tieuDeAlbum, giaHienThi, 0);
        }
      });
    }

    return el;
  }

  /* ---------- Bộ lọc riêng của từng trang ---------- */
  function docBoLoc() {
    var el = document.getElementById("bo-loc-trang");
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  function khopBoLoc(r, bl) {
    if (bl.loai && khoa(r["Loại"]) !== khoa(bl.loai)) return false;
    if (bl.phanKhu && khoa(tenPhanKhu(r["Tòa"])) !== khoa(bl.phanKhu)) return false;
    if (bl.noiThat && khoa(r["Nội thất"]) !== khoa(bl.noiThat)) return false;
    var g = soTien(r["Giá thuê"]);
    if (bl.giaTren && !(g > bl.giaTren)) return false;
    if (bl.giaMax && !(g > 0 && g <= bl.giaMax)) return false;
    return true;
  }

  function capNhatO(nhan, giaTri) {
    var ds = document.querySelectorAll(".sl .o");
    for (var i = 0; i < ds.length; i++) {
      var s = ds[i].querySelector("span"), b = ds[i].querySelector("b");
      if (s && b && s.textContent.indexOf(nhan) !== -1) { b.textContent = giaTri; return; }
    }
  }

  /* ---------- Chạy ---------- */
  function chay(duLieu, bl) {
    var luoi = document.querySelector(".luoi");
    if (!luoi || !duLieu || !duLieu.length) return;

    /* Chèn CSS ngay khi biết chắc sẽ dựng lưới - không chờ tới lúc khách mở
       album mới chèn, vì huy hiệu số ảnh và hiệu ứng hover cần CSS này ngay
       khi thẻ xuất hiện lần đầu. */
    dbcChenCss();

    var dsCan = [];
    for (var i = 0; i < duLieu.length; i++) {
      if (laCanHopLe(duLieu[i]) && chuan(duLieu[i]["Mã nội bộ"]) && khopBoLoc(duLieu[i], bl)) {
        dsCan.push(duLieu[i]);
      }
    }

    /* An toàn: dữ liệu về rỗng bất thường thì không phá trang tĩnh */
    var soCu = luoi.querySelectorAll("article.the").length;
    if (dsCan.length === 0 && soCu > 0) return;

    dsCan.sort(function (a, b) { return soTien(a["Giá thuê"]) - soTien(b["Giá thuê"]); });

    /* Căn có ảnh xếp trước (vẫn theo giá tăng dần), căn chưa có ảnh dồn xuống cuối,
       để khách không gặp ô "Đang cập nhật ảnh" xen giữa danh sách. */
    var coAnh = [], khongAnh = [];
    for (var n = 0; n < dsCan.length; n++) {
      if (anhBia(dsCan[n])) coAnh.push(dsCan[n]); else khongAnh.push(dsCan[n]);
    }
    dsCan = coAnh.concat(khongAnh);

    var moi = document.createDocumentFragment();
    for (var j = 0; j < dsCan.length; j++) moi.appendChild(dungThe(dsCan[j]));
    luoi.innerHTML = "";
    luoi.appendChild(moi);

    /* Thống kê */
    var soCan = dsCan.length, giaMin = 0, dtMin = 0, dtMax = 0, pk = {};
    for (var k = 0; k < dsCan.length; k++) {
      var g = soTien(dsCan[k]["Giá thuê"]);
      if (g > 0 && (giaMin === 0 || g < giaMin)) giaMin = g;
      var dt = dienTich(dsCan[k]["Diện tích"]);
      if (dt > 0) {
        if (dtMin === 0 || dt < dtMin) dtMin = dt;
        if (dt > dtMax) dtMax = dt;
      }
      var t = tenPhanKhu(dsCan[k]["Tòa"]); if (t) pk[t] = 1;
    }
    var soPk = 0; for (var x in pk) if (pk.hasOwnProperty(x)) soPk++;
    var chuoiDt = dtMin > 0 ? (dtMin === dtMax ? Math.round(dtMin) + "m²"
      : Math.round(dtMin) + "–" + Math.round(dtMax) + "m²") : "";

    capNhatO("căn đang trống", String(soCan));
    if (giaMin > 0) capNhatO("giá thấp nhất", dinhDangGia(giaMin));
    if (chuoiDt) capNhatO("diện tích", chuoiDt);
    if (soPk > 0) capNhatO("phân khu", String(soPk));

    var h2 = document.querySelector(".tieu-de-luoi");
    if (h2) h2.textContent = "Danh sách " + soCan + " căn đang cho thuê";

    var tt = document.querySelector(".tt");
    if (tt) {
      var s = tt.textContent;
      s = s.replace(/Danh sách\s+\d+\s+căn/, "Danh sách " + soCan + " căn");
      if (chuoiDt) s = s.replace(/diện tích\s*[\d.,]+\s*[–-]\s*[\d.,]+\s*m²/i, "diện tích " + chuoiDt);
      s = s.replace(/cập nhật\s*\d{1,2}\/\d{1,2}\/\d{4}/i, "cập nhật " + homNay());
      s = s.replace(/Cập nhật\s*\d{1,2}\/\d{1,2}\/\d{4}/, "Cập nhật " + homNay());
      tt.textContent = s;
    }

    if (soCan === 0) {
      luoi.innerHTML =
        '<p style="padding:22px;border:1px solid #e2e8f0;border-radius:12px;background:#f8fafc;line-height:1.7;margin:0">' +
        "Nhóm căn này vừa được thuê hết. Kho căn hộ cập nhật liên tục mỗi ngày — " +
        '<a href="/" style="color:#1d4ed8;font-weight:600">xem toàn bộ căn còn trống tại đây</a>' +
        " hoặc nhắn Zalo <b>" + SDT + "</b> để được báo ngay khi có căn phù hợp.</p>";
    }
  }

  function batDau() {
    var bl = docBoLoc();
    if (!bl || !window.fetch) return;
    /* Nạp bảng tra ảnh trước rồi mới dựng lưới, để thẻ căn hộ không kịp hiện
       ảnh Drive rồi mới đổi sang ảnh repo. Nạp lỗi cũng vẫn đi tiếp. */
    napBanDoAnh().then(function () {
      return fetch(NGUON, { cache: "no-cache" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { if (d) chay(d, bl); });
    }).catch(function () { /* giữ nguyên nội dung tĩnh */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", batDau);
  } else {
    batDau();
  }
})();
