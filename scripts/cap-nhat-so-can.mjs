#!/usr/bin/env node
/*!
 * cap-nhat-so-can.mjs — Cập nhật số căn và tháng trong thẻ SEO tĩnh
 * timthuesmartcity.com
 *
 * Vì sao cần script này: số căn nằm trong <title> / og:title / meta
 * description, còn tháng nằm trong <title> / og:title / <h1> của trang chủ.
 * dong-bo-can.js chạy trong trình duyệt nên sửa được nội dung trong <body>,
 * nhưng KHÔNG sửa được thẻ mà Google đọc lúc crawl. Hai loại số này vì thế
 * lệch dần theo thời gian.
 *
 * Script chạy trong GitHub Actions, sửa trực tiếp file HTML trong repo.
 *
 * NGUYÊN TẮC:
 *   - Logic đếm căn phải GIỐNG HỆT dong-bo-can.js. Mọi thay đổi bộ lọc ở đó
 *     phải được đồng bộ sang đây, nếu không title sẽ hứa khác lưới căn.
 *   - Chỉ thay con số và ngày/tháng, giữ nguyên 100% phần chữ của tiêu đề
 *     và của description.
 *   - Danh sách trang cần sửa được QUÉT từ repo (trang nào khai báo
 *     #bo-loc-trang thì là trang danh mục), không viết cứng.
 *   - Số căn về 0 -> giữ nguyên title cũ và ghi cảnh báo. Gần như chắc chắn
 *     đó là lỗi dữ liệu chứ không phải hết căn thật.
 *   - KHÔNG BAO GIỜ ghi vào data.json. File đó do Apps Script đẩy lên.
 *
 * Chạy tay để xem trước, không sửa file:  node scripts/cap-nhat-so-can.mjs --thu
 */

