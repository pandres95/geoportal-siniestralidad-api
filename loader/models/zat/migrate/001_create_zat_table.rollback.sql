-- Migration Rollback: Drop ZAT table
-- This migration removes the zat table and related objects

-- Drop the table and related objects
DROP TRIGGER IF EXISTS update_zat_updated_at ON public.zat;
DROP TABLE IF EXISTS public.zat;