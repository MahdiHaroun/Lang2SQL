-- Create extensions that might be needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the database schema that matches your SQLAlchemy models
-- This file will be executed when the PostgreSQL container starts for the first time

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    number_of_connections INTEGER DEFAULT 0 NOT NULL
);

-- Create database connection details table
CREATE TABLE IF NOT EXISTS db_connection_details (
    id SERIAL PRIMARY KEY,
    db_type VARCHAR NOT NULL,
    host VARCHAR NOT NULL,
    port INTEGER NOT NULL,
    database_name VARCHAR NOT NULL,
    username VARCHAR NOT NULL,
    db_password VARCHAR NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_db_connections_owner_id ON db_connection_details(owner_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);

-- Insert some default/demo data (optional)
-- Uncomment and modify as needed for your application

-- Default admin user (password is hashed 'admin123' - change in production!)
-- INSERT INTO users (name, email, password, number_of_connections) 
-- VALUES ('Admin User', 'admin@sqlagent.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYYi6hspcDB7rbW', 0)
-- ON CONFLICT (email) DO NOTHING;

-- You can add more default data here as needed