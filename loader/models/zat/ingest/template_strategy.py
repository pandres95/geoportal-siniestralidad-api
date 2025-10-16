"""
ZAT (Zonas de Atención Territorial) strategy for data loading.
This model handles territorial zones data from Bogota.
"""
import sys
import os
import glob
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from core.strategy import BaseLoaderStrategy
except ImportError:
    # Fallback for direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from core.strategy import BaseLoaderStrategy
import geopandas as gpd
import pandas as pd
from datetime import datetime
from typing import Dict, List


class ZATStrategy(BaseLoaderStrategy):
    """Strategy for loading ZAT (Zonas de Atención Territorial) data from .gpkg files"""

    def __init__(self):
        super().__init__("zat", "zat")
        self.source_crs = "EPSG:9377"  # MAGNA-SIRGAS / Origen-Nacional

    def load_data(self, file_path: str) -> gpd.GeoDataFrame:
        """Load data from file and return GeoDataFrame"""
        print(f"📖 Loading {self.table_name} data from: {file_path}")

        # Update based on your file format (.gpkg, .shp, etc.)
        gdf = gpd.read_file(file_path)

        print(f"✅ Loaded {len(gdf)} records")
        print(f"📋 Columns: {list(gdf.columns)}")
        print(f"📐 CRS: {gdf.crs}")

        return gdf

    def transform_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Transform data according to {MODEL_NAME} model requirements"""
        print(f"🔄 Transforming {self.table_name} data...")

        # Create a copy to avoid modifying original
        transformed_gdf = gdf.copy()

        # Add your specific transformations here
        # Examples:
        # - Date conversions
        # - Column renaming
        # - Data validation
        # - Coordinate transformations

        # Transform coordinate system if needed
        if gdf.crs and gdf.crs.to_string() != self.target_crs:
            print(f"🌐 Transforming CRS to {self.target_crs}")
            transformed_gdf = transformed_gdf.to_crs(self.target_crs)

        # Rename columns to match database schema
        column_mapping = self.get_column_mapping()
        for source_col, target_col in column_mapping.items():
            if source_col in transformed_gdf.columns:
                print(f"📝 Renaming {source_col} → {target_col}")
                transformed_gdf.rename(columns={source_col: target_col}, inplace=True)

        print(f"✅ Transformation completed")
        return transformed_gdf

    def get_column_mapping(self) -> Dict[str, str]:
        """Map source columns to target database columns"""
        return {
            'OBJECTID': 'objectid',
            'MUNCod': 'mun_cod',
            'NOMMun': 'nom_mun',
            'ZAT': 'zat',
            'UTAM': 'utam',
            'TMATRIC_GE_sum': 'tmatric_ge_sum',
            'Victimas': 'victimas',
            'Fallecidos': 'fallecidos',
            'PoblacionT': 'poblacion_t',
            'Poblacion<5': 'poblacion_menor_5',
            'Poblacion<18': 'poblacion_menor_18',
            'VICTIMAS<18': 'victimas_menor_18',
            'FALLECIDOS<18': 'fallecidos_menor_18',
            'Tasa_VictiXMatric_c1000': 'tasa_victi_x_matric_c1000',
            'Tasa_FalleXMatric_c1000': 'tasa_falle_x_matric_c1000',
            'geometry': 'geom',  # Geometry column (required)
        }

    def get_migration_files(self) -> Dict[str, List[str]]:
        """Return migration files for this model (up and down)"""
        model_path = f"models/{self.model_name}"
        migrate_path = f"{model_path}/migrate"

        up_migrations = []
        down_migrations = []

        if os.path.exists(migrate_path):
            # Get all .sql files in migrate directory
            for file_path in sorted(glob.glob(os.path.join(migrate_path, "*.sql"))):
                filename = os.path.basename(file_path)
                if 'rollback' in filename.lower() or 'down' in filename.lower():
                    down_migrations.append(file_path)
                elif filename != '001_create_migrations_table.sql':  # Skip the migrations table itself
                    up_migrations.append(file_path)

        return {
            'up': up_migrations,
            'down': down_migrations
        }

    def get_create_table_sql_path(self) -> str:
        """Return path to SQL CREATE TABLE file for {MODEL_NAME} model"""
        return "models/{model_name}/migrate/001_create_{table_name}_table.sql"

    def get_drop_table_sql_path(self) -> str:
        """Return path to SQL DROP TABLE file for {MODEL_NAME} model"""
        return "models/{model_name}/migrate/001_create_{table_name}_table_rollback.sql"

    def get_insert_sql(self) -> str:
        """Return SQL insert statement for ZAT table"""
        return """
        INSERT INTO public.zat
        (objectid, mun_cod, nom_mun, zat, utam, tmatric_ge_sum, victimas, fallecidos,
         poblacion_t, poblacion_menor_5, poblacion_menor_18, victimas_menor_18,
         fallecidos_menor_18, tasa_victi_x_matric_c1000, tasa_falle_x_matric_c1000, geom)
        VALUES %s
        """

    def validate_data(self, gdf: gpd.GeoDataFrame) -> List[str]:
        """Validate {MODEL_NAME}-specific data"""
        warnings = super().validate_data(gdf)

        # Add your specific validations here
        # Examples:
        # - Check for required columns
        # - Validate data ranges
        # - Check for duplicates

        return warnings