/*!
 * ngon-ngu.js — Đổi ngôn ngữ hiển thị VI / EN / 한 cho TRANG CHỦ
 * timthuesmartcity.com — thêm 11/08/2026
 *
 * ĐÂY LÀ TÍNH NĂNG TRẢI NGHIỆM NGƯỜI DÙNG, KHÔNG PHẢI TÍNH NĂNG SEO.
 *   - Chỉ một địa chỉ duy nhất "/" — không sinh /en/ /ko/, không đụng sitemap,
 *     không thêm hreflang.
 *   - KHÔNG đổi <title>, <meta description>, og:*, twitter:*, canonical hay
 *     bất kỳ khối <script type="application/ld+json"> nào. Google vẫn đọc
 *     đúng bản tiếng Việt như hôm nay.
 *   - KHÔNG tự đoán ngôn ngữ theo trình duyệt. Mặc định luôn là tiếng Việt.
 *     Googlebot thu thập trang với Accept-Language: en-US; tự đổi theo trình
 *     duyệt là Google sẽ index bản tiếng Anh thay cho bản tiếng Việt.
 *
 * CHỈ DỊCH LÚC HIỂN THỊ, KHÔNG BAO GIỜ DỊCH DỮ LIỆU.
 *   Script nội tuyến của trang chủ dùng chính chuỗi tiếng Việt trong data.json
 *   ("2 Ngủ", "Full nội thất", "Sapphire"…) làm khoá lọc và điều kiện so sánh.
 *   File này chỉ đổi CHỮ IN RA MÀN HÌNH; mọi khoá dữ liệu giữ nguyên 100%.
 *
 * XOÁ FILE NÀY ĐI THÌ TRANG CHỦ CHẠY Y HỆT HÔM NAY.
 *   Mọi nơi gọi tới đều đi qua hàm bọc có giá trị dự phòng tiếng Việt, nên
 *   thiếu file này chỉ đơn giản là không có bản dịch — không lỗi, không vỡ.
 */
