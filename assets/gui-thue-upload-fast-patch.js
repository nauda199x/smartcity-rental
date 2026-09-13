/* Tăng tốc video /gui-thue/ mà không thay luồng ảnh hiện tại.
   1) Upload video thẳng tới direct Storage hostname của Supabase.
   2) Bắt đầu upload ngay sau khi chọn video, trong lúc chủ nhà vẫn điền form.
   Khi bấm Gửi căn, luồng cũ chỉ phải chờ phần video còn lại (nếu có). */
(function () {
  "use strict";
  if (location.pathname.replace(/\/+$/, "") !== "/gui-thue") return;

  var PROJECT_ID = "owwqrgwezuwonwdzphie";
  var GATEWAY = "https://" + PROJECT_ID + ".supabase.co/storage/v1/object/";
  var DIRECT = "https://" + PROJECT_ID + ".storage.supabase.co/storage/v1/object/";
  var BUCKET = "timthuesmartcity-owner-videos";

  /* Supabase khuyến nghị direct storage hostname cho file lớn để bỏ bớt lớp gateway. */
  var openGoc = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    var args = Array.prototype.slice.call(arguments);
    if (String(method || "").toUpperCase() === "POST" &&
        typeof url === "string" &&
        url.indexOf(GATEWAY + BUCKET + "/") === 0) {
      args[1] = url.replace(GATEWAY, DIRECT);
    }
    return openGoc.apply(this, args);
  };

  var dangKhoiDong = false;
  var lanCuoi = 0;

  function coVideo() {
    return !!document.querySelector("#luoiAnh [data-owner-video]");
  }

  function taiNenNgay() {
    /* Chống MutationObserver/change gọi dồn nhiều lần. */
    var now = Date.now();
    if (dangKhoiDong || now - lanCuoi < 700 || !coVideo() || !window.fetch) return;
    lanCuoi = now;
    dangKhoiDong = true;

    /* app-shell video cũ đã patch fetch: action chuNhaGuiCan sẽ kích hoạt taiTatCaVideo().
       Request mồi này chỉ dùng để bắt đầu upload sớm; lỗi HTTP sau đó không ảnh hưởng form. */
    fetch("/robots.txt?video-preupload=1", {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ action: "chuNhaGuiCan", videoPreuploadOnly: true })
    }).catch(function () {
      /* Nếu mạng chập chờn, lần bấm Gửi căn thật sẽ tự thử lại. */
    }).finally(function () {
      dangKhoiDong = false;
    });
  }

  document.addEventListener("change", function (e) {
    if (!e.target || e.target.id !== "chonAnh") return;
    setTimeout(taiNenNgay, 80);
  }, false);

  var luoi = document.getElementById("luoiAnh");
  if (luoi && window.MutationObserver) {
    new MutationObserver(function () {
      if (coVideo()) setTimeout(taiNenNgay, 40);
    }).observe(luoi, { childList: true });
  }

  function suaChu() {
    var lead = document.querySelector(".gui-photo-lead span");
    if (lead) lead.textContent = "Video sẽ tự tải nền ngay khi chọn để giảm thời gian chờ lúc gửi căn.";
    var safe = document.querySelector('[data-step="2"] .gui-safe');
    if (safe) safe.textContent = "Có thể bấm Tiếp tục ngay; video vẫn tải nền trong lúc anh/chị điền liên hệ.";
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", suaChu, { once: true });
  else suaChu();
})();
