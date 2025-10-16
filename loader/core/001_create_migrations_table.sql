-- Migration: Create migrations tracking table
-- This table tracks which migrations have been applied to the database
-- Must be run before any other migrations

CREATE TABLE IF NOT EXISTS public.migrations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    model VARCHAR(255) NOT NULL,
    migration VARCHAR(255) NOT NULL,
    UNIQUE(model, migration)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_migrations_model ON public.migrations (model);
CREATE INDEX IF NOT EXISTS idx_migrations_migration ON public.migrations (migration);

-- Add comment for documentation
COMMENT ON TABLE public.migrations IS 'Tracks applied database migrations by model and migration name';