-- LibreTime Legacy Test Database Initialization
-- Minimal schema for PHPUnit testing

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create test user with proper permissions (already created by docker, but grant extra permissions)
GRANT ALL PRIVILEGES ON DATABASE airtimeunittests TO libretime;

-- Note: Actual tables are created by Propel during test bootstrap
-- via TestHelper::installTestDatabase() which calls AirtimeInstall methods
