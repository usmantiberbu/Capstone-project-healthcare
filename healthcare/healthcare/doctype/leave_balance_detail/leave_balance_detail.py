import frappe
from frappe.model.document import Document

class LeaveBalanceDetail(Document):
    def validate(self):
        self.validate_year()
        self.calculate_remaining_leaves()
    
    def validate_year(self):
        if self.year < 2000 or self.year > 2100:
            frappe.throw("Invalid year")
    
    def calculate_remaining_leaves(self):
        if self.total_leaves and self.leaves_taken:
            self.leaves_remaining = self.total_leaves - self.leaves_taken
            if self.leaves_remaining < 0:
                frappe.throw("Leaves taken cannot exceed total leaves")
    
    def on_update(self):
        # Update doctor's leave balance
        if self.parenttype == "Doctor":
            doctor = frappe.get_doc("Doctor", self.parent)
            doctor.save() 