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
  const maxAttempts = 4;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const r = await fetch(url, {
        headers: { "user-agent": "Mozilla/5.0", "cache-control": "no-cache" },
        signal: AbortSignal.timeout(25000),
      });
      // 4xx (trừ 429) thường là quyền truy cập hoặc tên tab sai: không thử lại.
      if (!r.ok && r.status !== 429 && r.status < 500)
        throw new Error(tab + ": HTTP " + r.status);
      if (!r.ok) throw new Error(tab + ": HTTP " + r.status + " (tạm thời)");
      const body = await r.text();
      if (!body.includes("ID CĂN"))
        throw new Error(tab + ": phản hồi không phải Sheet CTV");
      const rows = parseCsv(body);
      if (rows.length < 2)
        throw new Error(tab + ": dữ liệu tab rỗng/bất thường");
      return rows;
    } catch (err) {
      const retryable = err.name === "TimeoutError" ||
        /HTTP (?:429|5\d\d)|fetch failed|network|socket/i.test(err.message);
      if (!retryable || attempt === maxAttempts) throw err;
      const delay = 1500 * 2 ** (attempt - 1);
      console.warn("::warning::" + tab + ": " + err.message +
        " — thử lại " + (attempt + 1) + "/" + maxAttempts +
        " sau " + delay + "ms");
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
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

// Mỗi lần liên lạc tạo thêm một ghi chú. Chỉ cập nhật trạng thái khi đầu
// chủ nói rõ "còn" hoặc "đã thuê/không cho thuê". KNM/tắt máy không được
// xóa đi kết luận "không cho thuê" đã được xác nhận trước đó.
function ownerStatus(note) {
  const s = txt(note).normalize("NFC").toLocaleLowerCase("vi");
  const dated = [...s.matchAll(/\b(\d{1,2})\/(\d{1,2})(?:\/(\d{4}))?\b/g)];
  const parts = [];
  if (dated.length === 0) parts.push({ score: 0, text: s });
  else {
    const preface = s.slice(0, dated[0].index).trim();
    if (preface) parts.push({ score: 0, text: preface });
    for (let i = 0; i < dated.length; i++) {
      const m = dated[i], day = Number(m[1]), month = Number(m[2]);
      if (day < 1 || day > 31 || month < 1 || month > 12) continue;
      const year = Number(m[3] || nowVN().y);
      parts.push({
        score: year * 10000 + month * 100 + day,
        text: s.slice(m.index + m[0].length,
          i + 1 < dated.length ? dated[i + 1].index : s.length).trim(),
      });
    }
  }
  // 2 người gọi cùng ngày: ghi chú phía sau là thông tin mới hơn.
  parts.sort((a, b) => a.score - b.score);
  let state = null;
  for (const part of parts) {
    const t = part.text.replace(/\bc\s+ho\s+thuê\b/g, "cho thuê")
      .replace(/\s+/g, " ").trim();
    const unavailable =
      /cho\s*thuê\s*rồi|cho\s*thuê\s*xong|đã\s*cho\s*thuê|đã\s*thuê|thuê\s*rồi|đã\s*chốt|chốt\s*thuê|có\s*khách\s*thuê|đã\s*có\s*khách|(?:không|kh|k)\s*cho\s*thuê(?:\s*nữa)?|không\s*còn\s*cho\s*thuê|dừng\s*(?:cho\s*)?thuê|ngừng\s*(?:cho\s*)?thuê|chỉ\s*bán|để\s*ở[^\n]*?(?:không|k)\s*cho\s*thuê/.test(t);
    const available = /(?:^|\s)(?:vẫn\s*)?còn(?:\b|\s|$)|chưa\s*cho\s*thuê|còn\s*trống/.test(t);
    if (unavailable) state = "unavailable";
    else if (available) state = "available";
  }
  return state;
}
function inactive(note) {
  return ownerStatus(note) === "unavailable";
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
  if (map.size < 250 || map.size > 1200)
    throw new Error("Số ID hợp lệ bất thường: " + map.size + " (ngưỡng 250-1200)");
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
    // Giữ nguyên quy tắc An Việt cho nguồn cũ, nhưng KHÔNG tắt TT.* của Thu Thảo.
    // TT.* được đối soát độc lập sau khi tải đủ cả 5 tab nguồn thứ hai.
    if (touched.has(id) || id.startsWith("TT.")) continue;
    if (key(r["Hiển thị trên Web"]) === "có") {
      r["Hiển thị trên Web"] = "Không";
      stat.missing++;
    }
  }
  return { next, stat };
}


