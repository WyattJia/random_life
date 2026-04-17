#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import gzip
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path


AREA_CODE_URL = (
    "https://raw.githubusercontent.com/adyliu/china_area/master/area_code_2024.csv.gz"
)
GEO_ARCHIVE_URL = (
    "https://github.com/xiangyuecn/AreaCity-JsSpider-StatsGov/releases/download/"
    "2025.251231.260403/ok_geo.csv.7z"
)

SHORT_PROVINCES = {
    "内蒙古自治区": "内蒙古",
    "广西壮族自治区": "广西",
    "西藏自治区": "西藏",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
}
MUNICIPALITY_CODES = {"110000", "120000", "310000", "500000"}
PLACEHOLDER_CITY_NAMES = {
    "市辖区",
    "县",
    "省直辖县级行政区划",
    "自治区直辖县级行政区划",
}
PLACEHOLDER_CITY_CODES = {"429000", "469000", "659000"}
DROP_PATTERNS = (
    "开发区",
    "园区",
    "实验区",
    "管理区",
    "行政委员会",
    "办事处",
    "示范区",
    "风景名胜区",
    "聚集区",
    "食品区",
)
ALLOWED_NEW_AREAS = {"浦东新区", "滨海新区"}
EXCLUDED_CODES = {"133100"}
MANUAL_NAME_OVERRIDES = {
    "460300": "海南省三沙市",
    "460302": "海南省三沙市西沙区",
    "460303": "海南省三沙市南沙区",
}
REMOVED_CODES = {"460321", "460322", "460323"}
# These three districts are missing from the public geo cache; the values below
# are bounding-box midpoints taken from the official district overview pages.
MANUAL_COORDS = {
    "232762": ("124.656944", "50.775556"),
    "232763": ("124.550000", "51.750000"),
    "232764": ("123.504167", "51.830556"),
}
SAR_CODES = ("810000", "820000")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="按现行区划骨架和最新公开坐标修复全国县级以上地名代码表。"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "全国县级以上地名代码及经纬度.csv",
        help="待修复的 CSV 文件路径。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="输出 CSV 文件路径，默认直接覆盖输入文件。",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "random_life_place_data_cache",
        help="下载和解压外部数据的缓存目录。",
    )
    return parser.parse_args()


def require_py7zr():
    try:
        import py7zr  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "缺少依赖 py7zr。可先执行：\n"
            "  uv pip install --python .venv/bin/python py7zr"
        ) from exc
    return py7zr


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return
    print(f"下载 {url}")
    with urllib.request.urlopen(url) as response, destination.open("wb") as output_file:
        shutil.copyfileobj(response, output_file)


def extract_geo_archive(archive_path: Path, extract_dir: Path) -> Path:
    geo_csv_path = extract_dir / "ok_geo.csv"
    if geo_csv_path.exists():
        return geo_csv_path

    py7zr = require_py7zr()
    extract_dir.mkdir(parents=True, exist_ok=True)
    print(f"解压 {archive_path}")
    with py7zr.SevenZipFile(archive_path, mode="r") as archive:
        archive.extract(path=extract_dir)
    return geo_csv_path


