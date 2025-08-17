-- Initialize the Laso Medical Database
-- The database is already created by the POSTGRES_DB environment variable

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Grant privileges (user is already created via POSTGRES_USER)
-- Additional setup can be done here if needed