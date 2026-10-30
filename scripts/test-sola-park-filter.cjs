#!/usr/bin/env node
// Chạy: node scripts/test-sola-park-filter.cjs
// Kiểm tra chính hàm đang chạy trong trang chủ, không viết lại bảng quy đổi.
const fs = require("node:fs");
const assert = require("node:assert/strict");
const html = fs.readFileSync("index.html", "utf8");
function layThanHam(ten) {
  const re = new RegExp("function " + ten + "\\([^)]*\\) \\{([\\s\\S]*?)\\n    \\}");
  const match = html.match(re);
  assert.ok(match, "Không tìm thấy hàm " + ten + " trong homepage");
  return match[1];
}
const khu = new Function("toa", layThanHam("tenPhanKhu"));
for (const [toa, muon] of [
  ["SolaPark", "Sola Park"],
  ["Sola Park", "Sola Park"],
  ["G1", "Sola Park"], ["G6", "Sola Park"],
  ["GS1", "Miami"], ["GS6", "Miami"], ["GS", "Miami"],
  ["Lumiere", "Lumiere"], ["Imperia", "Imperia"],
  ["MasA", "Masteri"], ["SA5", "Sakura"], ["S3.03", "Sapphire"]
]) assert.equal(khu(toa), muon, toa + " phải thuộc " + muon);

const apartments = [
  { tower: "SolaPark", type: "Studio", show: true, price: 8500000 },
  { tower: "G2", type: "2 Ngủ", show: true, price: 11000000 },
  { tower: "GS1", type: "2 Ngủ", show: true, price: 9000000 },
  { tower: "SolaPark", type: "3 Ngủ", show: false, price: 15000000 }
].map(x => ({ ...x, phanKhu: khu(x.tower) }));
const state = { apartments };
const normalizeKey = s => String(s || "").trim().toLowerCase();
const getZones = new Function("state", "normalizeKey",
  "return (function() {" + layThanHam("danhSachPhanKhu") + "\\n})();");
const zones = getZones(state, normalizeKey);
assert.ok(zones.some(z => z.label === "Sola Park" && z.key === "sola park"),
  "Bộ lọc không có Sola Park");
assert.ok(zones.some(z => z.label === "Miami" && z.key === "miami"),
  "Bộ lọc nhận nhầm GS* thành Sola Park");
assert.ok(html.includes('id="locPcPhanKhu"') && html.includes('id="phanKhuFilters"'),
  "Thiếu bộ lọc desktop/mobile");
assert.ok(html.includes('href="/?pk=sola-park"'), "Thiếu link xem riêng Sola Park");
assert.ok(html.includes('"solapark": "sola park"'), "Thiếu alias ?pk=solapark");
const python = fs.readFileSync("scripts/dung-lai-trang-chu.py", "utf8");
assert.ok(python.includes('("Sola Park", "Sola Park", "/?pk=sola-park")'),
  "Bảng giá tĩnh chưa có Sola Park");
console.log("PASS Sola Park: bảng lọc, GS != G*, link, thống kê tĩnh");
