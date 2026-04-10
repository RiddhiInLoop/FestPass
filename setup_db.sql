-- Schema definitions are now handled dynamically by event_backend.py's init_db()
-- The following statements are kept as comments for reference:

-- CREATE DATABASE IF NOT EXISTS festpass_db;
-- USE festpass_db;

-- CREATE TABLE IF NOT EXISTS tickets (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     ticket_id VARCHAR(8) UNIQUE NOT NULL,
--     name VARCHAR(255) NOT NULL,
--     dept VARCHAR(255) NOT NULL,
--     event VARCHAR(255) NOT NULL,
--     seat VARCHAR(255) UNIQUE NOT NULL,
--     email VARCHAR(255),
--     scanned TINYINT(1) DEFAULT 0,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     scanned_at DATETIME DEFAULT NULL
-- );

-- CREATE INDEX idx_event ON tickets (event);
-- CREATE INDEX idx_scanned ON tickets (scanned);

-- Example Admin Queries:
-- 1. View all generated tickets
-- SELECT * FROM tickets ORDER BY created_at DESC;

-- 2. View only scanned (used) tickets
-- SELECT * FROM tickets WHERE scanned = 1;

-- 3. Search for a specific user's ticket by name
-- SELECT * FROM tickets WHERE name LIKE '%John%';

-- 4. Mark a ticket as UN-scanned manually
-- UPDATE tickets SET scanned = 0 WHERE ticket_id = 'ABC123XY';
