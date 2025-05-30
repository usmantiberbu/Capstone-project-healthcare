import frappe
import unittest
from frappe.test_runner import make_test_records
from frappe.utils import getdate, add_days, now_datetime

class TestHealthcareAPIs(unittest.TestCase):
    def setUp(self):
        # Create test records
        make_test_records("Patient")
        make_test_records("Doctor")
        make_test_records("Medical Department")
        
        # Create test patient
        self.patient = frappe.get_doc({
            "doctype": "Patient",
            "first_name": "Test",
            "last_name": "Patient",
            "gender": "Male",
            "dob": "1990-01-01",
            "email": "test@example.com",
            "phone": "1234567890"
        }).insert()
        
        # Create test doctor
        self.doctor = frappe.get_doc({
            "doctype": "Doctor",
            "first_name": "Test",
            "last_name": "Doctor",
            "gender": "Male",
            "email": "doctor@example.com",
            "phone": "9876543210",
            "department": "General Medicine",
            "specialization": "General Physician"
        }).insert()
        
        # Create test department
        self.department = frappe.get_doc({
            "doctype": "Medical Department",
            "department_name": "Test Department",
            "description": "Test Department Description"
        }).insert()
    
    def test_patient_apis(self):
        """Test Patient related APIs"""
        # Test get_patient_details
        patient_details = frappe.get_doc("Patient", self.patient.name)
        self.assertEqual(patient_details.first_name, "Test")
        self.assertEqual(patient_details.last_name, "Patient")
        
        # Test get_patient_appointments
        appointments = frappe.get_all("Appointment",
            filters={"patient": self.patient.name},
            fields=["name", "appointment_date", "status"]
        )
        self.assertIsInstance(appointments, list)
    
    def test_doctor_apis(self):
        """Test Doctor related APIs"""
        # Test get_doctor_details
        doctor_details = frappe.get_doc("Doctor", self.doctor.name)
        self.assertEqual(doctor_details.first_name, "Test")
        self.assertEqual(doctor_details.last_name, "Doctor")
        
        # Test get_doctor_schedule
        schedule = frappe.get_all("Doctor Schedule",
            filters={"doctor": self.doctor.name},
            fields=["day", "start_time", "end_time"]
        )
        self.assertIsInstance(schedule, list)
        
        # Test get_doctor_metrics
        metrics = frappe.get_doc("Doctor", self.doctor.name).get_doctor_metrics()
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_appointments", metrics)
        self.assertIn("patients_seen", metrics)
    
    def test_appointment_apis(self):
        """Test Appointment related APIs"""
        # Create test appointment
        appointment = frappe.get_doc({
            "doctype": "Appointment",
            "patient": self.patient.name,
            "doctor": self.doctor.name,
            "appointment_date": getdate(),
            "appointment_time": "10:00:00",
            "appointment_type": "New Visit",
            "status": "Scheduled"
        }).insert()
        
        # Test get_appointment_details
        appointment_details = frappe.get_doc("Appointment", appointment.name)
        self.assertEqual(appointment_details.patient, self.patient.name)
        self.assertEqual(appointment_details.doctor, self.doctor.name)
        
        # Test update_appointment_status
        appointment_details.status = "Completed"
        appointment_details.save()
        self.assertEqual(appointment_details.status, "Completed")
    
    def test_medical_record_apis(self):
        """Test Medical Record related APIs"""
        # Create test medical record
        medical_record = frappe.get_doc({
            "doctype": "Medical Record",
            "patient": self.patient.name,
            "doctor": self.doctor.name,
            "record_type": "Consultation",
            "record_date": getdate(),
            "access_level": "Private"
        }).insert()
        
        # Test get_record_details
        record_details = frappe.get_doc("Medical Record", medical_record.name)
        self.assertEqual(record_details.patient, self.patient.name)
        self.assertEqual(record_details.doctor, self.doctor.name)
        
        # Test add_attachment
        result = medical_record.add_attachment(
            file_name="test.pdf",
            file_url="/files/test.pdf",
            content_type="application/pdf"
        )
        self.assertEqual(result["message"], "Attachment added successfully")
        
        # Test remove_attachment
        result = medical_record.remove_attachment("test.pdf")
        self.assertEqual(result["message"], "Attachment removed successfully")
    
    def test_department_apis(self):
        """Test Department related APIs"""
        # Test get_department_details
        department_details = frappe.get_doc("Medical Department", self.department.name)
        self.assertEqual(department_details.department_name, "Test Department")
        
        # Test get_doctors_by_department
        doctors = frappe.get_all("Doctor",
            filters={"department": self.department.name},
            fields=["name", "first_name", "last_name"]
        )
        self.assertIsInstance(doctors, list)
    
    def test_notification_apis(self):
        """Test Notification related APIs"""
        # Create test appointment for notification
        appointment = frappe.get_doc({
            "doctype": "Appointment",
            "patient": self.patient.name,
            "doctor": self.doctor.name,
            "appointment_date": add_days(getdate(), 1),
            "appointment_time": "10:00:00",
            "appointment_type": "New Visit",
            "status": "Scheduled"
        }).insert()
        
        # Test send_appointment_reminder
        result = appointment.send_appointment_reminder()
        self.assertTrue(result)
    
    def tearDown(self):
        # Clean up test records
        frappe.delete_doc("Patient", self.patient.name)
        frappe.delete_doc("Doctor", self.doctor.name)
        frappe.delete_doc("Medical Department", self.department.name) 