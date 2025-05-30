import frappe
from frappe.model.document import Document

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
            if not self.mobile_no.isdigit():
                frappe.throw("Mobile number should contain only digits")
            if len(self.mobile_no) < 10:
                frappe.throw("Mobile number should be at least 10 digits")
        
        if self.email:
            if not frappe.utils.validate_email_address(self.email):
                frappe.throw("Please enter a valid email address")
    
    def on_update(self):
        self.update_patient_history()
    
    def update_patient_history(self):
        if self.is_new():
            frappe.get_doc({
                "doctype": "Patient Medical History",
                "patient": self.name,
                "date": frappe.utils.today(),
                "description": "Patient record created"
            }).insert() 