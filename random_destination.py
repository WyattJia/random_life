import pandas as pd
import numpy as np
import argparse
from colorama import Fore, Style, init
from typing import Dict, Optional, Sequence, Tuple

init(autoreset=True)

DEFAULT_MAX_DISTANCE = 600
DEFAULT_REFERENCE_COORDS = (31.2304, 121.4737)
DEFAULT_PROVINCE_WEIGHT = {"浙江省": 0.5, "江苏省": 0.7, "上海市": 0.5}

def load_data(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"{Fore.RED}无法加载文件: {e}")
        return pd.DataFrame()

def calculate_distances_vectorized(df: pd.DataFrame, reference_coords: Tuple[float, float]) -> pd.DataFrame:
    reference_lat, reference_lon = np.radians(reference_coords)
    latitudes = np.radians(df['北纬'].values)
    longitudes = np.radians(df['东经'].values)

    dlat = latitudes - reference_lat
    dlon = longitudes - reference_lon

    a = np.sin(dlat / 2.0) ** 2 + np.cos(reference_lat) * np.cos(latitudes) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    R = 6371.0  # 地球半径，单位为公里
    df['距离'] = R * c
    return df

def filter_by_distance(df: pd.DataFrame, max_distance: float) -> pd.DataFrame:
    return df[df['距离'] <= max_distance].copy()


def assign_weights_vectorized(df: pd.DataFrame, province_weight: Dict[str, float]) -> pd.DataFrame:
    weights = np.ones(len(df))
    normalized_weights = {
        province.strip(): weight for province, weight in province_weight.items() if province.strip()
    }

    for province, weight in normalized_weights.items():
        mask = df['地名'].str.contains(province, regex=False, na=False)
        weights[mask] = weight
    df['权重'] = weights
    return df


def select_random_location(df: pd.DataFrame) -> Optional[Tuple[str, float, Tuple[float, float]]]:
    if df.empty:
        print(f"{Fore.RED}没有可供选择的地点。")
        return None
    
    selected_row = df.sample(weights=df['权重']).iloc[0]
    return selected_row['地名'], selected_row['权重'], (selected_row['北纬'], selected_row['东经'])

def select_location_within_distance(file_path: str, max_distance: float, reference_coords: Tuple[float, float], province_weight: Dict[str, float]) -> Optional[Tuple[str, float, Tuple[float, float]]]:
    df = load_data(file_path)
    if df.empty:
        return None

    df = calculate_distances_vectorized(df, reference_coords)
    df_close = filter_by_distance(df, max_distance)

    num_cities_within_range = len(df_close)
    print("\n")
    print(f"{Fore.CYAN}正在筛选方圆 {max_distance} 公里内的地点，共有 {num_cities_within_range} 个城市入围\n")

    if df_close.empty:
        print(f"{Fore.RED}没有找到任何距离小于或等于 {max_distance} 公里的地点。")
        return None

    df_close = assign_weights_vectorized(df_close, province_weight)
    return select_random_location(df_close)


def parse_reference_coords(value: str) -> Tuple[float, float]:
    parts = [part.strip() for part in value.split(",", 1)]
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError("参考坐标格式应为 '纬度,经度'。")

    try:
        latitude = float(parts[0])
        longitude = float(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError("参考坐标中的纬度和经度必须是数字。") from exc

    if not -90 <= latitude <= 90:
        raise argparse.ArgumentTypeError("纬度必须在 -90 到 90 之间。")

    if not -180 <= longitude <= 180:
        raise argparse.ArgumentTypeError("经度必须在 -180 到 180 之间。")

    return latitude, longitude


def parse_province_weights(value: str) -> Dict[str, float]:
    province_weights: Dict[str, float] = {}

    for item in value.split(","):
        chunk = item.strip()
        if not chunk:
            continue

        if ":" not in chunk:
            raise argparse.ArgumentTypeError(
                "省份权重格式应为 '省份:权重'，多个配置用逗号分隔。"
            )

        province, weight_text = chunk.split(":", 1)
        province = province.strip()
        weight_text = weight_text.strip()

        if not province:
            raise argparse.ArgumentTypeError("省份名称不能为空。")

        try:
            weight = float(weight_text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("省份权重必须是数字。") from exc

        if weight < 0:
            raise argparse.ArgumentTypeError("省份权重不能为负数。")

        province_weights[province] = weight

    if not province_weights:
        raise argparse.ArgumentTypeError("至少需要提供一个省份权重配置。")

    return province_weights


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="地点数据文件路径。")
    parser.add_argument(
        "--max-distance",
        type=float,
        default=DEFAULT_MAX_DISTANCE,
        help=f"最大筛选半径，单位公里，默认值为 {DEFAULT_MAX_DISTANCE}。",
    )
    parser.add_argument(
        "--reference-coords",
        type=parse_reference_coords,
        default=DEFAULT_REFERENCE_COORDS,
        help=(
            "筛选圆心坐标，格式为 '纬度,经度'。"
            f" 默认值为 {DEFAULT_REFERENCE_COORDS[0]},{DEFAULT_REFERENCE_COORDS[1]}。"
        ),
    )
    parser.add_argument(
        "--province-weights",
        type=parse_province_weights,
        default=None,
        help=(
            "省份权重配置，格式为 '省份:权重,省份:权重'。"
            " 未传入时沿用默认配置。"
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    province_weight = DEFAULT_PROVINCE_WEIGHT.copy()
    if args.province_weights is not None:
        province_weight.update(args.province_weights)

    selected_location = select_location_within_distance(
        args.csv_file,
        args.max_distance,
        args.reference_coords,
        province_weight,
    )
    if selected_location:
        location_name, weight, coords = selected_location
        print(f"最终选定的位置是：\n   {Fore.YELLOW}{Style.BRIGHT}-----        {location_name} (权重：{weight}, 坐标：{coords})       -----\n")
    else:
        print(f"{Fore.RED}未能选择地点，请检查数据文件或参数。")

if __name__ == "__main__":
    main()
