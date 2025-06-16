import frappe
from frappe.model.document import Document
import re
from frappe import _
from frappe.utils import now_datetime
from frappe.utils import cstr
from frappe.sessions import Session

class Patient(Document):
    def validate(self):
        self.validate_age()
        self.validate_contact()
    
    def validate_age(self):
        if self.date_of_birth:
            age = frappe.utils.date_diff(frappe.utils.today(), self.date_of_birth) / 365
            if age < 0:
                frappe.throw("Date of Birth cannot be in the future")
            if age > 120:
                frappe.throw("Please check the Date of Birth")
    
    def validate_contact(self):
        if self.mobile_no:
            if not re.match(r"^\+?\d+$", self.mobile_no):
                frappe.throw("Mobile number should contain only digits and may start with a + for country code")
            if len(self.mobile_no.lstrip('+')) < 10:
                frappe.throw("Mobile number should be at least 10 digits (excluding country code)")
        
        if self.email:
            if not frappe.utils.validate_email_address(self.email):
                frappe.throw("Please enter a valid email address")
    
    def after_insert(self):
        # Append a Patient Medical History record to the child table and save
        self.append("medical_history_table", {
            "patient": self.name,
            "date": frappe.utils.today(),
            "description": "Patient record created"
        })
        self.save(ignore_permissions=True)

@frappe.whitelist(allow_guest=True)
def api_create_patient():
    frappe.local.conf.disable_csrf = True
    try:
        # Get the request data
        data = frappe.form_dict
        
        # Log the received data
        frappe.logger().debug(f"Received data: {data}")
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'mobile_no', 'email']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return {
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }

        # Check for existing patient
        if frappe.db.exists("Patient", {"email": data.get('email')}):
            return {"error": "Email already registered"}
        if frappe.db.exists("Patient", {"mobile_no": data.get('mobile_no')}):
            return {"error": "Mobile number already registered"}

        # Create new patient
        patient = frappe.get_doc({
            "doctype": "Patient",
            "first_name": cstr(data.get('first_name')),
            "last_name": cstr(data.get('last_name')),
            "gender": cstr(data.get('gender')),
            "date_of_birth": cstr(data.get('date_of_birth')),
            "mobile_no": cstr(data.get('mobile_no')),
            "email": cstr(data.get('email')),
            "address": cstr(data.get('address')),
            "insurance_provider": cstr(data.get('insurance_provider')),
            "insurance_number": cstr(data.get('insurance_number'))
        })

        # Insert the patient
        patient.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "message": "Patient registered successfully",
            "patient": patient.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Create Patient Error")
        return {
            "error": str(e),
            "traceback": frappe.get_traceback()
        }

@frappe.whitelist(allow_guest=True)
def get_csrf_token():
    """Get CSRF token for guest access"""
    try:
        session = Session()
        return {
            "csrf_token": session.csrf_token
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get CSRF Token Error")
        return {
            "error": str(e)
        } 