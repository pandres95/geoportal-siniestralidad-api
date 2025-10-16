-- Template: Create {MODEL_NAME} table
-- Copy and modify this file for your specific model
--
-- SEARCH AND REPLACE:
-- - Replace {MODEL_NAME} with your model name (e.g., Schools)
-- - Replace {TABLE_NAME} with your database table name (e.g., schools)
-- - Replace {GEOMETRY_TYPE} with your geometry type (e.g., POINT, POLYGON)
-- - Replace {MODEL_DESCRIPTION} with a description of your model

-- Create the new {table_name} table with proper data types
CREATE TABLE IF NOT EXISTS public.{table_name} (
  id SERIAL PRIMARY KEY,
  -- Add your model-specific columns here
  -- Examples:
  -- name TEXT,
  -- description TEXT,
  -- value DECIMAL(10,2),
  -- category TEXT,
  -- created_date DATE,
  -- updated_date DATE,

  -- Required geometry column (adjust type and SRID as needed)
  geom GEOMETRY({GEOMETRY_TYPE}, 4326) NOT NULL,

  -- Standard metadata columns
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
-- Add indexes based on your query patterns
CREATE INDEX IF NOT EXISTS idx_{table_name}_geom ON public.{table_name} USING GIST (geom);
-- CREATE INDEX IF NOT EXISTS idx_{table_name}_column ON public.{table_name} (column_name);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_{table_name}_updated_at
  BEFORE UPDATE ON public.{table_name}
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE public.{table_name} IS '{MODEL_DESCRIPTION}';
-- Add column comments as needed
-- COMMENT ON COLUMN public.{table_name}.column_name IS 'Column description';