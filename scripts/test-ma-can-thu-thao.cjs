#!/usr/bin/env node
const fs = require("node:fs");
const assert = require("node:assert/strict");
const home = fs.readFileSync("index.html", "utf8");
const categories = fs.readFileSync("dong-bo-can.js", "utf8");
const sync = fs.readFileSync("scripts/dong-bo-ctv.mjs", "utf8");
const pythonDetail = fs.readFileSync("scripts/sinh-trang-can.py", "utf8");
const pythonTower = fs.readFileSync("scripts/sinh-trang-toa.py", "utf8");

function functionBody(src, signature, closingIndent) {
  const pos = src.indexOf(signature);
  assert.ok(pos >= 0, "Thiếu hàm: " + signature);
  const bodyStart = src.indexOf("{", pos) + 1;
  const end = src.indexOf("\n" + closingIndent + "}", bodyStart);
  assert.ok(end > bodyStart, "Không thấy phần đóng hàm " + signature);
  return src.slice(bodyStart, end);
}
const displayOnHome = new Function("normalizeText", "row",
  functionBody(home, "function maCanHienThi(row)", "    "));
const displayOnCategories = new Function("chuan", "r",
  functionBody(categories, "function maCanHienThi(r)", "  "));
const norm = s => String(s == null ? "" : s).trim();
const cases = [
  [{ "Mã nội bộ": "TT.2N.4127", "Mã căn": "4127" }, "4127"],
  [{ "Mã nội bộ": "TT.ST.5207" }, "5207"],
  [{ "Mã nội bộ": "TT.2NP.1234", "Mã căn": "1234" }, "1234"],
  [{ "Mã nội bộ": "TT.3N.7777", "Mã căn": "" }, "7777"],
  [{ "Mã nội bộ": "CT.2N1.280" }, "CT.2N1.280"],
  [{ "Mã nội bộ": "CC123" }, "CC123"]
];
for (const [row, expected] of cases) {
  assert.equal(displayOnHome(norm, row), expected, "Trang chủ: " + JSON.stringify(row));
  assert.equal(displayOnCategories(norm, row), expected, "Danh mục: " + JSON.stringify(row));
}
assert.ok(sync.includes('const id = "TT." + tab.prefix + "." + stt;'), "Mã nội bộ mất namespace");
assert.ok(sync.includes('"Mã căn": src.stt'), "Căn thêm mới thiếu mã STT");
assert.ok(sync.includes('row["Mã căn"] = src.stt;'), "Căn cũ chưa nhận mã STT");
assert.ok(home.includes("const displayId = maCanHienThi(row)"), "Trang chủ thiếu mã hiển thị");
assert.ok(home.includes("apartment.displayId"), "Thẻ/Zalo chưa chuyển sang mã hiển thị");
assert.ok(home.includes("data-ma-noi-bo=\"\${apartment.apartmentId"), "Trang chủ mất ID kỹ thuật");
assert.ok(categories.includes('el.setAttribute("data-ma-noi-bo", ma)'), "Danh mục mất ID kỹ thuật");
assert.ok(pythonDetail.includes('ma_hien_thi = ma_can_hien_thi(can)'), "Trang chi tiết thiếu mã STT");
assert.ok(pythonTower.includes('ma_hien_thi = ma_can_hien_thi(can)'), "Danh mục tĩnh thiếu mã STT");
console.log("PASS: STT 4127 trên trang chủ, danh mục, chi tiết; An Việt & ID nội bộ giữ nguyên");
