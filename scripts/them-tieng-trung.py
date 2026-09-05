#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "assets/ngon-ngu.js"
DETAIL = ROOT / "assets/can-ho-detail-i18n.js"
INDEX = ROOT / "index.html"

ZH = {
  "nav.brand":"Smart City 公寓出租","nav.brandSub":"智能筛选 • 每日更新","nav.home":"首页","nav.rent":"出租房源","nav.zone":"分区","nav.type":"户型","nav.price":"租金","nav.guideShort":"租房指南","nav.consignShort":"发布房源","nav.moveIn":"可立即入住","nav.guide":"租房指南","nav.consign":"发布出租房源","nav.zalo":"Zalo 咨询","nav.main":"主导航",
  "search.ph":"按分区、房源编号或户型搜索（如 Sapphire、2居、800万）","search.al":"按分区、房源编号、户型或价格搜索公寓","search.suggest":"快捷推荐","search.phShort":"Sapphire、2居、800万、房源编号…","qb.search":"前往搜索框","qb.filter":"打开全部筛选",
  "bar.new1":"✨ 今日新增：","bar.new2":"套新房源 — 点击查看","hero.h1":"Vinhomes Smart City 公寓出租 — {NAM}年{THANG}月","hero.p":"智能筛选租金、户型和家具配置。真实房源持续同步，几分钟内找到合适的公寓。","hero.sync":"房源每30分钟自动同步","hero.total":"全部房源","hero.ready":"可立即入住","hero.zone":"分区","hero.statsAl":"房源概览",
  "f.type":"户型","f.typeAll":"全部户型","f.zone":"分区","f.zoneAll":"全部分区","f.zonePick":"选择楼栋或分区","f.price":"价格区间","f.priceAll":"全部价格","f.pricePick":"选择价格区间","f.furn":"家具配置","f.furnAll":"全部配置","f.furnPick":"选择家具配置","f.find":"搜索","f.clear":"清除筛选","f.clearShort":"清除","f.remove":"移除筛选","f.view":"查看","f.unit":"套","f.tapHere":"点击快速筛选匹配房源","f.filterNow":"立即筛选","f.byZoneBed":"按分区、卧室和租金筛选","f.panelAl":"公寓筛选","f.bedStruct":"卧室户型","f.monthly":"月租区间","f.openAl":"打开筛选查找公寓","f.allRooms":"全部户型","f.all":"全部","f.under75":"750万越南盾以下","f.75to10":"750万–1000万越南盾","f.10to12":"1000万–1200万越南盾","f.12to15":"1200万–1500万越南盾","f.over15":"1500万越南盾以上","f.furnFull":"家具家电齐全","f.furnBasic":"基础家具","f.furnNone":"无家具","f.close":"关闭",
  "f.typeStudio":"Studio","f.type1pn":"1居室","f.type1pnp":"1居室+","f.type2pn":"2居室","f.type2pnp":"2居室+","f.type3pn":"3居室","f.sAll":"全部","f.sStudio":"Studio","f.s1pn":"1居","f.s1pnp":"1居+","f.s2pn":"2居","f.s2pnp":"2居+","f.s3pn":"3居","f.sUnder75":"<750万","f.s75to10":"750–1000万","f.s10to12":"1000–1200万","f.s12to15":"1200–1500万","f.sOver15":">1500万","f.sFurnFull":"全配","f.sFurnBasic":"基础","f.sFurnNone":"无家具",
  "l.loading":"正在加载房源…","l.wait":"请稍候…","l.sortAl":"房源排序","l.random":"推荐","l.priceAsc":"价格：从低到高","l.priceDesc":"价格：从高到低","l.onlyNew":"✨ 仅看新房源和最近更新","l.badgeNew":"✨ 新房源","l.badgeNow":"可立即入住","l.badgeFrom":"{NGAY} 起可入住","l.furnUpd":"家具信息更新中","l.photos":"{N} 张照片","l.code":"房源编号：","l.detail":"查看详情","l.perMonth":"/月","l.contact":"咨询价格","l.galleryAl":"查看公寓照片","l.pageAl":"房源分页","l.prev":"上一页","l.next":"下一页","l.filtering":"当前筛选：","l.noneNew":"最近3天暂无新房源或更新房源，请查看全部房源。","l.noneMatch":"目前没有符合这些条件的公寓。留下需求，我们会帮您寻找合适房源并尽快联系。","l.loadErr":"无法加载房源","l.h2":"目前有 <strong>{N}</strong> 套公寓可出租","l.ask":"咨询此房源","l.imgUpd":"照片更新中","l.noPhoto":"此房源暂时没有照片","l.noPhotoCta":"通过 Zalo 获取实拍照片","l.photosTitle":"公寓照片","l.photoAlt":"公寓照片",
  "cta.mid.h":"不用把所有房源都看一遍","cta.mid.p":"告诉我们预算和入住时间，我们会挑选3–5套最合适的房源发给您。","cta.mid.btn":"帮我找合适房源",
  "lead.title":"还没找到合适的房子？","lead.desc":"留下您的需求，我们帮您寻找并尽快联系。","lead.btn":"请帮我找房","lead.mTitle":"您想找什么样的房子？","lead.mDesc":"留下信息，我们会寻找合适公寓并尽快联系您。","lead.name":"姓名 *","lead.namePh":"例如：王先生","lead.phone":"电话号码 *","lead.type":"户型","lead.typeAny":"还不确定 — 请推荐","lead.budget":"预算","lead.budgetAny":"暂未确定","lead.b1":"650万–750万越南盾","lead.b2":"750万–1000万越南盾","lead.b3":"1000万–1200万越南盾","lead.b4":"1200万–1500万越南盾","lead.b5":"1500万越南盾以上","lead.moveIn":"入住日期","lead.area":"希望的分区 / 楼栋","lead.areaPh":"例如：Sa2、靠近湖边…","lead.note":"补充说明","lead.notePh":"其他需求（入住人数、宠物、景观等）","lead.send":"提交需求","lead.sending":"正在提交…","lead.ok":"已收到您的需求","lead.okDesc":"我们会尽快联系您，谢谢！","lead.errName":"请输入姓名和电话号码。","lead.errPhone":"电话号码格式似乎不正确，请检查。","lead.errSend":"提交失败，请重试或通过 Zalo 联系我们。","lead.errNet":"无法提交需求，请重试或通过 Zalo 联系我们。",
  "market.eyebrow":"实时房源数据","market.title":"Vinhomes Smart City 当前租金","market.desc":"直接根据网站当前展示的真实房源统计。房源数量和价格区间会随实时库存更新，而不是固定广告价格。","market.full":"查看详细租金表 →","market.byType":"按户型","market.byZone":"按分区","market.colType":"户型","market.colZone":"分区","market.colCount":"可租房源","market.colPrice":"租金区间","market.unit":"套","market.hot":"热门：","market.hotAl":"热门租房主题",
  "idx.title":"Vinhomes Smart City 租房目录","idx.desc":"所有公寓按户型、分区、价格和家具配置整理。选择分类可查看真实租金的完整列表。部分专题页目前为越南语。","idx.byType":"按户型","idx.byZone":"按分区","idx.byPrice":"按价格","idx.byFurn":"按家具配置","idx.byTower":"按楼栋","idx.al":"租房目录索引",
  "idx.t1":"Studio 出租","idx.t2":"1居室出租","idx.t3":"1居室+ 出租","idx.t4":"2居室出租","idx.t5":"2居室+ 出租","idx.t6":"3居室出租","idx.g1":"700万越南盾以下 Studio","idx.g2":"700万–1000万越南盾 Studio","idx.g3":"1000万越南盾以下 1居+","idx.g4":"1000万越南盾以下 2居","idx.g5":"1000万–1200万越南盾 2居","idx.g6":"1200万–1500万越南盾 2居+","idx.g7":"1200万–1500万越南盾 3居","idx.n1":"全配 Studio","idx.n2":"全配 1居+","idx.n3":"全配 2居","idx.n4":"全配 3居","idx.w1":"S4.01 楼栋公寓","idx.b1":"各分区租金表","idx.b2":"各分区服务费","idx.b3":"Studio 租金详情","idx.b4":"社区配套","idx.b5":"租房经验","idx.b6":"停车、宠物和服务费","idx.b7":"各分区租金对比","idx.b8":"租赁流程和手续","idx.b9":"Vinschool 附近公寓",
  "disc.title":"按户型浏览","disc.desc":"每种户型都有完整房源、各分区真实价格和租房建议。（部分页面为越南语）","disc.studio":"开放式，适合1–2人","disc.1pn":"独立卧室","disc.1pnp":"额外空间，可放第二张床","disc.2pn":"房源数量最多","disc.2pnp":"边户，更大更明亮","disc.3pn":"适合大家庭","faq.title":"常见问题","own.title":"您有公寓要出租吗？","own.desc":"把房源信息和照片发给我们，我们帮您发布并寻找租客。免费，无需注册。","own.btn":"房东发布房源 →","ft.copy":"© 2026 Smart City 公寓出租","ft.owner":"房东发布房源","ft.privacy":"隐私政策","ft.zones":"当前可租分区：","ft.follow":"关注我们，查看每日新房源","ft.call":"电话","ft.allPosts":"查看全部文章 →","ft.fb":"关注 Facebook","ft.tt":"关注 TikTok","ft.yt":"关注 YouTube","ft.ig":"关注 Instagram",
  "seo.h2":"Smart City 租房 — Vinhomes Smart City 公寓出租","seo.p1":"<strong>Smart City 公寓出租</strong>汇集 Vinhomes Smart City（河内 Tây Mỗ）的可租公寓，房源每天自动同步多次，及时更新空置情况、租金和实拍照片。户型包括 Studio、1居、2居和3居，覆盖 Sapphire、Miami、Sakura、Masteri West Heights、Imperia、Lumière、Canopy 和 Tonkin 等分区。","seo.p2":"目前 <strong>Smart City 公寓</strong>租金大约从 Studio 每月550万越南盾起，具体取决于面积、分区和家具配置。可查看<a href=\"/bang-gia-thue-vinhomes-smart-city.html\">各分区租金表</a>（越南语），或使用上方筛选按预算和户型查找。","seo.p3":"每条 <strong>Vinhomes Smart City 出租房源</strong>都会标明租金、面积和家具配置（全配 / 基础 / 无家具）。可按<a href=\"#mucLucKhoDuLieu\">分类</a>浏览，然后通过 Zalo 联系我们预约实地看房。",
  "notice.vn":"首页和房源详情支持简体中文。其他专题页目前主要为越南语，如需帮助请通过 Zalo 联系我们。",
  "g.open":"查看公寓照片","g.close":"关闭","g.prev":"上一张照片","g.next":"下一张照片",
  "sh.guide":"指南","sh.contact":"联系","sh.zalo":"Zalo","sh.call":"电话","sh.priceLookup":"租金指南","sh.priceTable":"各分区租金表","sh.priceCompare":"各分区租金对比","sh.priceStudio":"Studio 租金","sh.before":"租房前须知","sh.guideFull":"租房指南","sh.exp":"Smart City 租房经验","sh.amen":"社区配套","sh.fees":"服务费、停车、宠物","sh.other":"其他","sh.cat":"按分区查看房源","sh.privacy":"隐私政策","sh.close":"关闭","sh.home":"首页","sh.consign":"发布出租","sh.menu":"菜单","sh.rent":"出租","sh.price":"租金","sh.findRent":"找公寓","sh.allRent":"全部可租公寓","sh.zones":"分区","sh.priceGuide":"租金与指南","sh.navAl":"快捷导航",
  "zl.copied":"消息已复制","zl.copiedHow":"在 Zalo 聊天框长按1秒，选择 <b>Dán</b>（粘贴）后发送","zl.copyFail":"设备阻止了复制","zl.copyFailHow":"请复制下面这段文字并粘贴到 Zalo：",
  "faq.q1":"Vinhomes Smart City 公寓租金大约多少？","faq.a1":"租金因房源而异。Studio 通常每月约650万越南盾起，2–3居可超过1500万越南盾，具体取决于面积、楼栋和家具配置。可使用上方价格筛选查看符合预算的房源。","faq.q2":"Vinhomes Smart City 在哪里？","faq.a2":"Vinhomes Smart City 位于河内 Tây Mỗ，是河内西部大型智慧社区之一。","faq.q3":"Vinhomes Smart City 有哪些出租户型？","faq.a3":"有 Studio、1居、1居+、2居、2居+ 和3居，分布在多个楼栋，适合单身、情侣和家庭。","faq.q4":"出租公寓带家具吗？","faq.a4":"每套房不同。房源会清楚标注家具家电齐全、基础家具或无家具，也可以直接按家具配置筛选。","faq.q5":"如何看房或联系？","faq.a5":"点击任意房源的“咨询此房源”即可通过 Zalo 联系，或拨打/添加 Zalo 0977923284 预约看房。","faq.q6":"房源信息会及时更新吗？","faq.a6":"数据每天自动同步多次，让空置状态、租金和照片尽量反映真实情况。"
}

