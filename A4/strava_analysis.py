"""
strava_analysis.py

This script processes and analyzes geospatial data collected from Strava activities.
It performs the following:
- Loads and cleans raw Strava data.
- Extracts relevant temporal and spatial features.
- Visualizes activities on an interactive folium map and plots using seaborn.

Requirements:
    * pandas
    * geopandas
    * folium
    * matplotlib
    * seaborn

This file can also be importaed as a module, and the fuctions which could be used are:
    * load_strava_data
    * plot_speed_distribution
    * map_activities
"""

import pandas as pd
import geopandas as gpd
import folium
import seaborn as sns
import matplotlib.pyplot as plt
from shapely.geometry import Point


def load_strava_data(filepath):
    """
    Load and clean the Strava activity data from a CSV file.

    Args:
        filepath (str): Path to the Strava CSV file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with selected and formatted columns.
    """
    cols = [
        'name', 'upload_id', 'type', 'distance', 'moving_time',
        'average_speed', 'max_speed', 'total_elevation_gain',
        'start_date_local', 'start_latlng', 'end_latlng', 'map.summary_polyline'
    ]
    
    df = pd.read_csv(filepath)
    df = df[cols].copy()

    # Convert date-time and extract time separately
    df['start_date_local'] = pd.to_datetime(df['start_date_local'], errors='coerce')
    df['start_time'] = df['start_date_local'].dt.time
    df['start_date_local'] = df['start_date_local'].dt.date

    # Remove entries without lat/lng
    df = df[df['start_latlng'].notnull()]
    
    return df


def plot_speed_distribution(df):
    """
    Plot the distribution of average and maximum speed using seaborn.

    Args:
        df (pd.DataFrame): Cleaned Strava DataFrame.
    """
    plt.figure(figsize=(12, 6))
    sns.histplot(df['average_speed'], bins=30, kde=True, label='Average Speed', color='blue')
    sns.histplot(df['max_speed'], bins=30, kde=True, label='Max Speed', color='red', alpha=0.6)
    plt.title('Distribution of Speeds in Activities')
    plt.xlabel('Speed (m/s)')
    plt.legend()
    plt.grid(True)
    plt.show()


def map_activities_with_endpoints(df, zoom_start=12):
    """
    Plot activity start and end points on an interactive folium map using GeoDataFrame geometry.

    Args:
        df (pd.DataFrame): DataFrame with 'start_latlng' and 'end_latlng' as stringified lists.
        zoom_start (int): Initial zoom level for the folium map.

    Returns:
        folium.Map: A folium map with start (blue) and end (red) points.
    """
    # Extract coordinates from list-like strings
    df['start_lat'] = df['start_latlng'].apply(lambda x: eval(x)[0])
    df['start_lon'] = df['start_latlng'].apply(lambda x: eval(x)[1])
    df['end_lat'] = df['end_latlng'].apply(lambda x: eval(x)[0] if pd.notnull(x) else None)
    df['end_lon'] = df['end_latlng'].apply(lambda x: eval(x)[1] if pd.notnull(x) else None)

    # Drop rows with any missing coordinates
    df = df.dropna(subset=['start_lat', 'start_lon', 'end_lat', 'end_lon'])

    # Create Point geometries
    start_geometry = [Point(xy) for xy in zip(df['start_lon'], df['start_lat'])]
    end_geometry = [Point(xy) for xy in zip(df['end_lon'], df['end_lat'])]

    # Create GeoDataFrame with start points
    gdf = gpd.GeoDataFrame(df.copy(), geometry=start_geometry, crs="EPSG:4326")

    # Create the folium map centered on mean start coordinates
    map_center = [df['start_lat'].mean(), df['start_lon'].mean()]
    fmap = folium.Map(location=map_center, zoom_start=zoom_start)

    # Add start points (blue)
    for _, row in gdf.iterrows():
        folium.CircleMarker(
            location=[row['start_lat'], row['start_lon']],
            radius=5,
            popup=f"{row['name']} ({row['type']}) - Start",
            color='blue',
            fill=True,
            fill_opacity=0.7
        ).add_to(fmap)

    # Add end points (red)
    for i, row in gdf.iterrows():
        folium.CircleMarker(
            location=[row['end_lat'], row['end_lon']],
            radius=4,
            popup=f"{row['name']} ({row['type']}) - End",
            color='red',
            fill=True,
            fill_opacity=0.6
        ).add_to(fmap)

    return fmap