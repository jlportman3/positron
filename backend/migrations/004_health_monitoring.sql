-- Health monitoring migration
-- Add health fields to devices table
ALTER TABLE devices ADD COLUMN IF NOT EXISTS health_score INTEGER DEFAULT 100;
ALTER TABLE devices ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) DEFAULT 'healthy';
ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_health_check TIMESTAMP;

-- Create sync_attempts table
CREATE TABLE IF NOT EXISTS sync_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    operation VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    duration_ms INTEGER NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sync_attempts_device_id ON sync_attempts(device_id);
CREATE INDEX IF NOT EXISTS idx_sync_attempts_timestamp ON sync_attempts(timestamp DESC);

-- Create device_health_history table
CREATE TABLE IF NOT EXISTS device_health_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    health_score INTEGER NOT NULL,
    sync_success_rate FLOAT NOT NULL,
    avg_response_ms INTEGER NOT NULL,
    alarm_count INTEGER NOT NULL,
    uptime_seconds INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_history_device_id ON device_health_history(device_id);
CREATE INDEX IF NOT EXISTS idx_health_history_timestamp ON device_health_history(timestamp DESC);
