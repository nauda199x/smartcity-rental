/* SEO guard 06/09/2026 + loader cho app-shell gốc.
   URL filter chỉ phục vụ UX; landing SEO dùng URL sạch (/studio/, /masteri/...).
   Không chặn robots.txt để Google vẫn crawl được URL cũ và đọc noindex. */
(function () {
  "use strict";

  var khoaLoc = ["loai", "pk", "gia", "q", "noi_that", "noithat", "interior", "price", "type", "phankhu", "page", "sort"];
  var loaiSach = {
    "studio": "Studio",
    "1pn": "1 Ngủ",
    "1pn-plus": "1 Ngủ +",
    "2pn": "2 Ngủ",
    "2pn-plus": "2 Ngủ +",
    "3pn": "3 Ngủ"
  };
  var phanKhuSach = {
    "sapphire": "Sapphire",
    "masteri": "Masteri",
    "miami": "Miami",
    "sakura": "Sakura",
    "imperia": "Imperia",
    "lumiere": "Lumiere",
    "canopy": "Canopy",
    "tonkin": "Tonkin"
  };
  var toaSach = {
    "masteri|masa": "/west-a-masteri-smart-city/",
    "masteri|masb": "/west-b-masteri-smart-city/",
    "masteri|masd": "/west-d-masteri-smart-city/",
    "lumiere|a2": "/a2-lumiere-evergreen/",
    "lumiere|a3": "/a3-lumiere-evergreen/",
    "miami|gs5": "/gs5-the-miami-smart-city/",
    "miami|gs6": "/gs6-the-miami-smart-city/",
    "sakura|sa1": "/sa1-the-sakura-smart-city/",
    "sakura|sa3": "/sa3-the-sakura-smart-city/",
    "sapphire|s101": "/s1-01-vinhomes-smart-city/",
    "sapphire|s202": "/s2-02-vinhomes-smart-city/",
    "sapphire|s303": "/s3-03-vinhomes-smart-city/",
    "sapphire|s401": "/s4-01-vinhomes-smart-city/",
    "canopy|tc1": "/tc1-canopy-smart-city/",
    "imperia|i1": "/i1-imperia-smart-city/"
  };

  function params(search) {
    return new URLSearchParams(search || "");
  }
  function coThamSoLoc(search) {
    if (!search) return false;
    var p = params(search);
    return khoaLoc.some(function (k) { return p.has(k); });
  }
  function chiCo(p, keys) {
    var ds = [];
    p.forEach(function (_v, k) { if (ds.indexOf(k) === -1) ds.push(k); });
    return ds.length === keys.length && ds.every(function (k) { return keys.indexOf(k) !== -1; });
  }
  function slugToaTuQuery(search) {
    var p = params(search);
    if (!chiCo(p, ["pk", "q"])) return "";
    var pk = String(p.get("pk") || "").trim().toLowerCase();
    var q = String(p.get("q") || "").replace(/[\s._-]/g, "").toLowerCase();
    return toaSach[pk + "|" + q] || "";
  }

  try {
    /* Deep-link tòa cũ: chuyển thẳng sang landing tòa sạch nếu đã tồn tại. */
    if (location.pathname === "/" && location.search) {
      var dichToa = slugToaTuQuery(location.search);
      if (dichToa) {
        location.replace(dichToa);
        return;
      }
    }

    /* URL filter đã từng được crawler phát hiện: cho bot vào đọc trang nhưng
       yêu cầu không index; canonical tĩnh của trang chủ vẫn dồn về URL sạch. */
    if (coThamSoLoc(location.search)) {
      var robots = document.querySelector('meta[name="robots"]');
      if (!robots) {
        robots = document.createElement("meta");
        robots.setAttribute("name", "robots");
        document.head.appendChild(robots);
      }
      robots.setAttribute("content", "noindex,follow,max-image-preview:large");
    }

    /* Tổ hợp Loại căn × Phân khu cũ chỉ redirect khi registry hiện tại xác nhận
       đã có landing sạch và indexable. Nếu ít căn/không indexable thì giữ filter
       cho người dùng và meta noindex ở trên sẽ ngăn nó cạnh tranh SEO. */
    if (location.pathname === "/" && location.search) {
      var pTrang = params(location.search);
      if (chiCo(pTrang, ["loai", "pk"])) {
        var loai = loaiSach[String(pTrang.get("loai") || "").toLowerCase()];
        var pk = phanKhuSach[String(pTrang.get("pk") || "").toLowerCase()];
        if (loai && pk && window.fetch) {
          fetch("/seo-phan-khu-loai-can.json?v=20260906-seo3", { cache: "no-store" })
            .then(function (r) { return r.ok ? r.json() : {}; })
            .then(function (registry) {
              Object.keys(registry || {}).some(function (slug) {
                var rec = registry[slug];
                if (rec && rec.indexable && rec.loai === loai && rec.phanKhu === pk) {
                  location.replace("/" + slug.replace(/^\/+|\/+$/g, "") + "/");
                  return true;
                }
                return false;
              });
            })
            .catch(function () { /* noindex vẫn là fallback an toàn */ });
        }
      }
    }
  } catch (e) { /* SEO guard hỏng không được ảnh hưởng UX */ }

  /* Giữ trải nghiệm deep-link bộ lọc, nhưng ưu tiên URL tòa sạch nếu có;
     các query còn lại được nofollow để không tiếp tục truyền tín hiệu SEO. */
  function danhDauLinkLoc() {
    document.querySelectorAll('a[href]').forEach(function (a) {
      try {
        var u = new URL(a.getAttribute("href"), location.href);
        if (u.origin !== location.origin || !coThamSoLoc(u.search)) return;
        var dichToa = u.pathname === "/" ? slugToaTuQuery(u.search) : "";
        if (dichToa) {
          a.setAttribute("href", dichToa);
          return;
        }
        var rel = (a.getAttribute("rel") || "").split(/\s+/).filter(Boolean);
        if (rel.indexOf("nofollow") === -1) rel.push("nofollow");
        a.setAttribute("rel", rel.join(" "));
      } catch (e) { /* bỏ qua href không hợp lệ */ }
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", danhDauLinkLoc, { once: true });
  } else {
    danhDauLinkLoc();
  }

  var s = document.createElement("script");
  s.src = "/assets/app-shell-core.js?v=20260906-seo3";
  s.async = false;
  document.head.appendChild(s);
})();
