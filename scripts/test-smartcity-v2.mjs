import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import { validateListings } from "./validate-listings.mjs";

const read = p => readFileSync(new URL("../" + p, import.meta.url), "utf8");
const html = read("index.html");
const search = html.slice(html.indexOf("let boNhoTuKhoa ="), html.indexOf("function apartmentMatchesQuery"));
const accents = html.slice(html.indexOf("function boDau(value)"), html.indexOf("/** Sinh cac cach viet gia"));
const ctx = vm.createContext({});
vm.runInContext(accents + search, ctx);
const matches = (query, price, blobTim) => ctx.khopTuKhoa({price, blobTim}, query);
assert(matches("2 ngủ, full đồ, dưới 10 triệu", 9500000, "2 ngu full do sapphire"));
assert(!matches("2 ngủ, full đồ, dưới 10 triệu", 10000000, "2 ngu full do sapphire"));
assert(!matches("2 ngủ, full đồ, dưới 10 triệu", 9000000, "1 ngu full do sapphire"));
assert(matches("tối đa 8,5 triệu", 8500000, "studio"));
assert(!matches("trên 8,5 triệu", 8500000, "studio"));
assert(matches("8,5 triệu", 8500000, "studio 8,5 trieu"));

const sync = read("scripts/dong-bo-ctv.mjs");
const cash = vm.createContext({});
vm.runInContext('const txt = v => String(v ?? "").trim();\n' + sync.slice(sync.indexOf("function money(v)"), sync.indexOf("function area(v)")), cash);
for (const v of ["8.000.000", "8,000,000", "8.000", "8,000", "8000000", "8000", "8 triệu"]) assert.equal(cash.money(v), 8000000, v);
assert.equal(cash.money("8,5 triệu"), 8500000);
assert.equal(cash.money("8-9 triệu"), 0);

const valid = {"Mã nội bộ":"test.1", "Tòa":"S101", "Loại":"2 Ngủ", "Diện tích":54, "Giá thuê":8000000, "Hiển thị trên Web":"Có"};
assert.deepEqual(validateListings([valid]), {rows:1, public:1});
assert.throws(() => validateListings([valid, valid]), /trùng mã/);
assert.throws(() => validateListings([{...valid,"Giá thuê":8000000000}]), /không hợp lệ/);
assert.throws(() => validateListings([{...valid,"SĐT chủ nhà":"example"}]), /chưa được phép/);
assert.equal(validateListings([valid, {...valid,"Hiển thị trên Web":"Không"}]).public, 1);
const data = JSON.parse(read("data.json"));
console.log("PASS: Natural-language budget filters, Sheet price parsing, public fields and duplicate guard; actual snapshot:", validateListings(data));