DETAIL_ZH = {
  "brand":"Smart City 公寓出租","brandSub":"实拍照片 · 每日更新","nav.all":"全部房源","nav.studio":"Studio","nav.1p":"1居+","nav.2":"2居","nav.3":"3居","nav.guide":"租房指南","bc.home":"首页",
  "title.active":"Vinhomes Smart City 出租：{TYPE}，{AREA}，{TOWER}楼","title.rented":"{TYPE}，{AREA}，{TOWER}楼 — 已出租","lead.active":"Vinhomes Smart City {ZONE} {TOWER}楼，{TYPE}，{AREA}。{FURN}。租金 {PRICE}。更新于 {DATE}。","rented.note1":"这套公寓已经出租。","rented.note2":"下面是目前仍可出租的相似房源。",
  "table.code":"房源编号","table.type":"户型","table.area":"面积","table.tower":"楼栋","table.zone":"分区","table.furn":"家具配置","table.price":"月租","table.move":"入住时间","table.updated":"更新时间","stat.area":"面积","stat.price":"月租","stat.furn":"家具配置","stat.status":"入住状态","status.now":"可立即入住","status.from":"{DATE} 起可入住","status.liveNow":"可立即入住","price.contact":"咨询价格","aside.price":"月租","aside.type":"户型","aside.area":"面积","aside.tower":"楼栋","aside.furn":"家具配置","action.book":"预约看房","action.zalo":"Zalo 咨询","action.call":"电话 0977 923 284","action.callShort":"电话","action.bookShort":"预约看房","aside.code":"房源编号：{CODE}","aside.note":"房源详情与网站当前可租库存同步。","gallery.all":"查看全部 {N} 张照片","gallery.count":"{I}/{N} 张照片","gallery.open":"打开第 {I}/{N} 张照片","gallery.none1":"照片更新中","gallery.none2":"通过 Zalo 获取实拍照片和视频。","toast":"看房消息已复制，请打开 Zalo 粘贴后发送。","h.more":"按需求继续浏览","h.similar":"相似房源","h.availableSimilar":"仍可出租的相似房源","empty.similar":"目前没有相似空置房源，请查看全部出租公寓。","cta.ask":"通过 Zalo 咨询房源 {CODE}","cta.call":"拨打 {PHONE}","mobile.available":"查看可租房源","footer.find":"找公寓","footer.guide":"租房指南","footer.owner":"发布房源","footer.privacy":"隐私政策","zalo.float":"Zalo 咨询"
}

