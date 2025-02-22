from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database initialization function
def init_db():
    try:
        # First try to create the database
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="anand$2005"
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS it")
            print("Database 'it' created or already exists!")
            
            # Close cursor and connection properly
            cursor.close()
            connection.close()
            print("MySQL connection is closed")
            
            return True
            
    except Error as e:
        print(f"Error creating database: {e}")
        return False

# Initialize database
if not init_db():
    print("Failed to initialize database. Please check MySQL connection.")
    exit(1)

# Configure SQLAlchemy with the 'it' database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:anand$2005@localhost/it'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10))
    contact_info = db.Column(db.String(255), unique=True)
    address = db.Column(db.Text)
    disease = db.Column(db.String(255))
    surgery = db.Column(db.String(255))
    medicines = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id', ondelete='CASCADE'), nullable=False)
    doctor_name = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    reason_for_visit = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True, cascade='all, delete-orphan'))

def init_tables():
    try:
        with app.app_context():
            db.create_all()
            print("Tables created successfully!")
            return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if email == 'admin@example.com' and password == 'admin_password':
            session['logged_in'] = True
            flash('Login successful!', 'success')
            return redirect(url_for('admin_homepage'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/admin')
def admin_homepage():
    try:
        total_patients = Patient.query.count()
        total_appointments = Appointment.query.count()
        return render_template('adminhomepage.html', 
                             total_patients=total_patients,
                             total_appointments=total_appointments,
                             results=None)
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return render_template('adminhomepage.html', 
                             total_patients=0,
                             total_appointments=0,
                             results=None)

@app.route('/search', methods=['POST'])
def search():
    try:
        name = request.form.get('name', '')
        contact_info = request.form.get('contact_info', '')
        
        # Use SQLAlchemy query instead of raw MySQL
        query = Patient.query
        
        if name:
            query = query.filter(Patient.name.like(f'%{name}%'))
        if contact_info:
            query = query.filter(Patient.contact_info.like(f'%{contact_info}%'))
            
        results = query.all()
        
        if not results:
            flash('No patients found matching your search criteria.', 'warning')
        
        return render_template('adminhomepage.html', 
                             results=results,
                             total_patients=Patient.query.count(),
                             total_appointments=Appointment.query.count())
                             
    except Exception as e:
        print(f"Search error: {e}")
        flash('An error occurred while searching. Please try again.', 'danger')
        return redirect(url_for('admin_homepage'))

@app.route('/details/<int:patient_id>')
def patient_details(patient_id):
    patient = Patient.query.get(patient_id)  # Fetch the patient by ID from the database
    if patient:
        return render_template('patient_details.html', patient=patient)
    else:
        flash('Patient not found.', 'danger')
        return redirect(url_for('admin_homepage'))

@app.route('/view_patients')
def view_patients():
    # Fetch the list of patients
    patients = Patient.query.all()  # Assuming you're using SQLAlchemy
    return render_template('view_patients.html', patients=patients)

@app.route('/dashboard')
def dashboard():
    # Fetch the total number of patients and appointments
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()

    # If you need a specific patient (example: first patient)
    patient = Patient.query.first()  # Or fetch based on criteria

    # Render the admin dashboard page
    return render_template('adminhomepage.html', 
                           total_patients=total_patients, 
                           total_appointments=total_appointments, 
                           patient=patient)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        # Patient details from the form
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact_info = request.form['contact_info']
        address = request.form['address']

        # Medical history details from the form
        disease = request.form.get('disease', 'N/A')
        surgery = request.form.get('surgery', 'N/A')
        medicines = request.form.get('medicines', 'N/A')

        # Create new patient instance
        new_patient = Patient(name=name, age=age, gender=gender, contact_info=contact_info, address=address,
                              disease=disease, surgery=surgery, medicines=medicines)
        db.session.add(new_patient)
        db.session.commit()  # Commit to save the patient to the database

        flash('Patient added successfully!', 'success')
        return redirect(url_for('admin_homepage'))

    return render_template('add_patient.html')

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    # Query the patient by ID
    patient = db.session.query(Patient).filter_by(patient_id=patient_id).first()

    if request.method == 'POST':
        # Update basic details
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.contact_info = request.form['contact_info']
        patient.address = request.form['address']

        # Update medical history
        patient.disease = request.form['disease']
        patient.surgery = request.form['surgery']
        patient.medicines = request.form['medicines']

        # Commit the changes to the database
        db.session.commit()

        # Redirect to the patient details page after the update
        return redirect(url_for('patient_details', patient_id=patient.patient_id))

    return render_template('edit_details.html', patient=patient)

@app.route('/add_appointment/<int:patient_id>', methods=['GET', 'POST'])
def add_appointment(patient_id):
    if request.method == 'POST':
        doctor_name = request.form['doctor_name']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        reason_for_visit = request.form['reason_for_visit']

        # Create a new appointment instance
        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_name=doctor_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason_for_visit=reason_for_visit
        )

        # Add the appointment to the database
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment added successfully!', 'success')
        return redirect(url_for('patient_details', patient_id=patient_id))

    return render_template('add_appointment.html', patient_id=patient_id)

@app.route('/view_appointments', defaults={'patient_id': None})
@app.route('/view_appointments/<int:patient_id>')
def view_appointments(patient_id):
    if patient_id:
        # Show appointments for a specific patient
        patient = Patient.query.get_or_404(patient_id)
        appointments = Appointment.query.filter_by(patient_id=patient_id).all()
        
        if not appointments:
            flash('No appointments found for this patient.', 'danger')

        return render_template('view_appointments.html', appointments=appointments, patient=patient)
    else:
        # Show appointments for all patients if no patient_id is provided
        appointments = Appointment.query.all()
        
        if not appointments:
            flash('No appointments found.', 'danger')
        
        return render_template('view_appointments.html', appointments=appointments)

@app.route('/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    # Find the patient by their ID
    patient = db.session.query(Patient).filter_by(patient_id=patient_id).first()

    if patient:
        # Delete the patient record from the database
        db.session.delete(patient)
        db.session.commit()

    # Redirect back to the patient list or dashboard after deletion
    return redirect(url_for('admin_homepage'))  # Or any page you prefer after deletion

@app.route('/logout')
def logout():
    session.pop('logged_in', None)  # Remove the session variable
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Initialize tables before running the app
    if not init_tables():
        print("Failed to create tables. Please check database connection.")
        exit(1)
    
    app.run(debug=True)
