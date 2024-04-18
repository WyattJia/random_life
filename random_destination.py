import pandas as pd
from geopy.distance import geodesic
import argparse
from colorama import Fore, Style, init

init(autoreset=True)

def select_location_within_distance(file_path, max_distance, reference_coords, province_weight):
    """
    选择一个随机地点，该地点距离上海不超过600公里，并根据省份权重进行选择调整。
    
    参数:
    - file_path: CSV文件路径，包含位置数据。
    - max_distance: 允许的最大距离（公里）。
    - reference_coords: 上海的坐标（纬度，经度）。
    - province_weight: 省份权重字典。
    
    返回:
    - 随机选定的位置名称。
    """
    print(f"{Fore.YELLOW}加载数据... \n       <<<<<  {file_path}  >>>>>     ")
    df = pd.read_csv(file_path, names=['行政代码', '地名', '东经', '北纬'], header=None, skiprows=1)
    
    df['距离'] = df.apply(lambda row: geodesic((row['北纬'], row['东经']), reference_coords).km, axis=1)
    
    print(f"{Fore.CYAN}筛选距离≤ {max_distance}公里的地点")
    df_close = df[df['距离'] <= max_distance].copy()
    
    if df_close.empty:
        print(f"{Fore.RED}没有找到任何距离小于或等于 {max_distance} 公里的地点。")
        return None
    
    # 确保省份权重计算中至少有一个默认值1
    df_close['权重'] = df_close['地名'].apply(
        lambda x: max((province_weight.get(prov, 1) for prov in province_weight if prov in x), default=1)
    )
    
    print(f"{Fore.GREEN}随机选择地点中...")
    selected_location = df_close.sample(weights=df_close['权重'])['地名'].iloc[0]
    return selected_location

def main():
    parser = argparse.ArgumentParser(description="启动位置选择器，从上海出发，随机选择一个不超过600公里的附近地点，考虑省份权重影响。")
    parser.add_argument("csv_file", help="地点数据文件路径。")
    args = parser.parse_args()

    print(f"{Fore.MAGENTA}启动位置选择器，从上海出发，随机选择一个不超过600公里的附近地点，考虑省份权重影响。")
    MAX_DISTANCE = 600
    REFERENCE_COORDS = (31.2304, 121.4737)
    PROVINCE_WEIGHT = {'浙江省': 0.8, "福建省": 1.1}

    selected_location = select_location_within_distance(args.csv_file, MAX_DISTANCE, REFERENCE_COORDS, PROVINCE_WEIGHT)
    if selected_location:
        print(f"最终选定的位置是：\n   {Fore.YELLOW}{Style.BRIGHT}<<<<<<        {selected_location}        >>>>>>")
    else:
        print(f"{Fore.RED}未能选择地点，请检查数据文件或参数。")

if __name__ == "__main__":
    main()
