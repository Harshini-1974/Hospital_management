import sqlite3
from werkzeug.security import generate_password_hash

# Connect to SQLite database
conn = sqlite3.connect('hospital.db')
c = conn.cursor()

# Drop and recreate tables
c.execute('DROP TABLE IF EXISTS patients')
c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS doctors')
c.execute('DROP TABLE IF EXISTS medical_records')
c.execute('DROP TABLE IF EXISTS bills')

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    specialization TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT NOT NULL,
    age INTEGER,
    gender TEXT NOT NULL,
    assigned_doctor_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (assigned_doctor_id) REFERENCES doctors(id)
)''')

c.execute('''
CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    doctor_id INTEGER,
    description TEXT,
    date TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
)''')

# Generate hashed passwords
hashed_admin_pw = generate_password_hash('admin123')
hashed_doctor_pw = generate_password_hash('pass123')
hashed_patient_pw = generate_password_hash('1234')

# Insert users with hashed passwords
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', hashed_admin_pw, 'admin'))
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('drsmith', hashed_doctor_pw, 'doctor'))
c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('john_doe', hashed_patient_pw, 'patient'))

# Link doctor
c.execute("INSERT INTO doctors (user_id, name, specialization) VALUES (2, 'Dr. Smith', 'Cardiology')")

# Link patient to doctor
c.execute("INSERT INTO patients (user_id, name, age, gender, assigned_doctor_id) VALUES (3, 'John Doe', 30, 'Male', 1)")

# Commit changes and close
conn.commit()
conn.close()

print("Database initialized successfully with hashed passwords.")
