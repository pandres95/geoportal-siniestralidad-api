#!/usr/bin/env python3
"""
Generic script to explore any .gpkg file structure and understand the data format.
This is an auxiliary tool for discovering new models and their data structures.
"""
import geopandas as gpd
import pandas as pd
import numpy as np
import os
import argparse
import sys
from pathlib import Path


def explore_geospatial_file(file_path: str, show_sample: bool = True, show_stats: bool = True):
    """
    Explore the structure of any geospatial file (.gpkg, .shp, etc.)

    Args:
        file_path: Path to the geospatial file to explore
        show_sample: Whether to show sample rows
        show_stats: Whether to show statistical summary
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None

    # Determine file type from extension
    file_ext = Path(file_path).suffix.lower()
    file_type = {
        '.gpkg': 'GeoPackage',
        '.shp': 'Shapefile',
        '.geojson': 'GeoJSON',
        '.json': 'JSON',
        '.kml': 'KML',
        '.gml': 'GML'
    }.get(file_ext, 'Unknown')

    print(f"📖 Exploring {file_type} file: {file_path}")

    try:
        # Read the geospatial file
        print(f"🔄 Reading {file_type} file...")
        gdf = gpd.read_file(file_path)

        print("\n✅ Successfully loaded file!")
        print(f"📊 Shape: {gdf.shape} rows × {len(gdf.columns)} columns")
        print(f"📋 Columns: {list(gdf.columns)}")
        print(f"📐 CRS: {gdf.crs}")

        if hasattr(gdf.geometry, 'type'):
            print(f"🔢 Geometry types: {gdf.geometry.type.unique()}")

        print("\n📋 Data types:")
        for col, dtype in gdf.dtypes.items():
            print(f"   {col}: {dtype}")

        # Show sample rows if requested
        if show_sample:
            print("\n🔍 Sample data (first 5 rows):")
            print(gdf.head())

        # Show statistical summary if requested
        if show_stats:
            print("\n📈 Statistical summary:")
            numeric_cols = gdf.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                print(gdf[numeric_cols].describe())
            else:
                print("   No numeric columns found for statistical summary")

        # Analyze geometry column
        geometry_cols = [col for col in gdf.columns if col.lower() in ['geometry', 'geom', 'the_geom']]
        if geometry_cols:
            geom_col = geometry_cols[0]
            print(f"\n🗺️  Geometry analysis ({geom_col}):")
            print(f"   Type: {gdf[geom_col].dtype}")
            print(f"   Sample geometry: {gdf[geom_col].iloc[0] if len(gdf) > 0 else 'N/A'}")

            # Check for empty geometries
            empty_count = gdf[geom_col].is_empty.sum()
            if empty_count > 0:
                print(f"   ⚠️  Found {empty_count} empty geometries ({empty_count/len(gdf)*100:.1f}%)")
        else:
            print("\n🗺️  No standard geometry column found")

        # Column analysis
        print("\n📊 Column analysis:")
        for col in gdf.columns:
            if col != 'geometry':  # Skip geometry for null analysis
                null_count = gdf[col].isna().sum()
                unique_count = gdf[col].nunique()
                print(f"   {col}: {gdf[col].dtype} | {null_count} nulls | {unique_count} unique values")

        print(f"\n✅ Exploration completed for {len(gdf)} records")
        return gdf

    except Exception as e:
        print(f"❌ Error reading file: {e}")
        print(f"   Error type: {type(e).__name__}")
        return None


def suggest_model_strategy(gdf: gpd.GeoDataFrame, model_name: str = None) -> str:
    """
    Suggest a basic model strategy based on the explored data structure.

    Args:
        gdf: The explored GeoDataFrame
        model_name: Suggested name for the model

    Returns:
        Python code suggestion for a model strategy
    """
    if model_name is None:
        # Generate model name from filename or use generic
        model_name = "generic_model"

    columns = list(gdf.columns)
    geometry_cols = [col for col in columns if col.lower() in ['geometry', 'geom', 'the_geom']]

    suggestion = f'''
# Suggested strategy for {model_name} model
# Copy this to models/{model_name}/ingest/{model_name}_strategy.py

class {model_name.title()}Strategy(BaseLoaderStrategy):
    """Strategy for loading {model_name} data"""

    def __init__(self):
        super().__init__("{model_name}", "{model_name}")

    def load_data(self, file_path: str) -> gpd.GeoDataFrame:
        return gpd.read_file(file_path)

    def transform_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        # Add your transformations here
        return gdf

    def get_column_mapping(self) -> Dict[str, str]:
        return {{
            # Map your source columns to target columns
            {", ".join([f'"{col}": "{col}"' for col in columns[:5]])},  # Example for first 5 columns
            "geom": "geom"  # Geometry column
        }}

    def get_insert_sql(self) -> str:
        return """
        INSERT INTO public.{model_name}
        ({", ".join(columns[:5])}, geom)  # Adjust columns as needed
        VALUES %s
        """
'''

    return suggestion


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='Explore geospatial file structure')
    parser.add_argument('file_path', help='Path to the geospatial file to explore')
    parser.add_argument('--no-sample', action='store_true',
                       help='Skip showing sample rows')
    parser.add_argument('--no-stats', action='store_true',
                       help='Skip statistical summary')
    parser.add_argument('--suggest-strategy', action='store_true',
                       help='Suggest a model strategy based on the data')

    args = parser.parse_args()

    # Explore the file
    gdf = explore_geospatial_file(
        args.file_path,
        show_sample=not args.no_sample,
        show_stats=not args.no_stats
    )

    if gdf is not None and args.suggest_strategy:
        print("\n💡 Suggested model strategy:")
        print(suggestion)

    return 0 if gdf is not None else 1


if __name__ == "__main__":
    exit(main())