// ===== NGUỒN THỨ HAI: THU THẢO / MD HOMES (Smart City) =====
// Bảng có tiêu đề ở hàng 4-6, cột A=STT, B=Ngày cập nhật,
// C=Khu/phân khu, D=Diện tích, E=Đồ đạc, F=Ngày vào, G=Giá,
// H=Hoa hồng, I=Thư mục ảnh. Không đọc/hiển thị hoa hồng hoặc SĐT đối tác.
// Dùng gid cố định vì tab Studio có BỐN dấu cách cuối tên.
const THAO_SHEET = "1iZ6_Oy2AASaUbzFOtXbOd-yx93F2kTIVPnc3we4jgM0";
const THAO_TABS = [
  { gid: 0, name: "Studio", prefix: "ST", type: "Studio" },
  { gid: 849168037, name: "1PN", prefix: "1N", type: "1 Ngủ" },
  { gid: 1103219392, name: "2PN", prefix: "2N", type: "2 Ngủ" },
  { gid: 1789817511, name: "2PN+1", prefix: "2NP", type: "2 Ngủ +" },
  { gid: 26713528, name: "3PN", prefix: "3N", type: "3 Ngủ" },
];
const THAO_ID = /^TT\.(?:ST|1N|2N|2NP|3N)\.\d{3,6}$/;

function thaoPrice(v) {
  const s = txt(v).toLowerCase().replace(/\s+/g, " ");
  // Khoảng giá và hai phương án giá không phải một giá chắc chắn: không đoán.
  if (/(?:\d\s*[-–]\s*\d)|\(\s*[^)]*\d+(?:[,.]\d+)?\s*tr/i.test(s)) return 0;
  const m = s.match(/^(\d+(?:[,.]\d{1,2})?)\s*(?:tr|triệu)\b/i) ||
            s.match(/^(\d+(?:[,.]\d{1,2})?)\s*tr/i);
  if (!m) return 0;
  const n = Number(m[1].replace(",", "."));
  return n >= 3 && n <= 100 ? Math.round(n * 1000000) : 0;
}

function thaoDate(v) {
  const s = txt(v).trim();
  if (!s) return "";
  if (/^\d{5}$/.test(s)) {
    const d = new Date(Date.UTC(1899, 11, 30) + Number(s) * 86400000);
    return pad2(d.getUTCDate()) + "/" + pad2(d.getUTCMonth() + 1) + "/" + d.getUTCFullYear();
  }
  const m = s.match(/^(\d{1,2})[./-](\d{1,2})[./-](20\d{2})$/);
  if (m) return pad2(Number(m[1])) + "/" + pad2(Number(m[2])) + "/" + m[3];
  return "";
}

function thaoMove(v) {
  const s = txt(v);
  if (!s || /^(?:vào\s*luôn|vào\s*ngay|ở\s*ngay|luôn)$/i.test(s)) return "";
  return thaoDate(s) || s; // T10 / T12 giữ nguyên, KHÔNG phán đoán ngày.
}

function thaoFurniture(v) {
  const s = key(v);
  if (s === "đcb" || /đồ\s*cơ\s*bản/.test(s)) return "Đồ Cơ bản";
  if (s === "nb" || /nguyên\s*bản/.test(s)) return "Nhà Nguyên Bản";
  if (/full\s*đồ|full\s*nội\s*thất/.test(s)) return "Full nội thất";
  if (/full\s*gỗ/.test(s)) return "Full gỗ"; // KHÔNG quảng cáo nhầm thành full nội thất
  return txt(v);
}

