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
  var loaiDuong = {
    "studio": "/studio/",
    "1pn": "/1pn/",
    "1pn-plus": "/1pn-plus/",
    "2pn": "/2pn/",
    "2pn-plus": "/2pn-plus/",
    "3pn": "/3pn/"
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
  var phanKhuDuong = {
    "sapphire": "/sapphire/",
    "masteri": "/masteri/",
    "miami": "/miami/",
    "sakura": "/sakura/",
    "imperia": "/imperia/",
    "lumiere": "/lumiere/",
    "canopy": "/canopy/",
    "tonkin": "/tonkin/"
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
  function slugDanhMucTuQuery(search) {
    var p = params(search);
    if (chiCo(p, ["loai"])) {
      return loaiDuong[String(p.get("loai") || "").trim().toLowerCase()] || "";
    }
    if (chiCo(p, ["pk"])) {
      return phanKhuDuong[String(p.get("pk") || "").trim().toLowerCase()] || "";
    }
    return "";
  }
  function slugToaTuQuery(search) {
    var p = params(search);
    if (!chiCo(p, ["pk", "q"])) return "";
    var pk = String(p.get("pk") || "").trim().toLowerCase();
    var q = String(p.get("q") || "").replace(/[\s._-]/g, "").toLowerCase();
    return toaSach[pk + "|" + q] || "";
  }

  try {
    /* Các deep-link cũ có landing sạch tương đương được hợp nhất ngay. */
    if (location.pathname === "/" && location.search) {
      var dichDanhMuc = slugDanhMucTuQuery(location.search);
      if (dichDanhMuc) {
        location.replace(dichDanhMuc);
        return;
      }
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
          fetch("/seo-phan-khu-loai-can.json?v=20260906-seo4", { cache: "no-store" })
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

  /* Giữ trải nghiệm deep-link bộ lọc, nhưng ưu tiên URL sạch nếu có;
     các query còn lại được nofollow để không tiếp tục truyền tín hiệu SEO. */
  function danhDauLinkLoc() {
    document.querySelectorAll('a[href]').forEach(function (a) {
      try {
        var u = new URL(a.getAttribute("href"), location.href);
        if (u.origin !== location.origin || !coThamSoLoc(u.search)) return;
        var dichDanhMuc = u.pathname === "/" ? slugDanhMucTuQuery(u.search) : "";
        if (dichDanhMuc) {
          a.setAttribute("href", dichDanhMuc);
          return;
        }
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
  s.src = "/assets/app-shell-core.js?v=20260906-seo4";
  s.async = false;
  document.head.appendChild(s);
})();

/* /gui-thue/: bổ sung video cho chủ nhà mà không đụng luồng nén/tải ảnh cũ.
   Video đi thẳng lên Storage (không Base64 qua Apps Script) để tránh treo iPhone
   và tránh làm request Apps Script phình lớn. URL video vẫn được gửi kèm hồ sơ. */
(function () {
  "use strict";

  if (location.pathname.replace(/\/+$/, "") !== "/gui-thue") return;

  var SUPABASE_URL = "https://owwqrgwezuwonwdzphie.supabase.co";
  var SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93d3FyZ3dlenV3b253ZHpwaGllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNDUyMTcsImV4cCI6MjEwMzcyMTIxN30.F8OA1tRSN2fv-Alpbe3PHZDE6mvUuU4WU2wkFIBD04Q";
  var VIDEO_BUCKET = "timthuesmartcity-owner-videos";
  var TOI_DA_VIDEO = 2;
  var TOI_DA_MOI_VIDEO = 120 * 1024 * 1024;
  var MIME_VIDEO = ["video/mp4", "video/quicktime", "video/webm"];

  var state = {
    videos: [],
    urls: [],
    uploadPromise: null
  };

  function $(id) { return document.getElementById(id); }

  function thongBaoLoi(text) {
    var hop = $("hopLoi");
    if (hop) {
      hop.textContent = text;
      hop.classList.add("hien");
      try { hop.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (_e) {}
    } else {
      alert(text);
    }
  }

  function dinhDangMB(bytes) {
    return (bytes / 1048576).toFixed(bytes >= 10 * 1048576 ? 0 : 1) + " MB";
  }

  function duoiVideo(file) {
    var type = String(file.type || "").toLowerCase();
    if (type === "video/quicktime") return "mov";
    if (type === "video/webm") return "webm";
    return "mp4";
  }

  function taoId() {
    if (window.crypto && typeof window.crypto.randomUUID === "function") return window.crypto.randomUUID();
    return "v" + Date.now().toString(36) + Math.random().toString(36).slice(2, 12);
  }

  function encodePath(path) {
    return path.split("/").map(encodeURIComponent).join("/");
  }

  function capNhatDemMedia() {
    var dem = $("demAnh");
    var luoi = $("luoiAnh");
    if (!dem || !luoi) return;
    var soAnh = luoi.querySelectorAll(".o-anh:not([data-owner-video]) img").length;
    var soVideo = state.videos.length;
    if (!soAnh && !soVideo) {
      dem.textContent = "Chưa chọn ảnh/video. Có thể bỏ qua bước này và tiếp tục.";
      return;
    }
    var parts = [];
    if (soAnh) parts.push(soAnh + " ảnh");
    if (soVideo) parts.push(soVideo + " video");
    dem.textContent = "Đã chọn " + parts.join(" + ") + ". Ảnh đầu tiên dùng làm ảnh bìa.";
  }

  function dongBoPreviewVideo() {
    var luoi = $("luoiAnh");
    if (!luoi) return;
    var hienCo = luoi.querySelectorAll("[data-owner-video]").length;
    if (hienCo !== state.videos.length) {
      Array.prototype.slice.call(luoi.querySelectorAll("[data-owner-video]")).forEach(function (node) {
        node.remove();
      });
      state.videos.forEach(function (item, i) {
        var box = document.createElement("div");
        box.className = "o-anh owner-video-item";
        box.setAttribute("data-owner-video", String(i));

        var video = document.createElement("video");
        video.src = item.url;
        video.controls = true;
        video.preload = "metadata";
        video.playsInline = true;
        video.setAttribute("playsinline", "");
        video.setAttribute("aria-label", "Video căn hộ " + (i + 1));

        var badge = document.createElement("span");
        badge.className = "owner-video-badge";
        badge.textContent = "VIDEO";

        var del = document.createElement("button");
        del.type = "button";
        del.className = "owner-video-delete";
        del.setAttribute("aria-label", "Xóa video này");
        del.textContent = "×";
        del.addEventListener("click", function (e) {
          e.preventDefault();
          e.stopPropagation();
          var itemXoa = state.videos[i];
          if (itemXoa && itemXoa.url) URL.revokeObjectURL(itemXoa.url);
          state.videos.splice(i, 1);
          state.urls = [];
          state.uploadPromise = null;
          dongBoPreviewVideo();
        });

        box.appendChild(video);
        box.appendChild(badge);
        box.appendChild(del);
        luoi.appendChild(box);
      });
    }
    capNhatDemMedia();
  }

  function themVideo(files) {
    var conLai = TOI_DA_VIDEO - state.videos.length;
    if (conLai <= 0) {
      thongBaoLoi("Mỗi căn nhận tối đa " + TOI_DA_VIDEO + " video.");
      return;
    }

    var them = files.slice(0, conLai);
    var boQua = files.length - them.length;
    them.forEach(function (file) {
      if (MIME_VIDEO.indexOf(String(file.type || "").toLowerCase()) === -1) {
        thongBaoLoi("Video này chưa đúng định dạng. Anh/chị chọn MP4, MOV hoặc WebM giúp em.");
        return;
      }
      if (file.size > TOI_DA_MOI_VIDEO) {
        thongBaoLoi("Video " + file.name + " nặng " + dinhDangMB(file.size) + ". Mỗi video tối đa 120 MB để tải ổn định trên điện thoại.");
        return;
      }
      state.videos.push({ file: file, url: URL.createObjectURL(file) });
    });
    if (boQua > 0) thongBaoLoi("Mỗi căn nhận tối đa " + TOI_DA_VIDEO + " video, video thừa đã được bỏ qua.");
    state.urls = [];
    state.uploadPromise = null;
    dongBoPreviewVideo();
  }

  function ganNhanUI() {
    var input = $("chonAnh");
    if (!input) return;
    input.setAttribute("accept", "image/*,video/mp4,video/quicktime,video/webm");

    var lead = document.querySelector(".gui-photo-lead");
    if (lead) {
      var strong = lead.querySelector("strong");
      var span = lead.querySelector("span");
      if (strong) strong.textContent = "Ảnh / video là tùy chọn";
      if (span) span.textContent = "Anh/chị có thể tải ảnh hoặc video căn hộ trực tiếp từ điện thoại.";
    }
    var nut = document.querySelector('label.nut-anh[for="chonAnh"]');
    if (nut) {
      var b = nut.querySelector("b");
      var small = nut.querySelector("small");
      if (b) b.textContent = "Chọn ảnh hoặc video căn hộ";
      if (small) small.textContent = "Mở thư viện, chọn nhiều ảnh và tối đa 2 video (MP4/MOV/WebM).";
    }
    var safe = document.querySelector('[data-step="2"] .gui-safe');
    if (safe) safe.textContent = "Ảnh, video và ghi chú đều không bắt buộc.";
  }

  function themStyle() {
    if (document.getElementById("owner-video-style")) return;
    var st = document.createElement("style");
    st.id = "owner-video-style";
    st.textContent =
      ".owner-video-item{position:relative;background:#0b1728;overflow:hidden}" +
      ".owner-video-item video{display:block;width:100%;height:100%;min-height:130px;object-fit:cover;background:#0b1728}" +
      ".owner-video-badge{position:absolute;left:7px;top:7px;padding:3px 7px;border-radius:999px;background:rgba(8,25,48,.82);color:#fff;font-size:10px;font-weight:700;letter-spacing:.04em;pointer-events:none}" +
      ".owner-video-delete{position:absolute;right:7px;top:7px;width:29px;height:29px;border:0;border-radius:50%;background:rgba(255,255,255,.94);color:#163a68;font-size:20px;line-height:1;display:grid;place-items:center;box-shadow:0 3px 10px rgba(0,0,0,.18);cursor:pointer}";
    document.head.appendChild(st);
  }

  function xuLyChonFile(e) {
    var input = e.target;
    if (!input || input.id !== "chonAnh") return;
    var files = Array.prototype.slice.call(input.files || []);
    if (!files.length) return;

    var anh = [];
    var video = [];
    files.forEach(function (file) {
      if (String(file.type || "").toLowerCase().indexOf("video/") === 0) video.push(file);
      else anh.push(file);
    });
    if (!video.length) return;

    themVideo(video);

    /* Listener ảnh cũ vẫn chạy bình thường, nhưng chỉ nhận các file ảnh.
       DataTransfer được Safari iOS 18+ hỗ trợ và tránh phải sửa khối JS lớn của form. */
    try {
      var dt = new DataTransfer();
      anh.forEach(function (file) { dt.items.add(file); });
      input.files = dt.files;
    } catch (_err) {
      /* Fallback an toàn: nếu trình duyệt quá cũ, không cho video đi vào bộ nén ảnh. */
      if (!anh.length) {
        e.stopImmediatePropagation();
        input.value = "";
      }
    }

    setTimeout(dongBoPreviewVideo, 0);
  }

  function capNhatTienDoVideo(index, total, loaded, size) {
    var chu = $("chuTienTrinh");
    var thanh = $("thanhChay");
    var pctFile = size ? Math.min(100, Math.round((loaded / size) * 100)) : 0;
    if (chu) chu.textContent = "Đang tải video " + index + "/" + total + " · " + pctFile + "%";
    if (thanh) {
      var pctTong = 6 + Math.round((((index - 1) + pctFile / 100) / total) * 22);
      thanh.style.width = Math.min(28, pctTong) + "%";
    }
  }

  function taiMotVideo(item, index, total) {
    return new Promise(function (resolve, reject) {
      var file = item.file;
      var now = new Date();
      var thang = now.getFullYear() + "-" + String(now.getMonth() + 1).padStart(2, "0");
      var path = "pending/" + thang + "/" + taoId() + "." + duoiVideo(file);
      var uploadUrl = SUPABASE_URL + "/storage/v1/object/" + VIDEO_BUCKET + "/" + encodePath(path);
      var publicUrl = SUPABASE_URL + "/storage/v1/object/public/" + VIDEO_BUCKET + "/" + encodePath(path);

      var xhr = new XMLHttpRequest();
      xhr.open("POST", uploadUrl, true);
      xhr.setRequestHeader("Authorization", "Bearer " + SUPABASE_ANON_KEY);
      xhr.setRequestHeader("apikey", SUPABASE_ANON_KEY);
      xhr.setRequestHeader("Content-Type", file.type || "video/mp4");
      xhr.setRequestHeader("x-upsert", "false");
      xhr.timeout = 8 * 60 * 1000;
      xhr.upload.onprogress = function (ev) {
        if (ev.lengthComputable) capNhatTienDoVideo(index, total, ev.loaded, ev.total);
      };
      xhr.onerror = function () { reject(new Error("Mạng bị gián đoạn khi tải video. Anh/chị thử lại giúp.")); };
      xhr.ontimeout = function () { reject(new Error("Tải video quá lâu. Anh/chị thử lại khi mạng ổn định hơn.")); };
      xhr.onload = function () {
        if (xhr.status >= 200 && xhr.status < 300) {
          capNhatTienDoVideo(index, total, file.size, file.size);
          resolve(publicUrl);
          return;
        }
        var msg = "Không tải được video (mã " + xhr.status + ").";
        try {
          var data = JSON.parse(xhr.responseText || "{}");
          if (data && (data.message || data.error)) msg = data.message || data.error;
        } catch (_e) {}
        reject(new Error(msg));
      };
      xhr.send(file);
    });
  }

  async function taiTatCaVideo() {
    if (!state.videos.length) return [];
    if (state.urls.length === state.videos.length) return state.urls.slice();
    if (state.uploadPromise) return state.uploadPromise;

    state.uploadPromise = (async function () {
      var urls = [];
      for (var i = 0; i < state.videos.length; i++) {
        urls.push(await taiMotVideo(state.videos[i], i + 1, state.videos.length));
      }
      state.urls = urls;
      return urls.slice();
    })();

    try {
      return await state.uploadPromise;
    } finally {
      state.uploadPromise = null;
    }
  }

  function patchFetch() {
    if (!window.fetch || window.fetch.__ownerVideoPatched) return;
    var fetchGoc = window.fetch.bind(window);

    var fetchMoi = async function (input, init) {
      var opts = init;
      try {
        if (opts && typeof opts.body === "string") {
          var payload = JSON.parse(opts.body);
          if (payload && payload.action === "chuNhaGuiCan" && state.videos.length) {
            var urls = await taiTatCaVideo();
            payload.videoUrls = urls;
            payload.soVideo = urls.length;
            payload.video = urls[0] || "";

            /* Backend hiện tại chắc chắn đã lưu ghiChu. Gắn URL vào ghi chú là lớp
               tương thích ngược để video không bị thất lạc kể cả khi Apps Script
               chưa đọc các trường videoUrls/soVideo mới. */
            if (urls.length) {
              var dongVideo = "Video căn hộ: " + urls.join(" | ");
              payload.ghiChu = payload.ghiChu ? (payload.ghiChu + "\n" + dongVideo) : dongVideo;
            }
            opts = Object.assign({}, opts, { body: JSON.stringify(payload) });
          }
        }
      } catch (err) {
        if (err && /video|tải|mạng|upload/i.test(String(err.message || err))) throw err;
        /* Không để lớp video làm hỏng các fetch khác của site. */
      }
      return fetchGoc(input, opts);
    };
    fetchMoi.__ownerVideoPatched = true;
    window.fetch = fetchMoi;
  }

  function khoiTao() {
    if (!$("chonAnh") || !$("mauGui")) return;
    ganNhanUI();
    themStyle();
    patchFetch();

    document.addEventListener("change", xuLyChonFile, true);

    var luoi = $("luoiAnh");
    if (luoi && window.MutationObserver) {
      var observer = new MutationObserver(function () { dongBoPreviewVideo(); });
      observer.observe(luoi, { childList: true });
    }

    window.addEventListener("beforeunload", function () {
      state.videos.forEach(function (item) {
        if (item.url) URL.revokeObjectURL(item.url);
      });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", khoiTao, { once: true });
  else khoiTao();
})();
