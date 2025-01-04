CREATE DATABASE hospital_management;

USE hospital_management;

CREATE TABLE patients1 (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10),
    contact_info VARCHAR(255) UNIQUE NOT NULL,
    address TEXT,
    disease VARCHAR(255),
    surgery VARCHAR(255),
    medicines TEXT
);

CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    doctor_name VARCHAR(255) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason_for_visit TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients1(patient_id) ON DELETE CASCADE
);
