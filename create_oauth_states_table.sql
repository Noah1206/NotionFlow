-- Create oauth_states table if it doesn't exist
CREATE TABLE IF NOT EXISTS oauth_states (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    state VARCHAR(255) NOT NULL UNIQUE,
    code_verifier VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(state, provider)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_oauth_states_user_provider ON oauth_states(user_id, provider);

-- Clean up expired states (optional)
DELETE FROM oauth_states WHERE expires_at < NOW();