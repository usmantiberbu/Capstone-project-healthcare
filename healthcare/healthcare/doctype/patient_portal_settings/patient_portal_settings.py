import frappe
from frappe.model.document import Document
from frappe.utils import get_url

class PatientPortalSettings(Document):
    def validate(self):
        self.validate_departments()
        self.validate_payment_settings()
    
    def validate_departments(self):
        if not self.allowed_departments:
            frappe.throw("At least one department must be allowed for the patient portal")
    
    def validate_payment_settings(self):
        if self.enable_online_payment and not self.payment_gateway:
            frappe.throw("Payment gateway must be selected when online payment is enabled")
    
    @frappe.whitelist()
    def get_portal_url(self):
        """Get the URL for the patient portal"""
        return get_url("/patient-portal")
    
    @frappe.whitelist()
    def is_department_allowed(self, department):
        """Check if a department is allowed in the portal"""
        for dept in self.allowed_departments:
            if dept.department == department:
                return True
        return False
    
    @frappe.whitelist()
    def can_book_appointment(self, department):
        """Check if appointment booking is allowed for a department"""
        for dept in self.allowed_departments:
            if dept.department == department and dept.allow_appointment_booking:
                return True
        return False
    
    @frappe.whitelist()
    def can_view_medical_history(self, department):
        """Check if medical history viewing is allowed for a department"""
        for dept in self.allowed_departments:
            if dept.department == department and dept.allow_medical_history_view:
                return True
        return False
    
    @frappe.whitelist()
    def can_upload_documents(self, department):
        """Check if document upload is allowed for a department"""
        for dept in self.allowed_departments:
            if dept.department == department and dept.allow_document_upload:
                return True
        return False 