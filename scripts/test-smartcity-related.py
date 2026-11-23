import unittest
from importlib import import_module

gen = import_module('sinh-trang-can')

class RelatedTest(unittest.TestCase):
    def test_same_type_and_location_before_price(self):
        def rec(tower, zone, kind, price, area):
            return dict(toa=tower, phan_khu=zone, loai=kind, gia=price, dien_tich=area)
        active = {
            'current': rec('SA5','Sakura','3 Ngủ',16000000,78),
            'wrong-bedroom': rec('SA5','Sakura','1 Ngủ',7000000,42),
            'same-tower-expensive': rec('SA5','Sakura','3 Ngủ',20000000,85),
            'same-tower-close': rec('SA5','Sakura','3 Ngủ',16500000,79),
            'same-zone': rec('SA3','Sakura','3 Ngủ',16000000,78),
            'other-zone': rec('S401','Sapphire','3 Ngủ',16000000,78),
        }
        self.assertEqual(gen.can_tuong_tu('current','SA5','Sakura','3 Ngủ',active,gia=16000000,dien_tich=78),
                         ['same-tower-close','same-tower-expensive','same-zone','other-zone'])

if __name__ == '__main__': unittest.main()
