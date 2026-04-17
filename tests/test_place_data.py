import csv
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "全国县级以上地名代码及经纬度.csv"


class PlaceDataTests(unittest.TestCase):
    def test_shanghai_obsolete_divisions_are_removed(self) -> None:
        with DATA_PATH.open(encoding="utf-8") as data_file:
            rows = list(csv.DictReader(data_file))

        place_names = {row["地名"] for row in rows}

        self.assertNotIn("上海市卢湾区", place_names)
        self.assertNotIn("上海市闸北区", place_names)
        self.assertNotIn("上海市南汇区", place_names)
        self.assertNotIn("上海市县", place_names)
        self.assertNotIn("上海市崇明县", place_names)
        self.assertIn("上海市黄浦区", place_names)
        self.assertIn("上海市静安区", place_names)
        self.assertIn("上海市浦东新区", place_names)
        self.assertIn("上海市崇明区", place_names)


if __name__ == "__main__":
    unittest.main()
