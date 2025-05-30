import frappe
import unittest
from frappe.utils import getdate, add_days
from healthcare.healthcare.doctype.doctor_team_member.doctor_team_member import DoctorTeamMember

class TestDoctorTeamMember(unittest.TestCase):
    def setUp(self):
        # Create test doctors
        self.doctor = create_test_doctor("Test Doctor", "Cardiology", "Active")
        self.team_member = create_test_doctor("Test Team Member", "Cardiology", "Active")
        self.other_doctor = create_test_doctor("Other Doctor", "Neurology", "Active")
        
        # Create test role
        self.role = create_test_role()
        
        # Create test schedules
        create_test_schedule(self.doctor)
        create_test_schedule(self.team_member)
    
    def tearDown(self):
        # Clean up test data
        frappe.delete_doc("Doctor", self.doctor)
        frappe.delete_doc("Doctor", self.team_member)
        frappe.delete_doc("Doctor", self.other_doctor)
        frappe.delete_doc("Team Role", self.role)
    
    def test_team_member_creation(self):
        """Test creating a valid team member"""
        team_member = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        
        team_member.insert()
        self.assertTrue(frappe.db.exists("Doctor Team Member", team_member.name))
    
    def test_department_validation(self):
        """Test department compatibility validation"""
        team_member = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.other_doctor,
            "role": self.role,
            "status": "Active"
        })
        
        with self.assertRaises(frappe.ValidationError):
            team_member.insert()
    
    def test_duplicate_team_member(self):
        """Test duplicate team member validation"""
        # Create first team member
        team_member1 = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        team_member1.insert()
        
        # Try to create duplicate
        team_member2 = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        
        with self.assertRaises(frappe.ValidationError):
            team_member2.insert()
    
    def test_team_size_limit(self):
        """Test maximum team size validation"""
        # Set max team size
        frappe.db.set_single_value("Healthcare Settings", "max_team_size", 2)
        
        # Create first team member
        team_member1 = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        team_member1.insert()
        
        # Create second team member
        team_member2 = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.other_doctor,
            "role": self.role,
            "status": "Active"
        })
        
        with self.assertRaises(frappe.ValidationError):
            team_member2.insert()
    
    def test_team_member_performance(self):
        """Test team member performance metrics"""
        # Create team member
        team_member = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        team_member.insert()
        
        # Create test appointments
        create_test_appointments(self.team_member)
        
        # Create test feedback
        create_test_feedback(self.team_member)
        
        # Get performance metrics
        performance = team_member.get_member_performance(self.team_member)
        
        self.assertEqual(performance["total_appointments"], 2)
        self.assertEqual(performance["completed_appointments"], 1)
        self.assertEqual(performance["completion_rate"], 50.0)
        self.assertEqual(performance["satisfaction_rating"], 4.5)
    
    def test_team_availability(self):
        """Test team availability tracking"""
        # Create team member
        team_member = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        team_member.insert()
        
        # Get availability
        availability = team_member.get_team_availability(getdate())
        
        self.assertEqual(len(availability), 2)  # Both doctor and team member
        self.assertTrue(any(a["doctor"] == self.team_member for a in availability))
    
    def test_team_member_status_update(self):
        """Test team member status update"""
        # Create team member
        team_member = frappe.get_doc({
            "doctype": "Doctor Team Member",
            "doctor": self.doctor,
            "team_member": self.team_member,
            "role": self.role,
            "status": "Active"
        })
        team_member.insert()
        
        # Update status
        result = team_member.update_member_status(team_member.name, "On Leave")
        
        self.assertEqual(result["message"], "Status updated successfully")
        self.assertEqual(frappe.db.get_value("Doctor Team Member", team_member.name, "status"), "On Leave")

def create_test_doctor(name, specialization, status):
    """Create a test doctor"""
    doctor = frappe.get_doc({
        "doctype": "Doctor",
        "first_name": name,
        "specialization": specialization,
        "department": "Cardiology",
        "is_active": status == "Active"
    })
    doctor.insert()
    return doctor.name

def create_test_role():
    """Create a test team role"""
    role = frappe.get_doc({
        "doctype": "Team Role",
        "role_name": "Test Role",
        "description": "Test role for unit tests",
        "can_view_patients": 1,
        "can_edit_patients": 1,
        "can_view_schedule": 1,
        "can_edit_schedule": 1,
        "can_view_medical_records": 1,
        "can_edit_medical_records": 1,
        "can_manage_appointments": 1,
        "can_manage_team": 1
    })
    role.insert()
    return role.name

def create_test_schedule(doctor):
    """Create a test schedule for a doctor"""
    schedule = frappe.get_doc({
        "doctype": "Doctor Schedule",
        "doctor": doctor,
        "schedule_date": getdate(),
        "from_time": "09:00:00",
        "to_time": "17:00:00"
    })
    schedule.insert()

def create_test_appointments(doctor):
    """Create test appointments for a doctor"""
    # Completed appointment
    appointment1 = frappe.get_doc({
        "doctype": "Appointment",
        "doctor": doctor,
        "appointment_date": getdate(),
        "status": "Completed"
    })
    appointment1.insert()
    
    # Pending appointment
    appointment2 = frappe.get_doc({
        "doctype": "Appointment",
        "doctor": doctor,
        "appointment_date": add_days(getdate(), 1),
        "status": "Pending"
    })
    appointment2.insert()

def create_test_feedback(doctor):
    """Create test feedback for a doctor"""
    feedback = frappe.get_doc({
        "doctype": "Patient Feedback",
        "doctor": doctor,
        "rating": 4.5,
        "feedback": "Test feedback"
    })
    feedback.insert() 