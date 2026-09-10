#!/usr/bin/env node
/*!
 * cap-nhat-sitemap.mjs — Cập nhật <lastmod> cho sitemap chính và sitemap căn hộ
 * timthuesmartcity.com
 *
 * Mục tiêu:
 *   - sitemap.xml: trang động theo data.json dùng ngày commit gần nhất của data.json;
 *     trang tĩnh dùng ngày commit gần nhất của chính file HTML.
 *   - sitemap-can-ho.xml: KHÔNG được gắn ngày hôm nay cho toàn bộ căn mỗi lần
 *     generator chạy. Trang căn chỉ nhận ngày hôm nay khi nội dung HTML của nó
 *     thực sự khác HEAD trong run hiện tại; nếu không, giữ ngày commit thật gần
 *     nhất của chính trang căn.
 *   - URL noindex tự rời sitemap.
 *
 * Vì sao cần tách logic trang căn:
 * scripts/sinh-trang-can.py sinh lại sitemap-can-ho.xml và trước đây gắn cùng
 * một <lastmod> = hôm nay cho mọi URL hoạt động. Điều đó tạo freshness giả dù
 * phần lớn căn không đổi. Script này chạy SAU toàn bộ generator nên có thể dùng
 * git diff để biết chính xác file HTML nào thực sự đổi nội dung.
 *
 * LƯU Ý HẠ TẦNG: cần lịch sử git đầy đủ (actions/checkout fetch-depth: 0).
 * Chạy thử: node scripts/cap-nhat-sitemap.mjs --thu
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const GOC = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const CHI_THU = process.argv.includes("--thu") || process.argv.includes("--dry-run");

const TEN_MIEN = "https://timthuesmartcity.com";
const DUONG_SITEMAP_CHINH = join(GOC, "sitemap.xml");
const DUONG_SITEMAP_CAN_HO = join(GOC, "sitemap-can-ho.xml");

/* ===================================================================
 * PHẦN 1 — Git và ngày thay đổi thật
 * =================================================================== */

const nhoNgay = new Map();

function repoNong() {
  try {
    return execFileSync("git", ["rev-parse", "--is-shallow-repository"],
      { cwd: GOC, encoding: "utf8" }).trim() === "true";
  } catch {
    return false;
  }
}

/* %cs = YYYY-MM-DD, đúng định dạng W3C dùng cho sitemap. */
function ngayCommitGanNhat(duongTuongDoi) {
  if (nhoNgay.has(duongTuongDoi)) return nhoNgay.get(duongTuongDoi);
  let ngay = null;
  try {
    const ra = execFileSync(
      "git", ["log", "-1", "--format=%cs", "--", duongTuongDoi],
      { cwd: GOC, encoding: "utf8" }
    ).trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(ra)) ngay = ra;
  } catch {
    /* File mới/chưa từng commit hoặc không có git -> null, phía gọi xử lý. */
  }
  nhoNgay.set(duongTuongDoi, ngay);
  return ngay;
}

function ngayHomNayVietNam() {
  const phan = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Ho_Chi_Minh",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const lay = (loai) => phan.find((p) => p.type === loai)?.value;
  return `${lay("year")}-${lay("month")}-${lay("day")}`;
}

/* Chỉ gọi git 2 lần cho toàn bộ thư mục can-ho, không gọi 250 lần cho 250 URL.
 * - git diff: file đã track và đang khác HEAD.
 * - git ls-files --others: trang căn mới chưa từng commit.
 * Generator có thể ghi lại file giống hệt nội dung cũ; git diff sẽ không báo,
 * đúng với mục tiêu: ghi file lại không có nghĩa là nội dung đã thay đổi. */
function layTrangCanDangDoi() {
  const ra = new Set();
  const lenh = [
    ["diff", "--name-only", "HEAD", "--", "can-ho"],
    ["ls-files", "--others", "--exclude-standard", "--", "can-ho"],
  ];
  for (const thamSo of lenh) {
    try {
      const out = execFileSync("git", thamSo, { cwd: GOC, encoding: "utf8" });
      for (const dong of out.split(/\r?\n/)) {
        const f = dong.trim();
        if (f) ra.add(f);
      }
    } catch {
      /* Nếu git lỗi, tập này thiếu dữ liệu; fallback phía dưới sẽ dùng git log. */
    }
  }
  return ra;
}

