#!/usr/bin/env node
// Regression: one CTV source failure must not block or erase the other source.
const fs = require("node:fs");
const assert = require("node:assert/strict");

const source = fs.readFileSync("scripts/dong-bo-ctv.mjs", "utf8");
const start = source.indexOf("async function main() {");
const end = source.indexOf("\nmain().catch(", start);
assert.ok(start >= 0 && end > start, "Sync main() not found");
const mainSource = source.slice(start, end);
// Exercise the real merge: An Việt must never hide owner listings.
const vm = require("node:vm");
const sandbox = {process, console};
vm.createContext(sandbox);
vm.runInContext(source.slice(source.indexOf("const SHEET"), start), sandbox);
vm.runInContext(`
  const inputOwners = [
    {"Mã nội bộ":"CC35", "Hiển thị trên Web":"Có", "Giá thuê":1},
    {"Mã nội bộ":"CC99", "Hiển thị trên Web":"Có"},
    {"Mã nội bộ":"CT.2N1.1", "Hiển thị trên Web":"Có"},
    {"Mã nội bộ":"TT.2N.4127", "Hiển thị trên Web":"Có"}
  ];
  const afterCtv = sync(inputOwners, new Map()).next;
  if (afterCtv[0]["Hiển thị trên Web"] !== "Có") throw Error("CTV hid owner");
  const owner = {id:"CC35", tower:"S401", type:"2 Ngủ +", area:62,
    furniture:"Full nội thất", price:11000000, moveIn:"", cover:"cover", photos:"photo", show:true};
  const merged = syncOwners(afterCtv, new Map([[owner.id, owner]]));
  if (merged[0]["Giá thuê"] !== 11000000 || merged[0]["Danh sách ảnh"] !== "photo") throw Error("Owner fields lost");
  if (merged[1]["Hiển thị trên Web"] !== "Không") throw Error("Removed owner stayed active");
  if (merged[3]["Hiển thị trên Web"] !== "Có") throw Error("Owner sync changed TT");
  const hidden = syncOwners(merged, new Map([[owner.id, {...owner, show:false}]]));
  if (hidden[0]["Hiển thị trên Web"] !== "Không") throw Error("Owner flag ignored");
  const added = syncOwners([], new Map([[owner.id, owner]]));
  if (added.length !== 1 || added[0]["Mã nội bộ"] !== "CC35") throw Error("Owner add failed");
`, sandbox);
const factory = new Function("ctx",
  "const {readFileSync, writeFileSync, DATA, loadCtv, loadThao, sync, syncThao, " +
  "stable, DRY, console, process, loadOwners, syncOwners} = ctx;\n" + mainSource + "\nreturn main;");

const initial = [
  {"Mã nội bộ": "CT.2N1.1", "Giá thuê": 8000000, "Hiển thị trên Web": "Có"},
  {"Mã nội bộ": "TT.2N.4127", "Mã căn": "4127", "Giá thuê": 12000000,
   "Thư mục ảnh CTV": "https://drive.google.com/drive/folders/existingFolder1234",
   "Hiển thị trên Web": "Có"},
  ...Array.from({length: 148}, (_, i) => ({"Mã nội bộ": "manual." + i}))
];
const input = JSON.stringify(initial) + "\n";
const stats = {updated: 1, added: 0, on: 0, off: 0, missing: 0};

async function simulate({failCtv = false, failThao = false, strictCtv = false, strictThao = false} = {}) {
  const writes = [];
  const warnings = [];
  const ctx = {
    readFileSync: () => input,
    writeFileSync: (_path, value) => writes.push(value),
    DATA: "data.json",
    DRY: false,
    process: {env: {REQUIRE_CTV: strictCtv ? "1" : "0", REQUIRE_THAO: strictThao ? "1" : "0"}},
    console: {log: () => {}, warn: msg => warnings.push(msg)},
    stable: value => JSON.stringify(value) + "\n",
    loadCtv: async () => {
      if (failCtv) throw Error("An Viet is unavailable");
      return {nonEmpty: 350, invalid: [], map: new Map()};
    },
    sync: rows => {
      const next = rows.map(r => ({...r}));
      next[0]["Giá thuê"] = 9000000;
      return {next, stat: stats};
    },
    loadThao: async () => {
      if (failThao) throw Error("Thu Thao is unavailable");
      return {map: new Map(), stats: {rows: 600, excludedLumi: 0, badPrice: 0, photos: 100}};
    },
    loadOwners: async () => { throw Error("Owner source unavailable in this fixture"); },
    syncOwners: rows => rows,
    syncThao: rows => {
      rows[1]["Giá thuê"] = 13000000;
      return {added: 0, updated: 1, hidden: 0};
    }
  };
  let error;
  try { await factory(ctx)(); } catch (e) { error = e; }
  return {writes, warnings, error, rows: writes.length ? JSON.parse(writes[0]) : null};
}

(async () => {
  let result = await simulate();
  assert.equal(result.error, undefined);
  assert.equal(result.rows[0]["Giá thuê"], 9000000);
  assert.equal(result.rows[1]["Giá thuê"], 13000000);

  result = await simulate({failCtv: true});
  assert.equal(result.error, undefined);
  assert.equal(result.rows[0]["Giá thuê"], 8000000);
  assert.equal(result.rows[1]["Giá thuê"], 13000000);
  assert.equal(result.warnings.length, 2);

  result = await simulate({failThao: true});
  assert.equal(result.error, undefined);
  assert.equal(result.rows[0]["Giá thuê"], 9000000);
  assert.equal(result.rows[1]["Giá thuê"], 12000000);
  assert.equal(result.warnings.length, 2);

  result = await simulate({failCtv: true, failThao: true});
  assert.match(result.error.message, /Cả An Việt và Thu Thảo/);
  assert.equal(result.writes.length, 0);

  result = await simulate({failCtv: true, strictCtv: true});
  assert.match(result.error.message, /An Viet is unavailable/);
  assert.equal(result.writes.length, 0);

  result = await simulate({failThao: true, strictThao: true});
  assert.match(result.error.message, /Thu Thao is unavailable/);
  assert.equal(result.writes.length, 0);

  const syncYaml = fs.readFileSync(".github/workflows/dong-bo-ctv.yml", "utf8");
  const photoYaml = fs.readFileSync(".github/workflows/tai-anh-can-ho.yml", "utf8");
  assert.ok(syncYaml.includes('cron: "*/30 * * * *"'), "CTV 30-minute schedule missing");
  assert.ok(photoYaml.includes('cron: "7,37 * * * *"'), "Photos 30-minute schedule missing");
  console.log("PASS: 2 sources independent, safe fallback, strict checks and 30-minute sync");
})().catch(error => {console.error(error); process.exitCode = 1;});
