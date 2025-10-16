"""
Core strategy interface for all data loading models.
This defines the abstract base class that all model strategies must implement.
"""
from abc import ABC, abstractmethod
import geopandas as gpd
from typing import List, Dict, Any


class BaseLoaderStrategy(ABC):
    """Abstract base class for all data loading strategies"""

    def __init__(self, model_name: str, table_name: str):
        self.model_name = model_name
        self.table_name = table_name
        self.source_crs = None
        self.target_crs = "EPSG:4326"

    @abstractmethod
    def load_data(self, file_path: str) -> gpd.GeoDataFrame:
        """Load data from file and return GeoDataFrame"""
        pass

    @abstractmethod
    def transform_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Transform data according to model requirements"""
        pass

    @abstractmethod
    def get_column_mapping(self) -> Dict[str, str]:
        """Return mapping from source columns to target columns"""
        pass

    @abstractmethod
    def get_insert_sql(self) -> str:
        """Return SQL insert statement for this model"""
        pass

    def validate_data(self, gdf: gpd.GeoDataFrame) -> List[str]:
        """Validate data and return list of warnings/errors"""
        warnings = []

        # Check for required geometry column
        if 'geometry' not in gdf.columns and 'geom' not in gdf.columns:
            warnings.append("No geometry column found")

        # Check for empty geometries
        if 'geometry' in gdf.columns:
            empty_geoms = gdf['geometry'].is_empty.sum()
            if empty_geoms > 0:
                warnings.append(f"Found {empty_geoms} empty geometries")

        return warnings

    def get_model_info(self) -> Dict[str, Any]:
        """Return information about this model"""
        return {
            'model_name': self.model_name,
            'table_name': self.table_name,
            'source_crs': self.source_crs,
            'target_crs': self.target_crs,
        }