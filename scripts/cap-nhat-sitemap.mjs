#!/usr/bin/env node
/*!
 * cap-nhat-sitemap.mjs — Cập nhật <lastmod> trong sitemap.xml
 * timthuesmartcity.com
 *
 * Vì sao cần script này: 33/36 URL trong sitemap cùng ghi một ngày cứng
 * trong khi data.json được commit khoảng 40 lần mỗi ngày. Google dùng
 * <lastmod> để quyết định bao lâu quay lại crawl một URL; để ngày đứng yên
 * là tự nói với Google rằng trang không còn đổi nữa.
 *
 * NGUYÊN TẮC:
 *   - Trang ĐỌC DỮ LIỆU từ data.json (25 trang danh mục, index.html,
 *     bang-gia-thue-vinhomes-smart-city.html) -> lastmod = ngày commit gần
 *     nhất của data.json. Nội dung các trang này đổi mỗi lần data.json đổi,
 *     dù file HTML không đổi dòng nào.
 *   - Trang TĨNH (bài viết, cẩm nang, gửi thuê) -> lastmod = ngày commit gần
 *     nhất của CHÍNH file đó.
 *   - KHÔNG đặt tất cả về ngày hôm nay. Khai man freshness là tín hiệu xấu,
 *     Google đối chiếu lastmod với nội dung thật và sẽ bỏ qua cả sitemap nếu
 *     thấy ngày không đáng tin.
 *   - Giữ nguyên thứ tự URL, <priority>, <changefreq>, khối <image:image>
 *     và mọi comment. Script chỉ chạm đúng phần trong <lastmod></lastmod>.
 *   - Không lấy được ngày từ git -> GIỮ NGUYÊN lastmod cũ và ghi cảnh báo.
 *
 * LƯU Ý HẠ TẦNG: script cần lịch sử git đầy đủ. Trong GitHub Actions phải
 * đặt fetch-depth: 0 ở bước checkout, nếu không mọi file sẽ trả về cùng một
 * ngày của commit duy nhất được tải về.
 *
 * Chạy tay để xem trước, không sửa file:  node scripts/cap-nhat-sitemap.mjs --thu
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const GOC = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const CHI_THU = process.argv.includes("--thu") || process.argv.includes("--dry-run");

const TEN_MIEN = "https://timthuesmartcity.com";
const DUONG_SITEMAP = join(GOC, "sitemap.xml");

/* ===================================================================
 * PHẦN 1 — Hỏi git ngày commit gần nhất
 * =================================================================== */

const nhoNgay = new Map();

/* Trong repo checkout nông, git coi commit duy nhất tải về là commit đã tạo
   ra MỌI file, nên `git log -1 -- <bất kỳ file nào>` đều trả về cùng một
   ngày. Không có cảnh báo nào, chỉ có sitemap toàn ngày hôm nay — đúng cái
   tín hiệu freshness giả mà script này sinh ra để tránh. Phải chặn từ đầu. */
function repoNong() {
  try {
    return execFileSync("git", ["rev-parse", "--is-shallow-repository"],
      { cwd: GOC, encoding: "utf8" }).trim() === "true";
  } catch {
    return false;
  }
}

/* %cs = ngày commit, dạng YYYY-MM-DD, đúng dạng W3C mà sitemap cần. */
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
    /* không có git, hoặc file chưa từng được commit -> để null, phía gọi xử lý */
  }
  nhoNgay.set(duongTuongDoi, ngay);
  return ngay;
}

/* ===================================================================
 * PHẦN 2 — Đưa <loc> về đường dẫn file trong repo
 * =================================================================== */

