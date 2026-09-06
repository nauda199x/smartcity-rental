/* SEO guard 06/09/2026 + loader cho app-shell gốc.
   URL filter chỉ phục vụ UX; landing SEO dùng URL sạch (/studio/, /masteri/...).
   Không chặn robots.txt để Google vẫn crawl được URL cũ và đọc noindex. */
(function () {
  "use strict";

  var khoaLoc = ["loai", "pk", "gia", "q", "noi_that", "noithat", "interior", "price", "type", "phankhu", "page", "sort"];

  function coThamSoLoc(search) {
    if (!search) return false;
    var p = new URLSearchParams(search);
    return khoaLoc.some(function (k) { return p.has(k); });
  }

  try {
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
  } catch (e) { /* SEO guard hỏng không được ảnh hưởng UX */ }

  /* Một số bài cũ có deep-link dạng /?pk=masteri&q=MasA để mở đúng bộ lọc.
     Giữ nguyên trải nghiệm click cho người dùng, nhưng gắn nofollow để không
     tiếp tục truyền tín hiệu SEO/crawl vào các biến thể tham số này. */
  function danhDauLinkLoc() {
    document.querySelectorAll('a[href]').forEach(function (a) {
      try {
        var u = new URL(a.getAttribute("href"), location.href);
        if (u.origin !== location.origin || !coThamSoLoc(u.search)) return;
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
  s.src = "/assets/app-shell-core.js?v=20260906-seo2";
  s.async = false;
  document.head.appendChild(s);
})();
