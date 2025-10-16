-- Migration: Create ZAT table
-- This migration creates the zat table for the ZAT (Zonas de Atención Territorial) model
--
-- ZAT contains territorial zones data from Bogota with demographic and accident statistics

-- Create the new zat table with proper data types
CREATE TABLE IF NOT EXISTS public.zat (
  id SERIAL PRIMARY KEY,
  objectid INTEGER,
  mun_cod INTEGER,
  nom_mun TEXT,
  zat TEXT,
  utam TEXT,
  tmatric_ge_sum DECIMAL(15,2),
  victimas INTEGER,
  fallecidos INTEGER,
  poblacion_t INTEGER,
  poblacion_menor_5 INTEGER,
  poblacion_menor_18 INTEGER,
  victimas_menor_18 INTEGER,
  fallecidos_menor_18 INTEGER,
  tasa_victi_x_matric_c1000 DECIMAL(10,4),
  tasa_falle_x_matric_c1000 DECIMAL(10,4),

  -- Required geometry column (MultiPolygonZ for territorial zones with Z dimension)
  geom GEOMETRY(MULTIPOLYGONZ, 4326) NOT NULL,

  -- Standard metadata columns
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_zat_geom ON public.zat USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_zat_zat ON public.zat (zat);
CREATE INDEX IF NOT EXISTS idx_zat_mun_cod ON public.zat (mun_cod);
CREATE INDEX IF NOT EXISTS idx_zat_nom_mun ON public.zat (nom_mun);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_zat_updated_at
  BEFORE UPDATE ON public.zat
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE public.zat IS 'Zonas de Atención Territorial - Territorial zones in Bogota with demographic and accident statistics';
COMMENT ON COLUMN public.zat.objectid IS 'Original object identifier';
COMMENT ON COLUMN public.zat.mun_cod IS 'Municipality code';
COMMENT ON COLUMN public.zat.nom_mun IS 'Municipality name';
COMMENT ON COLUMN public.zat.zat IS 'ZAT zone identifier';
COMMENT ON COLUMN public.zat.utam IS 'UTAM zone identifier';
COMMENT ON COLUMN public.zat.tmatric_ge_sum IS 'Sum of registered vehicles by geometry';
COMMENT ON COLUMN public.zat.victimas IS 'Total victims in the zone';
COMMENT ON COLUMN public.zat.fallecidos IS 'Total fatalities in the zone';
COMMENT ON COLUMN public.zat.poblacion_t IS 'Total population';
COMMENT ON COLUMN public.zat.poblacion_menor_5 IS 'Population under 5 years';
COMMENT ON COLUMN public.zat.poblacion_menor_18 IS 'Population under 18 years';
COMMENT ON COLUMN public.zat.victimas_menor_18 IS 'Victims under 18 years';
COMMENT ON COLUMN public.zat.fallecidos_menor_18 IS 'Fatalities under 18 years';
COMMENT ON COLUMN public.zat.tasa_victi_x_matric_c1000 IS 'Victim rate per 1000 registered vehicles';
COMMENT ON COLUMN public.zat.tasa_falle_x_matric_c1000 IS 'Fatality rate per 1000 registered vehicles';