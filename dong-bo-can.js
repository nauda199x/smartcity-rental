/*!
 * dong-bo-can.js  v2 — Đồng bộ HAI CHIỀU cho 25 trang danh mục tĩnh
 * timthuesmartcity.com
 *
 * v1 chỉ ẩn căn đã thuê. v2 dựng lại toàn bộ lưới căn từ data.json:
 *   - Căn đã tắt "Hiển thị trên Web"  -> biến mất
 *   - Căn mới nhập vào Sheet          -> tự xuất hiện
 *   - Giá / diện tích / nội thất đổi  -> tự cập nhật theo dữ liệu mới
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
  var SDT = "0977923284";

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

  function anhBia(r) {
    var a = chuan(r["Ảnh đại diện"]);
    if (a) return a;
    var ds = chuan(r["Danh sách ảnh"]).split(/\s*\n\s*/);
    return ds[0] || "";
  }

  function homNay() {
    var d = new Date(), h = function (n) { return (n < 10 ? "0" : "") + n; };
    return h(d.getDate()) + "/" + h(d.getMonth() + 1) + "/" + d.getFullYear();
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
    var ngayHtml = vaoONgay(r)
      ? '<span class="ngay san">Có thể vào ở ngay</span>'
      : '<span class="ngay">Vào ở: ' + esc(r["Ngày vào ở"]) + "</span>";

    var meta = [];
    if (dt) meta.push(Math.round(dt) + "m²");
    if (noiThat) meta.push(noiThat);
    if (pk) meta.push(pk);

    var alt = "Cho thuê " + loai + " " + toa + " Vinhomes Smart City" + (dt ? " " + Math.round(dt) + "m2" : "");
    var khungAnh = anh
      ? '<div class="the-anh"><img src="' + esc(anh) + '" alt="' + esc(alt) + '" loading="lazy" ' +
        'decoding="async" width="400" height="300" ' +
        "onerror=\"this.closest('.the').classList.add('khong-anh');this.remove()\"></div>"
      : '<div class="the-anh"></div>';

    var el = document.createElement("article");
    el.className = anh ? "the" : "the khong-anh";
    el.setAttribute("data-ma-noi-bo", ma);
    el.innerHTML =
      khungAnh +
      '<div class="than">' +
        '<div class="gia">' + esc(dinhDangGia(soTien(r["Giá thuê"]))) + "<small>/tháng</small></div>" +
        '<h3 class="ten">' + esc(loai) + " · " + esc(toa) +
          ' <span class="ma">Mã ' + esc(ma) + "</span></h3>" +
        '<p class="meta">' + esc(meta.join(" · ")) + "</p>" +
        ngayHtml +
        '<div class="nut">' +
          '<a class="zalo" href="https://zalo.me/' + SDT + '" target="_blank" rel="noopener">Nhắn Zalo</a>' +
          '<a href="tel:' + SDT + '">Gọi</a>' +
        "</div>" +
      "</div>";
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
    fetch(NGUON, { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) chay(d, bl); })
      .catch(function () { /* giữ nguyên nội dung tĩnh */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", batDau);
  } else {
    batDau();
  }
})();
