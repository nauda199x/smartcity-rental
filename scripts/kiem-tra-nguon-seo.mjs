#!/usr/bin/env node
/**
 * Chốt chặn SEO trước khi sinh HTML căn hộ.
 *
 * data.json được ghi bởi hai luồng: Apps Script từ Sheet chính và CTV sync.
 * Apps Script có thể ghi bản chưa hợp nhất; nếu generator chạy lúc đó,
 * hàng loạt trang sẽ tạm chuyển index -> noindex rồi trở lại ngay sau đó.
 * Dùng sitemap đã publish làm baseline, chỉ CHẶN đợt sụt số lượng bất thường.
 * Không tự sửa data.json/sitemap, không can thiệp trường hợp giảm nhẹ thực tế.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const dataPath = resolve(process.argv[2] || "data.json");
const sitemapPath = resolve(process.argv[3] || "sitemap-can-ho.xml");
const source = JSON.parse(readFileSync(dataPath, "utf8"));
const sitemap = readFileSync(sitemapPath, "utf8");

if (!Array.isArray(source) || source.length < 150) {
  console.error("::error::SEO SOURCE GUARD: data.json rỗng hoặc dữ liệu bất thường; dừng sinh trang.");
  process.exit(1);
}

const active = source.filter((row) =>
  String(row?.["Hiển thị trên Web"] ?? "").trim().toLocaleLowerCase("vi") === "có"
).length;

// Sitemap có một URL hub /can-ho/ không tính vào số trang căn.
const existing = [...sitemap.matchAll(
  /<loc>https:\/\/timthuesmartcity\.com\/can-ho\/[^<]+<\/loc>/g
)].length;

if (existing < 50) {
  console.error("::error::SEO SOURCE GUARD: sitemap căn hộ không có baseline tin cậy (" + existing + ").");
  process.exit(1);
}

console.log("SEO SOURCE GUARD: data.json=" + source.length +
  " dòng; đang hiển thị=" + active + "; URL căn đã publish=" + existing + ".");

const ratio = active / existing;
if (ratio < 0.80 && process.env.SEO_SOURCE_GUARD_ALLOW !== "1") {
  console.error("::error::SEO SOURCE GUARD: số căn active giảm " +
    (100 * (1 - ratio)).toFixed(1) + "% so với sitemap; nguy cơ snapshot " +
    "Apps Script chưa ghép CTV. DỪNG trước khi sinh HTML/noindex/lastmod. " +
    "Hãy chạy workflow Đồng bộ quỹ căn từ Sheet CTV rồi chạy lại.");
  process.exit(1);
}

console.log("SEO SOURCE GUARD: PASS (không phát hiện sụt quỹ căn bất thường).");
