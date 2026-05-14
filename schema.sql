CREATE DATABASE IF NOT EXISTS nyakabanda_youth_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nyakabanda_youth_system;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    active TINYINT(1) NOT NULL DEFAULT 1,
    reset_token VARCHAR(120),
    reset_expires DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS youth_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    gender ENUM('Female', 'Male', 'Other') NOT NULL,
    age INT NOT NULL,
    phone VARCHAR(40),
    email VARCHAR(120),
    address VARCHAR(255),
    education_level VARCHAR(120),
    skills TEXT,
    employment_status VARCHAR(120),
    profile_photo VARCHAR(255),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    location VARCHAR(160),
    image_path VARCHAR(255),
    starts_at DATETIME NOT NULL,
    ends_at DATETIME,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS event_attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    youth_member_id INT NOT NULL,
    status ENUM('registered', 'attended', 'absent') NOT NULL DEFAULT 'registered',
    checked_at TIMESTAMP NULL,
    UNIQUE KEY unique_event_member (event_id, youth_member_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (youth_member_id) REFERENCES youth_members(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(160) NOT NULL,
    description TEXT,
    status ENUM('planned', 'active', 'completed', 'paused') NOT NULL DEFAULT 'planned',
    progress INT NOT NULL DEFAULT 0,
    file_path VARCHAR(255),
    image_path VARCHAR(255),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS announcements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    body TEXT NOT NULL,
    priority ENUM('normal', 'important', 'urgent') NOT NULL DEFAULT 'normal',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120),
    subject VARCHAR(160) NOT NULL,
    message TEXT NOT NULL,
    category ENUM('contact', 'feedback') NOT NULL DEFAULT 'feedback',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    report_type VARCHAR(80) NOT NULL,
    file_path VARCHAR(255),
    generated_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(id) ON DELETE SET NULL
);
