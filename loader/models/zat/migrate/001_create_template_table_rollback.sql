-- Migration Rollback: Drop ZAT table
-- This migration removes the zat table and related objects

-- Check if migration was applied before attempting rollback
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.migrations
        WHERE model = 'zat' AND migration = '001_create_zat_table'
    ) THEN

        -- Drop the table and related objects
        DROP TRIGGER IF EXISTS update_zat_updated_at ON public.zat;
        DROP TABLE IF EXISTS public.zat;

        -- Remove migration record
        DELETE FROM public.migrations
        WHERE model = 'zat' AND migration = '001_create_zat_table';

        RAISE NOTICE 'Successfully rolled back migration 001_create_zat_table for model zat';

    ELSE
        RAISE NOTICE 'Migration 001_create_zat_table for model zat not found in migrations table, skipping rollback...';
    END IF;
END $$;