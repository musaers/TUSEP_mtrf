-- TÜSEP Healthcare Equipment Maintenance System
-- PostgreSQL Database Schema

-- Drop tables if exist (dikkatli kullan!)
DROP TABLE IF EXISTS logs CASCADE;
DROP TABLE IF EXISTS equipment_transfers CASCADE;
DROP TABLE IF EXISTS fault_records CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users Table
CREATE TABLE users (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('health_staff', 'technician', 'manager', 'quality')),
    successful_repairs INTEGER DEFAULT 0,
    failed_repairs INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Devices Table
CREATE TABLE devices (
    id VARCHAR(50) PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    total_failures INTEGER DEFAULT 0,
    total_operating_hours DECIMAL(10, 2) DEFAULT 0.0,
    total_repair_hours DECIMAL(10, 2) DEFAULT 0.0,
    mtbf DECIMAL(10, 2) DEFAULT 0.0,
    mttr DECIMAL(10, 2) DEFAULT 0.0,
    availability DECIMAL(5, 2) DEFAULT 100.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Excel'den gelen ekstra alanlar
    kat VARCHAR(50),
    demirbas_adi VARCHAR(255),
    marka VARCHAR(255),
    model VARCHAR(255),
    seri_no VARCHAR(255),
    adet INTEGER DEFAULT 1,
    ariza_adeti INTEGER DEFAULT 0,
    ortalama_yil_sure VARCHAR(50)
);

-- Fault Records Table
CREATE TABLE fault_records (
    id VARCHAR(50) PRIMARY KEY,
    created_by VARCHAR(50) NOT NULL REFERENCES users(id),
    created_by_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    device_id VARCHAR(50) NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    device_code VARCHAR(100),
    device_type VARCHAR(255),
    description TEXT NOT NULL,
    assigned_to VARCHAR(50) REFERENCES users(id),
    assigned_to_name VARCHAR(255),
    repair_start TIMESTAMP WITH TIME ZONE,
    repair_end TIMESTAMP WITH TIME ZONE,
    repair_duration DECIMAL(10, 2) DEFAULT 0.0,
    repair_notes TEXT,
    repair_category VARCHAR(50) CHECK (repair_category IN ('part_replacement', 'adjustment', 'complete_repair', 'other')),
    breakdown_iteration INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'closed')),
    confirmed_by VARCHAR(50) REFERENCES users(id),
    confirmed_at TIMESTAMP WITH TIME ZONE
);

-- Equipment Transfers Table
CREATE TABLE equipment_transfers (
    id VARCHAR(50) PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    device_code VARCHAR(100),
    device_type VARCHAR(255),
    from_location VARCHAR(255) NOT NULL,
    to_location VARCHAR(255) NOT NULL,
    requested_by VARCHAR(50) NOT NULL REFERENCES users(id),
    requested_by_name VARCHAR(255),
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'completed')),
    approved_by VARCHAR(50) REFERENCES users(id),
    approved_by_name VARCHAR(255),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Logs Table
CREATE TABLE logs (
    id VARCHAR(50) PRIMARY KEY,
    record_id VARCHAR(50),
    event TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(50) REFERENCES users(id),
    user_name VARCHAR(255)
);

-- Create Indexes for Performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE INDEX idx_devices_code ON devices(code);
CREATE INDEX idx_devices_location ON devices(location);
CREATE INDEX idx_devices_type ON devices(type);

CREATE INDEX idx_fault_records_device ON fault_records(device_id);
CREATE INDEX idx_fault_records_status ON fault_records(status);
CREATE INDEX idx_fault_records_created_by ON fault_records(created_by);
CREATE INDEX idx_fault_records_assigned_to ON fault_records(assigned_to);
CREATE INDEX idx_fault_records_created_at ON fault_records(created_at);

CREATE INDEX idx_transfers_device ON equipment_transfers(device_id);
CREATE INDEX idx_transfers_status ON equipment_transfers(status);
CREATE INDEX idx_transfers_requested_at ON equipment_transfers(requested_at);

CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_record_id ON logs(record_id);

-- Insert Demo Users
INSERT INTO users (id, name, email, password, role, successful_repairs, failed_repairs) VALUES
('user-1', 'Dr. Ayşe Yılmaz', 'ayse@hastane.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo2IQ6RYqQ6W', 'health_staff', 0, 0),
('user-2', 'Mehmet Kaya', 'mehmet@hastane.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo2IQ6RYqQ6W', 'technician', 15, 2),
('user-3', 'Ali Demir', 'ali@hastane.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo2IQ6RYqQ6W', 'technician', 12, 1),
('user-4', 'Fatma Şahin', 'fatma@hastane.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo2IQ6RYqQ6W', 'manager', 0, 0),
('user-5', 'Zeynep Arslan', 'zeynep@hastane.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5oo2IQ6RYqQ6W', 'quality', 0, 0);

-- Password for all: 12345

COMMIT;
