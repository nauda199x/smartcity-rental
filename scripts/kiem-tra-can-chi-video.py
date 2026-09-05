"""Regression: a new public apartment with no photos uses the automatic pipeline."""
import datetime
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
import media_can_ho

SCRIPTS = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class VideoOnlyApartment(unittest.TestCase):
    def test_new_code_without_any_photo_is_encoded_and_shown_everywhere(self):
        sync = module('dong-bo-video')
        detail = module('sinh-trang-can')
        cards = module('dung-lai-trang-danh-muc')
        home = module('dung-lai-trang-chu')
        code = 'CT.Video.New.9001'
        url = 'https://drive.google.com/file/d/new_public_clip/preview'
        row = {'Mã nội bộ': code, 'Tòa': 'SA2', 'Loại': 'Studio', 'Diện tích': 30,
               'Giá thuê': 7500000, 'Hiển thị trên Web': 'Có', 'Ảnh đại diện': '',
               'Danh sách ảnh': '', 'Video': ''}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / 'fixture.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=180x320:d=1',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-threads', '1', str(original)], check=True)
            (root / 'data.json').write_text(json.dumps([row]))
            before_data = (root / 'data.json').read_bytes()
            inventory = root / 'inventory.json'
            inventory.write_text(json.dumps({'ok': True, 'items': [
                {'id': code, 'videoList': url, 'videoCover': ''},
                {'id': 'PRIVATE', 'videoList': url}]}))
            with patch.object(sync, 'ROOT', root), patch.object(sync, 'OUT', root / 'video-can-ho'), \
                    patch.object(media_can_ho, 'ROOT', root), \
                    patch.object(sys, 'argv', ['sync', '--inventory', str(inventory)]), \
                    patch.object(sync, 'download', side_effect=lambda url, target: shutil.copyfile(original, target)) as download:
                media_can_ho.video_manifest.cache_clear()
                sync.main()
                self.assertEqual(download.call_count, 1)
                manifest_path = root / 'video-can-ho/manifest.json'
                first = manifest_path.read_bytes()
                items = json.loads(first)['items']
                self.assertEqual(list(items), [code])
                self.assertTrue((root / items[code]['cover'].lstrip('/')).is_file())
                self.assertIn(url, items[code]['sources'])
                self.assertEqual(detail.danh_sach_anh(row), [])
                self.assertTrue(detail.du_dieu_kien(row))
                slug = detail.tinh_slug(row)
                page = detail.dung_trang_can(row, slug, {'_map_anh': {}, 'ban_do': {slug: {}}}, datetime.date(2026, 9, 5))
                self.assertIn('ct-video-placeholder', page)
                self.assertNotIn('ct-no-photo', page)
                self.assertIn('content="https://timthuesmartcity.com' + items[code]['cover'] + '"', page)
                card = cards.dung_the(row, {}, datetime.date(2026, 9, 5))
                self.assertIn(items[code]['cover'], card)
                self.assertNotIn('class="the khong-anh"', card)
                self.assertEqual(home.anh_bia(row, {}), items[code]['cover'])
                self.assertEqual((root / 'data.json').read_bytes(), before_data)
                sync.main()
                self.assertEqual(download.call_count, 1, 'existing clip is reused on the next automatic run')
                self.assertEqual(manifest_path.read_bytes(), first, 'unchanged inventory creates no churn')
                inventory.write_text(json.dumps({'ok': True, 'items': []}))
                with self.assertRaises(ValueError):
                    sync.main()
                self.assertEqual(manifest_path.read_bytes(), first, 'invalid inventory preserves public media')
            media_can_ho.video_manifest.cache_clear()


if __name__ == '__main__':
    unittest.main()
