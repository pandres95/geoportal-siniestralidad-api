-- Rollback: Drop schools table
-- This script undoes the changes made by 001_create_schools_table.sql

-- Drop the trigger first
DROP TRIGGER IF EXISTS update_schools_updated_at ON public.schools;

-- Drop the function if no other tables use it
-- (This function might be shared across multiple tables, so check before dropping)
-- DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_schools_geom;

-- Drop the table
DROP TABLE IF EXISTS public.schools;