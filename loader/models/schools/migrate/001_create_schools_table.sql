-- Template: Create Schools table
-- Copy and modify this file for your specific model
--
-- SEARCH AND REPLACE:
-- - Replace {MODEL_NAME} with your model name (e.g., Schools)
-- - Replace {TABLE_NAME} with your database table name (e.g., schools)
-- - Replace {GEOMETRY_TYPE} with your geometry type (e.g., POINT, POLYGON)
-- - Replace {MODEL_DESCRIPTION} with a description of your model

-- Create the new schools table with proper data types
CREATE TABLE IF NOT EXISTS public.schools (
  id SERIAL PRIMARY KEY,

  -- School information
  nombre_est TEXT,
  nombre_sed TEXT,
  orden_de_s TEXT,
  direccion TEXT,
  discapacidad TEXT,
  talentos_o TEXT,
  grupos_etn TEXT,

  -- Administrative data
  sector INTEGER,
  natu_jur INTEGER,
  calendario INTEGER,
  genero INTEGER,
  cod_loca TEXT,
  especialid INTEGER,
  clase_tipo INTEGER,
  bilingue INTEGER,
  fecha TIMESTAMP,
  dane12_est TEXT,
  dane12_sed TEXT,

  -- Disability data
  da_hipoacu INTEGER,
  da_sordera INTEGER,
  da_lenguas INTEGER,
  da_ucastel INTEGER,
  discap_fis INTEGER,
  discap_fle INTEGER,
  discap_pce INTEGER,
  di_dcognit INTEGER,
  di_sdown INTEGER,
  dis_multip INTEGER,
  dis_psicos INTEGER,
  dv_bajavis INTEGER,
  dis_ceguer INTEGER,
  t_espectro INTEGER,
  t_voz_y_ha INTEGER,
  sistemica INTEGER,
  sordocegue INTEGER,
  otra INTEGER,

  -- Enrollment data
  tot_est_ma INTEGER,
  afrodescen INTEGER,
  indigenas INTEGER,
  negritudes INTEGER,
  palenquero INTEGER,
  raizales INTEGER,
  rom INTEGER,
  tot_est_et INTEGER,

  -- Special education
  capacid_ex INTEGER,
  doble_exce INTEGER,
  te_actfisi INTEGER,
  te_artes INTEGER,
  te_cnatur INTEGER,
  te_csociai INTEGER,
  te_ldsocia INTEGER,
  te_tecnolo INTEGER,
  tot_est_ca INTEGER,

  -- General data
  tmatric_ge INTEGER,
  zona INTEGER,

  -- Required geometry column (adjust type and SRID as needed)
  geom GEOMETRY(POINT, 4326) NOT NULL,

  -- Standard metadata columns
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
-- Add indexes based on your query patterns
CREATE INDEX IF NOT EXISTS idx_schools_geom ON public.schools USING GIST (geom);
-- CREATE INDEX IF NOT EXISTS idx_schools_column ON public.schools (column_name);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_schools_updated_at
  BEFORE UPDATE ON public.schools
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE public.schools IS 'School locations in Bogota';
-- Add column comments as needed
-- COMMENT ON COLUMN public.schools.column_name IS 'Column description';