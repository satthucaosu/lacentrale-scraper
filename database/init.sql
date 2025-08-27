-- LaCentrale Database Initialization Script
-- This script will be executed when PostgreSQL container starts

-- Create database if it doesn't exist (already created by POSTGRES_DB)
-- CREATE DATABASE IF NOT EXISTS lacentrale_db;

-- Connect to the lacentrale_db database
\c lacentrale_db;

-- Create extensions for better performance
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create custom functions for better JSON handling
CREATE OR REPLACE FUNCTION safe_json_extract_text(json_data jsonb, key_path text)
RETURNS text AS $$
BEGIN
    RETURN json_data #>> string_to_array(key_path, '.');
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create index types for better performance
-- (Tables will be created by SQLAlchemy)

-- Set up some performance optimizations
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Note: These settings require a restart to take effect
-- Docker will handle this automatically on container creation

-- Create a user for read-only access (optional)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN
        CREATE ROLE readonly_user LOGIN PASSWORD 'readonly_password';
    END IF;
END
$$;

-- Grant read permissions to readonly user (after tables are created)
-- This will be done by the application after schema creation

-- Log successful initialization
INSERT INTO pg_stat_statements_reset();

-- Display some useful information
SELECT 'LaCentrale Database initialized successfully!' as status,
       current_database() as database_name,
       current_user as current_user,
       version() as postgresql_version;