ENUM_ZH = {
  "studio":"Studio","1 ngủ":"1居室","1 ngủ +":"1居室+","2 ngủ":"2居室","2 ngủ +":"2居室+","3 ngủ":"3居室","full nội thất":"家具家电齐全","đồ cơ bản":"基础家具","nhà nguyên bản":"无家具"
}

def js_obj(name, data):
    return "\n  var %s = %s;\n" % (name, json.dumps(data, ensure_ascii=False, separators=(",", ":")))

def patch_home():
    s = HOME.read_text(encoding="utf-8")
    if "var TU_DIEN_ZH =" not in s:
        marker = "  var DU_LIEU = {"
        s = s.replace(marker, js_obj("TU_DIEN_ZH", ZH) + "\n" + marker, 1)
    if "var DU_LIEU_ZH =" not in s:
        marker = "  /** Dịch một giá trị enum lúc IN RA MÀN HÌNH. Không khớp bảng -> giữ nguyên. */"
        s = s.replace(marker, js_obj("DU_LIEU_ZH", ENUM_ZH) + "\n" + marker, 1)

    s = s.replace('var MA = "vi";                 // mã ngôn ngữ đang hiển thị: vi | en | ko', 'var MA = "vi";                 // mã ngôn ngữ đang hiển thị: vi | en | ko | zh')
    old = '    var chu = MA === "en" ? muc[0] : muc[1];\n    return (chu === undefined || chu === null || chu === "") ? macDinh : chu;'
    new = '    if (MA === "zh") {\n      var zh = TU_DIEN_ZH[khoa];\n      return (zh === undefined || zh === null || zh === "") ? macDinh : zh;\n    }\n    var chu = MA === "en" ? muc[0] : muc[1];\n    return (chu === undefined || chu === null || chu === "") ? macDinh : chu;'
    s = s.replace(old, new, 1)

    s = s.replace('  var HOP_LE = { vi: 1, en: 1, ko: 1 };', '  var HOP_LE = { vi: 1, en: 1, ko: 1, zh: 1 };')
    s = s.replace('    document.documentElement.lang = ma;', '    document.documentElement.lang = ma === "zh" ? "zh-CN" : ma;')

    old = '    return (MA === "en" ? muc[0] : muc[1]) || goc;'
    new = '    if (MA === "zh") return DU_LIEU_ZH[goc.trim().toLowerCase()] || goc;\n    return (MA === "en" ? muc[0] : muc[1]) || goc;'
    s = s.replace(old, new, 1)

    old = '    if (MA === "en") {\n      return (so / 1000000).toFixed(1).replace(/\\.0$/, "") + "M VND";\n    }\n    return ngancachNghin(Math.round(so / 10000)) + "만 동";'
    new = '    if (MA === "en") {\n      return (so / 1000000).toFixed(1).replace(/\\.0$/, "") + "M VND";\n    }\n    if (MA === "zh") return ngancachNghin(Math.round(so / 10000)) + "万越南盾";\n    return ngancachNghin(Math.round(so / 10000)) + "만 동";'
    s = s.replace(old, new, 1)

    old = '    if (MA === "en") return ngay + " " + THANG_EN[thang - 1] + " " + nam;\n    return nam + "년 " + thang + "월 " + ngay + "일";'
    new = '    if (MA === "en") return ngay + " " + THANG_EN[thang - 1] + " " + nam;\n    if (MA === "zh") return nam + "年" + thang + "月" + ngay + "日";\n    return nam + "년 " + thang + "월 " + ngay + "일";'
    s = s.replace(old, new, 1)

    if "function damBaoNutTrung" not in s:
        marker = '  function ganNut() {'
        add = '''  function damBaoNutTrung() {\n    var khung = document.querySelectorAll(".doi-tieng");\n    for (var i = 0; i < khung.length; i++) {\n      if (khung[i].querySelector('button[data-lang="zh"]')) continue;\n      var b = document.createElement("button");\n      b.type = "button"; b.setAttribute("data-lang", "zh");\n      b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", "简体中文");\n      b.title = "简体中文"; b.textContent = "中";\n      khung[i].appendChild(b);\n      khung[i].setAttribute("aria-label", "Language / 언어 / 语言");\n    }\n  }\n\n'''
        s = s.replace(marker, add + marker, 1)
    s = s.replace('    ganNut();\n    var ma = maTuUrl()', '    damBaoNutTrung();\n    ganNut();\n    var ma = maTuUrl()', 1)
    HOME.write_text(s, encoding="utf-8")

