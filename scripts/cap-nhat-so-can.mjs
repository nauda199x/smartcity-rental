#!/usr/bin/env node
/*!
 * cap-nhat-so-can.mjs — Cập nhật số căn, tháng và khối ItemList trong thẻ SEO tĩnh
 * timthuesmartcity.com
 *
 * Vì sao cần script này: số căn nằm trong <title> / og:title / meta
 * description, còn tháng nằm trong <title> / og:title / <h1> của trang chủ.
 * dong-bo-can.js chạy trong trình duyệt nên sửa được nội dung trong <body>,
 * nhưng KHÔNG sửa được thẻ mà Google đọc lúc crawl. Hai loại số này vì thế
 * lệch dần theo thời gian.
 *
 * Khối application/ld+json cũng vậy: numberOfItems và itemListElement của
 * ItemList trước đây viết tay nên đóng băng từ lúc viết, mô tả những căn đã
 * thuê xong từ lâu. Script dựng lại hai khoá đó từ data.json.
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

/* SAO CHÉP NGUYÊN VĂN từ hàm dienTich trong dong-bo-can.js.
   Hai bản PHẢI LUÔN GIỐNG NHAU: diện tích ở đây đi vào chuỗi name của
   ListItem, còn bản kia đi vào thẻ căn trên lưới. Lệch nhau thì structured
   data ghi diện tích khác với con số khách đọc trên trang. */