import { readFileSync, writeFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const GOC = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const CHI_THU = process.argv.includes("--thu") || process.argv.includes("--dry-run");

const BO_QUA_THU_MUC = new Set([".git", ".github", "node_modules", "images", "scripts"]);

/* ===================================================================
 * PHẦN 1 — Logic đếm căn, port nguyên từ dong-bo-can.js
 * =================================================================== */

function chuan(v) { return String(v == null ? "" : v).trim(); }
function khoa(v) { return chuan(v).toLowerCase(); }

function laCanHopLe(r) {
  const v = khoa(r["Hiển thị trên Web"] || r["Hiển thị trên web"] || r["Hiển thị"]);
  return v === "có" || v === "co" || v === "yes" || v === "true";
}

function soTien(v) {
  if (typeof v === "number") return v;
  return Number(chuan(v).replace(/[^\d]/g, "") || 0);
}

/* Ánh xạ mã tòa -> tên phân khu (giống hệt dong-bo-can.js, tiền tố dài đứng trước) */
function tenPhanKhu(toa) {
  const t = chuan(toa).toUpperCase().replace(/[\s.\-_]/g, "");
  if (!t) return "";
  if (t.indexOf("MAS") === 0 || t.indexOf("WEST") === 0) return "Masteri";
  if (t.indexOf("SA") === 0) return "Sakura";
  if (t.indexOf("GS") === 0) return "Miami";
  if (t.indexOf("TC") === 0) return "Canopy";
  if (t.indexOf("TK") === 0) return "Tonkin";
  if (/^I\d/.test(t)) return "Imperia";
  if (/^A\d/.test(t)) return "Lumiere";
  if (/^V\d/.test(t)) return "Victoria";
  if (/^S\d/.test(t)) return "Sapphire";
  if (/^G\d/.test(t)) return "Sola Park";
  return "";
}

function khopBoLoc(r, bl) {
  if (bl.loai && khoa(r["Loại"]) !== khoa(bl.loai)) return false;
  if (bl.phanKhu && khoa(tenPhanKhu(r["Tòa"])) !== khoa(bl.phanKhu)) return false;
  if (bl.noiThat && khoa(r["Nội thất"]) !== khoa(bl.noiThat)) return false;
  const g = soTien(r["Giá thuê"]);
  if (bl.giaTren && !(g > bl.giaTren)) return false;
  if (bl.giaMax && !(g > 0 && g <= bl.giaMax)) return false;
  return true;
}

/* Đúng ba điều kiện mà dong-bo-can.js dùng để chọn căn đưa lên lưới */
function demCan(duLieu, bl) {
  let n = 0;
  for (const r of duLieu) {
    if (laCanHopLe(r) && chuan(r["Mã nội bộ"]) && khopBoLoc(r, bl)) n++;
  }
  return n;
}

/* ===================================================================
 * PHẦN 2 — Quét repo tìm trang danh mục
 * =================================================================== */

function quetHtml(thuMuc, ra = []) {
  for (const ten of readdirSync(thuMuc)) {
    if (BO_QUA_THU_MUC.has(ten)) continue;
    const duong = join(thuMuc, ten);
    if (statSync(duong).isDirectory()) quetHtml(duong, ra);
    else if (ten.endsWith(".html")) ra.push(duong);
  }
  return ra;
}

function docBoLoc(html) {
  const m = html.match(/<script[^>]*id="bo-loc-trang"[^>]*>([\s\S]*?)<\/script>/);
  if (!m) return null;
  try { return JSON.parse(m[1]); } catch { return null; }
}

/* ===================================================================
 * PHẦN 3 — Sửa thẻ SEO
 * =================================================================== */

/* Bắt đúng phần text bên trong <title>…</title> */
const RE_TITLE = /(<title[^>]*>)([\s\S]*?)(<\/title>)/i;
/* Bắt đúng giá trị content của một thẻ meta theo property/name */
function reMeta(khoaThe, ten) {
  return new RegExp(
    `(<meta[^>]*\\b${khoaThe}="${ten}"[^>]*\\bcontent=")([^"]*)(")`, "i");
}
const RE_H1 = /(<h1[^>]*>)([\s\S]*?)(<\/h1>)/i;

/* Thay con số trong "68 căn" -> "40 căn". Giữ nguyên mọi chữ còn lại. */
const RE_SO_CAN = /(\d+)(\s+căn)/;

function thaySoCan(doan, soMoi) {
  if (!RE_SO_CAN.test(doan)) return { doan, doiRoi: false };
  const moi = doan.replace(RE_SO_CAN, (_, __, sau) => soMoi + sau);
  return { doan: moi, doiRoi: moi !== doan };
}

/* --- Description ---
 * Description có hai con số trôi theo thời gian: số căn ("Danh sách 33 căn…")
 * và ngày ("cập nhật 24/07/2026"). Trước đây script không đụng tới nên
 * description lệch hẳn so với <title> — ví dụ title ghi 16 căn còn
 * description ghi 12 căn.
 *
 * Hai regex dưới đây neo vào đúng cụm chữ đứng ngay trước con số, nên chỉ
 * con số và ngày bị thay, còn lại giữ nguyên từng ký tự.
 *
 * Chữ "cập nhật" trong repo có cả hai kiểu viết hoa/thường (8 chỗ viết
 * thường, 3 chỗ viết hoa ở <meta name="description">; 15/10 ở og:description).
 * Regex bắt cả hai và trả lại đúng cụm đã khớp, không tự chuẩn hoá kiểu viết.
 */
const RE_DESC_SO_CAN = /(Danh sách\s+)\d+(\s+căn)/;
const RE_DESC_NGAY = /([Cc]ập nhật\s+)\d{2}\/\d{2}\/\d{4}/;

/* Google cắt description quanh mốc này. Vượt thì ghi cảnh báo để rà tay,
   không tự cắt chữ — cắt máy móc dễ đứt câu giữa chừng. */
const DAI_TOI_DA_DESC = 165;

function thayTrongDescription(doan, soMoi, ngayMoi, ten, nhan, canhBao) {
  let moi = doan;
  let khop = false;

  if (RE_DESC_SO_CAN.test(moi)) {
    moi = moi.replace(RE_DESC_SO_CAN, (_, truoc, sau) => truoc + soMoi + sau);
    khop = true;
  } else {
    canhBao.push(`${ten} ${nhan}: không khớp mẫu "Danh sách N căn" — GIỮ NGUYÊN số căn.`);
  }

  if (RE_DESC_NGAY.test(moi)) {
    moi = moi.replace(RE_DESC_NGAY, (_, truoc) => truoc + ngayMoi);
    khop = true;
  } else if (/[Cc]ập nhật/.test(moi)) {
    /* Có chữ "cập nhật" nhưng ngày viết theo kiểu khác — đây mới là bất
       thường đáng báo. */
    canhBao.push(`${ten} ${nhan}: có chữ "cập nhật" nhưng không khớp mẫu DD/MM/YYYY — GIỮ NGUYÊN ngày.`);
  }
  /* Description không nhắc tới ngày thì không có gì để đồng bộ — im lặng.
     14/25 trang đang như vậy, cảnh báo ở đây chỉ làm trôi cảnh báo thật. */

  if (!khop) return { doan, doiRoi: false };
  if (moi.length > DAI_TOI_DA_DESC) {
    canhBao.push(`${ten} ${nhan}: dài ${moi.length} ký tự (> ${DAI_TOI_DA_DESC}) — nên rà tay.`);
  }
  return { doan: moi, doiRoi: moi !== doan };
}

/* Ngày hôm nay theo giờ Việt Nam, dạng DD/MM/YYYY. */
function ngayVietNam() {
  const gio = new Date(Date.now() + 7 * 60 * 60 * 1000);
  const hai = (n) => String(n).padStart(2, "0");
  return `${hai(gio.getUTCDate())}/${hai(gio.getUTCMonth() + 1)}/${gio.getUTCFullYear()}`;
}

/* Áp một hàm biến đổi lên đúng một vùng khớp regex, chừa nguyên phần bọc ngoài */
function suaVung(html, re, bienDoi) {
  const m = html.match(re);
  if (!m) return { html, doiRoi: false };
  const kq = bienDoi(m[2]);
  if (!kq.doiRoi) return { html, doiRoi: false };
  const thay = m[1] + kq.doan + m[3];
  return {
    html: html.slice(0, m.index) + thay + html.slice(m.index + m[0].length),
    doiRoi: true,
  };
}

function capNhatTrangDanhMuc(duong, html, soCan, log, canhBao) {
  const ten = relative(GOC, duong);
  const ngay = ngayVietNam();
  let doi = false;

  /* Thứ tự: <title>, og:title, rồi <h1>. Trang danh mục hiện không để số căn
     trong <h1>, nhưng vẫn xử lý để sau này thêm vào là tự chạy. */
  for (const [nhan, re] of [
    ["<title>", RE_TITLE],
    ["og:title", reMeta("property", "og:title")],
    ["<h1>", RE_H1],
  ]) {
    const kq = suaVung(html, re, (d) => thaySoCan(d, soCan));
    if (kq.doiRoi) {
      html = kq.html;
      doi = true;
      log.push(`  ${ten}  ${nhan} -> ${soCan} căn`);
    }
  }

  /* Description: số căn + ngày. Regex nào không khớp thì phần đó giữ nguyên
     và ghi cảnh báo — không throw, không làm hỏng cả lượt chạy. */
  for (const [nhan, re] of [
    ["description", reMeta("name", "description")],
    ["og:description", reMeta("property", "og:description")],
  ]) {
    if (!re.test(html)) {
      canhBao.push(`${ten}: không có thẻ ${nhan} — bỏ qua.`);
      continue;
    }
    const kq = suaVung(html, re, (d) =>
      thayTrongDescription(d, soCan, ngay, ten, nhan, canhBao));
    if (kq.doiRoi) {
      html = kq.html;
      doi = true;
      log.push(`  ${ten}  ${nhan} -> ${soCan} căn, ${ngay}`);
    }
  }
  return { html, doi };
}

/* --- Tháng/năm của trang chủ --- */

/* Giờ Việt Nam (UTC+7). Runner của GitHub chạy theo UTC nên phải quy đổi,
   nếu không thì đêm 31 tháng trước sẽ ghi sai tháng. */
function thangVietNam() {
  const gio = new Date(Date.now() + 7 * 60 * 60 * 1000);
  return {
    thang: String(gio.getUTCMonth() + 1).padStart(2, "0"),
    nam: String(gio.getUTCFullYear()),
  };
}

function capNhatThangTrangChu(duong, html, log) {
  const { thang, nam } = thangVietNam();
  const ten = relative(GOC, duong);
  let doi = false;

  /* Hai cách viết đang dùng trong repo: "T07/2026" ở <title> và
     "tháng 07/2026" ở og:title / twitter:title / <h1>. Regex neo vào đúng
     từng thẻ, KHÔNG thay toàn file — trong index.html có rất nhiều comment
     ghi ngày kiểu "(thêm 23/07/2026)" và phải giữ nguyên. */
  const dangViet = [
    [/\bT(\d{2})\/(\d{4})\b/, `T${thang}/${nam}`],
    [/\btháng (\d{2})\/(\d{4})\b/, `tháng ${thang}/${nam}`],
  ];

  const thayThang = (doan) => {
    for (const [re, moi] of dangViet) {
      if (re.test(doan)) {
        const sua = doan.replace(re, moi);
        return { doan: sua, doiRoi: sua !== doan };
      }
    }
    return { doan, doiRoi: false };
  };

  for (const [nhan, re] of [
    ["<title>", RE_TITLE],
    ["og:title", reMeta("property", "og:title")],
    ["twitter:title", reMeta("name", "twitter:title")],
    ["<h1>", RE_H1],
  ]) {
    const kq = suaVung(html, re, thayThang);
    if (kq.doiRoi) {
      html = kq.html;
      doi = true;
      log.push(`  ${ten}  ${nhan} -> ${thang}/${nam}`);
    }
  }
  return { html, doi };
}

/* ===================================================================
 * PHẦN 4 — Chạy
 * =================================================================== */

function main() {
  const duLieu = JSON.parse(readFileSync(join(GOC, "data.json"), "utf8"));
  if (!Array.isArray(duLieu) || duLieu.length === 0) {
    console.error("LỖI: data.json rỗng hoặc không phải mảng. Dừng, không sửa gì.");
    process.exit(1);
  }
  console.log(`data.json: ${duLieu.length} dòng.`);

  const tatCaHtml = quetHtml(GOC);
  const daSua = [];
  const canhBao = [];
  const nhatKy = [];

  /* --- Trang danh mục: số căn --- */
  let soTrangDanhMuc = 0;
  for (const duong of tatCaHtml) {
    const html = readFileSync(duong, "utf8");
    const bl = docBoLoc(html);
    if (!bl) continue;
    soTrangDanhMuc++;

    const soCan = demCan(duLieu, bl);
    const ten = relative(GOC, duong);

    /* Ngưỡng an toàn: 0 căn gần như luôn là lỗi dữ liệu (Apps Script đẩy lên
       file lỗi, đổi tên cột, sai chính tả giá trị lọc...). Viết "0 căn" lên
       tiêu đề sẽ hại hơn là để tạm số cũ. */
    if (soCan === 0) {
      canhBao.push(`${ten}: đếm được 0 căn với bộ lọc ${JSON.stringify(bl)} — GIỮ NGUYÊN title cũ.`);
      continue;
    }

    const kq = capNhatTrangDanhMuc(duong, html, soCan, nhatKy, canhBao);
    if (kq.doi) {
      if (!CHI_THU) writeFileSync(duong, kq.html, "utf8");
      daSua.push(ten);
    }
  }
  console.log(`Quét thấy ${soTrangDanhMuc} trang danh mục.`);

  /* --- Trang chủ: tháng/năm --- */
  const trangChu = join(GOC, "index.html");
  const htmlChu = readFileSync(trangChu, "utf8");
  const kqChu = capNhatThangTrangChu(trangChu, htmlChu, nhatKy);
  if (kqChu.doi) {
    if (!CHI_THU) writeFileSync(trangChu, kqChu.html, "utf8");
    if (!daSua.includes("index.html")) daSua.push("index.html");
  }

  /* --- Báo cáo --- */
  if (nhatKy.length) {
    console.log("\nThay đổi:");
    for (const d of nhatKy) console.log(d);
  }
  if (canhBao.length) {
    console.log("\n⚠️  CẢNH BÁO:");
    for (const c of canhBao) console.log(`  ${c}`);
  }
  console.log(
    `\n${daSua.length === 0 ? "Không có gì thay đổi." : `Đã cập nhật ${daSua.length} file.`}` +
    (CHI_THU ? " (chế độ --thu: KHÔNG ghi file)" : "")
  );
}

main();
