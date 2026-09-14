"""Regression: ảnh thêm vào cùng thư mục, xóa/replace ảnh và lỗi nguồn."""
import contextlib
import copy
import importlib.util
import io
import json
import unittest
from unittest.mock import patch
from pathlib import Path

import media_anh

spec = importlib.util.spec_from_file_location("scan_photos", Path(__file__).with_name("quet-thu-muc-anh.py"))
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
FOLDER = "folder_123456789"
A, B, C = "photo_A123456789", "photo_B123456789", "photo_C123456789"


def photo(ident, modified=1):
    return {"id": ident, "name": ident + ".jpg", "modified": modified, "size": 123}


def fixture(files, **changes):
    rows = [[f["id"], [FOLDER], f["name"], "image/jpeg", 0, None, 0, 0, 0,
             f["modified"], 1, None, None, f["size"]] for f in files]
    data = [rows, None, None, None, [[FOLDER]], 1]
    for index, value in changes.items():
        data[int(index)] = value
    encoded = json.dumps(json.dumps(data))[1:-1].replace("[", r"\x5b")
    return "window['_DRIVE_ivd'] = '" + encoded + "';"


class PhotoSyncTest(unittest.TestCase):
    def setUp(self):
        self.row = {"Mã nội bộ": "CT.test", "Ảnh đại diện": "https://drive.google.com/thumbnail?id=" + A,
                    "Danh sách ảnh": "https://drive.google.com/file/d/" + A + "/view",
                    "Hiển thị trên Web": "Có", "Video": "keep-video"}
        self.source = {**self.row, "folderId": FOLDER}

    def test_real_drive_encoding_and_video_exclusion(self):
        text = fixture([photo(A), photo(B)])
        self.assertEqual([f["id"] for f in scanner.parse_folder(text, FOLDER)], [A, B])
        files = scanner.parse_folder(text.replace("image/jpeg", "video/mp4"), FOLDER)
        item = scanner.build_item(self.row, self.source, files, None)
        self.assertEqual(item["photos"], [])
        self.assertEqual(item["poster"], A)
        self.assertEqual(item["cover"], A)

    def test_empty_is_valid_only_with_complete_folder_metadata(self):
        self.assertEqual(scanner.parse_folder(fixture([]), FOLDER), [])
        for text in ["Login required", fixture([], **{"1": "next-page"}),
                     fixture([], **{"4": []}), fixture([photo(A)] * 100)]:
            with self.assertRaises(ValueError):
                scanner.parse_folder(text, FOLDER)

    def test_add_and_remove_preserve_cover_and_order(self):
        previous = {"folderId": FOLDER, "photos": [A, B]}
        item = scanner.build_item(self.row, self.source, [photo(C), photo(B), photo(A)], previous)
        self.assertEqual(item["photos"], [A, B, C])
        item = scanner.build_item(self.row, self.source, [photo(C), photo(B)], previous)
        self.assertEqual(item["photos"], [B, C])
        self.assertEqual(item["cover"], B)

    def test_first_photos_for_previously_empty_listing(self):
        row = {**self.row, "Ảnh đại diện": "", "Danh sách ảnh": ""}
        item = scanner.build_item(row, {**row, "folderId": FOLDER}, [photo(B)], None)
        self.assertEqual(item["photos"], [B])
        with patch.object(media_anh, "photo_manifest", return_value={"items": {"CT.test": item}}):
            effective = media_anh.ap_dung_anh(row)
        self.assertIn(B, effective["Ảnh đại diện"])
        self.assertEqual(effective["Video"], "keep-video")
        self.assertEqual(row["Ảnh đại diện"], "")

    def test_newer_sheet_snapshot_wins(self):
        item = scanner.build_item(self.row, self.source, [photo(A), photo(B)], None)
        with patch.object(media_anh, "photo_manifest", return_value={"items": {"CT.test": item}}):
            updated = {**self.row, "Ảnh đại diện": "https://drive.google.com/thumbnail?id=" + C}
            self.assertIs(media_anh.ap_dung_anh(updated), updated)
            self.assertIn(B, media_anh.ap_dung_anh(self.row)["Danh sách ảnh"])

    def scan(self, old, fetch):
        rows = [{**self.row, "Mã nội bộ": str(i)} for i in range(150)]
        sources = {str(i): self.source for i in range(150)}
        with contextlib.redirect_stdout(io.StringIO()):
            return scanner.scan(rows, sources, old, fetch)

    def test_unchanged_is_idempotent_and_replace_changes_filename(self):
        first = self.scan({}, lambda _: [photo(A)])
        self.assertEqual(self.scan(first, lambda _: [photo(A)]), first)
        updated = self.scan(first, lambda _: [photo(A, modified=2)])
        self.assertEqual(updated["items"], first["items"])
        self.assertNotEqual(updated["revisions"][A]["revision"], "")
        with patch.object(media_anh, "photo_manifest", return_value=updated):
            name = media_anh.ten_file_co_phien_ban("cover.webp", A)
            self.assertRegex(name, r"^cover-v[a-f0-9]{12}\.webp$")
            self.assertEqual(media_anh.ten_file_co_phien_ban(name, A), name)

    def test_temporary_failure_preserves_last_good(self):
        old = self.scan({}, lambda _: [photo(A), photo(B)])
        before = copy.deepcopy(old)
        def fail(_):
            raise OSError("Drive temporarily unavailable")
        self.assertEqual(self.scan(old, fail), before)
        self.assertEqual(old, before)

    def test_widespread_failure_does_not_publish(self):
        rows = [{**self.row, "Mã nội bộ": str(i)} for i in range(150)]
        sources = {str(i): {**self.source, "folderId": "folder" + str(i)} for i in range(150)}
        def fail(_):
            raise OSError("Unavailable")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(ValueError):
            scanner.scan(rows, sources, {}, fail)

    def test_old_cover_kept_in_gallery_cannot_overwrite_new_cover(self):
        spec = importlib.util.spec_from_file_location("image_list", Path(__file__).with_name("sinh-danh-sach-anh.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = {**self.row, "Danh sách ảnh": "https://drive.google.com/thumbnail?id=" + A}
        records = {B: {"drive_id": B, "ten_file": "cover.webp", "loai_anh": "bia"}}
        result = module.dung_ban_ghi_gallery(row, "test", {A: "cover.webp", C: "test-a3-v123456abcdef.webp"}, records, [])
        self.assertEqual(result[0]["ten_file"], "test-a4.webp")


if __name__ == "__main__":
    unittest.main()
