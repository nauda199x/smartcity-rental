#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DATA = join(ROOT, "data-lumi.json");
const SHEET = "1Buw_vjB_2x8KExje34lqmJKEFzCUM79LOmcvCVWw-yQ";
const DRY = process.argv.includes("--thu") || process.argv.includes("--dry-run");

const STANDARD_COLS = { tower: 2, sourceCode: 3, direction: 4, area: 5, price: 6, interior: 7, updated: 9, imageCell: 10, note: 11, move: 13, stt: 14 };
const EXTENDED_COLS = { tower: 2, sourceCode: 3, direction: 4, area: 5, price: 7, interior: 8, updated: 10, imageCell: 11, note: 12, move: 14, stt: 15 };

const TABS = [
  { tab: "THUÊ 1PN", gid: 910003, type: "1 Ngủ", publicPrefix: "thue1N", cols: STANDARD_COLS, imageCol: "K", sttCol: "O", endCol: "S" },
  { tab: "THUÊ 2PN", gid: 910004, type: "2 Ngủ", publicPrefix: "thue2N", cols: STANDARD_COLS, imageCol: "K", sttCol: "O", endCol: "S" },
  { tab: "THUÊ 3PN", gid: 910005, type: "3 Ngủ", publicPrefix: "thue3N", cols: STANDARD_COLS, imageCol: "K", sttCol: "O", endCol: "S" },
  { tab: "THUÊ DUPLEX", gid: 910006, type: "Duplex", publicPrefix: "thueDuplex", cols: EXTENDED_COLS, imageCol: "L", sttCol: "P", endCol: "S" },
  { tab: "THUÊ PENTHOUSE", gid: 910007, type: "Penthouse", publicPrefix: "thuePenthouse", cols: EXTENDED_COLS, imageCol: "L", sttCol: "P", endCol: "S" },
  { tab: "THUÊ SHOP", gid: 910008, type: "Shop", publicPrefix: "thueShop", cols: EXTENDED_COLS, imageCol: "L", sttCol: "P", endCol: "S" },
];

const txt = v => String(v == null ? "" : v).trim();
const key = v => txt(v).toLowerCase();
const pad2 = n => String(n).padStart(2, "0");

