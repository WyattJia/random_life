import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import pandas as pd

import random_destination as rd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "random_destination.py"


class AssignWeightsTests(unittest.TestCase):
    def test_assign_weights_normalizes_province_names(self) -> None:
        df = pd.DataFrame(
            {
                "地名": ["江苏省苏州市", "上海市", "北京市"],
                "北纬": [31.3, 31.2, 39.9],
                "东经": [120.6, 121.4, 116.4],
            }
        )

        weighted = rd.assign_weights_vectorized(
            df,
            {" 江苏省 ": 0.7, "\t上海市": 0.5},
        )

        self.assertEqual(weighted.loc[0, "权重"], 0.7)
        self.assertEqual(weighted.loc[1, "权重"], 0.5)
        self.assertEqual(weighted.loc[2, "权重"], 1.0)


class AdminLevelTests(unittest.TestCase):
    def test_select_location_filters_to_third_level_divisions_by_default(self) -> None:
        df = pd.DataFrame(
            {
                "行政代码": ["330000", "330100", "330106"],
                "地名": ["浙江省", "浙江省杭州市", "浙江省杭州市西湖区"],
                "北纬": [29.159494, 30.274085, 30.259615],
                "东经": [119.957202, 120.15507, 120.130663],
            }
        )

        filtered = rd.filter_to_third_level_divisions(df)

        self.assertEqual(filtered["行政代码"].tolist(), ["330106"])
        self.assertEqual(filtered["地名"].tolist(), ["浙江省杭州市西湖区"])


class CliTests(unittest.TestCase):
    def test_script_accepts_runtime_configuration_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "places.csv"
            csv_path.write_text(
                textwrap.dedent(
                    """\
                    地名,北纬,东经
                    上海市,31.2304,121.4737
                    """
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(csv_path),
                    "--max-distance",
                    "10",
                    "--reference-coords",
                    "31.2304,121.4737",
                    "--province-weights",
                    "上海市:0.5",
                ],
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
            )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("上海市", result.stdout)


if __name__ == "__main__":
    unittest.main()
