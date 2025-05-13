from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_db_connection():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND role = ?', 
                            (username, role)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            if role == 'doctor':
                return redirect('/doctor')
            elif role == 'patient':
                return redirect('/patient')
            elif role == 'admin':
                return redirect('/admin')
        else:
            flash("Invalid credentials")

    return render_template('login.html')

@app.route('/doctor', methods=['GET', 'POST'])
def doctor_dashboard():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/')

    conn = get_db_connection()
    doctor = conn.execute('SELECT * FROM doctors WHERE user_id = ?', (session['user_id'],)).fetchone()
    patients = conn.execute('SELECT * FROM patients WHERE assigned_doctor_id = ?', (doctor['id'],)).fetchall()

    if request.method == 'POST':
        patient_id = request.form['patient_id']
        description = request.form['description']
        conn.execute('INSERT INTO medical_records (patient_id, doctor_id, description, date) VALUES (?, ?, ?, DATE("now"))',
                     (patient_id, doctor['id'], description))
        conn.commit()
        flash('Description saved!')

    conn.close()
    return render_template('doctor.html', doctor=doctor, patients=patients)

@app.route('/patient')
def patient_dashboard():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/')

    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE user_id = ?', (session['user_id'],)).fetchone()
    records = conn.execute('''
        SELECT doctors.name AS doctor_name, medical_records.description, medical_records.date
        FROM medical_records
        JOIN doctors ON doctors.id = medical_records.doctor_id
        WHERE medical_records.patient_id = ?
    ''', (patient['id'],)).fetchall()
    conn.close()
    return render_template('patient.html', patient=patient, records=records)

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/')

    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients').fetchall()
    doctors = conn.execute('SELECT * FROM doctors').fetchall()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_user':
            username = request.form['username']
            password = request.form['password']
            role = request.form['role']
            name = request.form['name']
            extra = request.form.get('extra')
            assigned_doctor = request.form.get('assigned_doctor')
            gender = request.form.get('gender', 'Not specified')

            hashed_password = generate_password_hash(password)

            try:
                # Insert into users
                conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                             (username, hashed_password, role))
                user_id = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()['id']

                # Insert into respective table
                if role == 'doctor':
                    conn.execute('INSERT INTO doctors (user_id, name, specialization) VALUES (?, ?, ?)',
                                 (user_id, name, extra))
                elif role == 'patient':
                    conn.execute('INSERT INTO patients (user_id, name, age, gender, assigned_doctor_id) VALUES (?, ?, ?, ?, ?)',
                                 (user_id, name, extra, gender, assigned_doctor))

                conn.commit()
                flash(f"{role.capitalize()} user added!")
            except Exception as e:
                conn.rollback()
                flash(f"Error: {e}")

        elif action == 'pay_bill':
            patient_id = request.form['patient_id']
            amount = request.form['amount']
            conn.execute('INSERT INTO bills (patient_id, amount, status) VALUES (?, ?, ?)',
                         (patient_id, amount, 'Paid'))
            conn.commit()
            flash('Bill payment recorded!')

    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('admin.html', patients=patients, users=users, doctors=doctors)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def create_admin_user():
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = 'admin' AND role = 'admin'").fetchone()
    if not user:
        hashed_password = generate_password_hash('admin123')
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                     ('admin', hashed_password, 'admin'))
        conn.commit()
        print("Default admin user created: admin / admin123")
    conn.close()

create_admin_user()

if __name__ == '__main__':
    app.run(debug=True)
