"""
Template strategy for new model implementation.
Copy and modify this file for your specific model requirements.

SEARCH AND REPLACE:
- Replace {MODEL_NAME} with your model name (e.g., Schools)
- Replace {TABLE_NAME} with your database table name (e.g., schools)
- Replace {SOURCE_CRS} with your source coordinate system (e.g., EPSG:4326)
"""
import sys
import os
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


class SchoolsStrategy(BaseLoaderStrategy):
    """Strategy for loading Schools data from .gpkg files"""

    def __init__(self):
        super().__init__("schools", "schools")
        self.source_crs = "EPSG:3857"  # Update as needed

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
        """Transform data according to Schools model requirements"""
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
            # Map all the school data columns
            'NOMBRE_EST': 'nombre_est',
            'NOMBRE_SED': 'nombre_sed',
            'ORDEN_DE_S': 'orden_de_s',
            'DIRECCION': 'direccion',
            'DISCAPACID': 'discapacidad',
            'TALENTOS_O': 'talentos_o',
            'GRUPOS_ETN': 'grupos_etn',
            'SECTOR': 'sector',
            'NATU_JUR': 'natu_jur',
            'CALENDARIO': 'calendario',
            'GENERO': 'genero',
            'COD_LOCA': 'cod_loca',
            'ESPECIALID': 'especialid',
            'CLASE_TIPO': 'clase_tipo',
            'BILINGUE': 'bilingue',
            'FECHA': 'fecha',
            'DANE12_EST': 'dane12_est',
            'DANE12_SED': 'dane12_sed',
            'DA_HIPOACU': 'da_hipoacu',
            'DA_SORDERA': 'da_sordera',
            'DA_LENGUAS': 'da_lenguas',
            'DA_UCASTEL': 'da_ucastel',
            'DISCAP_FIS': 'discap_fis',
            'DISCAP_FLE': 'discap_fle',
            'DISCAP_PCE': 'discap_pce',
            'DI_DCOGNIT': 'di_dcognit',
            'DI_SDOWN': 'di_sdown',
            'DIS_MULTIP': 'dis_multip',
            'DIS_PSICOS': 'dis_psicos',
            'DV_BAJAVIS': 'dv_bajavis',
            'DIS_CEGUER': 'dis_ceguer',
            'T_ESPECTRO': 't_espectro',
            'T_VOZ_Y_HA': 't_voz_y_ha',
            'SISTEMICA': 'sistemica',
            'SORDOCEGUE': 'sordocegue',
            'OTRA': 'otra',
            'TOT_EST_MA': 'tot_est_ma',
            'AFRODESCEN': 'afrodescen',
            'INDIGENAS': 'indigenas',
            'NEGRITUDES': 'negritudes',
            'PALENQUERO': 'palenquero',
            'RAIZALES': 'raizales',
            'ROM': 'rom',
            'TOT_EST_ET': 'tot_est_et',
            'CAPACID_EX': 'capacid_ex',
            'DOBLE_EXCE': 'doble_exce',
            'TE_ACTFISI': 'te_actfisi',
            'TE_ARTES': 'te_artes',
            'TE_CNATUR': 'te_cnatur',
            'TE_CSOCIAL': 'te_csociai',
            'TE_LDSOCIA': 'te_ldsocia',
            'TE_TECNOLO': 'te_tecnolo',
            'TOT_EST_CA': 'tot_est_ca',
            'TMATRIC_GE': 'tmatric_ge',
            'Zona': 'zona',
            'geom': 'geom',  # Geometry column (required)
        }

    def get_create_table_sql_path(self) -> str:
        """Return path to SQL CREATE TABLE file for Schools model"""
        return "models/schools/migrate/001_create_schools_table.sql"

    def get_drop_table_sql_path(self) -> str:
        """Return path to SQL DROP TABLE file for Schools model"""
        return "models/schools/migrate/001_create_schools_table_rollback.sql"

    def get_insert_sql(self) -> str:
        """Return SQL insert statement for this model"""
        return """
        INSERT INTO public.schools
        (nombre_est, nombre_sed, orden_de_s, direccion, discapacidad, talentos_o, grupos_etn, sector, natu_jur, calendario, genero, cod_loca, especialid, clase_tipo, bilingue, fecha, dane12_est, dane12_sed, da_hipoacu, da_sordera, da_lenguas, da_ucastel, discap_fis, discap_fle, discap_pce, di_dcognit, di_sdown, dis_multip, dis_psicos, dv_bajavis, dis_ceguer, t_espectro, t_voz_y_ha, sistemica, sordocegue, otra, tot_est_ma, afrodescen, indigenas, negritudes, palenquero, raizales, rom, tot_est_et, capacid_ex, doble_exce, te_actfisi, te_artes, te_cnatur, te_csociai, te_ldsocia, te_tecnolo, tot_est_ca, tmatric_ge, zona, geom)
        VALUES %s
        """

    def validate_data(self, gdf: gpd.GeoDataFrame) -> List[str]:
        """Validate Schools-specific data"""
        warnings = super().validate_data(gdf)

        # Add your specific validations here
        # Examples:
        # - Check for required columns
        # - Validate data ranges
        # - Check for duplicates

        return warnings