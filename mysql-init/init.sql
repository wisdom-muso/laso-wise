-- Initialize the Laso Medical Database
CREATE DATABASE IF NOT EXISTS laso_medical;

-- Create user if not exists
CREATE USER IF NOT EXISTS 'laso_user'@'%' IDENTIFIED BY 'laso_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON laso_medical.* TO 'laso_user'@'%';

-- Refresh privileges
FLUSH PRIVILEGES;

-- Use the database
USE laso_medical;