#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DATA = join(ROOT, "data-lumi.json");
const SHEET = "1Buw_vjB_2x8KExje34lqmJKEFzCUM79LOmcvCVWw-yQ";
const DRY = process.argv.includes("--thu") || process.argv.includes("--dry-run");

const TABS = [
  { tab: "THUÊ 1PN", type: "1 Ngủ", code: "1N", query: "select D,E,F,G,H,I,K,L,M,O", imageCol: "L" },
  { tab: "THUÊ 2PN", type: "2 Ngủ", code: "2N", query: "select D,E,F,G,H,I,K,L,M,O", imageCol: "L" },
  { tab: "THUÊ 3PN", type: "3 Ngủ", code: "3N", query: "select D,E,F,G,H,I,K,L,M,O", imageCol: "L" },
  { tab: "THUÊ DUPLEX", type: "Duplex", code: "DUPLEX", query: "select D,E,F,G,I,J,L,M,N,P", imageCol: "M" },
  { tab: "THUÊ PENTHOUSE", type: "Penthouse", code: "PENTHOUSE", query: "select D,E,F,G,I,J,L,M,N,P", imageCol: "M" },
  { tab: "THUÊ SHOP", type: "Shop", code: "SHOP", query: "select D,E,F,G,I,J,L,M,N,P", imageCol: "M" },
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

function internalId(spec, code, areaValue) {
  const a = String(areaValue || 0).replace(/[^0-9.]/g, "").replace(".", "_");
  return "LH." + spec.code + "." + txt(code).replace(/\s+/g, "") + "." + a;
}

function decodeHtml(s) {
  return String(s || "")
    .replace(/&amp;/g, "&").replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
}

async function fetchCsv(spec) {
  const u = new URL("https://docs.google.com/spreadsheets/d/" + SHEET + "/gviz/tq");
  u.searchParams.set("tqx", "out:csv");
  u.searchParams.set("sheet", spec.tab);
  u.searchParams.set("headers", "1");
  u.searchParams.set("range", "A5:P");
  u.searchParams.set("tq", spec.query);
  const r = await fetch(u, { headers: { "user-agent": "Mozilla/5.0" } });
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
    u.searchParams.set("range", "A5:P");
    u.searchParams.set("tq", "select E," + spec.imageCol);
    const r = await fetch(u, { headers: { "user-agent": "Mozilla/5.0" } });
    if (!r.ok) return { ok: false, map: new Map() };
    const html = await r.text();
    const map = new Map();
    const trs = html.match(/<tr[\s\S]*?<\/tr>/gi) || [];
    for (const tr of trs.slice(1)) {
      const tds = tr.match(/<td[\s\S]*?<\/td>/gi) || [];
      if (tds.length < 2) continue;
      const code = decodeHtml(tds[0].replace(/<[^>]+>/g, "")).trim();
      const href = (tds[1].match(/href="([^"]+)"/i) || [])[1] || "";
      const clean = decodeHtml(href);
      if (code && /https:\/\/drive\.google\.com\//i.test(clean)) map.set(code, clean);
    }
    return { ok: map.size > 0, map };
  } catch {
    return { ok: false, map: new Map() };
  }
}

function sourceRow(spec, c) {
  /* Hai truy vấn đều trả đúng 10 cột public theo cùng thứ tự logic:
     tower, code, direction, area, price, interior, updated, image label, note, move. */
  return {
    spec,
    tower: txt(c[0]), code: txt(c[1]), direction: txt(c[2]),
    area: area(c[3]), price: money(c[4]), interior: txt(c[5]),
    updated: date(c[6]), note: txt(c[8]), move: publicMove(c[9], c[8])
  };
}

async function loadSource() {
  const byId = new Map();
  let nonEmpty = 0;
  for (const spec of TABS) {
    const [rows, links] = await Promise.all([fetchCsv(spec), fetchImageLinks(spec)]);
    for (let i = 1; i < rows.length; i++) {
      const c = rows[i];
      if (!c || c.every(x => !txt(x))) continue;
      nonEmpty++;
      const src = sourceRow(spec, c);
      if (!src.code && !src.tower && !src.area && !src.price) continue;
      if (!src.code) continue;
      src.folderKnown = links.ok;
      src.folder = links.map.get(src.code) || "";
      const id = internalId(spec, src.code, src.area);
      if (byId.has(id)) throw new Error("Trùng mã trong " + spec.tab + ": " + src.code);
      byId.set(id, src);
    }
  }
  if (byId.size < 10 || byId.size > 300)
    throw new Error("Số căn Lumi bất thường: " + byId.size + " (ngưỡng 10-300)");
  return { byId, nonEmpty };
}

function sync(old, source) {
  /* Chỉ dọn các dòng header rác từng lọt vào snapshot; căn lịch sử vẫn giữ lại. */
  const next = old.filter(r => deaccent(r["Mã căn"]) !== "ma can").map(r => ({ ...r }));
  const oldById = new Map(next.map((r, i) => [txt(r["Mã nội bộ"]), i]));
  const touched = new Set();
  const stat = { updated: 0, added: 0, on: 0, off: 0, missing: 0 };

  for (const [id, src] of source.entries()) {
    const complete = Boolean(src.tower && src.code && src.area > 0 && src.price > 0);
    const show = complete && !inactive(src.note);
    const payload = {
      "Mã nội bộ": id,
      "Mã căn": src.code,
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
    /* Chuyển đổi snapshot đầu tiên từng dùng LH.<Mã căn> sang ID mới có loại
       căn để tránh đụng mã khi cùng một mã xuất hiện ở hai tab khác nhau. */
    if (pos == null) {
      const legacy = next.findIndex(r => txt(r["Mã căn"]) === src.code &&
        key(r["Loại"]) === key(src.spec.type) &&
        Math.abs(area(r["Diện tích"]) - src.area) < 0.01);
      if (legacy >= 0 && !touched.has(legacy)) pos = legacy;
    }

    if (pos == null) {
      const row = {
        ...payload,
        "Ngày thêm vào hệ thống": src.updated || todayVN(),
        "Ảnh thư mục": src.folderKnown ? src.folder : "",
        "Ảnh đại diện": "",
        "Danh sách ảnh": ""
      };
      next.push(row);
      oldById.set(id, next.length - 1);
      touched.add(next.length - 1);
      stat.added++; show ? stat.on++ : stat.off++;
      continue;
    }

    const out = next[pos];
    const was = key(out["Hiển thị trên Web"]) === "có";
    Object.assign(out, payload);
    if (!txt(out["Ngày thêm vào hệ thống"])) out["Ngày thêm vào hệ thống"] = src.updated || todayVN();
    if (src.folderKnown) out["Ảnh thư mục"] = src.folder;
    if (!("Ảnh đại diện" in out)) out["Ảnh đại diện"] = "";
    if (!("Danh sách ảnh" in out)) out["Danh sách ảnh"] = "";
    touched.add(pos);
    stat.updated++;
    if (!was && show) stat.on++;
    if (was && !show) stat.off++;
  }

  for (let i = 0; i < next.length; i++) {
    if (touched.has(i)) continue;
    if (!/^LH\./.test(txt(next[i]["Mã nội bộ"]))) continue;
    if (key(next[i]["Hiển thị trên Web"]) === "có") {
      next[i]["Hiển thị trên Web"] = "Không";
      stat.missing++;
    }
  }

  return { next, stat };
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
