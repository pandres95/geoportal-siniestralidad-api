-- Migration Rollback: Drop {MODEL_NAME} table
-- This migration removes the {table_name} table and related objects
--
-- SEARCH AND REPLACE:
-- - Replace {MODEL_NAME} with your model name (e.g., Schools)
-- - Replace {TABLE_NAME} with your database table name (e.g., schools)

-- Check if migration was applied before attempting rollback
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.migrations
        WHERE model = '{model_name}' AND migration = '001_create_{table_name}_table'
    ) THEN

        -- Drop the table and related objects
        DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON public.{table_name};
        DROP TABLE IF EXISTS public.{table_name};

        -- Remove migration record
        DELETE FROM public.migrations
        WHERE model = '{model_name}' AND migration = '001_create_{table_name}_table';

        RAISE NOTICE 'Successfully rolled back migration 001_create_{table_name}_table for model {model_name}';

    ELSE
        RAISE NOTICE 'Migration 001_create_{table_name}_table for model {model_name} not found in migrations table, skipping rollback...';
    END IF;
END $$;