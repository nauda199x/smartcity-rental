#!/usr/bin/env node
// Gate a Sheet snapshot before publishing it to the public website.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const PUBLIC_FIELDS = new Set([
  "Mã nội bộ", "Mã căn", "Tòa", "Loại", "Diện tích", "Nội thất", "Giá thuê",
  "Ngày vào ở", "Ảnh đại diện", "Danh sách ảnh", "Video", "Ngày thêm vào hệ thống",
  "Hiển thị trên Web", "Nguồn CTV", "Thư mục ảnh CTV"
]);
const TYPES = new Set(["Studio", "1 Ngủ", "1 Ngủ +", "2 Ngủ", "2 Ngủ +", "3 Ngủ"]);
export function validateListings(rows) {
  if (!Array.isArray(rows) || rows.length < 1) throw new Error("Snapshot không có dữ liệu");
  const seen = new Set(); let count = 0;
  for (const row of rows) {
    if (!row || typeof row !== "object" || Array.isArray(row)) throw new Error("Dòng không hợp lệ");
    for (const field of Object.keys(row)) if (!PUBLIC_FIELDS.has(field)) throw new Error("Snapshot có cột chưa được phép xuất công khai: " + field);
    if (!/^(có|co|yes|true)$/i.test(String(row["Hiển thị trên Web"]).trim())) continue;
    const id = String(row["Mã nội bộ"] || "").trim().toLowerCase();
    if (!id || seen.has(id)) throw new Error("Căn công khai thiếu hoặc trùng mã");
    seen.add(id); count++;
    const price = Number(row["Giá thuê"]), area = Number(String(row["Diện tích"]).replace(",", "."));
    if (!String(row["Tòa"] || "").trim() || !TYPES.has(row["Loại"]) || !Number.isFinite(price) || price < 1000000 || price > 100000000 || !Number.isFinite(area) || area <= 0 || area > 1000) {
      throw new Error("Thông tin căn công khai không hợp lệ: " + id);
    }
  }
  return {rows:rows.length, public:count};
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const stats = validateListings(JSON.parse(readFileSync(new URL("../data.json", import.meta.url), "utf8")));
  if (stats.public < 50) throw new Error("Quỹ căn công khai giảm bất thường; dừng để đối soát Sheet");
  console.log(`Snapshot hợp lệ: ${stats.rows} dòng, ${stats.public} căn công khai, không trùng mã công khai.`);
}
