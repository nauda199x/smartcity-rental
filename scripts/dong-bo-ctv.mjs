#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const DATA = join(ROOT, "data.json");
const SHEET = "1Gnh6ILQT1mV1bQFw5OLVSXMIvqcrO-M36vjlinMiH0w";
const DRY = process.argv.includes("--thu") || process.argv.includes("--dry-run");
const TABS = [
  ["Stu", "Studio"], ["1N", "1 Ngủ"], ["1n+", "1 Ngủ +"],
  ["2n1", "2 Ngủ"], ["2n2", "2 Ngủ"], ["2n+", "2 Ngủ +"], ["3n", "3 Ngủ"],
];
const ID_RE = /^CT\.[A-Za-z0-9+]+\.\d+$/;

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
    else if (c === "\n") {
      row.push(cell.replace(/\r$/, "")); rows.push(row); row = []; cell = "";
    } else cell += c;
  }
  if (quoted) throw new Error("CSV có dấu nháy chưa đóng");
  if (cell || row.length) { row.push(cell.replace(/\r$/, "")); rows.push(row); }
  return rows;
}

async function fetchTab(tab) {
  const url = "https://docs.google.com/spreadsheets/d/" + SHEET +
    "/gviz/tq?tqx=out:csv&sheet=" + encodeURIComponent(tab);
  const r = await fetch(url, { headers: { "user-agent": "Mozilla/5.0" } });
  if (!r.ok) throw new Error(tab + ": HTTP " + r.status);
  const body = await r.text();
  if (!body.includes("ID CĂN")) throw new Error(tab + ": phản hồi không phải Sheet CTV");
  return parseCsv(body);
}

function money(v) {
  const s = txt(v).replace(/\s+/g, "").replace(/₫|vnd|triệu|tr|tháng/gi, "");
  if (!s) return 0;
  if (/^\d{1,3}(?:\.\d{3})+$/.test(s)) return Number(s.replace(/\./g, "")) * 1000;
  if (/^\d{1,3}(?:,\d{3})+$/.test(s)) return Number(s.replace(/,/g, "")) * 1000;
  if (/^\d+[,.]\d{1,2}$/.test(s)) return Math.round(Number(s.replace(",", ".")) * 1000000);
  const n = Number(s.replace(/[^\d]/g, ""));
  if (!Number.isFinite(n) || n <= 0) return 0;
  if (n >= 1000000) return n;
  if (n >= 1000) return n * 1000;
  return n * 1000000;
}

function area(v) {
  const n = Number(txt(v).replace(",", ".").replace(/[^\d.]/g, ""));
  return Number.isFinite(n) && n > 0 ? n : 0;
}

function tower(v) {
  const s = txt(v).replace(/\s+/g, " ");
  return /^mas\s*[abcd]$/i.test(s) ? s.replace(/\s+/g, "") : s;
}

function furniture(v) {
  const s = key(v);
  if (!s) return "";
  if (s === "nb" || /nguyên\s*bản/.test(s)) return "Nhà Nguyên Bản";
  if (s === "cb" || /cơ\s*bản/.test(s)) return "Đồ Cơ bản";
  if (/full/.test(s)) return "Full nội thất";
  return txt(v);
}

function nowVN() {
  const d = new Date(Date.now() + 7 * 3600000);
  return { d: d.getUTCDate(), m: d.getUTCMonth() + 1, y: d.getUTCFullYear() };
}

function date(v, immediate = true) {
  const s = txt(v);
  if (!s) return "";
  if (immediate && /^(luôn|o ngay|ở ngay|ngay)$/i.test(s)) return "";
  let m = s.match(/\b(\d{1,2})\/(\d{1,2})\/(\d{4})\b/);
  if (m) return pad2(+m[1]) + "/" + pad2(+m[2]) + "/" + m[3];
  m = s.match(/\b(\d{1,2})\/(\d{1,2})\b/);
  if (!m) return s;
  const n = nowVN();
  let y = n.y;
  const candidate = Date.UTC(y, +m[2] - 1, +m[1]);
  const today = Date.UTC(n.y, n.m - 1, n.d);
  if (candidate < today - 120 * 86400000) y++;
  return pad2(+m[1]) + "/" + pad2(+m[2]) + "/" + y;
}

function inactive(note) {
  const s = key(note).replace(/\s+/g, " ");
  return /(?:không|k) cho thuê nữa/.test(s) ||
    /dừng thuê/.test(s) || /chỉ bán/.test(s) ||
    /để ở[^\n]*?(?:không|k) cho thuê/.test(s) ||
    /đã thuê|đã chốt|chốt thuê/.test(s);
}