/* ===================================================================
 * PHẦN 2 — Đưa URL về file HTML và kiểm tra indexability
 * =================================================================== */

function locSangFile(loc) {
  let duong = loc.trim();
  if (!duong.startsWith(TEN_MIEN)) return null;
  duong = duong.slice(TEN_MIEN.length).split("#")[0].split("?")[0];
  if (duong === "" || duong === "/") return "index.html";
  duong = duong.replace(/^\//, "");
  return duong.endsWith("/") ? duong + "index.html" : duong;
}

/* Trang danh mục đọc dữ liệu trực tiếp từ data.json: dù HTML tĩnh không đổi,
 * nội dung người dùng/Google nhận được có thể đổi theo data.json. */
function laTrangDong(duongFile) {
  const day = join(GOC, duongFile);
  if (!existsSync(day)) return false;
  const html = readFileSync(day, "utf8");
  return html.includes("dong-bo-can.js") || html.includes("data.json");
}

const RE_META_ROBOTS = /<meta[^>]*\bname=["']robots["'][^>]*\bcontent=["']([^"']*)["']/gi;

function laNoIndex(duongFile) {
  const day = join(GOC, duongFile);
  if (!existsSync(day)) return false;
  const html = readFileSync(day, "utf8");
  for (const m of html.matchAll(RE_META_ROBOTS)) {
    const noiDung = m[1].toLowerCase();
    if (noiDung.includes("noindex") || noiDung.includes("none")) return true;
  }
  return false;
}

/* ===================================================================
 * PHẦN 3 — Cập nhật từng sitemap
 * =================================================================== */

const RE_KHOI_URL = /[ \t]*<url>[\s\S]*?<\/url>\r?\n?/g;
const RE_LOC = /<loc>([^<]+)<\/loc>/;
const RE_LASTMOD = /(<lastmod>)([^<]*)(<\/lastmod>)/;

function xuLySitemap({ duongSitemap, ten, cheDoCanHo, ngayDuLieu, trangCanDangDoi }) {
  if (!existsSync(duongSitemap)) {
    console.error(`LỖI: không tìm thấy ${ten}.`);
    return { loi: 1, doi: 0, xoa: 0 };
  }

  const goc = readFileSync(duongSitemap, "utf8");
  const nhatKy = [];
  const canhBao = [];
  let soDong = 0, soTinh = 0, soCan = 0, soCanDoi = 0, soDoi = 0, soXoa = 0;

  const moi = goc.replace(RE_KHOI_URL, (khoi) => {
    const mLoc = khoi.match(RE_LOC);
    if (!mLoc) {
      canhBao.push("Có khối <url> không chứa <loc> — bỏ qua.");
      return khoi;
    }

    const loc = mLoc[1];
    const duongFile = locSangFile(loc);
    if (!duongFile) {
      canhBao.push(`${loc}: không thuộc tên miền — GIỮ NGUYÊN lastmod.`);
      return khoi;
    }
    if (!existsSync(join(GOC, duongFile))) {
      canhBao.push(`${loc}: không có file ${duongFile} — GIỮ NGUYÊN lastmod.`);
      return khoi;
    }

    if (laNoIndex(duongFile)) {
      soXoa++;
      nhatKy.push(`  ${duongFile}  GỠ khỏi sitemap (noindex)`);
      return "";
    }

    let ngay = null;
    let nhan = "";

    if (cheDoCanHo && duongFile.startsWith("can-ho/")) {
      soCan++;
      if (trangCanDangDoi.has(duongFile)) {
        /* File thực sự đổi trong run hiện tại hoặc là file mới. */
        ngay = ngayHomNayVietNam();
        soCanDoi++;
        nhan = "căn đổi thật trong run";
      } else {
        /* File không đổi: dùng ngày commit thật của chính trang. */
        ngay = ngayCommitGanNhat(duongFile);
        nhan = "commit thật của trang căn";
      }
    } else {
      const dong = laTrangDong(duongFile);
      ngay = dong ? ngayDuLieu : ngayCommitGanNhat(duongFile);
      dong ? soDong++ : soTinh++;
      nhan = dong ? "động theo data.json" : "commit file";
    }

    if (!ngay) {
      canhBao.push(`${duongFile}: không xác định được ngày thật — GIỮ NGUYÊN lastmod.`);
      return khoi;
    }

    const mLast = khoi.match(RE_LASTMOD);
    if (!mLast) {
      canhBao.push(`${duongFile}: khối <url> không có <lastmod> — bỏ qua.`);
      return khoi;
    }
    if (mLast[2] === ngay) return khoi;

    soDoi++;
    nhatKy.push(`  ${duongFile}  ${mLast[2] || "(rỗng)"} -> ${ngay}  [${nhan}]`);
    return khoi.replace(RE_LASTMOD, (_, mo, __, dong2) => mo + ngay + dong2);
  });

  console.log(`\n[${ten}]`);
  if (cheDoCanHo) {
    console.log(`Kiểm tra ${soCan} URL trong /can-ho/: ${soCanDoi} trang thực sự đổi nội dung ở run này.`);
  } else {
    console.log(`Xử lý ${soDong} URL động (theo data.json) và ${soTinh} URL tĩnh (theo file).`);
  }

  if (nhatKy.length) {
    console.log("Thay đổi:");
    for (const d of nhatKy) console.log(d);
  }
  if (canhBao.length) {
    console.log("⚠️  CẢNH BÁO:");
    for (const c of canhBao) console.log(`  ${c}`);
  }

  if (soDoi === 0 && soXoa === 0) {
    console.log(`${ten} đã đúng — không có gì thay đổi.`);
    return { loi: 0, doi: 0, xoa: 0 };
  }

  if (!CHI_THU) writeFileSync(duongSitemap, moi, "utf8");
  console.log(
    `Đã cập nhật ${soDoi} URL` +
    (soXoa ? ` và gỡ ${soXoa} URL noindex` : "") +
    ` trong ${ten}.` +
    (CHI_THU ? " (--thu: KHÔNG ghi file)" : "")
  );
  return { loi: 0, doi: soDoi, xoa: soXoa };
}

function main() {
  if (repoNong()) {
    console.error(
      "LỖI: repo đang checkout nông (shallow). Không thể tính lastmod đáng tin. " +
      "Đặt fetch-depth: 0 ở actions/checkout. Dừng, không sửa gì."
    );
    process.exit(1);
  }

  const ngayDuLieu = ngayCommitGanNhat("data.json");
  if (!ngayDuLieu) {
    console.error("LỖI: không đọc được ngày commit gần nhất của data.json. Dừng.");
    process.exit(1);
  }

  const trangCanDangDoi = layTrangCanDangDoi();
  console.log(`data.json commit gần nhất: ${ngayDuLieu}`);
  console.log(`File trong can-ho/ đang khác HEAD hoặc chưa track: ${trangCanDangDoi.size}`);

  const kqChinh = xuLySitemap({
    duongSitemap: DUONG_SITEMAP_CHINH,
    ten: "sitemap.xml",
    cheDoCanHo: false,
    ngayDuLieu,
    trangCanDangDoi,
  });

  const kqCanHo = xuLySitemap({
    duongSitemap: DUONG_SITEMAP_CAN_HO,
    ten: "sitemap-can-ho.xml",
    cheDoCanHo: true,
    ngayDuLieu,
    trangCanDangDoi,
  });

  if (kqChinh.loi || kqCanHo.loi) process.exit(1);

  console.log(
    `\nHoàn tất: sitemap.xml đổi ${kqChinh.doi} URL; ` +
    `sitemap-can-ho.xml đổi ${kqCanHo.doi} URL.`
  );
}

main();