function dienTich(v) {
  if (typeof v === "number") return v;
  return parseFloat(chuan(v).replace(",", ".").replace(/[^\d.]/g, "")) || 0;
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
function canLenLuoi(r, bl) {
  return laCanHopLe(r) && chuan(r["Mã nội bộ"]) && khopBoLoc(r, bl);
}

/* Có ảnh bìa hay không — logic hàm anhBia trong dong-bo-can.js, chỉ xét có/không
   nên không cần driveUrlToViewUrl (hàm đó chỉ đổi dạng URL, không đổi rỗng/không
   rỗng). Dùng để tách hai nhóm khi sắp xếp, xem dsCanLenLuoi. */
function coAnhBia(r) {
  if (chuan(r["Ảnh đại diện"])) return true;
  return Boolean(chuan(r["Danh sách ảnh"]).split(/\s*\n\s*/)[0]);
}

/* Đúng tập căn VÀ đúng thứ tự mà dong-bo-can.js (hàm chay) dựng trên lưới:
     1. lọc bằng canLenLuoi;
     2. sắp xếp theo giá tăng dần;
     3. căn có ảnh bìa đứng trước, căn chưa có ảnh dồn xuống cuối, mỗi nhóm
        giữ nguyên thứ tự tương đối theo giá.
   Array.prototype.sort của Node 20 là sort ổn định (ES2019 bắt buộc), nên hai
   căn cùng giá luôn giữ thứ tự xuất hiện trong data.json — chạy lại script cho
   ra đúng kết quả cũ, không sinh diff giả. */
function dsCanLenLuoi(duLieu, bl) {
  const ds = duLieu.filter((r) => canLenLuoi(r, bl));
  ds.sort((a, b) => soTien(a["Giá thuê"]) - soTien(b["Giá thuê"]));
  const coAnh = [];
  const khongAnh = [];
  for (const r of ds) (coAnhBia(r) ? coAnh : khongAnh).push(r);
  return coAnh.concat(khongAnh);
}

/* Giá sàn = giá nhỏ nhất trong đúng tập căn mà dsCanLenLuoi trả về — cùng bộ
   lọc, cùng điều kiện, không thêm bớt gì. Nếu hai hàm này lệch nhau thì title
   sẽ hứa "N căn từ X triệu" với X không thuộc N căn đó.

   Căn giá <= 0 bị bỏ qua: đó là căn chưa điền giá hoặc ghi "Liên hệ", lấy làm
   giá sàn thì title hứa 0 triệu. */
function giaSan(duLieu, bl) {
  let min = 0;
  for (const r of duLieu) {
    if (!canLenLuoi(r, bl)) continue;
    const g = soTien(r["Giá thuê"]);
    if (g <= 0) continue;
    if (min === 0 || g < min) min = g;
  }
  return min;
}

/* Định dạng theo đúng kiểu đang dùng trên site: dấu phẩy thập phân, bỏ phần
   thập phân khi bằng 0. 5500000 -> "5,5"; 7000000 -> "7". */
function dinhDangTrieu(gia) {
  return String(Math.round(gia / 100000) / 10).replace(".", ",");
}

/* Khoảng giá (min/max) lấy trực tiếp từ đúng tập dsCan đã lọc — không quét
   lại duLieu bằng một bộ lọc riêng như giaSan(): dsCan là chính tập căn
   script đang dùng để đếm số căn và dựng ItemList, nên khoảng giá trong
   description phải tính thẳng từ đó, không có đường tính thứ hai để lệch
   nhau (Việc C, ràng buộc C.3). Căn giá <= 0 bị bỏ qua như giaSan(). */
function khoangGiaTuDsCan(dsCan) {
  let min = 0;
  let max = 0;
  for (const r of dsCan) {
    const g = soTien(r["Giá thuê"]);
    if (g <= 0) continue;
    if (min === 0 || g < min) min = g;
    if (g > max) max = g;
  }
  return { min, max };
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

/* Thay con số trong "từ 6,8 triệu" -> "từ 5,5 triệu". Neo vào cả chữ "từ" lẫn
   chữ "triệu" nên chỉ đúng con số giá sàn bị đổi; những chỗ khác cũng có số
   kèm "triệu" (ví dụ "dưới 10 triệu") không khớp và giữ nguyên.
   Trang không có cụm này thì không chèn thêm — đây là lý do hàm trả doiRoi
   false thay vì tự dựng chuỗi mới. */
const RE_GIA_SAN = /(từ\s+)[\d,.]+(\s+triệu)/;

function thayGiaSan(doan, giaChu) {
  if (!giaChu || !RE_GIA_SAN.test(doan)) return { doan, doiRoi: false };
  const moi = doan.replace(RE_GIA_SAN, (_, truoc, sau) => truoc + giaChu + sau);
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

/* --- Khoảng giá trong description (Việc C) ---
 * Một số trang có câu "giá <N> triệu–<M> triệu" trong description/
 * og:description (dấu – U+2013), nhưng trước đây script chỉ ghi lại số căn,
 * không ghi lại khoảng giá — sai ở 13/25 trang (đo 16/08/2026, ví dụ
 * /tonkin/: description ghi "8 triệu–16 triệu" trong khi bảng giá/lưới thật
 * là 8–14 triệu).
 *
 * Chỉ thay khi khớp ĐÚNG MỘT lần mẫu; 0 lần hoặc từ 2 lần trở lên thì giữ
 * nguyên + cảnh báo, không đoán (Việc C, ràng buộc C.1). Mẫu neo cả hai chữ
 * "triệu" nên không khớp nhầm dạng rút gọn "10–12 triệu" (một chữ "triệu"
 * duy nhất) — đó là ngưỡng giá trong TÊN danh mục, không phải khoảng giá
 * thật của tập căn đang trống, và không thuộc phạm vi Việc C.
 *
 * Bốn nhóm bắt giữ nguyên phần chữ quanh hai con số ("triệu–", " triệu")
 * đúng như đã có trong file, chỉ hai con số bị thay (ràng buộc C.2). */
const RE_KHOANG_GIA = /([\d,]+)(\s*triệu–)([\d,]+)(\s*triệu)/g;

function thayKhoangGiaTrongDescription(doan, giaKhoang, ten, nhan, canhBao) {
  const soLan = (doan.match(RE_KHOANG_GIA) || []).length;
  if (soLan !== 1) {
    const lyDo = soLan === 0 ? "không khớp mẫu" : `khớp mẫu ${soLan} lần`;
    canhBao.push(`${ten} ${nhan}: ${lyDo} "N triệu–M triệu" — GIỮ NGUYÊN khoảng giá, không đoán.`);
    return { doan, doiRoi: false };
  }
  /* Không căn nào trong dsCan có giá > 0 — cũng như giá sàn, gần như luôn là
     lỗi dữ liệu, giữ nguyên khoảng giá cũ thay vì viết "0 triệu". */
  if (giaKhoang.min <= 0 || giaKhoang.max <= 0) {
    canhBao.push(`${ten} ${nhan}: không tính được khoảng giá (không căn nào có giá > 0) — GIỮ NGUYÊN.`);
    return { doan, doiRoi: false };
  }
  const minChu = dinhDangTrieu(giaKhoang.min);
  const maxChu = dinhDangTrieu(giaKhoang.max);
  const moi = doan.replace(RE_KHOANG_GIA, (_, g1, g2, g3, g4) => minChu + g2 + maxChu + g4);
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

function capNhatTrangDanhMuc(duong, html, soCan, giaChu, giaKhoang, log, canhBao) {
  const ten = relative(GOC, duong);
  const ngay = ngayVietNam();
  let doi = false;
  let doiGia = false;   // có vùng nào thật sự đổi con số giá sàn không

  /* Thứ tự: <title>, og:title, rồi <h1>. Trang danh mục hiện không để số căn
     trong <h1>, nhưng vẫn xử lý để sau này thêm vào là tự chạy.
     Giá sàn chỉ áp cho <title> và og:title theo đúng phạm vi nhiệm vụ. */
  for (const [nhan, re, coGia] of [
    ["<title>", RE_TITLE, true],
    ["og:title", reMeta("property", "og:title"), true],
    ["<h1>", RE_H1, false],
  ]) {
    let daDoi = [];
    const kq = suaVung(html, re, (d) => {
      const a = thaySoCan(d, soCan);
      const b = coGia ? thayGiaSan(a.doan, giaChu) : { doan: a.doan, doiRoi: false };
      daDoi = [];
      if (a.doiRoi) daDoi.push(`${soCan} căn`);
      if (b.doiRoi) daDoi.push(`từ ${giaChu} triệu`);
      return { doan: b.doan, doiRoi: a.doiRoi || b.doiRoi };
    });
    if (kq.doiRoi) {
      html = kq.html;
      doi = true;
      if (daDoi.some((x) => x.startsWith("từ "))) doiGia = true;
      log.push(`  ${ten}  ${nhan} -> ${daDoi.join(", ")}`);
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
    let daDoi = [];
    const kq = suaVung(html, re, (d) => {
      const a = thayTrongDescription(d, soCan, ngay, ten, nhan, canhBao);
      const b = thayGiaSan(a.doan, giaChu);
      const c = thayKhoangGiaTrongDescription(b.doan, giaKhoang, ten, nhan, canhBao);
      daDoi = [];
      if (a.doiRoi) daDoi.push(`${soCan} căn, ${ngay}`);
      if (b.doiRoi) daDoi.push(`từ ${giaChu} triệu`);
      if (c.doiRoi) daDoi.push(`khoảng giá ${dinhDangTrieu(giaKhoang.min)}–${dinhDangTrieu(giaKhoang.max)} triệu`);
      return { doan: c.doan, doiRoi: a.doiRoi || b.doiRoi || c.doiRoi };
    });
    if (kq.doiRoi) {
      html = kq.html;
      doi = true;
      if (daDoi.some((x) => x.startsWith("từ "))) doiGia = true;
      log.push(`  ${ten}  ${nhan} -> ${daDoi.join(", ")}`);
    }
  }
  return { html, doi, doiGia };
}

/* --- Khối ItemList trong application/ld+json ---
 *
 * Mỗi trang danh mục có đúng một thẻ <script type="application/ld+json"> chứa
 * một @graph gồm BreadcrumbList, ItemList, FAQPage. Chỉ hai khoá
 * numberOfItems và itemListElement của ItemList được ghi đè; name, @type và
 * mọi khoá khác giữ nguyên, BreadcrumbList/FAQPage không bị đụng tới.
 *
 * Không tự tạo ItemList mới khi trang không có: khối JSON-LD là nội dung do
 * người viết, script chỉ đồng bộ con số, không phát minh structured data.
 */
const RE_LD_JSON = /(<script[^>]*type="application\/ld\+json"[^>]*>)([\s\S]*?)(<\/script>)/i;

/* URL từng ListItem phải trỏ vào trang chi tiết căn, không trỏ ngược về
   canonical của landing. Sổ đăng ký được sinh ngay trước bước này trong
   workflow nên là nguồn duy nhất ánh xạ Mã nội bộ -> slug trang căn. */
const TEN_MIEN = "https://timthuesmartcity.com";

function docUrlChiTietTheoMa(canhBao) {
  const duong = join(GOC, "can-ho", "danh-sach-trang.json");
  let raw;
  try {
    raw = JSON.parse(readFileSync(duong, "utf8"));
  } catch (e) {
    canhBao.push(`Không đọc được can-ho/danh-sach-trang.json (${e.message}) — ItemList sẽ giữ nguyên.`);
    return null;
  }
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    canhBao.push("can-ho/danh-sach-trang.json không phải object — ItemList sẽ giữ nguyên.");
    return null;
  }

  const ra = new Map();
  for (const [slug, rec] of Object.entries(raw)) {
    const ma = chuan(rec && rec.ma);
    if (!ma || !/^[a-z0-9-]+$/.test(slug)) continue;
    ra.set(ma, `${TEN_MIEN}/can-ho/${slug}/`);
  }
  return ra;
}

/* Chuỗi name của một ListItem, đúng định dạng đang dùng trong repo:
     {Loại} {Tòa} {diện tích}m² – {giá} triệu/tháng
   Diện tích làm tròn 0 thì bỏ hẳn cụm diện tích (không in "0m²"), giá <= 0 thì
   ghi "Liên hệ" và bỏ chữ "triệu/tháng". Dấu gạch là gạch ngang dài U+2013. */
function tenListItem(r) {
  const phan = [chuan(r["Loại"]), chuan(r["Tòa"])].filter(Boolean);
  const dt = Math.round(dienTich(r["Diện tích"]));
  if (dt > 0) phan.push(`${dt}m²`);
  const g = soTien(r["Giá thuê"]);
  phan.push("–", g > 0 ? `${dinhDangTrieu(g)} triệu/tháng` : "Liên hệ");
  return phan.join(" ");
}

function capNhatItemList(duong, html, dsCan, urlChiTietTheoMa, log, canhBao) {
  const ten = relative(GOC, duong);
  const m = html.match(RE_LD_JSON);
  if (!m) {
    canhBao.push(`${ten}: không có thẻ application/ld+json — BỎ QUA ItemList.`);
    return { html, doi: false };
  }

  let goc;
  try {
    goc = JSON.parse(m[2]);
  } catch (e) {
    canhBao.push(`${ten}: khối ld+json không parse được (${e.message}) — GIỮ NGUYÊN, BỎ QUA ItemList.`);
    return { html, doi: false };
  }

  /* Chấp nhận cả dạng @graph và dạng một đối tượng đơn lẻ, để trang viết theo
     kiểu khác cũng không bị bỏ sót. */
  const graph = Array.isArray(goc["@graph"]) ? goc["@graph"] : [goc];
  const dsItemList = graph.filter((x) => x && x["@type"] === "ItemList");
  if (dsItemList.length === 0) {
    canhBao.push(`${ten}: khối ld+json không có phần tử ItemList — BỎ QUA, không tự tạo mới.`);
    return { html, doi: false };
  }
  if (dsItemList.length > 1) {
    canhBao.push(`${ten}: có ${dsItemList.length} phần tử ItemList — BỎ QUA, không đoán khối nào là danh sách căn.`);
    return { html, doi: false };
  }

  if (!urlChiTietTheoMa) {
    canhBao.push(`${ten}: chưa có bản đồ URL chi tiết — GIỮ NGUYÊN ItemList.`);
    return { html, doi: false };
  }

  const itemList = dsItemList[0];
  const soCu = itemList.numberOfItems;

  /* Gán vào khoá đã tồn tại nên vị trí khoá trong JSON không đổi. */
  itemList.numberOfItems = dsCan.length;
  const thieuUrl = [];
  itemList.itemListElement = dsCan.map((r, i) => {
    const ma = chuan(r["Mã nội bộ"]);
    const url = ma ? urlChiTietTheoMa.get(ma) : "";
    const item = {
      "@type": "ListItem",
      position: i + 1,
      name: tenListItem(r),
    };
    if (url) item.url = url;
    else thieuUrl.push(ma || "(không có Mã nội bộ)");
    return item;
  });
  if (thieuUrl.length) {
    canhBao.push(
      `${ten}: ${thieuUrl.length}/${dsCan.length} căn chưa có URL chi tiết trong sổ đăng ký (${thieuUrl.slice(0, 5).join(", ")}${thieuUrl.length > 5 ? ", …" : ""}).`
    );
  }

  /* Một dòng, không indent — đúng định dạng khối JSON-LD trong repo.
     "</" được escape thành "<\/" (JSON hợp lệ, JSON.parse trả lại nguyên văn)
     để một giá trị dữ liệu chứa "</script>" không thể đóng sớm thẻ script. */
  const moi = JSON.stringify(goc).replace(/<\//g, "<\\/");
  if (moi === m[2]) return { html, doi: false };

  log.push(`  ${ten}  ItemList: ${soCu} -> ${dsCan.length} căn`);
  return {
    html: html.slice(0, m.index) + m[1] + moi + m[3] + html.slice(m.index + m[0].length),
    doi: true,
  };
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
  const doiGiaSan = [];   // trang có con số giá sàn thật sự thay đổi
  const urlChiTietTheoMa = docUrlChiTietTheoMa(canhBao);
  if (urlChiTietTheoMa) console.log(`Sổ URL chi tiết: ${urlChiTietTheoMa.size} căn.`);

  /* --- Trang danh mục: số căn --- */
  let soTrangDanhMuc = 0;
  for (const duong of tatCaHtml) {
    const html = readFileSync(duong, "utf8");
    const bl = docBoLoc(html);
    if (!bl) continue;
    soTrangDanhMuc++;

    /* Một danh sách duy nhất phục vụ cả <title> lẫn ItemList — cùng bộ lọc,
       cùng thứ tự, nên hai chỗ không thể mô tả hai tập căn khác nhau. */
    const dsCan = dsCanLenLuoi(duLieu, bl);
    const soCan = dsCan.length;
    const ten = relative(GOC, duong);

    /* Ngưỡng an toàn: 0 căn gần như luôn là lỗi dữ liệu (Apps Script đẩy lên
       file lỗi, đổi tên cột, sai chính tả giá trị lọc...). Viết "0 căn" lên
       tiêu đề sẽ hại hơn là để tạm số cũ. */
    if (soCan === 0) {
      canhBao.push(`${ten}: đếm được 0 căn với bộ lọc ${JSON.stringify(bl)} — GIỮ NGUYÊN title và khối ItemList cũ.`);
      continue;
    }

    /* Giá sàn 0 = không căn nào trong tập có giá dương. Cũng như số căn = 0,
       đây gần như luôn là lỗi dữ liệu, nên giữ nguyên con số cũ trong title
       và ghi cảnh báo thay vì viết "từ 0 triệu" lên Google. */
    const gia = giaSan(duLieu, bl);
    let giaChu = "";
    if (gia > 0) {
      giaChu = dinhDangTrieu(gia);
    } else if (RE_GIA_SAN.test(html)) {
      canhBao.push(`${ten}: không tính được giá sàn (không căn nào có giá > 0) — GIỮ NGUYÊN giá cũ trong title.`);
    }

    const giaKhoang = khoangGiaTuDsCan(dsCan);

    const kq = capNhatTrangDanhMuc(duong, html, soCan, giaChu, giaKhoang, nhatKy, canhBao);
    const kqLd = capNhatItemList(duong, kq.html, dsCan, urlChiTietTheoMa, nhatKy, canhBao);
    if (kq.doi || kqLd.doi) {
      if (!CHI_THU) writeFileSync(duong, kqLd.html, "utf8");
      daSua.push(ten);
    }
    if (kq.doiGia) doiGiaSan.push(`${ten} -> từ ${giaChu} triệu`);
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
  if (doiGiaSan.length) {
    console.log(`\nGiá sàn thay đổi ở ${doiGiaSan.length} trang:`);
    for (const d of doiGiaSan) console.log(`  ${d}`);
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