function sourceRow(tab, type, c, row) {
  return {
    tab, type, row, first: date(c[0], false), note: txt(c[1]), id: txt(c[2]),
    tower: tower(c[3]), furniture: furniture(c[4]), price: money(c[5]),
    area: area(c[6]), moveIn: date(c[7]), folder: txt(c[9]),
  };
}
const complete = r => Boolean(r.tower && r.price > 0 && r.area > 0);

async function loadCtv() {
  const map = new Map(), invalid = [];
  let nonEmpty = 0;
  for (const [tab, type] of TABS) {
    const rows = await fetchTab(tab);
    for (let i = 1; i < rows.length; i++) {
      const c = rows[i];
      if (!c || c.every(x => !txt(x))) continue;
      nonEmpty++;
      const r = sourceRow(tab, type, c, i + 1);
      if (!r.id) continue;
      if (!ID_RE.test(r.id)) { invalid.push(r); continue; }
      if (map.has(r.id)) throw new Error("ID trùng trong CTV: " + r.id);
      map.set(r.id, r);
    }
  }
  if (map.size < 250 || map.size > 500)
    throw new Error("Số ID hợp lệ bất thường: " + map.size + " (ngưỡng 250-500)");
  return { map, invalid, nonEmpty };
}

function sync(old, ctv) {
  const byId = new Map();
  old.forEach((r, i) => {
    const id = txt(r["Mã nội bộ"]);
    if (id && !byId.has(id)) byId.set(id, i);
  });
  const next = old.map(r => ({ ...r }));
  const touched = new Set();
  const stat = { updated: 0, added: 0, on: 0, off: 0, missing: 0 };

  for (const [id, src] of ctv.entries()) {
    const pos = byId.get(id);
    if (pos == null) {
      if (!complete(src)) continue;
      const n = nowVN();
      next.push({
        "Mã nội bộ": id, "Tòa": src.tower, "Loại": src.type,
        "Diện tích": src.area, "Nội thất": src.furniture, "Giá thuê": src.price,
        "Ngày vào ở": src.moveIn, "Ảnh đại diện": "", "Danh sách ảnh": "", "Video": "",
        "Ngày thêm vào hệ thống": src.first || (pad2(n.d) + "/" + pad2(n.m) + "/" + n.y),
        "Hiển thị trên Web": inactive(src.note) ? "Không" : "Có",
      });
      stat.added++; inactive(src.note) ? stat.off++ : stat.on++;
      touched.add(id);
      continue;
    }

    const out = next[pos];
    touched.add(id);
    const was = key(out["Hiển thị trên Web"]) === "có";
    const ok = complete(src);
    const show = ok && !inactive(src.note);

    if (ok) {
      out["Tòa"] = src.tower;
      out["Loại"] = src.type;
      out["Diện tích"] = src.area;
      out["Nội thất"] = src.furniture || out["Nội thất"] || "";
      out["Giá thuê"] = src.price;
      out["Ngày vào ở"] = src.moveIn;
      if (!txt(out["Ngày thêm vào hệ thống"]) && src.first)
        out["Ngày thêm vào hệ thống"] = src.first;
    }
    out["Hiển thị trên Web"] = show ? "Có" : "Không";
    stat.updated++;
    if (!was && show) stat.on++;
    if (was && !show) stat.off++;
  }

  for (const r of next) {
    const id = txt(r["Mã nội bộ"]);
    if (!ID_RE.test(id) || touched.has(id)) continue;
    if (key(r["Hiển thị trên Web"]) === "có") {
      r["Hiển thị trên Web"] = "Không";
      stat.missing++;
    }
  }
  return { next, stat };
}

const stable = x => JSON.stringify(x) + "\n";

async function main() {
  const raw = readFileSync(DATA, "utf8");\n  const old = JSON.parse(raw);
  if (!Array.isArray(old) || old.length < 150)
    throw new Error("data.json rỗng/bất thường; dừng an toàn");

  const src = await loadCtv();
  const result = sync(old, src.map);
  const before = raw, after = stable(result.next);

  console.log("CTV: " + src.nonEmpty + " dòng, " + src.map.size + " ID hợp lệ.");
  for (const r of src.invalid)
    console.log("::warning::Bỏ qua ID không hợp lệ " + (r.id || "(trống)") +
      " tại " + r.tab + "!" + r.row);
  console.log("Đối chiếu: cập nhật " + result.stat.updated +
    ", thêm " + result.stat.added + ", bật " + result.stat.on +
    ", tắt " + result.stat.off + ", tắt vì rời CTV " + result.stat.missing + ".");

  if (before === after) {
    console.log("data.json đã khớp Sheet CTV; không có thay đổi.");
    return;
  }
  if (!DRY) writeFileSync(DATA, after, "utf8");
  console.log(DRY ? "Chế độ --thu: không ghi file." :
    "Đã ghi data.json (" + result.next.length + " dòng).");
}

main().catch(err => {
  console.error("::error::" + (err.stack || err.message || err));
  process.exit(1);
});