def patch_detail():
    s = DETAIL.read_text(encoding="utf-8")
    if "var TU_ZH =" not in s:
        marker = '  function q(s, r) {'
        s = s.replace(marker, js_obj("TU_ZH", DETAIL_ZH) + "\n" + marker, 1)
    old = '    var muc = TU[k];\n    if (!muc) return thay(vi, bien);\n    return thay(m === "en" ? muc[0] : muc[1], bien);'
    new = '    var muc = TU[k];\n    if (m === "zh") return thay(TU_ZH[k] || vi, bien);\n    if (!muc) return thay(vi, bien);\n    return thay(m === "en" ? muc[0] : muc[1], bien);'
    s = s.replace(old, new, 1)
    s = s.replace('    return base + (ma() === "en" ? "/month" : "/월");', '    return base + (ma() === "en" ? "/month" : ma() === "zh" ? "/月" : "/월");', 1)
    s = s.replace('VI / EN / KO cho trang chi tiết căn hộ', 'VI / EN / KO / ZH cho trang chi tiết căn hộ')
    DETAIL.write_text(s, encoding="utf-8")

def patch_index():
    s = INDEX.read_text(encoding="utf-8")
    s = s.replace('availableLanguage\": [\"vi\", \"en\", \"ko\"]', 'availableLanguage\": [\"vi\", \"en\", \"ko\", \"zh-CN\"]')
    s = s.replace('availableLanguage": ["vi", "en", "ko"]', 'availableLanguage": ["vi", "en", "ko", "zh-CN"]')
    INDEX.write_text(s, encoding="utf-8")

patch_home()
patch_detail()
patch_index()
print("Simplified Chinese UI patch applied.")
