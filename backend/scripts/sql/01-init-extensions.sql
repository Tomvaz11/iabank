-- Initialize PostgreSQL extensions for IABANK multi-tenant setup
-- This script runs automatically when the PostgreSQL container starts

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create extension for case-insensitive text
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create indexes for performance
-- These will be created by Django migrations but we prepare the environment