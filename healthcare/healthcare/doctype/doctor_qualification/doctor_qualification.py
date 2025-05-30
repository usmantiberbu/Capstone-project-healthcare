import frappe
from frappe.model.document import Document

class DoctorQualification(Document):
    def validate(self):
        self.validate_year_of_completion()
    
    def validate_year_of_completion(self):
        if self.year_of_completion:
            current_year = frappe.utils.getdate().year
            if self.year_of_completion > current_year:
                frappe.throw("Year of completion cannot be in the future")
            if self.year_of_completion < 1900:
                frappe.throw("Year of completion seems invalid") 