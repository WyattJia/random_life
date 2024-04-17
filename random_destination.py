import pandas as pd
from geopy.distance import geodesic
import argparse

def select_location_within_distance(file_path, max_distance, reference_coords, province_weight):
    """
    Select a random location within a specified maximum distance from a reference point,
    with adjusted weights based on whether the location is in a specified province.

    Parameters:
    - file_path: str, path to the CSV file containing locations and their coordinates.
    - max_distance: float, maximum distance in kilometers from the reference point.
    - reference_coords: tuple, coordinates (latitude, longitude) of the reference point.
    - province_weight: dict, dictionary containing the province name and its associated weight.

    Returns:
    - A pandas Series containing the randomly selected location.
    """
    # Load the CSV file
    df = pd.read_csv(file_path, names=['行政代码', '地名', '东经', '北纬'], header=None, skiprows=1)
    
    # Calculate the distance to the reference point
    df['距离'] = df.apply(lambda row: geodesic((row['北纬'], row['东经']), reference_coords).km, axis=1)
    
    # Filter locations within the maximum distance
    df_close = df[df['距离'] <= max_distance].copy()
    
    # Apply weights based on province
    df_close.loc[:, '权重'] = df_close['地名'].apply(lambda x: province_weight['浙江省'] if '浙江省' in x else 1)
    
    # Randomly select a location based on weights
    random_choice = df_close.sample(weights=df_close['权重'])
    
    return random_choice['地名']

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Select a random location within a certain distance from Shanghai.")
    parser.add_argument("csv_file", help="Path to the CSV file containing location data.")
    args = parser.parse_args()

    # Constants
    MAX_DISTANCE = 600  # in kilometers
    REFERENCE_COORDS = (31.2304, 121.4737)  # Shanghai's coordinates
    PROVINCE_WEIGHT = {'浙江省': 0.9}

    # Call the function and print the selected location
    selected_location1 = select_location_within_distance(args.csv_file, MAX_DISTANCE, REFERENCE_COORDS, PROVINCE_WEIGHT)
    selected_location2 = select_location_within_distance(args.csv_file, MAX_DISTANCE, REFERENCE_COORDS, PROVINCE_WEIGHT)
    selected_location3 = select_location_within_distance(args.csv_file, MAX_DISTANCE, REFERENCE_COORDS, PROVINCE_WEIGHT)

    print(selected_location1.iloc[0])  # Changed here to print the actual location name
    print(selected_location2.iloc[0])  # Changed here to print the actual location name
    print(selected_location3.iloc[0])  # Changed here to print the actual location name


if __name__ == "__main__":
    main()

