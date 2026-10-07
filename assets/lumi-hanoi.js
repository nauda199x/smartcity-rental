
(function () {
  "use strict";

  var DATA_URL = "/data-lumi.json";
  var ZALO = "0977923284";
  var PAGE_DESKTOP = 24;
  var PAGE_NARROW = 12;
  var TYPES = ["1 Ngủ", "2 Ngủ", "3 Ngủ", "Duplex", "Penthouse", "Shop"];
  var TOWERS = ["S1", "S2", "S3", "S5", "S6", "P1", "P2", "E1", "E2"];
  var state = { apartments: [], type: "all", tower: "all", price: "all", interior: "all", query: "", sort: "price-asc", page: 1 };

  var PRICE_FILTERS = [
    { value: "all", label: "Tất cả mức giá", short: "Tất cả" },
    { value: "under10", label: "Dưới 10 triệu", short: "< 10tr" },
    { value: "10to12", label: "10 - 12 triệu", short: "10-12tr" },
    { value: "12to15", label: "12 - 15 triệu", short: "12-15tr" },
    { value: "15to20", label: "15 - 20 triệu", short: "15-20tr" },
    { value: "over20", label: "Trên 20 triệu", short: "> 20tr" }
  ];
  var INTERIORS = ["Nguyên bản", "Đồ cơ bản", "Full nội thất"];

  var $ = function (s) { return document.querySelector(s); };
  var text = function (v) { return String(v == null ? "" : v).trim(); };
  var key = function (v) { return text(v).toLowerCase(); };

  function T(k, vi, vars) {
    var out = vi;
    try {
      if (typeof window.NGON_NGU_T === "function") out = window.NGON_NGU_T(k, vi);
    } catch (e) {}
    vars = vars || {};
    Object.keys(vars).forEach(function (name) {
      out = String(out).replace(new RegExp("\\{" + name + "\\}", "g"), vars[name]);
    });
    return out;
  }

  function D(v) {
    try {
      if (typeof window.NGON_NGU_DU_LIEU === "function") return window.NGON_NGU_DU_LIEU(v);
    } catch (e) {}
    return v || "";
  }

  function dateLabel(v) {
    try {
      if (typeof window.NGON_NGU_NGAY === "function") return window.NGON_NGU_NGAY(v, v);
    } catch (e) {}
    return v || "";
  }

  function setDirectText(el, value) {
    if (!el) return;
    for (var i = 0; i < el.childNodes.length; i++) {
      if (el.childNodes[i].nodeType === 3 && el.childNodes[i].nodeValue.trim()) {
        el.childNodes[i].nodeValue = value;
        return;
      }
    }
    el.appendChild(document.createTextNode(value));
  }

  function priceFilterLabel(value) {
    var map = {
      all: ["f.priceAll", "Tất cả mức giá"],
      under10: ["lumi.price.under10", "Dưới 10 triệu"],
      "10to12": ["lumi.price.10to12", "10 - 12 triệu"],
      "12to15": ["lumi.price.12to15", "12 - 15 triệu"],
      "15to20": ["lumi.price.15to20", "15 - 20 triệu"],
      over20: ["lumi.price.over20", "Trên 20 triệu"]
    };
    var x = map[value] || ["", value];
    return x[0] ? T(x[0], x[1]) : x[1];
  }

  function assistantUnit(a) {
    var furn = a.interior;
    if (key(furn) === "nguyên bản") furn = "Nhà Nguyên Bản";
    if (key(furn) === "đồ cơ bản") furn = "Đồ Cơ bản";
    return {
      apartmentId: a.id || a.code,
      type: a.type,
      interior: furn,
      price: a.price,
      phanKhu: "Lumi Hanoi",
      tower: a.tower,
      area: a.area,
      availableDate: a.available,
      show: a.show
    };
  }

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
    if (readyNow(a)) return T("l.badgeNow", "Vào ngay");
    if (!s || /chưa xác nhận/i.test(s)) return T("lumi.contactMove", "Liên hệ ngày vào");
    return T("l.badgeFrom", "Trống từ {NGAY}", { NGAY: dateLabel(s) });
  }

  function formatPrice(v) {
    var p = money(v);
    if (!p) return T("l.contact", "Liên hệ");
    var m = p / 1000000;
    var vi = (Number.isInteger(m) ? String(m) : m.toFixed(1).replace(".", ",")) + " triệu";
    try {
      if (typeof window.NGON_NGU_GIA === "function") return window.NGON_NGU_GIA(p, vi);
    } catch (e) {}
    return vi;
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

  function countWith(group, value) {
    var old = state[group];
    state[group] = value;
    var n = state.apartments.filter(matches).length;
    state[group] = old;
    return n;
  }

  function chipHtml(label, shortLabel, count, group, value, selected) {
    var disabled = count === 0 && !selected ? " disabled" : "";
    return '<button class="chip ' + (selected ? 'active' : '') + '" type="button" data-lumi-filter="' + group +
      '" data-value="' + value + '"' + disabled + ' aria-label="' + label + ' - ' + count + ' căn">' +
      '<span class="chip-full">' + label + '</span><span class="chip-short">' + (shortLabel || label) +
      '</span> <small>' + count + '</small></button>';
  }

  function bindChipBox(selector) {
    var box = $(selector);
    if (!box) return;
    box.querySelectorAll("[data-lumi-filter]").forEach(function (button) {
      button.addEventListener("click", function () {
        state[button.dataset.lumiFilter] = button.dataset.value;
        state.page = 1;
        render();
      });
    });
  }

  function buildFilters() {
    var active = state.apartments.filter(function (a) { return a.show; });
    var typeRows = TYPES.map(function (t) {
      var n = active.filter(function (a) { return key(a.type) === key(t); }).length;
      return { value: key(t), label: D(t), full: D(t), raw: t, count: n };
    });
    var towerRows = TOWERS.map(function (t) {
      var n = active.filter(function (a) { return key(a.tower) === key(t); }).length;
      return { value: key(t), label: t, full: t, raw: t, count: n };
    });
    var furnRows = INTERIORS.map(function (t) {
      var n = active.filter(function (a) { return key(a.interior) === key(t); }).length;
      return { value: key(t), label: D(t), full: D(t), raw: t, count: n };
    });

    setOptions($("#lumiType"), typeRows.map(function (r) {
      return { value: r.value, label: r.label + " (" + r.count + ")" };
    }), T("f.allRooms", "Tất cả phòng") + " (" + active.length + ")");
    setOptions($("#lumiTower"), towerRows.map(function (r) {
      return { value: r.value, label: r.label + " (" + r.count + ")" };
    }), T("lumi.f.towerAll", "Tất cả tòa") + " (" + active.length + ")");
    setOptions($("#lumiInterior"), furnRows.map(function (r) {
      return { value: r.value, label: r.label + " (" + r.count + ")" };
    }), T("f.all", "Tất cả") + " (" + active.length + ")");

    var p = $("#lumiPrice");
    if (p) {
      p.innerHTML = PRICE_FILTERS.map(function (r) {
        var count = r.value === "all" ? active.length : countWith("price", r.value);
        return '<option value="' + r.value + '">' + priceFilterLabel(r.value) + (r.value === "all" ? " (" + count + ")" : "") + '</option>';
      }).join("");
      p.value = state.price;
    }

    var towerBox = $("#lumiTowerFilters");
    if (towerBox) {
      towerBox.innerHTML = chipHtml(T("lumi.f.towerAll", "Tất cả tòa"), T("f.all", "Tất cả"), countWith("tower", "all"), "tower", "all", state.tower === "all") +
        towerRows.map(function (r) {
          return chipHtml(r.full, r.label, countWith("tower", r.value), "tower", r.value, state.tower === r.value);
        }).join("");
    }

    var typeHtml = chipHtml(T("f.allRooms", "Tất cả phòng"), T("f.all", "Tất cả"), countWith("type", "all"), "type", "all", state.type === "all") +
      typeRows.map(function (r) {
        return chipHtml(r.full, r.label, countWith("type", r.value), "type", r.value, state.type === r.value);
      }).join("");
    if ($("#lumiTypeFilters")) $("#lumiTypeFilters").innerHTML = typeHtml;
    if ($("#lumiQuickTypeFilters")) $("#lumiQuickTypeFilters").innerHTML = typeHtml;

    var priceBox = $("#lumiPriceFilters");
    if (priceBox) {
      priceBox.innerHTML = PRICE_FILTERS.map(function (r) {
        var label = priceFilterLabel(r.value);
        return chipHtml(label, label, countWith("price", r.value), "price", r.value, state.price === r.value);
      }).join("");
    }

    var interiorBox = $("#lumiInteriorFilters");
    if (interiorBox) {
      interiorBox.innerHTML = chipHtml(T("f.all", "Tất cả"), T("f.all", "Tất cả"), countWith("interior", "all"), "interior", "all", state.interior === "all") +
        furnRows.map(function (r) {
          return chipHtml(r.full, r.label, countWith("interior", r.value), "interior", r.value, state.interior === r.value);
        }).join("");
    }

    bindChipBox("#lumiTowerFilters");
    bindChipBox("#lumiTypeFilters");
    bindChipBox("#lumiQuickTypeFilters");
    bindChipBox("#lumiPriceFilters");
    bindChipBox("#lumiInteriorFilters");

    var quick = $("#lumiQuickTypeFilters");
    if (quick) {
      if (state.type === "all") quick.scrollLeft = 0;
      else {
        var chosen = quick.querySelector(".chip.active");
        if (chosen) quick.scrollLeft = Math.max(0, chosen.offsetLeft - (quick.clientWidth - chosen.offsetWidth) / 2);
      }
    }
  }

  function activeFilterCount() {
    var n = 0;
    if (state.type !== "all") n++;
    if (state.tower !== "all") n++;
    if (state.price !== "all") n++;
    if (state.interior !== "all") n++;
    if (state.query) n++;
    return n;
  }

  function filterLabel(group, value) {
    if (group === "type") {
      var t = TYPES.find(function (x) { return key(x) === value; });
      return t ? D(t) : value;
    }
    if (group === "tower") return value.toUpperCase();
    if (group === "price") {
      var p = PRICE_FILTERS.find(function (x) { return x.value === value; });
      return p ? priceFilterLabel(p.value) : value;
    }
    if (group === "interior") {
      var i = INTERIORS.find(function (x) { return key(x) === value; });
      return i ? D(i) : value;
    }
    return value;
  }

  function renderFilterUi(total) {
    buildFilters();
    var count = activeFilterCount();
    var badge = $("#lumiFilterCount");
    if (badge) { badge.textContent = count; badge.hidden = count === 0; }
    var clearMobile = $("#lumiClearMobile");
    if (clearMobile) clearMobile.hidden = count === 0;
    var qb = $("#lumiQbFilter");
    if (qb) {
      qb.classList.toggle("dang-loc", count > 0);
      qb.dataset.count = String(count);
    }
    if ($("#lumiMatchCount")) $("#lumiMatchCount").textContent = total;

    var summary = $("#lumiFilterSummary");
    if (summary) summary.textContent = count
      ? count + " · " + T("lumi.viewN", "Xem {N} căn", { N: total })
      : T("f.tapHere", "Bấm để lọc nhanh căn phù hợp");

    var items = [];
    if (state.tower !== "all") items.push({ group: "tower", label: filterLabel("tower", state.tower) });
    if (state.type !== "all") items.push({ group: "type", label: filterLabel("type", state.type) });
    if (state.price !== "all") items.push({ group: "price", label: filterLabel("price", state.price) });
    if (state.interior !== "all") items.push({ group: "interior", label: filterLabel("interior", state.interior) });
    if (state.query) items.push({ group: "query", label: "“" + state.query + "”" });

    var strip = $("#lumiActiveFilterStrip");
    var chips = $("#lumiActiveFilterChips");
    if (strip && chips) {
      strip.hidden = items.length === 0;
      chips.innerHTML = items.map(function (item) {
        return '<button class="afs-chip" type="button" data-remove-lumi="' + item.group + '"><span>' +
          item.label + '</span><b aria-hidden="true">×</b></button>';
      }).join("");
      chips.querySelectorAll("[data-remove-lumi]").forEach(function (button) {
        button.addEventListener("click", function () {
          var group = button.dataset.removeLumi;
          if (group === "query") {
            state.query = "";
            if ($("#searchInput")) $("#searchInput").value = "";
          } else state[group] = "all";
          state.page = 1;
          render();
        });
      });
    }
  }

  function openFilters(group) {
    var sheet = $("#lumiFiltersSection"), backdrop = $("#lumiFiltersBackdrop");
    if (!sheet || !backdrop) return;
    sheet.classList.add("open");
    backdrop.classList.add("open");
    sheet.setAttribute("aria-hidden", "false");
    var toggle = $("#lumiMobileFilterToggle"), qb = $("#lumiQbFilter");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
    if (qb) qb.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
    if (group) {
      var section = sheet.querySelector('[data-lumi-section="' + group + '"]');
      if (section) window.setTimeout(function () { section.scrollIntoView({ block: "start" }); }, 30);
    }
  }

  function closeFilters() {
    var sheet = $("#lumiFiltersSection"), backdrop = $("#lumiFiltersBackdrop");
    if (!sheet || !backdrop) return;
    sheet.classList.remove("open");
    backdrop.classList.remove("open");
    sheet.setAttribute("aria-hidden", "true");
    var toggle = $("#lumiMobileFilterToggle"), qb = $("#lumiQbFilter");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
    if (qb) qb.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
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
    var typeLabel = D(a.type);
    var furnLabel = D(a.interior);
    var photoCount = Math.max(1, a.photos.length || 1);
    if (a.cover) {
      media = '<a class="media" href="' + href + '" aria-label="' + T("l.detail", "Xem chi tiết") + ' ' + a.code + '">' +
        '<span class="badge">' + availabilityLabel(a) + '</span>' +
        (a.interior ? '<span class="badge-nt' + furnitureClass(a.interior) + '">' + furnLabel + '</span>' : '') +
        '<span class="pcount">' + T("l.photos", "{N} ảnh", { N: photoCount }) + '</span>' +
        '<img src="' + a.cover + '" width="800" height="600" loading="lazy" decoding="async" alt="' +
        typeLabel + ' ' + a.tower + ' Lumi Hanoi">' +
        '</a>';
    } else {
      media = '<a class="media empty" href="' + href + '">' +
        '<span class="badge">' + availabilityLabel(a) + '</span>' +
        '<div class="lumi-no-photo"><strong>' + a.tower + ' · ' + a.code + '</strong><span>' +
        T("lumi.noPhoto", "Căn này chưa có ảnh thực tế") + '</span><span class="lumi-source">' +
        T("lumi.noPhotoCta", "Bấm để xem thông tin căn") + '</span></div>' +
        '</a>';
    }

    return '<article class="card" data-ma-noi-bo="' + a.id + '">' + media +
      '<div class="body">' +
      '<h3><a class="card-detail-title" href="' + href + '">' + typeLabel + (a.area ? ' · ' + a.area + ' m²' : '') + '</a></h3>' +
      '<div class="price">' + formatPrice(a.price) + '<small>' + T("l.perMonth", "/tháng") + '</small></div>' +
      '<span class="tower">' +
      '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><circle cx="12" cy="10" r="2.4" stroke="currentColor" stroke-width="2"/></svg>' +
      'Lumi Hanoi · ' + a.tower + '</span>' +
      '<div class="card-chips">' +
      (a.interior ? '<span class="cc-nt' + furnitureClass(a.interior) + '">' + furnLabel + '</span>' : '') +
      '<span class="cc-ma">' + a.code + '</span></div>' +
      '<div class="card-foot co-chi-tiet">' +
      '<a class="detail-card-link" href="' + href + '">' + T("l.detail", "Xem chi tiết") + '</a>' +
      '<a class="ask" href="https://zalo.me/' + ZALO + '" target="_blank" rel="noopener">' + T("nav.zalo", "Nhắn Zalo") + '</a>' +
      '</div><p class="ma-can">' + T("l.code", "Mã căn:") + ' <b>' + a.code + '</b></p></div></article>';
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
        '<div class="empty-state">' + T("lumi.empty", "Chưa có căn phù hợp với bộ lọc hiện tại. Anh/chị thử đổi mức giá, loại căn hoặc tòa.") + '</div>';
    }
    if ($("#lumiResultCount")) $("#lumiResultCount").innerHTML = T("lumi.result", "<strong>{N}</strong> căn hộ đang trống phù hợp", { N: filtered.length });
    if ($("#lumiFind")) $("#lumiFind").textContent = T("lumi.viewN", "Xem {N} căn", { N: filtered.length });
    renderFilterUi(filtered.length);
    renderPagination(filtered.length);
  }

  function applyStaticLanguage() {
    var search = $("#searchInput");
    if (search) {
      search.placeholder = T("lumi.search.ph", "Tìm tòa, mã tin, loại căn… (VD: S2, 2PN, 12 triệu)");
      search.setAttribute("aria-label", T("lumi.search.al", "Tìm căn hộ Lumi Hanoi"));
    }

    var brand = document.querySelector(".brand > span:last-child");
    if (brand) {
      setDirectText(brand, T("nav.brand", "Cho thuê chung cư Smart City"));
      var small = brand.querySelector("small");
      if (small) small.textContent = "Smart City · Lumi Hanoi";
    }

    var nav = document.querySelector(".topnav");
    if (nav && !nav.classList.contains("site-nav-v4")) {
      var links = nav.querySelectorAll("a");
      if (links[0]) links[0].textContent = T("lumi.nav.all", "Thuê căn hộ");
      if (links[1]) links[1].textContent = T("lumi.f.tower", "Tòa");
      if (links[2]) links[2].textContent = T("nav.type", "Loại căn");
      if (links[4]) links[4].textContent = T("nav.guideShort", "Cẩm nang");
    }
    var zalo = document.querySelector(".actions .pill-btn span");
    if (zalo) zalo.textContent = T("nav.zalo", "Nhắn Zalo");

    var eyebrow = document.querySelector(".project-switch__eyebrow");
    if (eyebrow) eyebrow.textContent = T("lumi.switch", "Chọn dự án · Chuyển nhanh giữa 2 quỹ căn");
    var heroTitle = document.querySelector(".hero-v4__chu h1");
    if (heroTitle) heroTitle.textContent = T("lumi.hero.h1", "Cho Thuê Căn Hộ Lumi Hanoi");
    var heroDesc = document.querySelector(".hero-v4__chu > p:not(.hero-dong-bo)");
    if (heroDesc) heroDesc.textContent = T("lumi.hero.p", "Bộ lọc thông minh — tìm nhanh theo tòa, giá thuê, loại căn hộ và tình trạng nội thất. Quỹ căn lấy trực tiếp từ bảng hàng Lumi và được cập nhật thường xuyên.");
    var heroSync = document.querySelector(".hero-dong-bo");
    if (heroSync) setDirectText(heroSync, T("hero.sync", "Quỹ căn đồng bộ lại mỗi 30 phút"));

    var stats = document.querySelectorAll(".stats .stat span");
    if (stats[0]) stats[0].textContent = T("hero.total", "Tổng căn");
    if (stats[1]) stats[1].textContent = T("hero.ready", "Ở ngay");
    if (stats[2]) stats[2].textContent = T("lumi.hero.tower", "Tòa");

    var labels = document.querySelectorAll(".filter-card .loc-pc-o > span");
    if (labels[0]) labels[0].textContent = T("f.type", "Loại căn");
    if (labels[1]) labels[1].textContent = T("lumi.f.tower", "Tòa");
    if (labels[2]) labels[2].textContent = T("f.price", "Khoảng giá");
    if (labels[3]) labels[3].textContent = T("f.furn", "Nội thất");
    if ($("#lumiClear")) $("#lumiClear").textContent = T("f.clear", "Xóa bộ lọc");

    var qts = document.querySelectorAll("#lumiQuickTiles .qt");
    if (qts[0]) {
      var b0=qts[0].querySelector("b"), s0=qts[0].querySelector("span:last-child");
      if(b0)b0.textContent=T("lumi.f.tower","Tòa"); if(s0)s0.textContent=T("lumi.f.towerPick","Chọn tòa Lumi");
    }
    if (qts[1]) {
      var b1=qts[1].querySelector("b"), s1=qts[1].querySelector("span:last-child");
      if(b1)b1.textContent=T("f.price","Khoảng giá"); if(s1)s1.textContent=T("f.pricePick","Chọn mức giá");
    }
    if (qts[2]) {
      var b2=qts[2].querySelector("b"), s2=qts[2].querySelector("span:last-child");
      if(b2)b2.textContent=T("f.furn","Nội thất"); if(s2)s2.textContent=T("f.furnPick","Chọn nội thất");
    }

    var mft = $("#lumiMobileFilterToggle");
    if (mft) {
      var mb=mft.querySelector(".mft-text b"), ms=mft.querySelector(".mft-text small"), mc=mft.querySelector(".mft-cta");
      if(mb)mb.textContent=T("f.panelAl","Bộ lọc căn hộ");
      if(ms && !activeFilterCount())ms.textContent=T("f.tapHere","Bấm để lọc nhanh căn phù hợp");
      if(mc)mc.textContent=T("f.filterNow","Lọc ngay");
    }
    var sheetHead=document.querySelector("#lumiFiltersSection .filters-sheet-head strong");
    if(sheetHead)sheetHead.textContent=T("f.panelAl","Bộ lọc căn hộ");
    var fl=document.querySelectorAll("#lumiFiltersSection .filter-label");
    if(fl[0])fl[0].textContent=T("lumi.f.tower","Tòa");
    if(fl[1])fl[1].textContent=T("f.bedStruct","Cấu trúc phòng ngủ");
    if(fl[2])fl[2].textContent=T("f.monthly","Khoảng giá thuê tháng");
    if(fl[3])fl[3].textContent=T("f.furn","Nội thất");
    if($("#lumiClearMobile"))$("#lumiClearMobile").textContent=T("f.clear","Xóa bộ lọc");
    var afs=document.querySelector(".afs-label"); if(afs)afs.textContent=T("l.filtering","Đang lọc:");
    if($("#lumiActiveFilterClear"))$("#lumiActiveFilterClear").textContent=T("f.clear","Xóa bộ lọc");

    var sort=$("#sortSelect");
    if(sort){
      var op=sort.options;
      if(op[0])op[0].textContent=T("l.priceAsc","Giá: Thấp đến Cao");
      if(op[1])op[1].textContent=T("l.priceDesc","Giá: Cao đến Thấp");
      if(op[2])op[2].textContent=T("l.onlyNew","Vừa cập nhật");
      sort.setAttribute("aria-label",T("l.sortAl","Sắp xếp căn hộ"));
    }

    var note=document.querySelector(".lumi-note");
    if(note){
      var nh=note.querySelector("h2"), np=note.querySelector("p");
      if(nh)nh.textContent=T("lumi.note.title","Quỹ căn cho thuê Lumi Hanoi");
      if(np)np.textContent=T("lumi.note.p","Dữ liệu trên trang được xuất từ bảng hàng làm việc và chỉ công khai các trường cần thiết cho người thuê: tòa, mã căn, loại căn, diện tích, giá, nội thất, thời gian vào ở và ảnh. Thông tin nội bộ của chủ nhà không được đưa lên website.");
    }
    var zfloat=document.querySelector(".zalo-noi"); if(zfloat)zfloat.textContent=T("nav.zalo","Nhắn Zalo");
  }

  function reset() {
    state.type = state.tower = state.price = state.interior = "all";
    state.query = ""; state.sort = "price-asc"; state.page = 1;
    ["#lumiType","#lumiTower","#lumiPrice","#lumiInterior"].forEach(function (selector) { if ($(selector)) $(selector).value = "all"; });
    if ($("#searchInput")) $("#searchInput").value = "";
    if ($("#sortSelect")) $("#sortSelect").value = "price-asc";
    render();
  }

  function bind() {
    [["#lumiType","type"],["#lumiTower","tower"],["#lumiPrice","price"],["#lumiInterior","interior"]].forEach(function (pair) {
      var el = $(pair[0]); if (!el) return;
      el.addEventListener("change", function () { state[pair[1]] = el.value; state.page = 1; render(); });
    });

    var search = $("#searchInput");
    if (search) search.addEventListener("input", function () { state.query = search.value.trim(); state.page = 1; render(); });

    var sort = $("#sortSelect");
    if (sort) sort.addEventListener("change", function () { state.sort = sort.value; state.page = 1; render(); });

    ["#lumiClear","#lumiClearMobile","#lumiActiveFilterClear"].forEach(function (selector) {
      var el = $(selector); if (el) el.addEventListener("click", reset);
    });

    if ($("#lumiFind")) $("#lumiFind").addEventListener("click", function () {
      var grid = $("#lumiListingGrid"); if (grid) window.scrollTo({ top: grid.offsetTop - 100, behavior: "smooth" });
    });

    if ($("#lumiMobileFilterToggle")) $("#lumiMobileFilterToggle").addEventListener("click", function () { openFilters(); });
    if ($("#lumiQbFilter")) $("#lumiQbFilter").addEventListener("click", function () { openFilters(); });
    if ($("#lumiCloseFilters")) $("#lumiCloseFilters").addEventListener("click", closeFilters);
    if ($("#lumiFiltersBackdrop")) $("#lumiFiltersBackdrop").addEventListener("click", closeFilters);
    if ($("#lumiApplyFilters")) $("#lumiApplyFilters").addEventListener("click", function () {
      closeFilters();
      var grid = $("#lumiListingGrid"); if (grid) window.scrollTo({ top: grid.offsetTop - 100, behavior: "smooth" });
    });

    document.querySelectorAll("[data-lumi-group]").forEach(function (button) {
      button.addEventListener("click", function () { openFilters(button.dataset.lumiGroup); });
    });

    if ($("#lumiQbSearch")) $("#lumiQbSearch").addEventListener("click", function () {
      var box = $("#searchInput");
      if (box) {
        window.scrollTo({ top: Math.max(0, box.getBoundingClientRect().top + window.scrollY - 80), behavior: "smooth" });
        window.setTimeout(function () { box.focus(); }, 250);
      }
    });

    document.addEventListener("keydown", function (event) { if (event.key === "Escape") closeFilters(); });

    var mq = window.matchMedia("(min-width:1081px)");
    var rerender = function () { state.page = 1; render(); };
    if (mq.addEventListener) mq.addEventListener("change", rerender); else if (mq.addListener) mq.addListener(rerender);

    document.addEventListener("ngonngu:doi", function () {
      state.page = 1;
      applyStaticLanguage();
      if (state.apartments.length) render();
    });
  }

  var dataSnapshot = "";
  var initialized = false;
  var refreshing = false;

  function refreshLumiData(force) {
    if (refreshing) return Promise.resolve(false);
    refreshing = true;

    var separator = DATA_URL.indexOf("?") === -1 ? "?" : "&";
    var freshUrl = DATA_URL + separator + "_=" + Date.now();

    return fetch(freshUrl, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (rows) {
      rows = Array.isArray(rows) ? rows : [];
      var nextSnapshot = JSON.stringify(rows);

      if (!force && initialized && nextSnapshot === dataSnapshot) return false;

      dataSnapshot = nextSnapshot;
      state.apartments = rows.map(toApartment);

      if (!initialized) {
        /* Deep-link từ trang chi tiết quay lại đúng tòa/loại căn. */
        try {
          var params = new URLSearchParams(location.search);
          var typeParam = params.get("type");
          var towerParam = params.get("tower");
          if (typeParam) {
            var matchedType = TYPES.find(function (t) { return slug(t) === slug(typeParam) || key(t) === key(typeParam); });
            if (matchedType) state.type = key(matchedType);
          }
          if (towerParam) {
            var matchedTower = TOWERS.find(function (t) { return key(t) === key(towerParam); });
            if (matchedTower) state.tower = key(matchedTower);
          }
        } catch (e) { /* query lỗi không được ảnh hưởng trang */ }

        bind();
        initialized = true;
      }

      buildFilters();
      renderStats();
      applyStaticLanguage();
      render();

      var assistantDetail = {
        project: "Lumi Hanoi",
        apartments: state.apartments.map(assistantUnit)
      };
      window.TROLY_V2_PENDING_DATA = assistantDetail;
      document.dispatchEvent(new CustomEvent("quy-can-san-sang", { detail: assistantDetail }));
      return true;
    }).catch(function () {
      if (!initialized) {
        var grid = $("#lumiListingGrid");
        if (grid) grid.innerHTML = '<div class="empty-state">' + T("l.loadErr", "Dữ liệu Lumi đang được đồng bộ. Vui lòng tải lại sau ít phút hoặc nhắn Zalo để nhận bảng hàng mới nhất.") + '</div>';
      }
      return false;
    }).finally(function () {
      refreshing = false;
    });
  }

  /* Lần đầu tải ngay; sau đó tự kiểm tra dữ liệu mới mỗi 2 phút.
     Khi người dùng quay lại tab hoặc mạng vừa online lại thì kiểm tra ngay,
     nên không cần F5 để thấy quỹ căn mới sau khi backend đồng bộ. */
  refreshLumiData(true);
  window.setInterval(function () { refreshLumiData(false); }, 120000);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) refreshLumiData(false);
  });
  window.addEventListener("online", function () { refreshLumiData(false); });
}());