(function () {
  "use strict";

  /* ==================================================================
     1. CỬA DỊCH — đặt NGAY dòng đầu, trước mọi thứ khác
     ------------------------------------------------------------------
     index.html / gallery.js / app-shell.js đều gọi qua đây. Đặt sớm nhất
     có thể để không phụ thuộc thứ tự tải giữa các file.
     ================================================================== */
  var MA = "vi";                 // mã ngôn ngữ đang hiển thị: vi | en | ko | zh
  var KHOA_NHO = "smartcity_lang";

  /** Tra một chuỗi hiển thị. Không có bản dịch -> trả lại đúng chữ tiếng Việt. */
  function tra(khoa, macDinh) {
    if (MA === "vi") return macDinh;
    var muc = TU_DIEN[khoa];
    if (!muc) return macDinh;
    if (MA === "zh") {
      var zh = TU_DIEN_ZH[khoa];
      return (zh === undefined || zh === null || zh === "") ? macDinh : zh;
    }
    var chu = MA === "en" ? muc[0] : muc[1];
    return (chu === undefined || chu === null || chu === "") ? macDinh : chu;
  }
  window.NGON_NGU_T = tra;
  window.NGON_NGU_MA = function () { return MA; };

  /* ==================================================================
     2. TỪ ĐIỂN — mỗi khoá là một mảng ["EN", "KO"]
     ------------------------------------------------------------------
     Bản tiếng Việt KHÔNG nằm ở đây: nó là chữ đang có sẵn trong index.html
     (hoặc tham số macDinh khi gọi từ JS), nên không bao giờ có chuyện hai
     nơi ghi hai câu tiếng Việt khác nhau rồi lệch nhau về sau.
     ================================================================== */
  var TU_DIEN = {

    /* ---- Đầu trang & điều hướng ---- */
    "nav.brand":      ["Smart City Apartments for Rent", "스마트시티 아파트 임대"],
    "nav.brandSub":   ["Smart filters • Updated daily", "스마트 필터 • 매일 업데이트"],
    "nav.home":       ["Home", "홈"],
    "nav.rent":       ["Apartments", "임대 매물"],
    "nav.zone":       ["Zones", "구역"],
    "nav.type":       ["Apartment types", "타입"],
    "nav.price":      ["Rent prices", "임대료"],
    "nav.guideShort": ["Guide", "가이드"],
    "nav.consignShort":["List unit", "매물 등록"],
    "nav.moveIn":     ["Move in now", "즉시 입주"],
    "nav.guide":      ["Renting guide", "임대 가이드"],
    "nav.consign":    ["List your apartment", "매물 등록"],
    "nav.zalo":       ["Chat on Zalo", "잘로 상담"],
    "nav.main":       ["Main navigation", "메인 메뉴"],
    "search.ph":      ["Search by zone, unit code or type (e.g. Sapphire, 2BR, 8 million)",
                       "구역·매물번호·타입 검색 (예: Sapphire, 2BR, 800만)"],
    "search.al":      ["Search apartments by zone, unit code, type or price",
                       "구역, 매물번호, 타입, 가격으로 검색"],
    "search.suggest": ["Quick suggestions", "빠른 추천"],
    "qb.search":      ["Go to search box", "검색창으로"],
    "qb.filter":      ["Open full filters", "전체 필터 열기"],

    /* ---- Dải chữ chạy & hero ---- */
    "bar.new1":       ["✨ Added today:", "✨ 오늘 등록"],
    "bar.new2":       ["brand-new listings — tap to view", "신규 매물 — 지금 확인하세요"],
    "hero.h1":        ["Apartments for Rent at Vinhomes Smart City — {THANG} {NAM}",
                       "빈홈즈 스마트시티 아파트 임대 — {NAM}년 {THANG}월"],
    "hero.p":         ["Smart filters — search by rent, apartment type and furnishing. Data is synced continuously from real listings, so you can find the right unit in minutes.",
                       "스마트 필터로 임대료·타입·옵션별 검색. 실제 매물 데이터가 계속 동기화되어 몇 분 안에 원하는 집을 찾을 수 있습니다."],
    "hero.sync":      ["Listings re-synced every 30 minutes", "매물 30분마다 자동 동기화"],
    "hero.total":     ["Total units", "전체 매물"],
    "hero.ready":     ["Move-in now", "즉시 입주"],
    "hero.zone":      ["Zones", "구역"],
    "hero.statsAl":   ["Listing overview", "매물 요약"],

    /* ---- Bộ lọc ---- */
    "f.type":         ["Apartment type", "타입"],
    "f.typeAll":      ["All types", "전체 타입"],
    "f.zone":         ["Zone", "구역"],
    "f.zoneAll":      ["All zones", "전체 구역"],
    "f.zonePick":     ["Choose a tower or zone", "동·구역 선택"],
    "f.price":        ["Price range", "임대료"],
    "f.priceAll":     ["All prices", "전체 가격"],
    "f.pricePick":    ["Choose a price range", "가격대 선택"],
    "f.furn":         ["Furnishing", "옵션"],
    "f.furnAll":      ["All furnishing", "전체 옵션"],
    "f.furnPick":     ["Choose furnishing", "옵션 선택"],
    "f.find":         ["Search", "검색"],
    "f.clear":        ["Clear filters", "필터 초기화"],
    "f.clearShort":   ["Clear", "초기화"],
    "f.remove":       ["Remove filter", "필터 해제"],
    "f.view":         ["View", "보기"],
    "f.unit":         ["units", "개"],
    "f.tapHere":      ["Tap to quickly filter matching apartments", "눌러서 맞는 매물을 빠르게 필터"],
    "f.filterNow":    ["Filter now", "지금 필터"],
    "f.byZoneBed":    ["Filter by zone, bedrooms and rent", "구역·침실·임대료로 필터"],
    "f.panelAl":      ["Apartment filters", "매물 필터"],
    "f.bedStruct":    ["Bedroom layout", "침실 구조"],
    "f.monthly":      ["Monthly rent range", "월 임대료"],
    "f.openAl":       ["Open filters to find an apartment", "필터를 열어 매물 찾기"],
    "f.allRooms":     ["All layouts", "전체"],
    "f.all":          ["All", "전체"],
    "f.under75":      ["Under 7.5M VND", "750만 동 미만"],
    "f.75to10":       ["7.5M – 10M VND", "750만 – 1,000만 동"],
    "f.10to12":       ["10M – 12M VND", "1,000만 – 1,200만 동"],
    "f.12to15":       ["12M – 15M VND", "1,200만 – 1,500만 동"],
    "f.over15":       ["Over 15M VND", "1,500만 동 초과"],
    "f.furnFull":     ["Fully furnished", "풀옵션"],
    "f.furnBasic":    ["Basic", "기본 옵션"],
    "f.furnNone":     ["Unfurnished", "옵션 없음"],
    "f.close":        ["Close", "닫기"],

    /* ---- Danh sách căn & sắp xếp ---- */
    "l.loading":      ["Loading listings…", "매물 불러오는 중…"],
    "l.wait":         ["Just a moment…", "잠시만 기다려 주세요…"],
    "l.sortAl":       ["Sort listings", "매물 정렬"],
    "l.random":       ["Featured", "추천순"],
    "l.priceAsc":     ["Price: low to high", "임대료: 낮은순"],
    "l.priceDesc":    ["Price: high to low", "임대료: 높은순"],
    "l.onlyNew":      ["✨ New & recently updated only", "✨ 신규·최근 업데이트만"],
    "l.badgeNew":     ["✨ New", "✨ 신규"],
    "l.badgeNow":     ["Move-in now", "즉시 입주"],
    "l.badgeFrom":    ["Available from {NGAY}", "{NGAY}부터 입주 가능"],
    "l.furnUpd":      ["Furnishing being updated", "옵션 정보 업데이트 중"],
    "l.photos":       ["{N} photos", "사진 {N}장"],
    "l.code":         ["Unit code:", "매물 번호:"],
    "l.detail":       ["View details", "상세 보기"],
    "l.perMonth":     ["/month", "/월"],
    "l.contact":      ["Contact us", "가격 문의"],
    "l.galleryAl":    ["View apartment photos", "매물 사진 보기"],
    "l.pageAl":       ["Listing pagination", "매물 페이지"],
    "l.prev":         ["Previous", "이전"],
    "l.next":         ["Next", "다음"],
    "l.filtering":    ["Filtering:", "필터 적용:"],
    "l.noneNew":      ["No new or updated listings in the last 3 days. Please switch to the full list.",
                       "최근 3일간 신규·업데이트 매물이 없습니다. 전체 목록을 확인해 주세요."],
    "l.noneMatch":    ["No apartments match these filters right now. Leave your requirements and we will look for a suitable unit and contact you today.",
                       "현재 조건에 맞는 매물이 없습니다. 원하시는 조건을 남겨 주시면 오늘 중으로 찾아 연락드리겠습니다."],
    "l.loadErr":      ["Could not load listings", "매물을 불러오지 못했습니다"],
    "l.h2":           ["<strong>{N}</strong> apartments currently available",
                       "현재 임대 가능 매물 <strong>{N}</strong>개"],

    /* ---- Khối CTA giữa danh sách căn (thêm 14/08/2026) ---- */
    "cta.mid.h":      ["No need to scroll through every listing", "매물을 하나하나 보실 필요 없습니다"],
    "cta.mid.p":      ["Send us your requirements and we'll pick the 3–5 units closest to your budget and move-in date, then send them back to you.",
                       "원하시는 조건을 보내 주시면 예산과 입주 시기에 가장 가까운 매물 3~5개를 골라 보내 드립니다."],
    "cta.mid.btn":    ["Ask us to find the right unit", "맞는 매물 찾아 주세요"],

    /* ---- Khối "Chưa thấy căn ưng ý" & form để lại nhu cầu ---- */
    "lead.title":     ["Haven't found the right one?", "원하는 매물이 없나요?"],
    "lead.desc":      ["Leave your requirements — we'll search for you and get back to you today.",
                       "조건을 남겨 주시면 저희가 찾아 오늘 중으로 연락드립니다."],
    "lead.btn":       ["Request a search", "매물 찾기 요청"],
    "lead.mTitle":    ["What are you looking for?", "어떤 집을 찾으시나요?"],
    "lead.mDesc":     ["Leave your details and we'll find a suitable apartment and contact you today.",
                       "정보를 남겨 주시면 적합한 매물을 찾아 오늘 중으로 연락드립니다."],
    "lead.name":      ["Full name *", "성함 *"],
    "lead.namePh":    ["e.g. John Smith", "예: 홍길동"],
    "lead.phone":     ["Phone number *", "전화번호 *"],
    "lead.type":      ["Apartment type", "원하는 타입"],
    "lead.typeAny":   ["Not sure — please advise", "미정 / 상담 희망"],
    "lead.budget":    ["Budget", "희망 임대료"],
    "lead.budgetAny": ["Not sure yet", "미정"],
    "lead.b1":        ["6.5M – 7.5M VND", "650만 – 750만 동"],
    "lead.b2":        ["7.5M – 10M VND", "750만 – 1,000만 동"],
    "lead.b3":        ["10M – 12M VND", "1,000만 – 1,200만 동"],
    "lead.b4":        ["12M – 15M VND", "1,200만 – 1,500만 동"],
    "lead.b5":        ["Over 15M VND", "1,500만 동 초과"],
    "lead.moveIn":    ["Move-in date", "입주 희망일"],
    "lead.area":      ["Preferred zone / tower", "희망 구역 / 동"],
    "lead.areaPh":    ["e.g. Sa2, near the lake…", "예: Sa2, 호수 근처…"],
    "lead.note":      ["Additional notes", "추가 요청 사항"],
    "lead.notePh":    ["Other needs (occupants, pets, view…)", "기타 (거주 인원, 반려동물, 전망 등)"],
    "lead.send":      ["Send request", "요청 보내기"],
    "lead.sending":   ["Sending…", "전송 중…"],
    "lead.ok":        ["We've received your request", "요청이 접수되었습니다"],
    "lead.okDesc":    ["We'll contact you as soon as possible. Thank you!", "최대한 빨리 연락드리겠습니다. 감사합니다!"],
    "lead.errName":   ["Please enter your name and phone number.", "성함과 전화번호를 입력해 주세요."],
    "lead.errPhone":  ["That phone number doesn't look right — please check it.",
                       "전화번호 형식이 올바르지 않습니다. 다시 확인해 주세요."],
    "lead.errSend":   ["Something went wrong. Please try again or contact us on Zalo.",
                       "오류가 발생했습니다. 다시 시도하거나 잘로로 문의해 주세요."],

    /* ---- Dữ liệu thị trường homepage (P0 SEO 30/08/2026) ---- */
    "market.eyebrow":  ["Live inventory data", "실시간 매물 데이터"],
    "market.title":    ["Vinhomes Smart City rents today", "오늘의 빈홈즈 스마트시티 임대료"],
    "market.desc":     ["Calculated directly from listings currently shown on the website. Counts and price ranges update with the live inventory rather than a fixed advertising price table.",
                        "웹사이트에 현재 표시 중인 실제 매물에서 직접 집계합니다. 매물 수와 가격 범위는 고정 광고표가 아니라 실제 재고에 따라 업데이트됩니다."],
    "market.full":     ["View detailed rent table →", "상세 임대료 보기 →"],
    "market.byType":   ["By apartment type", "타입별"],
    "market.byZone":   ["By zone", "구역별"],
    "market.colType":  ["Apartment type", "타입"],
    "market.colZone":  ["Zone", "구역"],
    "market.colCount": ["Available", "매물 수"],
    "market.colPrice": ["Rent range", "가격 범위"],
    "market.unit":     ["units", "개"],
    "market.hot":      ["Popular now:", "많이 찾는 항목:"],
    "market.hotAl":    ["Popular rental topics", "인기 임대 주제"],

    /* ---- Mục lục kho dữ liệu, khám phá, chân trang ---- */
    "idx.title":      ["Vinhomes Smart City rental directory", "빈홈즈 스마트시티 임대 매물 목록"],
    "idx.desc":       ["All apartments are grouped by type, zone, price range and furnishing. Pick the group you're interested in to see the full list with real rents. These pages are in Vietnamese.",
                       "모든 매물을 타입·구역·가격대·옵션별로 정리했습니다. 관심 있는 그룹을 선택하면 실제 임대료가 포함된 전체 목록을 볼 수 있습니다. 해당 페이지는 베트남어로 제공됩니다."],
    "idx.byType":     ["By apartment type", "타입별"],
    "idx.byZone":     ["By zone", "구역별"],
    "idx.byPrice":    ["By price range", "가격대별"],
    "idx.byFurn":     ["By furnishing", "옵션별"],
    "idx.byTower":    ["By tower", "동별"],
    "idx.al":         ["Rental directory index", "임대 매물 목록 색인"],

    /* 24 liên kết trong #mucLucKhoDuLieu. TÁM tên phân khu (The Sapphire,
       Masteri West Heights, The Miami…) là danh từ riêng nên KHÔNG có khoá ở
       đây — giữ nguyên ở cả 3 ngôn ngữ. Các trang đích đều là tiếng Việt;
       idx.desc đã nói rõ điều đó. */
    "idx.t1":         ["Studio apartments for rent", "스튜디오 임대 매물"],
    "idx.t2":         ["1-bedroom apartments for rent", "침실 1개 임대 매물"],
    "idx.t3":         ["1-bedroom + apartments for rent", "침실 1개+ 임대 매물"],
    "idx.t4":         ["2-bedroom apartments for rent", "침실 2개 임대 매물"],
    "idx.t5":         ["2-bedroom + apartments for rent", "침실 2개+ 임대 매물"],
    "idx.t6":         ["3-bedroom apartments for rent", "침실 3개 임대 매물"],
    "idx.g1":         ["Studios under 7M VND", "스튜디오 700만 동 미만"],
    "idx.g2":         ["Studios 7M – 10M VND", "스튜디오 700만 – 1,000만 동"],
    "idx.g3":         ["1BR+ under 10M VND", "침실 1개+ 1,000만 동 미만"],
    "idx.g4":         ["2BR under 10M VND", "침실 2개 1,000만 동 미만"],
    "idx.g5":         ["2BR 10M – 12M VND", "침실 2개 1,000만 – 1,200만 동"],
    "idx.g6":         ["2BR+ 12M – 15M VND", "침실 2개+ 1,200만 – 1,500만 동"],
    "idx.g7":         ["3BR 12M – 15M VND", "침실 3개 1,200만 – 1,500만 동"],
    "idx.n1":         ["Fully furnished studios", "풀옵션 스튜디오"],
    "idx.n2":         ["Fully furnished 1BR+", "풀옵션 침실 1개+"],
    "idx.n3":         ["Fully furnished 2BR", "풀옵션 침실 2개"],
    "idx.n4":         ["Fully furnished 3BR", "풀옵션 침실 3개"],
    "idx.w1":         ["Apartments in tower S4.01", "S4.01동 임대 매물"],
    "idx.b1":         ["Rent table by zone", "구역별 임대료 표"],
    "idx.b2":         ["Service fees by zone", "구역별 관리비"],
    "idx.b3":         ["Studio rents in detail", "스튜디오 임대료 상세"],
    "idx.b4":         ["On-site amenities", "단지 내 편의시설"],
    "idx.b5":         ["Renting tips", "임대 노하우"],
    "idx.b6":         ["Parking, pets and service fees", "주차·반려동물·관리비"],
    "idx.b7":         ["Rent comparison by zone", "구역별 임대료 비교"],
    "idx.b8":         ["Rental procedure and paperwork", "임대 절차 및 서류"],
    "idx.b9":         ["Apartments near Vinschool", "빈스쿨 인근 매물"],
    "disc.title":     ["Browse by apartment type", "타입별 둘러보기"],
    "disc.desc":      ["Each type has its own page with the full list, real prices by zone and renting tips. (Vietnamese)",
                       "각 타입별로 전체 목록, 구역별 실제 가격, 임대 시 유의사항 페이지가 있습니다. (베트남어)"],
    "disc.studio":    ["Open-plan, suits 1–2 people", "오픈형, 1–2인 적합"],
    "disc.1pn":       ["Separate bedroom", "침실 분리형"],
    "disc.1pnp":      ["Extra alcove for a second bed", "확장 공간, 침대 추가 가능"],
    "disc.2pn":       ["Largest inventory", "매물 수 가장 많음"],
    "disc.2pnp":      ["Corner unit, larger and brighter", "코너 세대, 더 넓고 채광 우수"],
    "disc.3pn":       ["For larger families", "대가족용"],
    "faq.title":      ["Frequently asked questions", "자주 묻는 질문"],
    "own.title":      ["Do you have an apartment to rent out?", "임대할 아파트가 있으신가요?"],
    "own.desc":       ["Send us the details and photos here — we'll publish the listing and find tenants for you. Free, no account needed.",
                       "정보와 사진을 보내 주시면 매물을 등록하고 세입자를 찾아드립니다. 무료이며 회원가입이 필요 없습니다."],
    "own.btn":        ["List your apartment — for owners →", "매물 등록 – 집주인용 →"],
    "ft.copy":        ["© 2026 Smart City Apartments for Rent", "© 2026 스마트시티 아파트 임대"],
    "ft.owner":       ["Owners: submit a listing", "집주인 매물 등록"],
    "ft.privacy":     ["Privacy policy", "개인정보 처리방침"],
    "ft.zones":       ["Zones currently available:", "임대 가능 구역:"],
    "ft.follow":      ["Follow us for daily new listings", "매일 신규 매물 확인"],
    "ft.call":        ["Call", "전화"],
    "ft.allPosts":    ["See all articles →", "전체 글 보기 →"],
    "ft.fb":          ["Follow on Facebook", "페이스북 팔로우"],
    "ft.tt":          ["Follow on TikTok", "틱톡 팔로우"],
    "ft.yt":          ["Follow on YouTube", "유튜브 구독"],
    "ft.ig":          ["Follow on Instagram", "인스타그램 팔로우"],

    /* ---- Khối giới thiệu cuối trang (.seo-block) ----
       seo.p1/p2/p3 dùng qua data-i18n-html: bản dịch thay CẢ innerHTML nên
       PHẢI giữ y nguyên <strong> và thuộc tính href của <a> — đổi hay bỏ href
       là làm gãy liên kết nội bộ, scripts/kiem-tra-lien-ket.py sẽ báo lỗi. */
    "seo.h2":         ["Renting at Smart City — apartments for rent at Vinhomes Smart City",
                       "스마트시티 임대 — 빈홈즈 스마트시티 아파트 임대"],
    "seo.p1":         ["<strong>Smart City Apartments for Rent</strong> brings together apartments available at Vinhomes Smart City (Tây Mỗ Ward, Hanoi), with data synced automatically several times a day so vacancy, rent and real photos stay accurate. Types range from studios and 1-bedroom to 2- and 3-bedroom units across the Sapphire, Miami, Sakura, Masteri West Heights, Imperia, Lumière, Canopy and Tonkin zones.",
                       "<strong>스마트시티 아파트 임대</strong>는 빈홈즈 스마트시티(떠이모, 남뜨리엠, 하노이)의 임대 매물을 모은 사이트입니다. 하루에 여러 번 자동 동기화되어 공실 현황, 임대료, 실제 사진이 정확하게 반영됩니다. 스튜디오, 침실 1개부터 침실 2개·3개까지 Sapphire, Miami, Sakura, Masteri West Heights, Imperia, Lumière, Canopy, Tonkin 구역에 걸쳐 있습니다."],
    "seo.p2":         ["Rent for <strong>housing at Smart City</strong> currently starts at around 5.5M VND/month for a studio and rises with floor area, zone and furnishing. See the breakdown in the <a href=\"/bang-gia-thue-vinhomes-smart-city.html\">rent table for each zone</a> (Vietnamese), or use the filters above to narrow by budget and type.",
                       "<strong>스마트시티 주택</strong>의 임대료는 스튜디오 기준 월 550만 동 정도부터 시작하며 면적·구역·옵션에 따라 올라갑니다. 자세한 내용은 <a href=\"/bang-gia-thue-vinhomes-smart-city.html\">구역별 임대료 표</a>(베트남어)를 참고하시거나, 위의 필터로 예산과 타입을 좁혀 보세요."],
    "seo.p3":         ["Every <strong>Vinhomes Smart City rental listing</strong> states the rent, floor area, orientation and furnishing (fully furnished / basic / unfurnished). Browse by <a href=\"#mucLucKhoDuLieu\">category</a>, then message us on Zalo and we'll take you to view the apartment in person.",
                       "모든 <strong>빈홈즈 스마트시티 임대 매물</strong>에는 임대료, 면적, 향, 옵션(풀옵션 / 기본 옵션 / 옵션 없음)이 명시되어 있습니다. <a href=\"#mucLucKhoDuLieu\">카테고리</a>별로 둘러보신 뒤 잘로로 연락 주시면 직접 집을 보여드립니다."],

    /* ---- Dải nhắc khách nước ngoài (không có bản tiếng Việt: ở VI thì để rỗng) ---- */
    "notice.vn":      ["This homepage is available in English. Other pages on the site are in Vietnamese — message us on Zalo and we'll assist you in English.",
                       "이 홈페이지는 한국어로 제공됩니다. 다른 페이지는 베트남어로만 제공되니, 잘로로 문의해 주시면 도와드리겠습니다."],

    /* ---- Album ảnh (assets/gallery.js) ---- */
    "g.open":         ["View apartment photos", "매물 사진 보기"],
    "g.close":        ["Close", "닫기"],
    "g.prev":         ["Previous photo", "이전 사진"],
    "g.next":         ["Next photo", "다음 사진"],

    /* ---- Thanh tab dưới & menu (assets/app-shell.js) ----
       Các mục này trỏ sang trang TIẾNG VIỆT. Bản dịch chỉ để khách biết link
       đó nói về gì, không hứa trang đích có tiếng Anh — đã ghi rõ ở notice.vn. */
    "sh.guide":        ["Guide", "가이드"],
    "sh.contact":      ["Contact", "문의"],
    "sh.zalo":         ["Zalo", "잘로"],
    "sh.call":         ["Call", "전화"],
    "sh.priceLookup":  ["Price guides", "가격 정보"],
    "sh.priceTable":   ["Rent table by zone", "구역별 임대료 표"],
    "sh.priceCompare": ["Compare rents across zones", "구역별 임대료 비교"],
    "sh.priceStudio":  ["Studio rents", "스튜디오 임대료"],
    "sh.before":       ["Before you rent", "임대 전 확인"],
    "sh.guideFull":    ["Renting guide", "임대 가이드"],
    "sh.exp":          ["Tips for renting at Smart City", "스마트시티 임대 노하우"],
    "sh.amen":         ["On-site amenities", "단지 내 편의시설"],
    "sh.fees":         ["Service fees, parking, pets", "관리비·주차·반려동물"],
    "sh.other":        ["Other", "기타"],
    "sh.cat":          ["Listings by zone", "구역별 매물"],
    "sh.privacy":      ["Privacy policy", "개인정보 처리방침"],
    "sh.close":        ["Close", "닫기"],
    "sh.home":         ["Home", "홈"],
    "sh.consign":      ["List for rent", "임대 등록"],
    "sh.menu":         ["Menu", "메뉴"],
    "sh.rent":         ["Rentals", "임대"],
    "sh.price":        ["Rent prices", "임대료"],
    "sh.findRent":     ["Find an apartment", "매물 찾기"],
    "sh.allRent":      ["All available apartments", "전체 임대 매물"],
    "sh.zones":        ["Zones", "구역"],
    "sh.priceGuide":   ["Rent prices & guides", "임대료·가이드"],
    "sh.navAl":        ["Quick navigation", "빠른 이동"],

    /* ==================================================================
       KHÓA THÊM — ngoài bảng ở HUONG-DAN mục 5.5
       ------------------------------------------------------------------
       Mục 6.5 yêu cầu dịch một số chuỗi mà bảng 5.5 chưa có khoá tương ứng
       (nhãn ngắn của chip trên điện thoại, nhãn loại căn, thông báo sao chép
       tin nhắn Zalo, 6 câu hỏi FAQ theo mục 6.4). Đặt riêng ở đây cho dễ đối
       chiếu khi duyệt.
       ================================================================== */

    /* Nhãn loại căn — dùng chung cho chip lọc, ô chọn trong form và khối
       "Khám phá theo loại căn hộ". Chữ khớp đúng bảng dữ liệu ở mục 5.2. */
    "f.typeStudio":   ["Studio", "스튜디오"],
    "f.type1pn":      ["1 Bedroom", "침실 1개"],
    "f.type1pnp":     ["1 Bedroom +", "침실 1개 +"],
    "f.type2pn":      ["2 Bedrooms", "침실 2개"],
    "f.type2pnp":     ["2 Bedrooms +", "침실 2개 +"],
    "f.type3pn":      ["3 Bedrooms", "침실 3개"],

    /* Nhãn NGẮN của chip — bản tiếng Việt là "1 PN", "< 7,5tr"… Chip trên
       điện thoại rất hẹp nên bản dịch cũng phải ngắn tương đương, không dùng
       lại nhãn dài ở trên (sẽ vỡ hàng chip). */
    "f.sAll":         ["All", "전체"],
    "f.sStudio":      ["Studio", "스튜디오"],
    "f.s1pn":         ["1BR", "침실1"],
    "f.s1pnp":        ["1BR+", "침실1+"],
    "f.s2pn":         ["2BR", "침실2"],
    "f.s2pnp":        ["2BR+", "침실2+"],
    "f.s3pn":         ["3BR", "침실3"],
    "f.sUnder75":     ["< 7.5M", "750만↓"],
    "f.s75to10":      ["7.5–10M", "750–1,000만"],
    "f.s10to12":      ["10–12M", "1,000–1,200만"],
    "f.s12to15":      ["12–15M", "1,200–1,500만"],
    "f.sOver15":      ["> 15M", "1,500만↑"],
    "f.sFurnFull":    ["Full", "풀옵션"],
    "f.sFurnBasic":   ["Basic", "기본"],
    "f.sFurnNone":    ["Unfurn.", "옵션없음"],

    /* Ô tìm kiếm bản điện thoại — chuỗi ngắn hơn search.ph */
    "search.phShort": ["Sapphire, 2BR, 8 million, unit code…", "Sapphire, 2BR, 800만, 매물번호…"],

    /* Thẻ căn hộ & gallery dự phòng */
    "l.ask":          ["Ask about this unit", "이 매물 문의"],
    "l.imgUpd":       ["Photos are being updated", "사진 업데이트 중"],
    /* Thẻ căn chưa có ảnh: nói thật là chưa có ảnh + mời nhắn Zalo. Thay chỗ
       l.imgUpd trong mediaMarkup(); l.imgUpd giữ lại phòng nơi khác còn dùng. */
    "l.noPhoto":      ["No photos for this unit yet", "이 매물은 아직 사진이 없습니다"],
    "l.noPhotoCta":   ["Message us on Zalo for real photos", "실제 사진은 잘로로 문의"],
    "l.photosTitle":  ["Apartment photos", "매물 사진"],
    "l.photoAlt":     ["Apartment photo", "매물 사진"],

    /* Thông báo lỗi còn thiếu khoá ở bảng 5.5 */
    "lead.errNet":    ["Could not send your request. Please try again or contact us on Zalo.",
                       "요청을 보내지 못했습니다. 다시 시도하거나 잘로로 문의해 주세요."],

    /* Hai thông báo hướng dẫn sao chép tin nhắn Zalo.
       TÊN NÚT "Dán" GIỮ NGUYÊN TIẾNG VIỆT — đó là chữ in trên app Zalo bản
       tiếng Việt mà khách đang nhìn thấy, dịch đi là khách không tìm ra nút. */
    "zl.copied":      ["Message copied", "메시지가 복사되었습니다"],
    "zl.copiedHow":   ["In Zalo, press and hold the chat box for a second, choose <b>Dán</b> (Paste) and send",
                       "잘로 채팅창을 1초간 길게 누른 뒤 <b>Dán</b>(붙여넣기)를 선택해 보내 주세요"],
    "zl.copyFail":    ["Your device blocked copying", "기기에서 복사가 차단되었습니다"],
    "zl.copyFailHow": ["Please copy this line and paste it into Zalo:", "아래 문장을 복사해 잘로에 붙여넣어 주세요:"],

    /* 6 câu hỏi FAQ hiển thị trên trang (mục 6.4).
       KHỐI <script type="application/ld+json"> Ở ĐẦU TRANG GIỮ NGUYÊN TIẾNG
       VIỆT — Google đọc khối đó, không phải khối này. */
    "faq.q1": ["How much does it cost to rent an apartment at Vinhomes Smart City?",
               "빈홈즈 스마트시티 아파트 임대료는 어느 정도인가요?"],
    "faq.a1": ["Rents vary widely, commonly from about 6.5M VND/month for a studio up to over 15M VND/month for a 2–3 bedroom unit, depending on size, tower and furnishing. Use the price filter above to see exactly which units fit your budget.",
               "임대료는 매물에 따라 다양하며, 스튜디오는 월 약 650만 동부터, 침실 2~3개는 월 1,500만 동 이상까지입니다. 면적·동·옵션에 따라 달라집니다. 위의 가격 필터로 예산에 맞는 매물을 확인해 보세요."],
    "faq.q2": ["Where is Vinhomes Smart City?", "빈홈즈 스마트시티는 어디에 있나요?"],
    "faq.a2": ["Vinhomes Smart City is in Tây Mỗ Ward, Hanoi — one of the largest smart township developments in the western part of the city.",
               "빈홈즈 스마트시티는 하노이 남뜨리엠구에 위치한, 하노이 서부 최대 규모의 스마트 신도시 중 하나입니다."],
    "faq.q3": ["What apartment types are available for rent at Vinhomes Smart City?",
               "빈홈즈 스마트시티에는 어떤 타입의 임대 매물이 있나요?"],
    "faq.a3": ["Studios, 1 bedroom, 1 bedroom+, 2 bedrooms, 2 bedrooms+ and 3 bedrooms, spread across many towers — suitable for singles, couples and families.",
               "스튜디오, 침실 1개, 침실 1개+, 침실 2개, 침실 2개+, 침실 3개까지 여러 동에 걸쳐 있으며 1인 가구, 커플, 가족 모두에게 적합합니다."],
    "faq.q4": ["Do the apartments come furnished?", "매물에 가구가 포함되어 있나요?"],
    "faq.a4": ["It depends on the unit. Every listing states the furnishing clearly: Fully furnished (ready to move in), Basic furniture, or Unfurnished. You can filter by furnishing right on this page.",
               "매물마다 다릅니다. 각 매물에 풀옵션(즉시 입주 가능), 기본 옵션, 옵션 없음이 명확히 표시되어 있으며, 이 페이지에서 옵션별로 필터링할 수 있습니다."],
    "faq.q5": ["How do I view an apartment or get in touch?", "매물을 보거나 문의하려면 어떻게 하나요?"],
    "faq.a5": ["Tap \"Ask about this unit\" on any listing to message us on Zalo, or contact hotline/Zalo 0977923284 to get advice and book a viewing.",
               "각 매물의 \"이 매물 문의\" 버튼을 눌러 잘로로 메시지를 보내시거나, 핫라인/잘로 0977923284로 연락 주시면 상담 및 방문 일정을 잡아드립니다."],
    "faq.q6": ["Are the listings kept up to date?", "매물 정보는 자주 업데이트되나요?"],
    "faq.a6": ["Data is synced automatically several times a day so availability, rent and photos reflect the real situation.",
               "데이터가 하루에 여러 번 자동으로 동기화되어 공실 여부, 임대료, 사진이 실제 상황을 반영합니다."]
  };

  /* ==================================================================
     3. DỊCH GIÁ TRỊ DỮ LIỆU (enum) — BẢNG TRA, KHÔNG ĐOÁN
     ------------------------------------------------------------------
     data.json chỉ có 6 giá trị "Loại" và 3 giá trị "Nội thất".
     Tên phân khu (Sapphire, Masteri West Heights, Imperia, Lumière, Canopy,
     Tonkin, Sakura, The Miami) và mã tòa (S4.01, GS3, TK1…) là danh từ riêng
     -> GIỮ NGUYÊN ở cả 3 ngôn ngữ, không có mặt trong bảng này.
     ================================================================== */

  var TU_DIEN_ZH = {"nav.brand":"Smart City 公寓出租","nav.brandSub":"智能筛选 • 每日更新","nav.home":"首页","nav.rent":"出租房源","nav.zone":"分区","nav.type":"户型","nav.price":"租金","nav.guideShort":"租房指南","nav.consignShort":"发布房源","nav.moveIn":"可立即入住","nav.guide":"租房指南","nav.consign":"发布出租房源","nav.zalo":"Zalo 咨询","nav.main":"主导航","search.ph":"按分区、房源编号或户型搜索（如 Sapphire、2居、800万）","search.al":"按分区、房源编号、户型或价格搜索公寓","search.suggest":"快捷推荐","search.phShort":"Sapphire、2居、800万、房源编号…","qb.search":"前往搜索框","qb.filter":"打开全部筛选","bar.new1":"✨ 今日新增：","bar.new2":"套新房源 — 点击查看","hero.h1":"Vinhomes Smart City 公寓出租 — {NAM}年{THANG}月","hero.p":"智能筛选租金、户型和家具配置。真实房源持续同步，几分钟内找到合适的公寓。","hero.sync":"房源每30分钟自动同步","hero.total":"全部房源","hero.ready":"可立即入住","hero.zone":"分区","hero.statsAl":"房源概览","f.type":"户型","f.typeAll":"全部户型","f.zone":"分区","f.zoneAll":"全部分区","f.zonePick":"选择楼栋或分区","f.price":"价格区间","f.priceAll":"全部价格","f.pricePick":"选择价格区间","f.furn":"家具配置","f.furnAll":"全部配置","f.furnPick":"选择家具配置","f.find":"搜索","f.clear":"清除筛选","f.clearShort":"清除","f.remove":"移除筛选","f.view":"查看","f.unit":"套","f.tapHere":"点击快速筛选匹配房源","f.filterNow":"立即筛选","f.byZoneBed":"按分区、卧室和租金筛选","f.panelAl":"公寓筛选","f.bedStruct":"卧室户型","f.monthly":"月租区间","f.openAl":"打开筛选查找公寓","f.allRooms":"全部户型","f.all":"全部","f.under75":"750万越南盾以下","f.75to10":"750万–1000万越南盾","f.10to12":"1000万–1200万越南盾","f.12to15":"1200万–1500万越南盾","f.over15":"1500万越南盾以上","f.furnFull":"家具家电齐全","f.furnBasic":"基础家具","f.furnNone":"无家具","f.close":"关闭","f.typeStudio":"Studio","f.type1pn":"1居室","f.type1pnp":"1居室+","f.type2pn":"2居室","f.type2pnp":"2居室+","f.type3pn":"3居室","f.sAll":"全部","f.sStudio":"Studio","f.s1pn":"1居","f.s1pnp":"1居+","f.s2pn":"2居","f.s2pnp":"2居+","f.s3pn":"3居","f.sUnder75":"<750万","f.s75to10":"750–1000万","f.s10to12":"1000–1200万","f.s12to15":"1200–1500万","f.sOver15":">1500万","f.sFurnFull":"全配","f.sFurnBasic":"基础","f.sFurnNone":"无家具","l.loading":"正在加载房源…","l.wait":"请稍候…","l.sortAl":"房源排序","l.random":"推荐","l.priceAsc":"价格：从低到高","l.priceDesc":"价格：从高到低","l.onlyNew":"✨ 仅看新房源和最近更新","l.badgeNew":"✨ 新房源","l.badgeNow":"可立即入住","l.badgeFrom":"{NGAY} 起可入住","l.furnUpd":"家具信息更新中","l.photos":"{N} 张照片","l.code":"房源编号：","l.detail":"查看详情","l.perMonth":"/月","l.contact":"咨询价格","l.galleryAl":"查看公寓照片","l.pageAl":"房源分页","l.prev":"上一页","l.next":"下一页","l.filtering":"当前筛选：","l.noneNew":"最近3天暂无新房源或更新房源，请查看全部房源。","l.noneMatch":"目前没有符合这些条件的公寓。留下需求，我们会帮您寻找合适房源并尽快联系。","l.loadErr":"无法加载房源","l.h2":"目前有 <strong>{N}</strong> 套公寓可出租","l.ask":"咨询此房源","l.imgUpd":"照片更新中","l.noPhoto":"此房源暂时没有照片","l.noPhotoCta":"通过 Zalo 获取实拍照片","l.photosTitle":"公寓照片","l.photoAlt":"公寓照片","cta.mid.h":"不用把所有房源都看一遍","cta.mid.p":"告诉我们预算和入住时间，我们会挑选3–5套最合适的房源发给您。","cta.mid.btn":"帮我找合适房源","lead.title":"还没找到合适的房子？","lead.desc":"留下您的需求，我们帮您寻找并尽快联系。","lead.btn":"请帮我找房","lead.mTitle":"您想找什么样的房子？","lead.mDesc":"留下信息，我们会寻找合适公寓并尽快联系您。","lead.name":"姓名 *","lead.namePh":"例如：王先生","lead.phone":"电话号码 *","lead.type":"户型","lead.typeAny":"还不确定 — 请推荐","lead.budget":"预算","lead.budgetAny":"暂未确定","lead.b1":"650万–750万越南盾","lead.b2":"750万–1000万越南盾","lead.b3":"1000万–1200万越南盾","lead.b4":"1200万–1500万越南盾","lead.b5":"1500万越南盾以上","lead.moveIn":"入住日期","lead.area":"希望的分区 / 楼栋","lead.areaPh":"例如：Sa2、靠近湖边…","lead.note":"补充说明","lead.notePh":"其他需求（入住人数、宠物、景观等）","lead.send":"提交需求","lead.sending":"正在提交…","lead.ok":"已收到您的需求","lead.okDesc":"我们会尽快联系您，谢谢！","lead.errName":"请输入姓名和电话号码。","lead.errPhone":"电话号码格式似乎不正确，请检查。","lead.errSend":"提交失败，请重试或通过 Zalo 联系我们。","lead.errNet":"无法提交需求，请重试或通过 Zalo 联系我们。","market.eyebrow":"实时房源数据","market.title":"Vinhomes Smart City 当前租金","market.desc":"直接根据网站当前展示的真实房源统计。房源数量和价格区间会随实时库存更新，而不是固定广告价格。","market.full":"查看详细租金表 →","market.byType":"按户型","market.byZone":"按分区","market.colType":"户型","market.colZone":"分区","market.colCount":"可租房源","market.colPrice":"租金区间","market.unit":"套","market.hot":"热门：","market.hotAl":"热门租房主题","idx.title":"Vinhomes Smart City 租房目录","idx.desc":"所有公寓按户型、分区、价格和家具配置整理。选择分类可查看真实租金的完整列表。部分专题页目前为越南语。","idx.byType":"按户型","idx.byZone":"按分区","idx.byPrice":"按价格","idx.byFurn":"按家具配置","idx.byTower":"按楼栋","idx.al":"租房目录索引","idx.t1":"Studio 出租","idx.t2":"1居室出租","idx.t3":"1居室+ 出租","idx.t4":"2居室出租","idx.t5":"2居室+ 出租","idx.t6":"3居室出租","idx.g1":"700万越南盾以下 Studio","idx.g2":"700万–1000万越南盾 Studio","idx.g3":"1000万越南盾以下 1居+","idx.g4":"1000万越南盾以下 2居","idx.g5":"1000万–1200万越南盾 2居","idx.g6":"1200万–1500万越南盾 2居+","idx.g7":"1200万–1500万越南盾 3居","idx.n1":"全配 Studio","idx.n2":"全配 1居+","idx.n3":"全配 2居","idx.n4":"全配 3居","idx.w1":"S4.01 楼栋公寓","idx.b1":"各分区租金表","idx.b2":"各分区服务费","idx.b3":"Studio 租金详情","idx.b4":"社区配套","idx.b5":"租房经验","idx.b6":"停车、宠物和服务费","idx.b7":"各分区租金对比","idx.b8":"租赁流程和手续","idx.b9":"Vinschool 附近公寓","disc.title":"按户型浏览","disc.desc":"每种户型都有完整房源、各分区真实价格和租房建议。（部分页面为越南语）","disc.studio":"开放式，适合1–2人","disc.1pn":"独立卧室","disc.1pnp":"额外空间，可放第二张床","disc.2pn":"房源数量最多","disc.2pnp":"边户，更大更明亮","disc.3pn":"适合大家庭","faq.title":"常见问题","own.title":"您有公寓要出租吗？","own.desc":"把房源信息和照片发给我们，我们帮您发布并寻找租客。免费，无需注册。","own.btn":"房东发布房源 →","ft.copy":"© 2026 Smart City 公寓出租","ft.owner":"房东发布房源","ft.privacy":"隐私政策","ft.zones":"当前可租分区：","ft.follow":"关注我们，查看每日新房源","ft.call":"电话","ft.allPosts":"查看全部文章 →","ft.fb":"关注 Facebook","ft.tt":"关注 TikTok","ft.yt":"关注 YouTube","ft.ig":"关注 Instagram","seo.h2":"Smart City 租房 — Vinhomes Smart City 公寓出租","seo.p1":"<strong>Smart City 公寓出租</strong>汇集 Vinhomes Smart City（河内 Tây Mỗ）的可租公寓，房源每天自动同步多次，及时更新空置情况、租金和实拍照片。户型包括 Studio、1居、2居和3居，覆盖 Sapphire、Miami、Sakura、Masteri West Heights、Imperia、Lumière、Canopy 和 Tonkin 等分区。","seo.p2":"目前 <strong>Smart City 公寓</strong>租金大约从 Studio 每月550万越南盾起，具体取决于面积、分区和家具配置。可查看<a href=\"/bang-gia-thue-vinhomes-smart-city.html\">各分区租金表</a>（越南语），或使用上方筛选按预算和户型查找。","seo.p3":"每条 <strong>Vinhomes Smart City 出租房源</strong>都会标明租金、面积和家具配置（全配 / 基础 / 无家具）。可按<a href=\"#mucLucKhoDuLieu\">分类</a>浏览，然后通过 Zalo 联系我们预约实地看房。","notice.vn":"首页和房源详情支持简体中文。其他专题页目前主要为越南语，如需帮助请通过 Zalo 联系我们。","g.open":"查看公寓照片","g.close":"关闭","g.prev":"上一张照片","g.next":"下一张照片","sh.guide":"指南","sh.contact":"联系","sh.zalo":"Zalo","sh.call":"电话","sh.priceLookup":"租金指南","sh.priceTable":"各分区租金表","sh.priceCompare":"各分区租金对比","sh.priceStudio":"Studio 租金","sh.before":"租房前须知","sh.guideFull":"租房指南","sh.exp":"Smart City 租房经验","sh.amen":"社区配套","sh.fees":"服务费、停车、宠物","sh.other":"其他","sh.cat":"按分区查看房源","sh.privacy":"隐私政策","sh.close":"关闭","sh.home":"首页","sh.consign":"发布出租","sh.menu":"菜单","sh.rent":"出租","sh.price":"租金","sh.findRent":"找公寓","sh.allRent":"全部可租公寓","sh.zones":"分区","sh.priceGuide":"租金与指南","sh.navAl":"快捷导航","zl.copied":"消息已复制","zl.copiedHow":"在 Zalo 聊天框长按1秒，选择 <b>Dán</b>（粘贴）后发送","zl.copyFail":"设备阻止了复制","zl.copyFailHow":"请复制下面这段文字并粘贴到 Zalo：","faq.q1":"Vinhomes Smart City 公寓租金大约多少？","faq.a1":"租金因房源而异。Studio 通常每月约650万越南盾起，2–3居可超过1500万越南盾，具体取决于面积、楼栋和家具配置。可使用上方价格筛选查看符合预算的房源。","faq.q2":"Vinhomes Smart City 在哪里？","faq.a2":"Vinhomes Smart City 位于河内 Tây Mỗ，是河内西部大型智慧社区之一。","faq.q3":"Vinhomes Smart City 有哪些出租户型？","faq.a3":"有 Studio、1居、1居+、2居、2居+ 和3居，分布在多个楼栋，适合单身、情侣和家庭。","faq.q4":"出租公寓带家具吗？","faq.a4":"每套房不同。房源会清楚标注家具家电齐全、基础家具或无家具，也可以直接按家具配置筛选。","faq.q5":"如何看房或联系？","faq.a5":"点击任意房源的“咨询此房源”即可通过 Zalo 联系，或拨打/添加 Zalo 0977923284 预约看房。","faq.q6":"房源信息会及时更新吗？","faq.a6":"数据每天自动同步多次，让空置状态、租金和照片尽量反映真实情况。"};

  var DU_LIEU = {
    "studio":         ["Studio", "스튜디오 (원룸)"],
    "1 ngủ":          ["1 Bedroom", "침실 1개"],
    "1 ngủ +":        ["1 Bedroom +", "침실 1개 +"],
    "2 ngủ":          ["2 Bedrooms", "침실 2개"],
    "2 ngủ +":        ["2 Bedrooms +", "침실 2개 +"],
    "3 ngủ":          ["3 Bedrooms", "침실 3개"],
    "full nội thất":  ["Fully furnished", "풀옵션"],
    "đồ cơ bản":      ["Basic furniture", "기본 옵션"],
    "nhà nguyên bản": ["Unfurnished", "옵션 없음"]
  };


  var DU_LIEU_ZH = {"studio":"Studio","1 ngủ":"1居室","1 ngủ +":"1居室+","2 ngủ":"2居室","2 ngủ +":"2居室+","3 ngủ":"3居室","full nội thất":"家具家电齐全","đồ cơ bản":"基础家具","nhà nguyên bản":"无家具"};

  /** Dịch một giá trị enum lúc IN RA MÀN HÌNH. Không khớp bảng -> giữ nguyên. */
  function dichDuLieu(giaTri) {
    var goc = giaTri == null ? "" : String(giaTri);
    if (MA === "vi" || !goc) return goc;
    var muc = DU_LIEU[goc.trim().toLowerCase()];
    if (!muc) return goc;
    if (MA === "zh") return DU_LIEU_ZH[goc.trim().toLowerCase()] || goc;
    return (MA === "en" ? muc[0] : muc[1]) || goc;
  }
  window.NGON_NGU_DU_LIEU = dichDuLieu;

  /* ==================================================================
     4. ĐỊNH DẠNG GIÁ VÀ NGÀY
     ================================================================== */

  /** Chèn dấu phẩy ngăn hàng nghìn: 1250 -> "1,250" */
  function ngancachNghin(so) {
    return String(so).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  /**
   * Giá trong dữ liệu là số VND thô (ví dụ 6800000).
   *   VI: giữ nguyên hàm hiện có của trang  -> "6,8 triệu"
   *   EN: "6.8M VND"     (chia 1.000.000, 1 số lẻ, bỏ ".0")
   *   KO: "680만 동"      (chia 10.000 — đơn vị 만 là cách đọc tự nhiên)
   * KHÔNG quy đổi ra USD/KRW: tỷ giá đổi liên tục, ghi vào là sai ngay hôm sau.
   */
  function dichGia(soVnd, macDinh) {
    if (MA === "vi") return macDinh;
    var so = Number(soVnd) || 0;
    if (!so) return tra("l.contact", macDinh);
    if (MA === "en") {
      return (so / 1000000).toFixed(1).replace(/\.0$/, "") + "M VND";
    }
    if (MA === "zh") return ngancachNghin(Math.round(so / 10000)) + "万越南盾";
    return ngancachNghin(Math.round(so / 10000)) + "만 동";
  }
  window.NGON_NGU_GIA = dichGia;

  var THANG_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  /**
   * "Ngày vào ở" trong dữ liệu là DD/MM/YYYY. Người Mỹ đọc 01/08/2026 thành
   * 8 tháng 1 nên phải viết rõ ràng:
   *   EN: "1 Aug 2026"      KO: "2026년 8월 1일"
   * Không khớp mẫu (ví dụ chữ "luôn", "ở ngay") -> trả lại bản tiếng Việt.
   */
  function dichNgay(chuoi, macDinh) {
    if (MA === "vi") return macDinh;
    var m = String(chuoi == null ? "" : chuoi).match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
    if (!m) return macDinh;
    var ngay = Number(m[1]), thang = Number(m[2]), nam = m[3];
    if (thang < 1 || thang > 12) return macDinh;
    if (MA === "en") return ngay + " " + THANG_EN[thang - 1] + " " + nam;
    if (MA === "zh") return nam + "年" + thang + "月" + ngay + "日";
    return nam + "년 " + thang + "월 " + ngay + "일";
  }
  window.NGON_NGU_NGAY = dichNgay;

  /* ==================================================================
     5. BỘ MÁY DỊCH CHỮ TĨNH
     ------------------------------------------------------------------
       data-i18n      -> chữ hiển thị (CHỈ nút chữ trực tiếp, giữ nguyên thẻ con)
       data-i18n-html -> thay CẢ innerHTML, cho đoạn văn có thẻ nằm xen giữa chữ
       data-i18n-ph   -> placeholder
       data-i18n-al   -> aria-label
     Bản tiếng Việt gốc được ghi nhớ vào data-vi-goc / data-vi-html / data-vi-ph
     / data-vi-al NGAY LÚC TẢI TRANG (kể cả khi đang ở tiếng Việt), nên bấm VI
     luôn trả về đúng từng chữ ban đầu.

     VÌ SAO data-i18n-html LÀ THUỘC TÍNH RIÊNG, KHÔNG SỬA data-i18n SẴN CÓ:
     đang có đúng 2 phần tử vừa mang data-i18n vừa có thẻ con — <span> trong
     .brand (giữ <small>) và <p class="hero-dong-bo"> (giữ chấm .cham). Cả hai
     CỐ Ý chỉ đổi phần chữ trực tiếp; đổi mặc định thành "có thẻ con thì ghi đè
     innerHTML" là mất <small> và mất chấm xanh. Hành vi mới vì vậy phải CHỌN
     THAM GIA. Một phần tử KHÔNG được mang đồng thời hai thuộc tính này.
     ================================================================== */

  /** Lấy phần CHỮ TRỰC TIẾP của thẻ (bỏ qua thẻ con như <small>, <svg>, <strong>) */
  function nutChu(el) {
    for (var i = 0; i < el.childNodes.length; i++) {
      var n = el.childNodes[i];
      if (n.nodeType === 3 && n.nodeValue.trim()) return n;
    }
    return null;
  }

  /** Có thẻ con thì chỉ đổi phần chữ trực tiếp, giữ nguyên mọi thẻ con. */
  function datChu(el, chu) {
    if (/<[a-z]/i.test(chu)) { el.innerHTML = chu; return; }
    var n = nutChu(el);
    if (n) n.nodeValue = chu;
    else el.textContent = chu;
  }

  function layChu(el) {
    var n = nutChu(el);
    return n ? n.nodeValue : el.innerHTML;
  }

  /* Chữ trong <h1> có "tháng MM/YYYY" do scripts/cap-nhat-so-can.mjs tự sửa mỗi
     tháng, nên bản dịch KHÔNG được ghi cứng "August 2026": đọc tháng/năm ra từ
     chính chữ tiếng Việt đang hiển thị rồi ghép vào mẫu {THANG} {NAM}. */
  function ghepThangNam(mau, viGoc) {
    var m = String(viGoc).match(/tháng\s*(\d{1,2})\s*\/\s*(\d{4})/i);
    var d = new Date();
    var thang = m ? Number(m[1]) : d.getMonth() + 1;
    var nam = m ? m[2] : String(d.getFullYear());
    var chuThang = (MA === "en" && thang >= 1 && thang <= 12)
      ? THANG_EN[thang - 1]
      : String(thang);
    return mau.replace("{THANG}", chuThang).replace("{NAM}", nam);
  }

  /* Khoá nào cần xử lý thêm sau khi tra từ điển */
  var XU_LY_THEM = {
    "hero.h1": ghepThangNam
  };

  function ghiNhoGoc(el) {
    if (el.hasAttribute("data-i18n") && el.dataset.viGoc === undefined) {
      el.dataset.viGoc = layChu(el);
    }
    /* data-i18n-html: bản dịch thay CẢ innerHTML nên phải ghi nhớ nguyên khối,
       khác data-i18n (chỉ nhớ nút chữ trực tiếp). Nhờ vậy bấm VI trả lại
       nguyên văn kèm đủ <strong> và <a href> bên trong. */
    if (el.hasAttribute("data-i18n-html") && el.dataset.viHtml === undefined) {
      el.dataset.viHtml = el.innerHTML;
    }
    if (el.hasAttribute("data-i18n-ph") && el.dataset.viPh === undefined) {
      el.dataset.viPh = el.getAttribute("placeholder") || "";
    }
    if (el.hasAttribute("data-i18n-al") && el.dataset.viAl === undefined) {
      el.dataset.viAl = el.getAttribute("aria-label") || "";
    }
  }

  function dichMot(el) {
    ghiNhoGoc(el);

    var khoa = el.getAttribute("data-i18n");
    if (khoa) {
      var goc = el.dataset.viGoc;
      var chu = tra(khoa, goc);
      if (MA !== "vi" && XU_LY_THEM[khoa] && chu !== goc) chu = XU_LY_THEM[khoa](chu, goc);
      datChu(el, chu);
    }
    var khoaHtml = el.getAttribute("data-i18n-html");
    if (khoaHtml) el.innerHTML = tra(khoaHtml, el.dataset.viHtml);

    var khoaPh = el.getAttribute("data-i18n-ph");
    if (khoaPh) el.setAttribute("placeholder", tra(khoaPh, el.dataset.viPh));

    var khoaAl = el.getAttribute("data-i18n-al");
    if (khoaAl) el.setAttribute("aria-label", tra(khoaAl, el.dataset.viAl));
  }

  var BO_CHON = "[data-i18n],[data-i18n-html],[data-i18n-ph],[data-i18n-al]";

  /**
   * Dịch (hoặc trả về tiếng Việt) toàn bộ chữ tĩnh trong một vùng.
   * gallery.js và app-shell.js gọi hàm này ngay sau khi dựng xong phần tử của
   * mình: chúng dựng bằng CHỮ TIẾNG VIỆT + data-i18n, nên thiếu file này thì
   * hai file đó vẫn hiện đúng tiếng Việt như hôm nay.
   */
  function apDung(goc) {
    var vung = goc || document;
    if (vung.nodeType === 1 && vung.matches && vung.matches(BO_CHON)) dichMot(vung);
    var cac = vung.querySelectorAll(BO_CHON);
    for (var i = 0; i < cac.length; i++) dichMot(cac[i]);
  }
  window.NGON_NGU_APDUNG = apDung;

  /* ==================================================================
     6. CHỌN NGÔN NGỮ
     ================================================================== */

  var HOP_LE = { vi: 1, en: 1, ko: 1, zh: 1 };

  function docNho() {
    try { return window.localStorage.getItem(KHOA_NHO); } catch (e) { return null; }
  }
  function ghiNho(ma) {
    try { window.localStorage.setItem(KHOA_NHO, ma); } catch (e) { /* trình duyệt chặn -> chỉ nhớ trong phiên */ }
  }

  /** ?lang=en / ?lang=ko trên URL được ưu tiên cao hơn lựa chọn đã nhớ. */
  function maTuUrl() {
    try {
      var m = new URLSearchParams(location.search).get("lang");
      m = m ? String(m).trim().toLowerCase() : "";
      return HOP_LE[m] ? m : "";
    } catch (e) { return ""; }
  }

  function veNutDangChon() {
    var nut = document.querySelectorAll(".doi-tieng button[data-lang]");
    for (var i = 0; i < nut.length; i++) {
      nut[i].setAttribute("aria-pressed", nut[i].getAttribute("data-lang") === MA ? "true" : "false");
    }
  }

  /**
   * Đổi ngôn ngữ hiển thị.
   * KHÔNG đụng <title>, meta, canonical hay JSON-LD — chỉ chữ trên màn hình.
   */
  function dat(ma, coNho) {
    if (!HOP_LE[ma]) ma = "vi";
    MA = ma;
    document.documentElement.lang = ma === "zh" ? "zh-CN" : ma;
    if (coNho) ghiNho(ma);
    apDung(document);
    veNutDangChon();
    document.dispatchEvent(new CustomEvent("ngonngu:doi", { detail: { ma: ma } }));
  }
  window.NGON_NGU_DAT = function (ma) { dat(ma, true); };

  function damBaoNutTrung() {
    var khung = document.querySelectorAll(".doi-tieng");
    for (var i = 0; i < khung.length; i++) {
      if (khung[i].querySelector('button[data-lang="zh"]')) continue;
      var b = document.createElement("button");
      b.type = "button"; b.setAttribute("data-lang", "zh");
      b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", "简体中文");
      b.title = "简体中文"; b.textContent = "中";
      khung[i].appendChild(b);
      khung[i].setAttribute("aria-label", "Language / 언어 / 语言");
    }
  }

  function ganNut() {
    var khung = document.querySelector(".doi-tieng");
    if (!khung) return;
    khung.addEventListener("click", function (e) {
      var nut = e.target.closest ? e.target.closest("button[data-lang]") : null;
      if (!nut) return;
      var ma = nut.getAttribute("data-lang");
      if (!HOP_LE[ma] || ma === MA) return;
      dat(ma, true);
      /* Chỉ THÊM MỚI một sự kiện. Khối gtag('config', 'G-VF9KHC5TWD') ở đầu
         index.html giữ nguyên tuyệt đối. */
      try {
        if (typeof window.gtag === "function") {
          window.gtag("event", "doi_ngon_ngu", { ngon_ngu: ma });
        }
      } catch (e2) { /* im lặng — đo lường hỏng không được ảnh hưởng người dùng */ }
    });
  }

  function khoiDong() {
    /* Ghi nhớ bản tiếng Việt gốc TRƯỚC khi dịch lần đầu, kể cả khi vào thẳng
       ?lang=en — có vậy bấm VI mới trả về đúng từng chữ ban đầu. */
    var cac = document.querySelectorAll(BO_CHON);
    for (var i = 0; i < cac.length; i++) ghiNhoGoc(cac[i]);

    damBaoNutTrung();
    ganNut();
    var ma = maTuUrl() || docNho() || "vi";
    dat(ma, ma !== "vi");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", khoiDong);
  } else {
    khoiDong();
  }
})();
