-- Migration: Create new victims table for unified victims model
-- This replaces the separate accidents_injuries and accidents_fatalities tables

-- Drop legacy tables first (data should be migrated separately using migrate_existing_data.py)
DROP TABLE IF EXISTS public.accidents_with_fatalities CASCADE;
DROP TABLE IF EXISTS public.accidents_with_injuries CASCADE;

-- Create the new victims table with proper data types (unified model for all accident victims)
CREATE TABLE IF NOT EXISTS public.victims (
  fid SERIAL PRIMARY KEY,
  formulario TEXT,
  codigo_accidentado INTEGER,
  codigo_victima INTEGER,
  codigo_vehiculo INTEGER,
  estado TEXT,
  muerte_posterior TEXT,
  fecha_posterior_muerte DATE,
  genero TEXT,
  fecha_nacimiento DATE,
  edad INTEGER,
  codigo TEXT,
  condicion TEXT,
  fecha_acc DATE,
  latitud DECIMAL(10,8),
  longitud DECIMAL(11,8),
  geom GEOMETRY(POINT, 4326) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_victims_geom ON public.victims USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_victims_fecha_acc ON public.victims (fecha_acc);
CREATE INDEX IF NOT EXISTS idx_victims_fecha_nacimiento ON public.victims (fecha_nacimiento);
CREATE INDEX IF NOT EXISTS idx_victims_edad ON public.victims (edad);
CREATE INDEX IF NOT EXISTS idx_victims_genero ON public.victims (genero);
CREATE INDEX IF NOT EXISTS idx_victims_condicion ON public.victims (condicion);
CREATE INDEX IF NOT EXISTS idx_victims_formulario ON public.victims (formulario);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_victims_updated_at
  BEFORE UPDATE ON public.victims
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Drop legacy tables (data should be migrated separately using migrate_existing_data.py)
DROP TABLE IF EXISTS public.accidents_with_fatalities;
DROP TABLE IF EXISTS public.accidents_with_injuries;

-- Add comments for documentation
COMMENT ON TABLE public.victims IS 'Unified table for all traffic accident victims (injuries and fatalities)';
COMMENT ON COLUMN public.victims.fid IS 'Primary key - auto-incrementing ID';
COMMENT ON COLUMN public.victims.formulario IS 'Form identifier';
COMMENT ON COLUMN public.victims.codigo_accidentado IS 'Accident participant code';
COMMENT ON COLUMN public.victims.codigo_victima IS 'Victim code';
COMMENT ON COLUMN public.victims.codigo_vehiculo IS 'Vehicle code';
COMMENT ON COLUMN public.victims.estado IS '30-day status';
COMMENT ON COLUMN public.victims.muerte_posterior IS 'Posterior death indicator';
COMMENT ON COLUMN public.victims.fecha_posterior_muerte IS 'Date of posterior death';
COMMENT ON COLUMN public.victims.genero IS 'Gender';
COMMENT ON COLUMN public.victims.fecha_nacimiento IS 'Birth date';
COMMENT ON COLUMN public.victims.edad IS 'Age';
COMMENT ON COLUMN public.victims.codigo IS 'Code';
COMMENT ON COLUMN public.victims.condicion IS 'Condition type A';
COMMENT ON COLUMN public.victims.fecha_acc IS 'Accident date';
COMMENT ON COLUMN public.victims.latitud IS 'Latitude coordinate';
COMMENT ON COLUMN public.victims.longitud IS 'Longitude coordinate';
COMMENT ON COLUMN public.victims.geom IS 'Geometry point in EPSG:4326';