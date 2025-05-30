import frappe
from frappe import _
from frappe.utils import getdate, now_datetime
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password
from frappe.core.doctype.user.user import User

@frappe.whitelist(allow_guest=True)
def register_patient(first_name, last_name, email, mobile, password):
    """Register a new patient"""
    try:
        # Validate email
        if frappe.db.exists("User", email):
            frappe.throw(_("Email already registered"))
        
        # Create User
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "user_type": "Website User",
            "send_welcome_email": 1
        })
        user.new_password = password
        user.insert()
        
        # Create Patient
        patient = frappe.get_doc({
            "doctype": "Patient",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "mobile": mobile,
            "user": email
        })
        patient.insert()
        
        # Add Patient role
        user.add_roles("Patient")
        
        return {"message": "Registration successful"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Patient Registration Error")
        frappe.throw(str(e))

@frappe.whitelist()
def update_patient_profile(first_name, last_name, email, mobile):
    """Update patient profile"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        patient = frappe.get_doc("Patient", {"user": frappe.session.user})
        patient.first_name = first_name
        patient.last_name = last_name
        patient.email = email
        patient.mobile = mobile
        patient.save()
        
        # Update User
        user = frappe.get_doc("User", frappe.session.user)
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()
        
        return {"message": "Profile updated successfully"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Profile Update Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_doctors_by_department(department):
    """Get doctors by department"""
    try:
        doctors = frappe.get_all("Doctor",
            filters={"department": department, "status": "Active"},
            fields=["name", "first_name", "last_name", "specialization"]
        )
        return doctors
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Doctors Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_doctor_schedule(doctor):
    """Get doctor's schedule"""
    try:
        schedule = frappe.get_all("Doctor Schedule",
            filters={"doctor": doctor, "status": "Active"},
            fields=["name", "schedule_date", "from_time", "to_time"]
        )
        return schedule
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Schedule Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_available_time_slots(doctor, date):
    """Get available time slots for a doctor on a specific date"""
    try:
        # Get doctor's schedule
        schedule = frappe.get_all("Doctor Schedule",
            filters={
                "doctor": doctor,
                "schedule_date": date,
                "status": "Active"
            },
            fields=["name"]
        )
        
        if not schedule:
            return []
        
        # Get booked appointments
        booked_slots = frappe.get_all("Appointment",
            filters={
                "doctor": doctor,
                "appointment_date": date,
                "status": ["in", ["Scheduled", "In Progress"]]
            },
            fields=["appointment_time"]
        )
        booked_times = [slot.appointment_time for slot in booked_slots]
        
        # Get available slots
        available_slots = frappe.get_all("Schedule Time Slot",
            filters={
                "parent": schedule[0].name,
                "appointment_time": ["not in", booked_times]
            },
            fields=["appointment_time"]
        )
        
        return [slot.appointment_time for slot in available_slots]
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Time Slots Error")
        frappe.throw(str(e))

@frappe.whitelist()
def create_appointment(doctor, appointment_date, appointment_time):
    """Create a new appointment"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        patient = frappe.get_doc("Patient", {"user": frappe.session.user})
        
        # Validate time slot availability
        available_slots = get_available_time_slots(doctor, appointment_date)
        if appointment_time not in available_slots:
            frappe.throw(_("Selected time slot is not available"))
        
        # Create appointment
        appointment = frappe.get_doc({
            "doctype": "Appointment",
            "patient": patient.name,
            "doctor": doctor,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "status": "Scheduled"
        })
        appointment.insert()
        
        return {"message": "Appointment created successfully", "appointment": appointment.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Appointment Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_patient_appointments():
    """Get patient's appointments"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        patient = frappe.get_doc("Patient", {"user": frappe.session.user})
        
        appointments = frappe.get_all("Appointment",
            filters={"patient": patient.name},
            fields=["name", "appointment_date", "appointment_time", "doctor", "status"],
            order_by="appointment_date desc"
        )
        
        # Get doctor names
        for appointment in appointments:
            doctor = frappe.get_doc("Doctor", appointment.doctor)
            appointment.doctor_name = f"{doctor.first_name} {doctor.last_name}"
            appointment.department = doctor.department
        
        return appointments
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Appointments Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_patient_medical_records():
    """Get patient's medical records"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        patient = frappe.get_doc("Patient", {"user": frappe.session.user})
        
        records = frappe.get_all("Medical Record",
            filters={"patient": patient.name},
            fields=["name", "date", "doctor", "diagnosis", "treatment_plan"],
            order_by="date desc"
        )
        
        # Get doctor names
        for record in records:
            doctor = frappe.get_doc("Doctor", record.doctor)
            record.doctor_name = f"{doctor.first_name} {doctor.last_name}"
        
        return records
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Medical Records Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_patient_prescriptions():
    """Get patient's prescriptions"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        patient = frappe.get_doc("Patient", {"user": frappe.session.user})
        
        prescriptions = frappe.get_all("Prescription",
            filters={"patient": patient.name},
            fields=["name", "date", "doctor", "medications", "duration"],
            order_by="date desc"
        )
        
        # Get doctor names
        for prescription in prescriptions:
            doctor = frappe.get_doc("Doctor", prescription.doctor)
            prescription.doctor_name = f"{doctor.first_name} {doctor.last_name}"
        
        return prescriptions
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Prescriptions Error")
        frappe.throw(str(e))

@frappe.whitelist()
def upload_document(file_name, file_content, doctype, docname):
    """Upload a document"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        # Check if document upload is allowed
        settings = frappe.get_doc("Patient Portal Settings")
        if not settings.enable_document_upload:
            frappe.throw(_("Document upload is not enabled"))
        
        # Create File document
        file = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "file_content": file_content,
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_private": 1
        })
        file.insert()
        
        return {"message": "Document uploaded successfully", "file": file.name}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Document Upload Error")
        frappe.throw(str(e))

@frappe.whitelist()
def get_patient_documents():
    """Get patient's documents"""
    try:
        if not frappe.session.user:
            frappe.throw(_("Not logged in"))
        
        patient = frappe.get_doc("Patient", {"user": frappe.session.user})
        
        files = frappe.get_all("File",
            filters={
                "attached_to_doctype": "Patient",
                "attached_to_name": patient.name
            },
            fields=["name", "file_name", "creation", "file_url"]
        )
        
        return files
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Documents Error")
        frappe.throw(str(e)) 