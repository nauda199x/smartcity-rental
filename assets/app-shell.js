/* SEO guard 06/09/2026 + loader cho app-shell gốc.
   URL filter chỉ phục vụ UX; landing SEO dùng URL sạch (/studio/, /masteri/...).
   Không chặn robots.txt để Google vẫn crawl được URL cũ và đọc noindex. */
(function () {
  "use strict";

  try {
    if (location.search) {
      var p = new URLSearchParams(location.search);
      var khoaLoc = ["loai", "pk", "gia", "q", "noi_that", "noithat", "interior", "price", "type", "phankhu", "page", "sort"];
      var laUrlLoc = khoaLoc.some(function (k) { return p.has(k); });
      if (laUrlLoc) {
        var robots = document.querySelector('meta[name="robots"]');
        if (!robots) {
          robots = document.createElement("meta");
          robots.setAttribute("name", "robots");
          document.head.appendChild(robots);
        }
        robots.setAttribute("content", "noindex,follow,max-image-preview:large");
      }
    }
  } catch (e) { /* SEO guard hỏng không được ảnh hưởng UX */ }

  var s = document.createElement("script");
  s.src = "/assets/app-shell-core.js?v=20260906-seo1";
  s.async = false;
  document.head.appendChild(s);
})();
