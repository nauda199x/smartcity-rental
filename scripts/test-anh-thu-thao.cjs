const fs = require("node:fs");
const assert = require("node:assert/strict");

for (const path of ["index.html", "dong-bo-can.js"]) {
  const source = fs.readFileSync(path, "utf8");
  const start = source.indexOf("    function apDungAnh(row) {");
  assert.ok(start >= 0, path);
  const end = source.indexOf("\n    }", start) + 6;
  const fn = new Function("anhTheoMa", "row", source.slice(start, end) + "\nreturn apDungAnh(row);");
  const id = "TT.2N.4127", photo = "photo_A123456789";
  const folder = "https://drive.google.com/drive/folders/folder_123456789";
  const row = {"Mã nội bộ": id, "Thư mục ảnh CTV": folder, "Ảnh đại diện": "", "Danh sách ảnh": ""};
  const map = {[id]: {source: "|folder:" + folder, cover: photo, photos: [photo]}};
  assert.ok(fn(map, row)["Ảnh đại diện"].includes(photo), path + ": new source photo");
  for (const next of ["", folder + "_new"]) {
    const changed = {...row, "Thư mục ảnh CTV": next};
    assert.equal(fn(map, changed), changed, path + ": stale folder rejected");
  }
  const original = {"Mã nội bộ": "CT.2N.4127", "Ảnh đại diện": ""};
  const originalMap = {"CT.2N.4127": {source: "", cover: photo, photos: [photo]}};
  assert.ok(fn(originalMap, original)["Ảnh đại diện"].includes(photo), path + ": An Viet remains compatible");
  assert.equal(fn(map, original), original, path + ": cannot cross sources");
}
console.log("PASS: ảnh Thu Thảo trên trang chủ/danh mục, đổi/xóa thư mục, giữ ảnh An Việt");
