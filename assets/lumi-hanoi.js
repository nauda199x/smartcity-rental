
(function () {
  "use strict";

  var DATA_URL = "/data-lumi.json";
  var ZALO = "0977923284";
  var PAGE_DESKTOP = 24;
  var PAGE_NARROW = 12;
  var TYPES = ["1 Ngủ", "2 Ngủ", "3 Ngủ", "Duplex", "Penthouse", "Shop"];
  var TOWERS = ["S1", "S2", "S3", "S5", "S6", "P1", "P2", "E1", "E2"];
  var state = { apartments: [], type: "all", tower: "all", price: "all", interior: "all", query: "", sort: "price-asc", page: 1 };

  var $ = function (s) { return document.querySelector(s); };
  var text = function (v) { return String(v == null ? "" : v).trim(); };
  var key = function (v) { return text(v).toLowerCase(); };

  function slug(v) {
    return text(v).normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase()
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  function detailSlug(a) {
    return "cho-thue-can-ho-" + slug(a.type) + "-" + slug(a.tower) + "-" +
      Math.round(a.area || 0) + "m2-" + slug(a.code);
  }

  function money(v) {
    if (typeof v === "number") return v;
    return Number(text(v).replace(/[^\d]/g, "") || 0);
  }

  function area(v) {
    if (typeof v === "number") return v;
    return Number(text(v).replace(",", ".").replace(/[^\d.]/g, "") || 0);
  }

  function links(v) {
    return text(v).split(/\r?\n|,|;/).map(function (x) { return x.trim(); }).filter(Boolean);
  }

  function driveImage(url) {
    var u = text(url);
    if (!u) return "";
    var m = u.match(/[?&]id=([A-Za-z0-9_-]+)/) || u.match(/\/file\/d\/([A-Za-z0-9_-]+)/);
    return m ? "https://drive.google.com/thumbnail?id=" + m[1] + "&sz=w1000" : u;
  }

  function parseDate(s) {
    var m = text(s).match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
    if (!m) return null;
    var d = new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]));
    return isNaN(d.getTime()) ? null : d;
  }

  function readyNow(a) {
    var s = text(a.available);
    if (!s) return true;
    if (/^(vào luôn|vào ngay|ở ngay|ngay)$/i.test(s)) return true;
    if (/chưa xác nhận/i.test(s)) return false;
    var d = parseDate(s);
    if (!d) return false;
    d.setHours(0, 0, 0, 0);
    var today = new Date(); today.setHours(0, 0, 0, 0);
    return d <= today;
  }

  function availabilityLabel(a) {
    var s = text(a.available);
    if (readyNow(a)) return "Vào ngay";
    if (!s || /chưa xác nhận/i.test(s)) return "Liên hệ ngày vào";
    return "Trống từ " + s;
  }

  function formatPrice(v) {
    var p = money(v);
    if (!p) return "Liên hệ";
    var m = p / 1000000;
    return (Number.isInteger(m) ? String(m) : m.toFixed(1).replace(".", ",")) + " triệu";
  }

  function furnitureClass(v) {
    return key(v) === "full nội thất" ? "" : " thuong";
  }

  function toApartment(r) {
    var photos = links(r["Danh sách ảnh"]).map(driveImage);
    var cover = driveImage(r["Ảnh đại diện"]) || photos[0] || "";
    return {
      id: text(r["Mã nội bộ"]),
      code: text(r["Mã căn"]) || text(r["Mã nội bộ"]).replace(/^LH\./, ""),
      tower: text(r["Tòa"]),
      type: text(r["Loại"]),
      area: area(r["Diện tích"]),
      interior: text(r["Nội thất"]),
      price: money(r["Giá thuê"]),
      direction: text(r["Hướng ban công"]),
      available: text(r["Ngày vào ở"]),
      updated: text(r["Ngày cập nhật"]),
      added: text(r["Ngày thêm vào hệ thống"]),
      show: key(r["Hiển thị trên Web"]) === "có",
      cover: cover,
      photos: photos
    };
  }

  function pageSize() {
    return window.matchMedia("(min-width:1081px)").matches ? PAGE_DESKTOP : PAGE_NARROW;
  }

  function priceTest(a) {
    var p = a.price;
    if (state.price === "all") return true;
    if (state.price === "under10") return p > 0 && p < 10000000;
    if (state.price === "10to12") return p >= 10000000 && p <= 12000000;
    if (state.price === "12to15") return p > 12000000 && p <= 15000000;
    if (state.price === "15to20") return p > 15000000 && p <= 20000000;
    if (state.price === "over20") return p > 20000000;
    return true;
  }

  function matches(a) {
    if (!a.show) return false;
    if (state.type !== "all" && key(a.type) !== state.type) return false;
    if (state.tower !== "all" && key(a.tower) !== state.tower) return false;
    if (state.interior !== "all" && key(a.interior) !== state.interior) return false;
    if (!priceTest(a)) return false;
    var q = slug(state.query).replace(/-/g, " ");
    if (q) {
      var blob = slug([a.code, a.tower, a.type, a.area, a.interior, formatPrice(a.price)].join(" ")).replace(/-/g, " ");
      var parts = q.split(/\s+/).filter(Boolean);
      if (!parts.every(function (p) { return blob.indexOf(p) !== -1; })) return false;
    }
    return true;
  }

  function sortList(list) {
    var out = list.slice();
    if (state.sort === "price-desc") out.sort(function (a, b) { return b.price - a.price; });
    else if (state.sort === "newest") out.sort(function (a, b) {
      var ad = parseDate(a.updated || a.added), bd = parseDate(b.updated || b.added);
      return (bd ? bd.getTime() : 0) - (ad ? ad.getTime() : 0);
    });
    else out.sort(function (a, b) { return a.price - b.price; });

    var withPhoto = [], withoutPhoto = [];
    out.forEach(function (a) { (a.cover ? withPhoto : withoutPhoto).push(a); });
    return withPhoto.concat(withoutPhoto);
  }

  function setOptions(select, rows, firstLabel) {
    if (!select) return;
    var current = select.value || "all";
    select.innerHTML = '<option value="all">' + firstLabel + '</option>' + rows.map(function (r) {
      return '<option value="' + r.value + '">' + r.label + '</option>';
    }).join("");
    select.value = Array.from(select.options).some(function (o) { return o.value === current; }) ? current : "all";
  }

  function buildFilters() {
    var active = state.apartments.filter(function (a) { return a.show; });
    var typeRows = TYPES.map(function (t) {
      var n = active.filter(function (a) { return key(a.type) === key(t); }).length;
      return { value: key(t), label: t.replace(" Ngủ", "PN") + " (" + n + ")" };
    });
    var towerRows = TOWERS.map(function (t) {
      var n = active.filter(function (a) { return key(a.tower) === key(t); }).length;
      return { value: key(t), label: t + " (" + n + ")" };
    });
    var furn = ["Nguyên bản", "Đồ cơ bản", "Full nội thất"].map(function (t) {
      var n = active.filter(function (a) { return key(a.interior) === key(t); }).length;
      return { value: key(t), label: t + " (" + n + ")" };
    });
    setOptions($("#lumiType"), typeRows, "Tất cả phòng (" + active.length + ")");
    setOptions($("#lumiTower"), towerRows, "Tất cả tòa (" + active.length + ")");
    setOptions($("#lumiInterior"), furn, "Tất cả (" + active.length + ")");

    var p = $("#lumiPrice");
    if (p) {
      p.innerHTML =
        '<option value="all">Tất cả mức giá (' + active.length + ')</option>' +
        '<option value="under10">Dưới 10 triệu</option>' +
        '<option value="10to12">10 - 12 triệu</option>' +
        '<option value="12to15">12 - 15 triệu</option>' +
        '<option value="15to20">15 - 20 triệu</option>' +
        '<option value="over20">Trên 20 triệu</option>';
      p.value = state.price;
    }
  }

  function renderStats() {
    var active = state.apartments.filter(function (a) { return a.show; });
    var ready = active.filter(readyNow).length;
    var towers = new Set(active.map(function (a) { return a.tower; }).filter(Boolean)).size;
    if ($("#lumiTotalCount")) $("#lumiTotalCount").textContent = active.length;
    if ($("#lumiReadyCount")) $("#lumiReadyCount").textContent = ready;
    if ($("#lumiTowerCount")) $("#lumiTowerCount").textContent = towers;
  }

  function card(a) {
    var href = "/lumi-hanoi/can-ho/" + detailSlug(a) + "/";
    var media;
    if (a.cover) {
      media = '<a class="media" href="' + href + '" aria-label="Xem chi tiết căn ' + a.code + '">' +
        '<span class="badge">' + availabilityLabel(a) + '</span>' +
        (a.interior ? '<span class="badge-nt' + furnitureClass(a.interior) + '">' + a.interior + '</span>' : '') +
        '<span class="pcount">' + Math.max(1, a.photos.length || 1) + ' ảnh</span>' +
        '<img src="' + a.cover + '" width="800" height="600" loading="lazy" decoding="async" alt="Căn hộ ' + a.type + ' tòa ' + a.tower + ' Lumi Hanoi">' +
        '</a>';
    } else {
      media = '<a class="media empty" href="' + href + '">' +
        '<span class="badge">' + availabilityLabel(a) + '</span>' +
        '<div class="lumi-no-photo"><strong>' + a.tower + ' · ' + a.code + '</strong><span>Căn này chưa có ảnh thực tế</span><span class="lumi-source">Bấm để xem thông tin căn</span></div>' +
        '</a>';
    }

    return '<article class="card" data-ma-noi-bo="' + a.id + '">' + media +
      '<div class="body">' +
      '<h3><a class="card-detail-title" href="' + href + '">' + a.type + (a.area ? ' · ' + a.area + ' m²' : '') + '</a></h3>' +
      '<div class="price">' + formatPrice(a.price) + '<small>/tháng</small></div>' +
      '<span class="tower">' +
      '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="10" r="2.4" stroke="currentColor" stroke-width="2"/></svg>' +
      'Lumi Hanoi · ' + a.tower + '</span>' +
      '<div class="card-chips">' +
      (a.interior ? '<span class="cc-nt' + furnitureClass(a.interior) + '">' + a.interior + '</span>' : '') +
      '<span class="cc-ma">' + a.code + '</span></div>' +
      '<div class="card-foot co-chi-tiet">' +
      '<a class="detail-card-link" href="' + href + '">Xem chi tiết</a>' +
      '<a class="ask" href="https://zalo.me/' + ZALO + '" target="_blank" rel="noopener">Nhắn Zalo</a>' +
      '</div><p class="ma-can">Mã căn: <b>' + a.code + '</b></p></div></article>';
  }

  function renderPagination(total) {
    var box = $("#lumiPagination");
    if (!box) return;
    var pages = Math.max(1, Math.ceil(total / pageSize()));
    if (state.page > pages) state.page = pages;
    if (pages <= 1) { box.innerHTML = ""; return; }
    var cur = state.page;
    var picks = [1, pages, cur - 1, cur, cur + 1].filter(function (p, i, arr) {
      return p >= 1 && p <= pages && arr.indexOf(p) === i;
    }).sort(function (a, b) { return a - b; });
    var html = '<button class="page-btn" type="button" data-page="' + (cur - 1) + '"' + (cur === 1 ? ' disabled' : '') + '>‹</button>';
    var prev = 0;
    picks.forEach(function (p) {
      if (prev && p - prev > 1) html += '<span class="page-ellipsis">…</span>';
      html += '<button class="page-btn ' + (p === cur ? 'active' : '') + '" type="button" data-page="' + p + '">' + p + '</button>';
      prev = p;
    });
    html += '<button class="page-btn" type="button" data-page="' + (cur + 1) + '"' + (cur === pages ? ' disabled' : '') + '>›</button>';
    box.innerHTML = html;
    box.querySelectorAll("[data-page]").forEach(function (b) {
      b.addEventListener("click", function () {
        if (b.disabled) return;
        state.page = Number(b.dataset.page);
        render();
        var grid = $("#lumiListingGrid");
        if (grid) window.scrollTo({ top: grid.offsetTop - 100, behavior: "smooth" });
      });
    });
  }

  function render() {
    var filtered = sortList(state.apartments.filter(matches));
    var start = (state.page - 1) * pageSize();
    var shown = filtered.slice(start, start + pageSize());
    var grid = $("#lumiListingGrid");
    if (grid) {
      grid.className = shown.length ? "grid" : "";
      grid.innerHTML = shown.length ? shown.map(card).join("") :
        '<div class="empty-state">Chưa có căn phù hợp với bộ lọc hiện tại. Anh/chị thử đổi mức giá, loại căn hoặc tòa.</div>';
    }
    if ($("#lumiResultCount")) $("#lumiResultCount").innerHTML = '<strong>' + filtered.length + '</strong> căn hộ đang trống phù hợp';
    if ($("#lumiFind")) $("#lumiFind").textContent = "Xem " + filtered.length + " căn";
    renderPagination(filtered.length);
  }

  function reset() {
    state.type = state.tower = state.price = state.interior = "all";
    state.query = ""; state.sort = "price-asc"; state.page = 1;
    ["#lumiType","#lumiTower","#lumiPrice","#lumiInterior"].forEach(function (s) { if ($(s)) $(s).value = "all"; });
    if ($("#searchInput")) $("#searchInput").value = "";
    if ($("#lumiSort")) $("#lumiSort").value = "price-asc";
    render();
  }

  function bind() {
    [["#lumiType","type"],["#lumiTower","tower"],["#lumiPrice","price"],["#lumiInterior","interior"]].forEach(function (pair) {
      var el = $(pair[0]); if (!el) return;
      el.addEventListener("change", function () { state[pair[1]] = el.value; state.page = 1; render(); });
    });
    var search = $("#searchInput");
    if (search) search.addEventListener("input", function () { state.query = search.value.trim(); state.page = 1; render(); });
    var sort = $("#lumiSort");
    if (sort) sort.addEventListener("change", function () { state.sort = sort.value; state.page = 1; render(); });
    if ($("#lumiClear")) $("#lumiClear").addEventListener("click", reset);
    if ($("#lumiFind")) $("#lumiFind").addEventListener("click", function () {
      var grid = $("#lumiListingGrid"); if (grid) window.scrollTo({ top: grid.offsetTop - 100, behavior: "smooth" });
    });
    var mq = window.matchMedia("(min-width:1081px)");
    var rerender = function () { state.page = 1; render(); };
    if (mq.addEventListener) mq.addEventListener("change", rerender); else if (mq.addListener) mq.addListener(rerender);
  }

  fetch(DATA_URL, { cache: "no-cache" }).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }).then(function (rows) {
    state.apartments = (Array.isArray(rows) ? rows : []).map(toApartment);
    buildFilters();
    renderStats();
    bind();
    render();
  }).catch(function () {
    var grid = $("#lumiListingGrid");
    if (grid) grid.innerHTML = '<div class="empty-state">Dữ liệu Lumi đang được đồng bộ. Vui lòng tải lại sau ít phút hoặc nhắn Zalo để nhận bảng hàng mới nhất.</div>';
  });
}());