function thaoFolder(v) {
  const s = txt(v);
  const m = s.match(/^https:\/\/drive\.google\.com\/drive\/folders\/[A-Za-z0-9_-]{10,}(?:[?&#].*)?$/);
  return m ? s : "";
}

async function fetchThaoTab(tab) {
  const url = "https://docs.google.com/spreadsheets/d/" + THAO_SHEET +
    "/gviz/tq?tqx=out:csv&headers=0&gid=" + tab.gid;
  for (let attempt = 1; attempt <= 4; attempt++) {
    try {
      const res = await fetch(url, {
        headers: { "user-agent": "Mozilla/5.0", "cache-control": "no-cache" },
        signal: AbortSignal.timeout(25000),
      });
      if (!res.ok) throw new Error(tab.name + " HTTP " + res.status);
      const body = await res.text();
      if (/<!doctype|<html|accounts\.google\.com/i.test(body.slice(0, 1000)))
        throw new Error(tab.name + ": nguồn yêu cầu đăng nhập Google");
      const rows = parseCsv(body);
      // Tên cột KHÔNG nằm ở hàng 1 như An Việt.
      const header = rows.findIndex(c => key(c[0]) === "stt" &&
        /giá|gia/i.test(txt(c[6])) && /tòa|khu/i.test(txt(c[2])));
      if (header < 0 || header > 12 || rows.length - header < 15)
        throw new Error(tab.name + ": thiếu header hoặc số hàng bất thường");
      return rows.slice(header + 1);
    } catch (e) {
      const retry = /HTTP (?:429|5\d\d)|timeout|fetch failed|network|socket/i.test(e.message);
      if (!retry || attempt === 4) throw e;
      await new Promise(resolve => setTimeout(resolve, 1200 * 2 ** (attempt - 1)));
    }
  }
}

async function loadThao() {
  const map = new Map();
  const stats = { rows: 0, excludedLumi: 0, badPrice: 0, incomplete: 0, photos: 0 };
  for (const tab of THAO_TABS) {
    const rows = await fetchThaoTab(tab);
    let tabCount = 0;
    for (const c of rows) {
      const stt = txt(c[0]);
      if (key(stt) === "stt" || !stt) continue;
      if (!/^\d{3,6}$/.test(stt)) continue;
      const id = "TT." + tab.prefix + "." + stt;
      const region = txt(c[2]);
      if (key(region).replace(/\s+/g, "") === "lumihn") {
        stats.excludedLumi++;
        continue; // Lumi Hanoi là dự án riêng, không lẫn vào Smart City.
      }
      if (!region || !/^(?:lumiere|solapark|gs|imperia|mas|s[1-4]|sa|tc|tk)$/i.test(region)) {
        throw new Error("Thu Thảo: khu/tòa chưa nhận diện tại " + tab.name + " STT " + stt);
      }
      if (map.has(id)) throw new Error("Thu Thảo: trùng mã " + id);
      const src = {
        id, type: tab.type, tower: region, area: area(c[3]),
        furniture: thaoFurniture(c[4]), moveIn: thaoMove(c[5]),
        price: thaoPrice(c[6]), updated: thaoDate(c[1]),
        folder: thaoFolder(c[8]),
      };
      if (!src.price) stats.badPrice++;
      if (!src.area || !src.furniture) stats.incomplete++;
      if (src.folder) stats.photos++;
      map.set(id, src);
      tabCount++;
    }
    if (tabCount < 15) throw new Error("Thu Thảo: tab " + tab.name + " chỉ có " + tabCount + " căn");
    stats.rows += tabCount;
  }
  if (map.size < 500 || map.size > 1200)
    throw new Error("Thu Thảo: số căn bất thường " + map.size + " (giữ snapshot cũ)");
  return { map, stats };
}

function syncThao(rows, source) {
  const index = new Map();
  rows.forEach((r, i) => {
    const id = txt(r["Mã nội bộ"]);
    if (THAO_ID.test(id) && index.has(id)) throw new Error("Trùng mã Thu Thảo trong data.json: " + id);
    if (id && !index.has(id)) index.set(id, i);
  });
  const stat = { added: 0, updated: 0, hidden: 0, incomplete: 0 };
  for (const [id, src] of source.entries()) {
    const completeRow = src.tower && src.area > 0 && src.price > 0 && src.furniture;
    const show = Boolean(completeRow);
    if (!show) stat.incomplete++;
    const pos = index.get(id);
    if (pos == null) {
      if (!show) continue;
      const n = nowVN();
      rows.push({
        "Mã nội bộ": id, "Tòa": src.tower, "Loại": src.type,
        "Diện tích": src.area, "Nội thất": src.furniture,
        "Giá thuê": src.price, "Ngày vào ở": src.moveIn,
        "Ảnh đại diện": "", "Danh sách ảnh": "", "Video": "",
        "Ngày thêm vào hệ thống": src.updated || (pad2(n.d) + "/" + pad2(n.m) + "/" + n.y),
        "Hiển thị trên Web": "Có", "Nguồn CTV": "Thu Thảo",
        "Thư mục ảnh CTV": src.folder,
      });
      stat.added++;
      continue;
    }
    const row = rows[pos];
    if (show) {
      row["Tòa"] = src.tower;
      row["Loại"] = src.type;
      row["Diện tích"] = src.area;
      row["Nội thất"] = src.furniture;
      row["Giá thuê"] = src.price;
      row["Ngày vào ở"] = src.moveIn;
      row["Thư mục ảnh CTV"] = src.folder;
      row["Nguồn CTV"] = "Thu Thảo";
    }
    row["Hiển thị trên Web"] = show ? "Có" : "Không";
    stat.updated++;
  }
  for (const row of rows) {
    const id = txt(row["Mã nội bộ"]);
    if (!THAO_ID.test(id) || source.has(id)) continue;
    if (key(row["Hiển thị trên Web"]) === "có") {
      row["Hiển thị trên Web"] = "Không";
      stat.hidden++;
    }
  }
  return stat;
}

const stable = x => JSON.stringify(x) + "\n";

async function main() {
  const raw = readFileSync(DATA, "utf8");
  const old = JSON.parse(raw);
  if (!Array.isArray(old) || old.length < 150)
    throw new Error("data.json rỗng/bất thường; dừng an toàn");

  const src = await loadCtv();
  const result = sync(old, src.map);
  // Không xoá/ẩn TT.* nếu Sheet mới mất mạng hoặc bị đổi quyền: giữ bản đang có.
  let thaoStat = null, thaoSync = null;
  try {
    const thao = await loadThao();
    thaoStat = thao.stats;
    thaoSync = syncThao(result.next, thao.map);
  } catch (err) {
    console.warn("::warning::Không đọc được toàn bộ Sheet Thu Thảo, giữ dữ liệu TT cũ: " + err.message);
  }
  const before = raw, after = stable(result.next);

  console.log("CTV: " + src.nonEmpty + " dòng, " + src.map.size + " ID hợp lệ.");
  for (const r of src.invalid)
    console.log("::warning::Bỏ qua ID không hợp lệ " + (r.id || "(trống)") +
      " tại " + r.tab + "!" + r.row);
  if (thaoStat)
    console.log("Thu Thảo: " + thaoStat.rows + " căn Smart City, bỏ qua " +
      thaoStat.excludedLumi + " Lumi HN, " + thaoStat.badPrice + " giá chưa rõ, " +
      thaoStat.photos + " link thư mục ảnh; thêm " + thaoSync.added +
      ", cập nhật " + thaoSync.updated + ", ẩn căn rời nguồn " + thaoSync.hidden + ".");
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