function locSangFile(loc) {
  let duong = loc.trim();
  if (!duong.startsWith(TEN_MIEN)) return null;
  duong = duong.slice(TEN_MIEN.length).split("#")[0].split("?")[0];
  if (duong === "" || duong === "/") return "index.html";
  duong = duong.replace(/^\//, "");
  return duong.endsWith("/") ? duong + "index.html" : duong;
}

/* Trang đọc dữ liệu từ data.json thì nội dung đổi theo data.json, không theo
   file HTML. Nhận diện bằng dấu vết trong chính file, không viết cứng danh
   sách — thêm trang danh mục mới là tự chạy đúng. */
function laTrangDong(duongFile) {
  const day = join(GOC, duongFile);
  if (!existsSync(day)) return false;
  const html = readFileSync(day, "utf8");
  return html.includes("dong-bo-can.js") || html.includes("data.json");
}

/* ===================================================================
 * PHẦN 3 — Chạy
 * =================================================================== */

const RE_KHOI_URL = /<url>[\s\S]*?<\/url>/g;
const RE_LOC = /<loc>([^<]+)<\/loc>/;
const RE_LASTMOD = /(<lastmod>)([^<]*)(<\/lastmod>)/;

function main() {
  if (!existsSync(DUONG_SITEMAP)) {
    console.error("LỖI: không tìm thấy sitemap.xml. Dừng, không sửa gì.");
    process.exit(1);
  }

  if (repoNong()) {
    console.error(
      "LỖI: repo đang ở dạng checkout nông (shallow). Mọi file sẽ trả về cùng " +
      "một ngày commit, sitemap sinh ra sẽ sai toàn bộ. Đặt fetch-depth: 0 ở " +
      "bước actions/checkout. Dừng, không sửa gì."
    );
    process.exit(1);
  }

  const ngayDuLieu = ngayCommitGanNhat("data.json");
  if (!ngayDuLieu) {
    console.error(
      "LỖI: không đọc được ngày commit của data.json — repo có lịch sử git không? " +
      "Dừng, không sửa gì."
    );
    process.exit(1);
  }
  console.log(`data.json commit gần nhất: ${ngayDuLieu}`);

  const goc = readFileSync(DUONG_SITEMAP, "utf8");
  const nhatKy = [];
  const canhBao = [];
  let soDong = 0, soTinh = 0, soDoi = 0;

  const moi = goc.replace(RE_KHOI_URL, (khoi) => {
    const mLoc = khoi.match(RE_LOC);
    if (!mLoc) {
      canhBao.push("Có khối <url> không chứa <loc> — bỏ qua.");
      return khoi;
    }
    const loc = mLoc[1];
    const duongFile = locSangFile(loc);
    if (!duongFile) {
      canhBao.push(`${loc}: không thuộc tên miền của site — GIỮ NGUYÊN lastmod.`);
      return khoi;
    }
    if (!existsSync(join(GOC, duongFile))) {
      canhBao.push(`${loc}: không có file ${duongFile} trong repo — GIỮ NGUYÊN lastmod.`);
      return khoi;
    }

    const dong = laTrangDong(duongFile);
    const ngay = dong ? ngayDuLieu : ngayCommitGanNhat(duongFile);
    if (!ngay) {
      canhBao.push(`${duongFile}: git không trả về ngày commit — GIỮ NGUYÊN lastmod.`);
      return khoi;
    }
    dong ? soDong++ : soTinh++;

    const mLast = khoi.match(RE_LASTMOD);
    if (!mLast) {
      canhBao.push(`${duongFile}: khối <url> không có <lastmod> — bỏ qua, không tự thêm.`);
      return khoi;
    }
    if (mLast[2] === ngay) return khoi;

    soDoi++;
    nhatKy.push(`  ${duongFile}  ${mLast[2] || "(rỗng)"} -> ${ngay}  [${dong ? "động" : "tĩnh"}]`);
    return khoi.replace(RE_LASTMOD, (_, mo, __, dong2) => mo + ngay + dong2);
  });

  console.log(`Xử lý ${soDong} URL động (theo data.json) và ${soTinh} URL tĩnh (theo file).`);

  if (nhatKy.length) {
    console.log("\nThay đổi:");
    for (const d of nhatKy) console.log(d);
  }
  if (canhBao.length) {
    console.log("\n⚠️  CẢNH BÁO:");
    for (const c of canhBao) console.log(`  ${c}`);
  }

  if (soDoi === 0) {
    console.log("\nsitemap.xml đã đúng — không có gì thay đổi.");
    return;
  }
  if (!CHI_THU) writeFileSync(DUONG_SITEMAP, moi, "utf8");
  console.log(
    `\nĐã cập nhật ${soDoi} URL trong sitemap.xml.` +
    (CHI_THU ? " (chế độ --thu: KHÔNG ghi file)" : "")
  );
}

main();
