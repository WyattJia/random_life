import pandas as pd
import numpy as np
import argparse
from colorama import Fore, Style, init
from typing import Tuple, Dict, Optional

init(autoreset=True)

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
    for province, weight in province_weight.items():
        mask = df['地名'].str.contains(province)
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="地点数据文件路径。")
    args = parser.parse_args()

    MAX_DISTANCE = 600
    REFERENCE_COORDS = (31.2304, 121.4737)
    PROVINCE_WEIGHT = {'浙江省': 0.5, " 江苏省": 0.7, "上海市": 0.5}

    selected_location = select_location_within_distance(args.csv_file, MAX_DISTANCE, REFERENCE_COORDS, PROVINCE_WEIGHT)
    if selected_location:
        location_name, weight, coords = selected_location
        print(f"最终选定的位置是：\n   {Fore.YELLOW}{Style.BRIGHT}-----        {location_name} (权重：{weight}, 坐标：{coords})       -----\n")
    else:
        print(f"{Fore.RED}未能选择地点，请检查数据文件或参数。")

if __name__ == "__main__":
    main()