def load_existing_rows(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as data_file:
        rows = list(csv.DictReader(data_file))
    return {row["行政代码"]: row for row in rows}


def load_area_code_rows(path: Path) -> list[dict[str, str | int]]:
    with gzip.open(path, "rt", encoding="utf-8") as data_file:
        raw_rows = list(csv.reader(data_file))
    return [
        {
            "code12": row[0],
            "name": row[1],
            "level": int(row[2]),
            "parent12": row[3],
        }
        for row in raw_rows
        if int(row[2]) <= 3
    ]


def normalize_geo_code(raw_code: str) -> str:
    if len(raw_code) < 6:
        return raw_code + "0" * (6 - len(raw_code))
    return raw_code[:6]


def load_geo_centers(path: Path) -> dict[str, tuple[str, str]]:
    csv.field_size_limit(sys.maxsize)
    centers: dict[str, tuple[str, str]] = {}
    with path.open(encoding="utf-8-sig", newline="") as data_file:
        reader = csv.DictReader(data_file)
        for row in reader:
            geo = row["geo"].strip()
            if not geo or geo == "EMPTY":
                continue
            longitude, latitude = geo.split()
            centers[normalize_geo_code(row["id"])] = (longitude, latitude)
    centers.update(MANUAL_COORDS)
    return centers


def short_province(name: str) -> str:
    return SHORT_PROVINCES.get(name, name)


def should_drop(name: str) -> bool:
    if name.endswith("新区") and name not in ALLOWED_NEW_AREAS:
        return True
    if name.endswith("新城"):
        return True
    return name == "市辖区" or any(pattern in name for pattern in DROP_PATTERNS)


def build_current_names(
    base_rows: list[dict[str, str | int]],
    existing_rows: dict[str, dict[str, str]],
) -> dict[str, str]:
    base_by_code12 = {
        row["code12"]: row
        for row in base_rows
    }
    current_names: dict[str, str] = {}

    for row in base_rows:
        code = str(row["code12"])[:6]
        if code.startswith(("71", "81", "82")) or code in EXCLUDED_CODES:
            continue

        level = int(row["level"])
        name = str(row["name"])

        if level == 1:
            current_names[code] = name
            continue

        parent = base_by_code12[str(row["parent12"])]
        if level == 2:
            province_code = str(parent["code12"])[:6]
            province_name = str(parent["name"])
            if province_code in MUNICIPALITY_CODES:
                if code.endswith("0100"):
                    current_names[code] = province_name
                continue
            if name in PLACEHOLDER_CITY_NAMES or should_drop(name):
                continue
            current_names[code] = short_province(province_name) + name
            continue

        city = parent
        province = base_by_code12[str(city["parent12"])]
        city_code = str(city["code12"])[:6]
        province_code = str(province["code12"])[:6]
        if city_code in PLACEHOLDER_CITY_CODES and code == city_code:
            continue
        if should_drop(name):
            continue

        province_prefix = short_province(str(province["name"]))
        if (
            str(city["name"]) in PLACEHOLDER_CITY_NAMES
            or city_code in PLACEHOLDER_CITY_CODES
            or province_code in MUNICIPALITY_CODES
            or code == city_code
        ):
            current_names[code] = province_prefix + name
        else:
            current_names[code] = province_prefix + str(city["name"]) + name

    current_names.update(MANUAL_NAME_OVERRIDES)
    for code in REMOVED_CODES:
        current_names.pop(code, None)

    for code in SAR_CODES:
        current_names[code] = existing_rows[code]["地名"]

    return current_names


def build_repaired_rows(
    existing_rows: dict[str, dict[str, str]],
    current_names: dict[str, str],
    geo_centers: dict[str, tuple[str, str]],
) -> list[dict[str, str]]:
    repaired_rows: list[dict[str, str]] = []
    missing_coords: list[tuple[str, str]] = []
    exact_reused = 0
    geo_filled = 0

    for code, name in sorted(current_names.items()):
        if code in existing_rows:
            longitude = existing_rows[code]["东经"]
            latitude = existing_rows[code]["北纬"]
            exact_reused += 1
        elif code in geo_centers:
            longitude, latitude = geo_centers[code]
            geo_filled += 1
        else:
            missing_coords.append((code, name))
            continue

        repaired_rows.append(
            {
                "行政代码": code,
                "地名": name,
                "东经": longitude,
                "北纬": latitude,
            }
        )

    if missing_coords:
        preview = "\n".join(f"{code} {name}" for code, name in missing_coords[:20])
        raise SystemExit(f"仍有条目缺少坐标：\n{preview}")

    print(f"沿用原表坐标: {exact_reused}")
    print(f"补入最新中心点: {geo_filled}")
    print(f"最终条目数: {len(repaired_rows)}")
    return repaired_rows


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8", newline="") as data_file:
        writer = csv.DictWriter(data_file, fieldnames=["行政代码", "地名", "东经", "北纬"])
        writer.writeheader()
        writer.writerows(rows)
    temporary_path.replace(path)


def main() -> None:
    args = parse_args()
    output_path = args.output or args.input
    cache_dir = args.cache_dir
    area_code_path = cache_dir / "area_code_2024.csv.gz"
    geo_archive_path = cache_dir / "ok_geo.csv.7z"
    geo_extract_dir = cache_dir / "ok_geo"

    download(AREA_CODE_URL, area_code_path)
    download(GEO_ARCHIVE_URL, geo_archive_path)
    geo_csv_path = extract_geo_archive(geo_archive_path, geo_extract_dir)

    existing_rows = load_existing_rows(args.input)
    base_rows = load_area_code_rows(area_code_path)
    geo_centers = load_geo_centers(geo_csv_path)
    current_names = build_current_names(base_rows, existing_rows)
    repaired_rows = build_repaired_rows(existing_rows, current_names, geo_centers)
    write_rows(output_path, repaired_rows)
    print(f"已写入 {output_path}")


if __name__ == "__main__":
    main()
