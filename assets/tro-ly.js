/* Trợ lý tìm căn V2 — loader. Giữ đường dẫn /assets/tro-ly.js để không phải sửa HTML. */
(function () {
  "use strict";
  var files = [
    "/assets/tro-ly-v2-i18n.js?v=20260915-1",
    "/assets/tro-ly-v2-engine.js?v=20260915-1",
    "/assets/tro-ly-v2-base.js?v=20260915-1",
    "/assets/tro-ly-v2-flow.js?v=20260915-1"
  ];
  function load(i) {
    if (i >= files.length) return;
    var s = document.createElement("script");
    s.src = files[i];
    s.async = false;
    s.onload = function () { load(i + 1); };
    s.onerror = function () { console.error("Không tải được module trợ lý V2:", files[i]); };
    document.head.appendChild(s);
  }
  load(0);
})();
