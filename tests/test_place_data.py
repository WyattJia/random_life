import csv
import re
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

    def test_beijing_and_tianjin_use_current_divisions(self) -> None:
        with DATA_PATH.open(encoding="utf-8") as data_file:
            rows = list(csv.DictReader(data_file))

        place_names = {row["地名"] for row in rows}

        self.assertNotIn("北京市崇文区", place_names)
        self.assertNotIn("北京市宣武区", place_names)
        self.assertNotIn("北京市密云县", place_names)
        self.assertNotIn("北京市延庆县", place_names)
        self.assertIn("北京市密云区", place_names)
        self.assertIn("北京市延庆区", place_names)

        self.assertNotIn("天津市塘沽区", place_names)
        self.assertNotIn("天津市汉沽区", place_names)
        self.assertNotIn("天津市大港区", place_names)
        self.assertNotIn("天津市蓟县", place_names)
        self.assertIn("天津市滨海新区", place_names)
        self.assertIn("天津市蓟州区", place_names)

    def test_suzhou_chongqing_and_hainan_use_current_divisions(self) -> None:
        with DATA_PATH.open(encoding="utf-8") as data_file:
            rows = list(csv.DictReader(data_file))

        place_names = {row["地名"] for row in rows}

        self.assertNotIn("江苏省苏州市沧浪区", place_names)
        self.assertNotIn("江苏省苏州市平江区", place_names)
        self.assertNotIn("江苏省苏州市金阊区", place_names)
        self.assertIn("江苏省苏州市姑苏区", place_names)
        self.assertIn("江苏省苏州市吴江区", place_names)

        self.assertNotIn("重庆市开县", place_names)
        self.assertNotIn("重庆市潼南县", place_names)
        self.assertNotIn("重庆市铜梁县", place_names)
        self.assertNotIn("重庆市荣昌县", place_names)
        self.assertIn("重庆市开州区", place_names)
        self.assertIn("重庆市潼南区", place_names)
        self.assertIn("重庆市铜梁区", place_names)
        self.assertIn("重庆市荣昌区", place_names)

        self.assertNotIn("海南省西沙群岛", place_names)
        self.assertNotIn("海南省南沙群岛", place_names)
        self.assertIn("海南省三沙市西沙区", place_names)
        self.assertIn("海南省三沙市南沙区", place_names)
        self.assertIn("海南省儋州市", place_names)

    def test_dataset_excludes_placeholder_and_statistical_zone_rows(self) -> None:
        with DATA_PATH.open(encoding="utf-8") as data_file:
            rows = list(csv.DictReader(data_file))

        place_names = {row["地名"] for row in rows}
        disallowed_patterns = (
            r"市辖区$",
            r"开发区",
            r"产业园区",
            r"实验区",
            r"管理区",
            r"行政单位$",
            r"行政区划$",
        )

        for pattern in disallowed_patterns:
            self.assertFalse(
                any(re.search(pattern, name) for name in place_names),
                f"发现不应保留的占位或统计口径地名: {pattern}",
            )


if __name__ == "__main__":
    unittest.main()
