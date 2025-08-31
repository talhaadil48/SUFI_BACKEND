-- =========================
-- USERS
-- =========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    permissions JSONB DEFAULT '{}'::jsonb,
    role VARCHAR(50) CHECK (role IN ('writer', 'vocalist', 'admin')),
    country VARCHAR(100),
    city VARCHAR(100),
    is_registered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    otp VARCHAR(6),
    otp_expiry TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_country_city ON users(country, city);
CREATE INDEX idx_users_created_at ON users(created_at);

-- =========================
-- VOCALISTS
-- =========================
CREATE TABLE vocalists (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    vocal_range VARCHAR(100),
    languages TEXT[],
    sample_title VARCHAR(255),
    audio_sample_url TEXT,
    sample_description TEXT,
    experience_background TEXT,
    portfolio TEXT,
    availability TEXT,
    status VARCHAR(50) CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_vocalists_user_id ON vocalists(user_id);
CREATE INDEX idx_vocalists_status ON vocalists(status);
CREATE INDEX idx_vocalists_created_at ON vocalists(created_at);

-- =========================
-- KALAM CONTENT
-- =========================
CREATE TABLE kalam_content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    language VARCHAR(100),
    theme VARCHAR(255),
    kalam_text TEXT,
    description TEXT,
    sufi_influence VARCHAR(255),
    musical_preference VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_kalam_content_language ON kalam_content(language);
CREATE INDEX idx_kalam_content_theme ON kalam_content(theme);
CREATE INDEX idx_kalam_content_created_at ON kalam_content(created_at);

-- =========================
-- KALAM SUBMISSIONS
-- =========================
CREATE TABLE kalam_submissions (
    id SERIAL PRIMARY KEY,
    content_id INT REFERENCES kalam_content(id) ON DELETE CASCADE,
    writer_id INT REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) CHECK (
        status IN (
            'draft',
            'submitted',
            'under_review',
            'changes_requested',
            'approved',
            'rejected'
        )
    ) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_kalam_submissions_content_id ON kalam_submissions(content_id);
CREATE INDEX idx_kalam_submissions_writer_id ON kalam_submissions(writer_id);
CREATE INDEX idx_kalam_submissions_status ON kalam_submissions(status);
CREATE INDEX idx_kalam_submissions_created_at ON kalam_submissions(created_at);

-- =========================
-- KALAM REVISIONS
-- =========================
CREATE TABLE kalam_revisions (
    id SERIAL PRIMARY KEY,
    content_id INT REFERENCES kalam_content(id) ON DELETE CASCADE,
    submission_id INT REFERENCES kalam_submissions(id) ON DELETE CASCADE,
    editor_id INT REFERENCES users(id) ON DELETE SET NULL,
    revised_text TEXT,
    comment TEXT,
    status VARCHAR(50) CHECK (
        status IN (
            'pending_writer_review',
            'pending_admin_review',
            'accepted',
            'rejected'
        )
    ) DEFAULT 'pending_writer_review',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_kalam_revisions_content_id ON kalam_revisions(content_id);
CREATE INDEX idx_kalam_revisions_submission_id ON kalam_revisions(submission_id);
CREATE INDEX idx_kalam_revisions_status ON kalam_revisions(status);

-- =========================
-- FINALIZED KALAMS
-- =========================
CREATE TABLE kalams (
    id SERIAL PRIMARY KEY,
    content_id INT UNIQUE REFERENCES kalam_content(id) ON DELETE CASCADE,
    submission_id INT UNIQUE REFERENCES kalam_submissions(id) ON DELETE SET NULL,
    writer_id INT REFERENCES users(id) ON DELETE SET NULL,
    vocalist_id INT REFERENCES vocalists(id) ON DELETE SET NULL,
    youtube_link TEXT,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_kalams_content_id ON kalams(content_id);
CREATE INDEX idx_kalams_vocalist_id ON kalams(vocalist_id);
CREATE INDEX idx_kalams_writer_id ON kalams(writer_id);
CREATE INDEX idx_kalams_published_at ON kalams(published_at);

-- =========================
-- STUDIO VISIT REQUESTS
-- =========================
CREATE TABLE studio_visit_requests (
    id SERIAL PRIMARY KEY,
    vocalist_id INT REFERENCES vocalists(id) ON DELETE CASCADE,
    kalam_id INT REFERENCES kalams(id) ON DELETE CASCADE,
    name VARCHAR(255),
    email VARCHAR(255),
    organization VARCHAR(255),
    contact_number VARCHAR(50),
    preferred_date DATE,
    preferred_time VARCHAR(50),
    purpose TEXT,
    number_of_visitors INT,
    additional_details TEXT,
    special_requests TEXT,
    status VARCHAR(50) CHECK (status IN ('pending', 'approved', 'rejected', 'completed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_studio_visit_vocalist_id ON studio_visit_requests(vocalist_id);
CREATE INDEX idx_studio_visit_kalam_id ON studio_visit_requests(kalam_id);
CREATE INDEX idx_studio_visit_status ON studio_visit_requests(status);
CREATE INDEX idx_studio_visit_created_at ON studio_visit_requests(created_at);

-- =========================
-- REMOTE RECORDING REQUESTS
-- =========================
CREATE TABLE remote_recording_requests (
    id SERIAL PRIMARY KEY,
    vocalist_id INT REFERENCES vocalists(id) ON DELETE CASCADE,
    kalam_id INT REFERENCES kalams(id) ON DELETE CASCADE,
    name VARCHAR(255),
    email VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    time_zone VARCHAR(100),
    role VARCHAR(100),
    project_type VARCHAR(100),
    recording_equipment TEXT,
    internet_speed VARCHAR(100),
    preferred_software VARCHAR(100),
    availability TEXT,
    recording_experience TEXT,
    technical_setup TEXT,
    additional_details TEXT,
    status VARCHAR(50) CHECK (status IN ('pending', 'approved', 'rejected', 'completed')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommended Indexes
CREATE INDEX idx_remote_recording_vocalist_id ON remote_recording_requests(vocalist_id);
CREATE INDEX idx_remote_recording_kalam_id ON remote_recording_requests(kalam_id);
CREATE INDEX idx_remote_recording_status ON remote_recording_requests(status);
CREATE INDEX idx_remote_recording_created_at ON remote_recording_requests(created_at);
