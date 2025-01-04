from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flashing messages and session management

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:anand$2005@localhost/hospital_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize MySQL connection for executing raw queries (e.g., search)
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="anand$2005",
    database="hospital_management"
)
cursor = connection.cursor(dictionary=True)

# Models
class Patient(db.Model):
    __tablename__ = 'patients1'  # Updated table name to 'patients1'
    patient_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10))
    contact_info = db.Column(db.String(255), unique=True)  # Assuming contact_info is the mobile number
    address = db.Column(db.Text)
    disease = db.Column(db.String(255))
    surgery = db.Column(db.String(255))
    medicines = db.Column(db.Text)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients1.patient_id'), nullable=False)
    doctor_name = db.Column(db.String(255), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    reason_for_visit = db.Column(db.Text)

    patient = db.relationship('Patient', backref=db.backref('appointments', lazy=True))

# Create tables before the first request
@app.before_request
def create_tables():
    db.create_all()

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Example validation (replace with actual validation)
        if email == 'admin@example.com' and password == 'admin_password':
            session['logged_in'] = True
            return redirect(url_for('admin_homepage'))
        else:
            flash('Invalid credentials, please try again.', 'danger')

    return render_template('login.html')

@app.route('/admin')
def admin_homepage():
    if 'logged_in' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    # Fetch total patients count from the database
    total_patients = Patient.query.count()

    # Fetch total appointments count from the database
    total_appointments = Appointment.query.count()

    # Fetch patient details
    patients = Patient.query.all()

    return render_template('adminhomepage.html', total_patients=total_patients, 
                           total_appointments=total_appointments, patients=patients)


@app.route('/search', methods=['POST'])
def search():
    name = request.form.get('name')  # Get the name from the form
    contact_info = request.form.get('contact_info')  # Get the mobile number from the form

    # Construct the search query based on available inputs
    query = "SELECT * FROM patients1 WHERE 1=1"  # Base query for patient search
    params = []

    if name:
        query += " AND name LIKE %s"
        params.append(f"%{name}%")
    if contact_info:
        query += " AND contact_info LIKE %s"
        params.append(f"%{contact_info}%")

    if not params:
        flash('Please enter either a name or contact number to search.', 'danger')
        return redirect(url_for('admin_homepage'))

    cursor.execute(query, tuple(params))
    results = cursor.fetchall()

    if results:
        # If there's only one result, redirect to the patient details page
        if len(results) == 1:
            patient_id = results[0]['patient_id']
            return redirect(url_for('patient_details', patient_id=patient_id))
        else:
            # If multiple results are found, pass them to the adminhomepage.html for display
            return render_template('adminhomepage.html', results=results)
    else:
        flash('No patient found with the given details.', 'danger')
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
    app.run(debug=True)