function parseCsv(s) {
  const rows = [];
  let row = [], cell = "", quoted = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (quoted) {
      if (c === '"' && s[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') quoted = false;
      else cell += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n") { row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = ""; }
    else cell += c;
  }
  if (quoted) throw new Error("CSV có dấu nháy chưa đóng");
  if (cell || row.length) { row.push(cell.replace(/\r$/, "")); rows.push(row); }
  return rows;
}

function deaccent(v) {
  return txt(v).normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
}

function money(v) {
  const s = txt(v).replace(/\s+/g, "").replace(/₫|vnd|triệu|tr|tháng/gi, "");
  if (!s) return 0;
  if (/^\d{1,3}(?:\.\d{3})+$/.test(s)) return Number(s.replace(/\./g, ""));
  if (/^\d{1,3}(?:,\d{3})+$/.test(s)) return Number(s.replace(/,/g, ""));
  if (/^\d+[,.]\d{1,2}$/.test(s)) return Math.round(Number(s.replace(",", ".")) * 1000000);
  const n = Number(s.replace(/[^\d]/g, ""));
  if (!Number.isFinite(n) || n <= 0) return 0;
  return n >= 1000000 ? n : n * 1000000;
}

function area(v) {
  const n = Number(txt(v).replace(",", ".").replace(/[^\d.]/g, ""));
  return Number.isFinite(n) && n > 0 ? n : 0;
}

function date(v) {
  const s = txt(v);
  if (!s) return "";
  let m = s.match(/\b(\d{1,2})\/(\d{1,2})\/(\d{4})\b/);
  if (m) return pad2(+m[1]) + "/" + pad2(+m[2]) + "/" + m[3];
  m = s.match(/\b(\d{1,2})\/(\d{1,2})\b/);
  if (!m) return s;
  const now = new Date(Date.now() + 7 * 3600000);
  return pad2(+m[1]) + "/" + pad2(+m[2]) + "/" + now.getUTCFullYear();
}

function todayVN() {
  const d = new Date(Date.now() + 7 * 3600000);
  return pad2(d.getUTCDate()) + "/" + pad2(d.getUTCMonth() + 1) + "/" + d.getUTCFullYear();
}

function inactive(note) {
  const s = deaccent(note).replace(/\s+/g, " ");
  return /cho thue roi|da cho thue|da thue|da coc|chot thue|khong cho thue|dung thue/.test(s);
}

function publicMove(move, note) {
  const direct = txt(move);
  if (direct) return date(direct);
  const raw = txt(note), s = deaccent(raw);
  if (/vao o dc luon|vao o duoc luon|vao luon|cho thue luon|nha trong.*vao luon/.test(s)) return "";
  let m = raw.match(/\b\d{1,2}\s*[-–]\s*\d{1,2}\/\d{1,2}\b/);
  if (m) return m[0];
  m = raw.match(/\b\d{1,2}\/\d{1,2}(?:\/\d{4})?\b/);
  if (m && /nhan nha|vao|trong/.test(s)) return date(m[0]);
  m = raw.match(/tháng\s+\d{1,2}/i);
  if (m && /nhan nha|vao/.test(s)) return m[0];
  return "Chưa xác nhận";
}

function normalizeStt(value) {
  const raw = txt(value).replace(/\.0+$/, "");
  return /^\d+$/.test(raw) ? raw : "";
}

function publicCode(spec, stt) {
  const n = normalizeStt(stt);
  return n ? spec.publicPrefix + "." + n : "";
}

function decodeHtml(s) {
  return String(s || "")
    .replace(/&amp;/g, "&").replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
}

async function fetchCsv(spec) {
  // Dữ liệu chính đọc từ CSV export theo gid. Endpoint này phản ánh Sheet mới
  // ổn định hơn GViz query, vốn đã từng trả snapshot cũ ở một vài dòng.
  const u = new URL("https://docs.google.com/spreadsheets/d/" + SHEET + "/export");
  u.searchParams.set("format", "csv");
  u.searchParams.set("gid", String(spec.gid));
  u.searchParams.set("range", "A5:" + spec.endCol);
  u.searchParams.set("_", String(Date.now()) + "-" + spec.publicPrefix);
  const r = await fetch(u, {
    headers: {
      "user-agent": "Mozilla/5.0",
      "cache-control": "no-cache, no-store, max-age=0",
      "pragma": "no-cache"
    }
  });
  if (!r.ok) throw new Error(spec.tab + ": HTTP " + r.status);
  const body = await r.text();
  const rows = parseCsv(body);
  if (!rows.length) throw new Error(spec.tab + ": CSV rỗng");
  return rows;
}

/* Gviz CSV chỉ trả chữ hiển thị "ảnh", không trả hyperlink ẩn của cell.
   Đọc riêng HTML chỉ 2 cột E + L/M để lấy href; nếu Google đổi markup thì
   sync dữ liệu vẫn chạy và giữ link ảnh cũ, tuyệt đối không xóa album đang tốt. */
async function fetchImageLinks(spec) {
  try {
    const u = new URL("https://docs.google.com/spreadsheets/d/" + SHEET + "/gviz/tq");
    u.searchParams.set("tqx", "out:html");
    u.searchParams.set("sheet", spec.tab);
    u.searchParams.set("headers", "1");
    u.searchParams.set("range", "A5:" + spec.endCol);
    u.searchParams.set("tq", "select " + spec.sttCol + "," + spec.imageCol);
    u.searchParams.set("_", String(Date.now()) + "-img-" + spec.publicPrefix);
    const r = await fetch(u, {
      headers: {
        "user-agent": "Mozilla/5.0",
        "cache-control": "no-cache, no-store, max-age=0",
        "pragma": "no-cache"
      }
    });
    if (!r.ok) return { ok: false, map: new Map() };
    const html = await r.text();
    const map = new Map();
    const trs = html.match(/<tr[\s\S]*?<\/tr>/gi) || [];
    for (const tr of trs.slice(1)) {
      const tds = tr.match(/<td[\s\S]*?<\/td>/gi) || [];
      if (tds.length < 2) continue;
      const stt = normalizeStt(decodeHtml(tds[0].replace(/<[^>]+>/g, "")).trim());
      const href = (tds[1].match(/href="([^"]+)"/i) || [])[1] || "";
      const clean = decodeHtml(href);
      if (stt && /https:\/\/drive\.google\.com\//i.test(clean)) map.set(stt, clean);
    }
    return { ok: map.size > 0, map };
  } catch {
    return { ok: false, map: new Map() };
  }
}

function parseSheetMedia(value) {
  try {
    const obj = JSON.parse(txt(value));
    if (!obj || typeof obj !== "object" || !Array.isArray(obj.images) || !Array.isArray(obj.videos)) return null;
    const valid = items => [...new Set(items.filter(id => typeof id === "string" && /^[A-Za-z0-9_-]{10,}$/.test(id)))];
    const images = valid(obj.images);
    const videos = valid(obj.videos);
    const thumbs = images.map(id => "https://drive.google.com/thumbnail?id=" + id + "&sz=w1000");
    return {
      cover: thumbs[0] || "",
      gallery: thumbs.join("\n"),
      videos: videos.map(id => "https://drive.google.com/file/d/" + id + "/preview").join("\n")
    };
  } catch { return null; }
}

function sourceRow(spec, c) {
  /* CSV export trả đủ cột nguồn. Mã căn thật chỉ tồn tại trong bộ nhớ
     để migrate snapshot cũ; tuyệt đối không ghi vào data-lumi.json/public HTML. */
  const x = spec.cols;
  const stt = normalizeStt(c[x.stt]);
  return {
    spec,
    stt,
    publicCode: publicCode(spec, stt),
    syncFolder: txt(c[17]),
    sheetMedia: parseSheetMedia(c[18]),
    tower: txt(c[x.tower]),
    sourceCode: txt(c[x.sourceCode]),
    direction: txt(c[x.direction]),
    area: area(c[x.area]),
    price: money(c[x.price]),
    interior: txt(c[x.interior]),
    updated: date(c[x.updated]),
    imageCell: txt(c[x.imageCell]),
    note: txt(c[x.note]),
    move: publicMove(c[x.move], c[x.note])
  };
}

async function loadSource() {
  const byId = new Map();
  const byType = new Map();
  let nonEmpty = 0, badStt = 0;
  for (const spec of TABS) {
    const [rows, links] = await Promise.all([fetchCsv(spec), fetchImageLinks(spec)]);
    // CSV export may return A5:S or the entire tab. Locate the real header so
    // the stable public ID is always its 1-based data-row ordinal (row 6 -> 1).
    // The STT column is sometimes #REF!, blank or offset by five rows: never
    // let that corrupt public IDs or deactivate otherwise valid apartments.
    const header = rows.findIndex(c => deaccent(c?.[spec.cols.sourceCode]) === "ma can");
    if (header < 0) throw new Error(spec.tab + ": không tìm thấy tiêu đề MÃ CĂN trong CSV");
    let tabCount = 0;
    for (let i = header + 1; i < rows.length; i++) {
      const c = rows[i];
      if (!c || c.every(x => !txt(x))) continue;
      const src = sourceRow(spec, c);
      // Skip preformatted empty rows; retain ordinal gaps to prevent ID reuse.
      if (!src.tower && !src.sourceCode && !src.area && !src.price) continue;
      nonEmpty++;
      const ordinal = String(i - header);
      if (src.stt !== ordinal) badStt++;
      const sheetStt = src.stt;
      src.stt = ordinal;
      src.publicCode = publicCode(spec, ordinal);
      // R contains the exact URL of a rich-text "ảnh" hyperlink in column K.
      // Prefer the explicit per-row URL, never infer an album from price/tower.
      const validFolder = v => /^https:\/\/drive\.google\.com\/(?:drive\/(?:u\/\d+\/)?folders\/|open\?id=)[A-Za-z0-9_-]{12,}/i.test(v);
      const directFolder = [src.syncFolder, src.imageCell].find(validFolder) || "";
      const mappedFolder = links.map.get(sheetStt) || links.map.get(ordinal) || "";
      src.folder = directFolder || mappedFolder;
      // Blank K and R explicitly mean "no images"; do not retain stale media.
      src.folderKnown = Boolean(directFolder) || !src.imageCell || links.ok;
      const id = src.publicCode;
      if (byId.has(id)) throw new Error("Trùng mã công khai: " + id);
      byId.set(id, src);
      tabCount++;
    }
    byType.set(spec.publicPrefix, tabCount);
  }
  // A broken Sheet/export must never turn off the whole stock board again.
  if (byId.size < 45 || byId.size > 300 ||
      (byType.get("thue1N") || 0) < 10 ||
      (byType.get("thue2N") || 0) < 20 ||
      (byType.get("thue3N") || 0) < 12)
    throw new Error("Quỹ Lumi bất thường, từ chối ghi snapshot thiếu căn: " +
      byId.size + " " + JSON.stringify(Object.fromEntries(byType)));
  console.log("Lumi: " + badStt + " STT nguồn sai/trống; mã công khai tính theo thứ tự dòng dữ liệu thực tế.");
  return { byId, nonEmpty };
}

function sync(old, source) {
  const next = old.filter(r => deaccent(r["Mã căn"]) !== "ma can").map(r => ({ ...r }));
  const oldById = new Map(next.map((r, i) => [txt(r["Mã nội bộ"]), i]));
  // Albums may be intentionally shared; reuse photos ONLY for the exact same
  // Drive folder URL. A stale public ID is not proof of media ownership.
  const mediaByFolder = new Map();
  for (const row of next) {
    const folder = txt(row["Ảnh thư mục"]);
    if (folder && !mediaByFolder.has(folder) &&
        (txt(row["Ảnh đại diện"]) || txt(row["Danh sách ảnh"])))
      mediaByFolder.set(folder, {
        cover: txt(row["Ảnh đại diện"]),
        gallery: txt(row["Danh sách ảnh"])
      });
  }
  function sourceAlbum(src) {
    // R/S là link + media JSON của đúng dòng, tuyệt đối không ghép media theo mã căn.
    return src.sheetMedia && src.syncFolder && src.syncFolder === src.folder ? src.sheetMedia : null;
  }
  function reconcileMedia(out, src) {
    const previousFolder = txt(out["Ảnh thư mục"]);
    const fromSheet = sourceAlbum(src);
    if (src.folderKnown) {
      if (previousFolder !== src.folder) {
        const matched = mediaByFolder.get(src.folder);
        out["Ảnh thư mục"] = src.folder;
        out["Ảnh đại diện"] = fromSheet ? fromSheet.cover : matched?.cover || "";
        out["Danh sách ảnh"] = fromSheet ? fromSheet.gallery : matched?.gallery || "";
        out["Danh sách video"] = fromSheet ? fromSheet.videos : "";
      } else if (fromSheet) {
        out["Ảnh đại diện"] = fromSheet.cover;
        out["Danh sách ảnh"] = fromSheet.gallery;
        out["Danh sách video"] = fromSheet.videos;
      }
    } else {
      // Nếu chưa đọc được link rich-text, chỉ giữ media khi căn vẫn đúng đặc điểm.
      const same = key(out["Tòa"]) === key(src.tower) &&
        Math.abs(area(out["Diện tích"]) - src.area) < 0.01 &&
        money(out["Giá thuê"]) === src.price &&
        key(out["Hướng ban công"]) === key(src.direction);
      if (!same) {
        out["Ảnh thư mục"] = "";
        out["Ảnh đại diện"] = "";
        out["Danh sách ảnh"] = "";
        out["Danh sách video"] = "";
      }
    }
  }
  const touched = new Set();
  const stat = { updated: 0, added: 0, on: 0, off: 0, missing: 0 };
  for (const [id, src] of source.entries()) {
    const complete = Boolean(src.stt && src.tower && src.area > 0 && src.price > 0);
    const show = complete && !inactive(src.note);
    const payload = {
      "Mã nội bộ": id,
      "Mã căn": src.publicCode,
      "Tòa": src.tower,
      "Loại": src.spec.type,
      "Diện tích": src.area,
      "Nội thất": src.interior,
      "Giá thuê": src.price,
      "Hướng ban công": src.direction,
      "Ngày vào ở": src.move,
      "Ngày cập nhật": src.updated,
      "Hiển thị trên Web": show ? "Có" : "Không",
    };
    let pos = oldById.get(id);
    if (pos == null) {
      const album = sourceAlbum(src) || mediaByFolder.get(src.folder);
      const row = {
        ...payload,
        "Ngày thêm vào hệ thống": src.updated || todayVN(),
        "Ảnh thư mục": src.folderKnown ? src.folder : "",
        "Ảnh đại diện": src.folderKnown ? album?.cover || "" : "",
        "Danh sách ảnh": src.folderKnown ? album?.gallery || "" : "",
        "Danh sách video": src.folderKnown ? album?.videos || "" : "",
      };
      next.push(row);
      oldById.set(id, next.length - 1);
      touched.add(next.length - 1);
      stat.added++;
      show ? stat.on++ : stat.off++;
      continue;
    }
    const out = next[pos];
    const was = key(out["Hiển thị trên Web"]) === "có";
    reconcileMedia(out, src);
    Object.assign(out, payload);
    if (!txt(out["Ngày thêm vào hệ thống"]))
      out["Ngày thêm vào hệ thống"] = src.updated || todayVN();
    if (!("Ảnh đại diện" in out)) out["Ảnh đại diện"] = "";
    if (!("Danh sách ảnh" in out)) out["Danh sách ảnh"] = "";
    if (!("Danh sách video" in out)) out["Danh sách video"] = "";
    touched.add(pos);
    stat.updated++;
    if (!was && show) stat.on++;
    if (was && !show) stat.off++;
  }
  // Keep historical URLs as inactive, never publicly invent stock from old
  // cache rows. A missing ID cannot be used to remove a current Sheet row.
  for (let i = 0; i < next.length; i++) {
    if (touched.has(i)) continue;
    if (key(next[i]["Hiển thị trên Web"]) === "có") {
      next[i]["Hiển thị trên Web"] = "Không";
      stat.missing++;
    }
  }
  const cleaned = next.filter(row =>
    /^thue(?:1N|2N|3N|Duplex|Penthouse|Shop)\.\d+$/.test(txt(row["Mã nội bộ"])));
  for (const row of cleaned) {
    if (!("Danh sách video" in row)) row["Danh sách video"] = "";
  }
  return { next: cleaned, stat };
}

async function main() {
  const raw = readFileSync(DATA, "utf8");
  const old = JSON.parse(raw);
  if (!Array.isArray(old)) throw new Error("data-lumi.json không phải mảng");

  const src = await loadSource();
  const result = sync(old, src.byId);
  const after = JSON.stringify(result.next, null, 2) + "\n";

  console.log("Lumi: " + src.nonEmpty + " dòng có dữ liệu, " + src.byId.size + " mã căn.");
  console.log("Đối chiếu: cập nhật " + result.stat.updated + ", thêm " + result.stat.added +
    ", bật " + result.stat.on + ", tắt " + result.stat.off +
    ", tắt vì rời nguồn " + result.stat.missing + ".");

  if (raw === after) {
    console.log("data-lumi.json đã khớp Google Sheet.");
    return;
  }
  if (!DRY) writeFileSync(DATA, after, "utf8");
  console.log(DRY ? "Chế độ --thu: không ghi file." : "Đã ghi data-lumi.json (" + result.next.length + " dòng).");
}

main().catch(err => {
  console.error("::error::" + (err.stack || err.message || err));
  process.exit(1);
});
