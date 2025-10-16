-- Rollback: Drop victims table and restore original structure
-- WARNING: This will delete all data in the victims table!

-- Drop the victims table first (use CASCADE to remove dependent objects like triggers and functions)
DROP TABLE IF EXISTS public.victims CASCADE;