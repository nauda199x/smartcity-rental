/*!
 * can-ho-detail-i18n.js — VI / EN / KO cho trang chi tiết căn hộ.
 * Dùng chung state localStorage và nút .doi-tieng của assets/ngon-ngu.js.
 * Không đổi title/meta/canonical/schema; chỉ đổi chữ hiển thị.
 */
(function () {
  "use strict";

  var DU_LIEU = null;

  var TU = {
    "brand": ["Smart City Apartments for Rent", "스마트시티 아파트 임대"],
    "brandSub": ["Real photos · Updated daily", "실사진 · 매일 업데이트"],
    "nav.all": ["All listings", "전체 매물"],
    "nav.studio": ["Studio", "스튜디오"],
    "nav.1p": ["1BR+", "침실 1개+"],
    "nav.2": ["2BR", "침실 2개"],
    "nav.3": ["3BR", "침실 3개"],
    "nav.guide": ["Renting guide", "임대 가이드"],
    "bc.home": ["Home", "홈"],
    "title.active": ["Apartment for rent: {TYPE}, {AREA}, Tower {TOWER} — Vinhomes Smart City",
                     "빈홈즈 스마트시티 임대: {TYPE}, {AREA}, {TOWER}동"],
    "title.rented": ["{TYPE} apartment, {AREA}, Tower {TOWER} — already rented",
                     "{TYPE} · {AREA} · {TOWER}동 — 임대 완료"],
    "lead.active": ["{TYPE} apartment, {AREA}, Tower {TOWER}, {ZONE}, Vinhomes Smart City. {FURN}. Rent {PRICE}. Updated {DATE}.",
                    "빈홈즈 스마트시티 {ZONE} {TOWER}동 {TYPE}, {AREA}. {FURN}. 월 임대료 {PRICE}. 업데이트 {DATE}."],
    "rented.note1": ["This apartment has already been rented.", "이 매물은 임대가 완료되었습니다."],
    "rented.note2": ["Here are similar apartments that are still available.", "현재 임대 가능한 비슷한 매물을 확인해 보세요."],
    "table.code": ["Unit code", "매물 번호"],
    "table.type": ["Apartment type", "타입"],
    "table.area": ["Area", "면적"],
    "table.tower": ["Tower", "동"],
    "table.zone": ["Zone", "구역"],
    "table.furn": ["Furnishing", "옵션"],
    "table.price": ["Monthly rent", "월 임대료"],
    "table.move": ["Move-in", "입주 가능일"],
    "table.updated": ["Updated", "업데이트"],
    "stat.area": ["area", "면적"],
    "stat.price": ["monthly rent", "월 임대료"],
    "stat.furn": ["furnishing", "옵션"],
    "stat.status": ["availability", "입주 가능"],
    "status.now": ["Available now", "즉시 입주"],
    "status.from": ["Available from {DATE}", "{DATE}부터 입주 가능"],
    "status.liveNow": ["Available for immediate move-in", "즉시 입주 가능"],
    "price.contact": ["Contact for price", "가격 문의"],
    "aside.price": ["Monthly rent", "월 임대료"],
    "aside.type": ["Apartment type", "타입"],
    "aside.area": ["Area", "면적"],
    "aside.tower": ["Tower", "동"],
    "aside.furn": ["Furnishing", "옵션"],
    "action.book": ["Book a viewing", "방문 예약"],
    "action.zalo": ["Chat on Zalo", "잘로 상담"],
    "action.call": ["Call 0977 923 284", "전화 0977 923 284"],
    "action.callShort": ["Call", "전화"],
    "action.bookShort": ["Book viewing", "방문 예약"],
    "aside.code": ["Unit code: {CODE}", "매물 번호: {CODE}"],
    "aside.note": ["Listing details are synced from the active inventory shown on this website.",
                   "이 매물 정보는 웹사이트에 표시되는 실시간 매물 목록에서 동기화됩니다."],
    "gallery.all": ["View all {N} photos", "사진 {N}장 모두 보기"],
    "gallery.count": ["{I}/{N} photos", "{I}/{N} 사진"],
    "gallery.open": ["Open photo {I} of {N}", "사진 {I}/{N} 열기"],
    "gallery.none1": ["Photos are being updated", "사진 업데이트 중"],
    "gallery.none2": ["Message us on Zalo for real photos and video.", "실사진과 영상은 잘로로 문의해 주세요."],
    "toast": ["Viewing message copied — open Zalo and paste it to send quickly.",
              "방문 예약 문구를 복사했습니다. 잘로에서 붙여넣어 보내세요."],
    "h.more": ["Browse by your needs", "조건별 더 보기"],
    "h.similar": ["Similar apartments", "비슷한 매물"],
    "h.availableSimilar": ["Similar apartments still available", "현재 임대 가능한 비슷한 매물"],
    "empty.similar": ["No similar apartment is available right now. View all apartments for rent.",
                      "현재 비슷한 공실이 없습니다. 전체 임대 매물을 확인해 주세요."],
    "cta.ask": ["Ask about unit {CODE} on Zalo", "매물 {CODE} 잘로 문의"],
    "cta.call": ["Call {PHONE}", "전화 {PHONE}"],
    "mobile.available": ["View available apartments", "공실 매물 보기"],
    "footer.find": ["Find an apartment", "매물 찾기"],
    "footer.guide": ["Renting guide", "임대 가이드"],
    "footer.owner": ["List your apartment", "매물 등록"],
    "footer.privacy": ["Privacy policy", "개인정보 처리방침"],
    "zalo.float": ["Chat on Zalo", "잘로 상담"]
  };

  function q(s, r) { return (r || document).querySelector(s); }
  function qa(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  function laTrang() {
    return /^\/can-ho\/[^/]+\/?$/.test(location.pathname.replace(/index\.html$/, ""));
  }

  function ma() {
    try {
      return typeof window.NGON_NGU_MA === "function" ? window.NGON_NGU_MA() : "vi";
    } catch (e) { return "vi"; }
  }

  function thay(mau, bien) {
    return String(mau).replace(/\{([A-Z]+)\}/g, function (_, k) {
      return bien && bien[k] !== undefined ? bien[k] : "";
    });
  }

  function T(k, vi, bien) {
    var m = ma();
    if (m === "vi") return thay(vi, bien);
    var muc = TU[k];
    if (!muc) return thay(vi, bien);
    return thay(m === "en" ? muc[0] : muc[1], bien);
  }
  window.CT_DETAIL_T = T;

  function nutChu(el) {
    if (!el) return null;
    for (var i = 0; i < el.childNodes.length; i++) {
      var n = el.childNodes[i];
      if (n.nodeType === 3 && n.nodeValue.trim()) return n;
    }
    return null;
  }

  function datChuTrucTiep(el, chu) {
    var n = nutChu(el);
    if (n) n.nodeValue = chu;
    else if (el) el.textContent = chu;
  }

  function docBang() {
    if (DU_LIEU) return DU_LIEU;
    var bang = q("table.bang");
    if (!bang) return null;
    var ra = { rows: [] };
    qa("tr", bang).forEach(function (tr) {
      var td = qa("td", tr);
      if (td.length < 2) return;
      var k = td[0].textContent.trim();
      var v = td[1].textContent.trim();
      ra[k] = v;
      ra.rows.push({ key: k, value: v, tr: tr });
    });
    DU_LIEU = ra;
    return ra;
  }

  function enumDich(v) {
    try {
      if (typeof window.NGON_NGU_DU_LIEU === "function") return window.NGON_NGU_DU_LIEU(v);
    } catch (e) {}
    return v || "";
  }

  function ngayDich(v) {
    if (!v) return "";
    if (/vào ngay|o ngay|luôn|ngay/i.test(v)) return T("status.now", "Vào ngay");
    try {
      if (typeof window.NGON_NGU_NGAY === "function") return window.NGON_NGU_NGAY(v, v);
    } catch (e) {}
    return v;
  }

  function giaVnd(v) {
    var m = String(v || "").match(/([\d.,]+)\s*triệu/i);
    if (!m) return 0;
    var n = parseFloat(m[1].replace(/\./g, "").replace(",", "."));
    return isFinite(n) ? Math.round(n * 1000000) : 0;
  }

  function giaDich(v) {
    if (ma() === "vi") return v || "Liên hệ";
    var so = giaVnd(v);
    if (!so) return T("price.contact", "Liên hệ");
    var goc = String(v || "").replace(/\s*\/\s*tháng/i, "");
    var base = goc;
    try {
      if (typeof window.NGON_NGU_GIA === "function") base = window.NGON_NGU_GIA(so, goc);
    } catch (e) {}
    return base + (ma() === "en" ? "/month" : "/월");
  }

  function tinhTrang(raw) {
    if (!raw || /vào ngay|o ngay|luôn|ngay/i.test(raw)) return T("status.now", "Vào ngay");
    return T("status.from", "Trống từ {DATE}", { DATE: ngayDich(raw) });
  }

  var NHAN_BANG = {
    "Mã căn": "table.code",
    "Loại": "table.type",
    "Diện tích": "table.area",
    "Tòa": "table.tower",
    "Phân khu": "table.zone",
    "Nội thất": "table.furn",
    "Giá thuê": "table.price",
    "Ngày vào ở": "table.move",
    "Ngày cập nhật": "table.updated"
  };

  function giaTriBang(k, v) {
    if (k === "Loại" || k === "Nội thất") return enumDich(v);
    if (k === "Giá thuê") return giaDich(v);
    if (k === "Ngày vào ở" || k === "Ngày cập nhật") return ngayDich(v);
    return v;
  }

  function capNhatHeader() {
    var hieu = q(".top .hieu");
    if (hieu) {
      datChuTrucTiep(hieu, T("brand", "Cho thuê chung cư Smart City"));
      var small = q("small", hieu);
      if (small) small.textContent = T("brandSub", "Ảnh thật · Cập nhật mỗi ngày");
    }
    var nav = q(".top nav");
    if (nav) {
      var map = {
        "/": ["nav.all", "Tất cả căn"],
        "/studio/": ["nav.studio", "Studio"],
        "/1pn-plus/": ["nav.1p", "1 ngủ +"],
        "/2pn/": ["nav.2", "2 ngủ"],
        "/3pn/": ["nav.3", "3 ngủ"],
        "/cam-nang-thue-nha.html": ["nav.guide", "Cẩm nang"]
      };
      qa("a", nav).forEach(function (a) {
        var x = map[a.getAttribute("href")];
        if (x) a.textContent = T(x[0], x[1]);
      });
    }
  }

  function capNhatBang(d) {
    d.rows.forEach(function (r) {
      var td = qa("td", r.tr);
      if (td.length < 2) return;
      var k = NHAN_BANG[r.key];
      if (k) td[0].textContent = T(k, r.key);
      td[1].textContent = giaTriBang(r.key, r.value);
    });
  }

  function capNhatNoiDung(d) {
    var rented = document.body.classList.contains("trang-chi-tiet-da-thue");
    var type = enumDich(d["Loại"] || "");
    var area = d["Diện tích"] || "";
    var tower = d["Tòa"] || "";
    var zone = d["Phân khu"] || tower;
    var furn = enumDich(d["Nội thất"] || "");
    var price = giaDich(d["Giá thuê"] || "");
    var updated = ngayDich(d["Ngày cập nhật"] || "");
    var h1 = q("main.khung h1");
    var title = rented
      ? T("title.rented", "", { TYPE:type, AREA:area, TOWER:tower })
      : T("title.active", "", { TYPE:type, AREA:area, TOWER:tower });
    if (h1 && !h1.dataset.ctVi) h1.dataset.ctVi = h1.textContent;
    if (h1) h1.textContent = ma() === "vi" ? h1.dataset.ctVi : title;

    var bc = q(".bc");
    if (bc) {
      var home = q("a:first-child", bc);
      if (home) home.textContent = T("bc.home", "Trang chủ");
      var cur = q("span", bc);
      if (cur && h1) cur.textContent = h1.textContent;
    }

    if (!rented) {
      var p = q("main.khung > .tt");
      if (p) {
        if (!p.dataset.ctVi) p.dataset.ctVi = p.textContent;
        p.textContent = ma() === "vi" ? p.dataset.ctVi : T("lead.active", "", {
          TYPE:type, AREA:area, TOWER:tower, ZONE:zone, FURN:furn, PRICE:price, DATE:updated
        });
      }
      var stats = qa(".sl .o");
      var labs = [
        ["stat.area", "diện tích"], ["stat.price", "giá thuê/tháng"],
        ["stat.furn", "nội thất"], ["stat.status", "tình trạng"]
      ];
      stats.forEach(function (o, i) {
        var s = q("span", o);
        if (s && labs[i]) s.textContent = T(labs[i][0], labs[i][1]);
      });
      if (stats[1]) { var b1=q("b",stats[1]); if(b1) b1.textContent=price; }
      if (stats[2]) { var b2=q("b",stats[2]); if(b2) b2.textContent=furn; }
      if (stats[3]) { var b3=q("b",stats[3]); if(b3) b3.textContent=tinhTrang(d["Ngày vào ở"]||""); }
    } else {
      var note = q(".ct-rented-note p") || q("main.khung .bai p");
      if (note) {
        if (ma() === "vi") {
          note.innerHTML = "<strong>Căn này đã có khách thuê.</strong> Dưới đây là các căn còn trống tương tự.";
        } else {
          note.innerHTML = "<strong>" + T("rented.note1", "") + "</strong> " + T("rented.note2", "");
        }
      }
    }
  }

  function capNhatTieuDePhu() {
    qa("main.khung h2").forEach(function (h) {
      if (!h.dataset.ctKind) {
        var s = h.textContent.trim();
        if (/^Xem thêm theo nhu cầu$/i.test(s)) h.dataset.ctKind = "more";
        else if (/^Căn tương tự$/i.test(s)) h.dataset.ctKind = "similar";
        else if (/^Căn còn trống tương tự$/i.test(s)) h.dataset.ctKind = "available";
      }
      if (h.dataset.ctKind === "more") h.textContent = T("h.more", "Xem thêm theo nhu cầu");
      if (h.dataset.ctKind === "similar") h.textContent = T("h.similar", "Căn tương tự");
      if (h.dataset.ctKind === "available") h.textContent = T("h.availableSimilar", "Căn còn trống tương tự");
    });

    var originalAsk = q("a.cta-loc");
    if (originalAsk) {
      var d = docBang(), code = d && d["Mã căn"] || "";
      originalAsk.textContent = T("cta.ask", "Nhắn Zalo hỏi căn {CODE}", {CODE:code});
    }
    var originalCall = q("a.cta-home.tren");
    if (originalCall) originalCall.textContent = T("cta.call", "Gọi {PHONE}", {PHONE:"0977923284"});

    var empty = q("main.khung > p:not(.bc):not(.tt)");
    if (empty && /Hiện chưa có căn trống tương tự/i.test(empty.textContent)) {
      if (ma() === "vi") {
        empty.innerHTML = 'Hiện chưa có căn trống tương tự, mời xem <a href="/can-ho/">toàn bộ căn hộ đang cho thuê</a>.';
      } else {
        empty.innerHTML = '<a href="/can-ho/">' + T("empty.similar", "") + "</a>";
      }
    }
  }

  function capNhatUxDong(d) {
    var rawMove = d["Ngày vào ở"] || "";
    var price = giaDich(d["Giá thuê"] || "");
    var furn = enumDich(d["Nội thất"] || "");
    var type = enumDich(d["Loại"] || "");
    var code = d["Mã căn"] || "";

    var p = q(".ct-title-price"); if (p) p.textContent = price;
    var st = q(".ct-title-status"); if (st) st.textContent = tinhTrang(rawMove);
    var badge = q(".ct-live-badge");
    if (badge) badge.textContent = (!rawMove || /vào ngay|o ngay|luôn|ngay/i.test(rawMove))
      ? T("status.liveNow", "Có thể vào ở ngay") : tinhTrang(rawMove);
    var ap = q(".ct-aside-price"); if (ap) ap.textContent = price;
    var sub = q(".ct-aside-sub"); if (sub) sub.textContent = T("aside.price", "Giá thuê căn hộ");

    var facts = qa(".ct-aside-fact");
    var fl = [
      ["aside.type","Loại căn",type], ["aside.area","Diện tích",d["Diện tích"]||""],
      ["aside.tower","Tòa",d["Tòa"]||""], ["aside.furn","Nội thất",furn]
    ];
    facts.forEach(function (row,i) {
      if (!fl[i]) return;
      var s=q("span",row), b=q("b",row);
      if(s) s.textContent=T(fl[i][0],fl[i][1]);
      if(b) b.textContent=fl[i][2];
    });

    var actions = qa(".ct-aside-actions a");
    if(actions[0]) actions[0].textContent=T("action.book","Đặt lịch xem căn");
    if(actions[1]) actions[1].textContent=T("action.zalo","Nhắn Zalo");
    if(actions[2]) actions[2].textContent=T("action.call","Gọi 0977 923 284");
    var codeEl=q(".ct-aside-code"); if(codeEl) codeEl.textContent=T("aside.code","Mã căn: {CODE}",{CODE:code});
    var note=q(".ct-aside-note"); if(note) note.textContent=T("aside.note","Thông tin căn được đồng bộ từ quỹ căn đang hiển thị trên website.");

    var mobile = q(".ct-mobile-actions");
    if (mobile) {
      mobile.setAttribute("aria-label", T("action.book","Liên hệ căn hộ"));
      var links=qa("a",mobile);
      if (document.body.classList.contains("trang-chi-tiet-da-thue")) {
        if(links[0]) links[0].textContent=T("mobile.available","Xem căn trống");
        if(links[1]) links[1].textContent=T("action.zalo","Nhắn Zalo");
      } else {
        if(links[0]) links[0].textContent=T("action.callShort","Gọi");
        if(links[1]) links[1].textContent="Zalo";
        if(links[2]) links[2].textContent=T("action.bookShort","Đặt lịch xem");
      }
    }

    var toast=q("#ctDetailToast"); if(toast) toast.textContent=T("toast","Đã sao chép nội dung đặt lịch — mở Zalo và dán để gửi nhanh.");
    var noPhoto=q(".ct-no-photo");
    if(noPhoto) {
      var b0=q("b",noPhoto), s0=q("span",noPhoto);
      if(b0) b0.textContent=T("gallery.none1","Căn này đang cập nhật ảnh");
      if(s0) s0.textContent=T("gallery.none2","Nhắn Zalo để nhận ảnh và video thực tế.");
    }
    var imgs=qa(".ct-gallery img");
    imgs.forEach(function(img,i){
      img.setAttribute("aria-label",T("gallery.open","Mở ảnh {I} trên {N}",{I:i+1,N:imgs.length}));
    });
    var all=q(".ct-gallery-all");
    if(all) {
      var dem = all.textContent.trim().match(/^(\d+)\/(\d+)/);
      all.textContent = dem
        ? T("gallery.count","{I}/{N} ảnh",{I:Number(dem[1]),N:Number(dem[2])})
        : T("gallery.all","Xem tất cả {N} ảnh",{N:imgs.length});
    }
  }

  function capNhatFooter() {
    var foot = q("footer.chan > .khung p");
    if (foot) {
      var links=qa("a",foot);
      if(links[0]) links[0].textContent=T("footer.find","Tìm căn hộ");
      if(links[1]) links[1].textContent=T("footer.guide","Cẩm nang thuê nhà");
      if(links[2]) links[2].textContent=T("footer.owner","Chủ nhà gửi căn");
      if(links[3]) links[3].textContent=T("footer.privacy","Chính sách quyền riêng tư");
    }
    var z=q(".zalo-noi"); if(z) z.textContent=T("zalo.float","Nhắn Zalo tư vấn");
  }

  function apDung() {
    if (!laTrang() || !document.body.classList.contains("trang-chi-tiet-can")) return;
    var d = docBang();
    if (!d) return;
    capNhatHeader();
    capNhatNoiDung(d);
    capNhatBang(d);
    capNhatTieuDePhu();
    capNhatUxDong(d);
    capNhatFooter();
  }

  document.addEventListener("ngonngu:doi", function () {
    if (!document.body.classList.contains("trang-chi-tiet-can")) return;
    apDung();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      setTimeout(apDung, 0);
    });
  } else {
    setTimeout(apDung, 0);
  }
})();