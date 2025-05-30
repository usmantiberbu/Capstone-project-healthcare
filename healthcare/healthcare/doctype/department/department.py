import frappe
from frappe.model.document import Document

class Department(Document):
    def validate(self):
        self.validate_department_code()
        self.validate_head_of_department()
        self.validate_contact()
        self.validate_operating_hours()
        self.validate_capacity()
    
    def validate_department_code(self):
        if self.department_code:
            # Check if department code is unique
            existing = frappe.get_all("Department",
                filters={
                    "department_code": self.department_code,
                    "name": ["!=", self.name]
                }
            )
            if existing:
                frappe.throw("Department Code must be unique")
    
    def validate_head_of_department(self):
        if self.head_of_department:
            doctor = frappe.get_doc("Doctor", self.head_of_department)
            if doctor.department and doctor.department != self.name:
                frappe.throw(f"Doctor {doctor.name} is already head of department {doctor.department}")
    
    def validate_contact(self):
        if self.contact_number:
            if not self.contact_number.isdigit():
                frappe.throw("Contact number should contain only digits")
            if len(self.contact_number) < 10:
                frappe.throw("Contact number should be at least 10 digits")
        
        if self.email:
            if not frappe.utils.validate_email_address(self.email):
                frappe.throw("Please enter a valid email address")
    
    def validate_operating_hours(self):
        if self.operating_hours:
            for schedule in self.operating_hours:
                if schedule.start_time >= schedule.end_time:
                    frappe.throw("Start time must be before end time")
    
    def validate_capacity(self):
        if self.capacity and self.capacity < 0:
            frappe.throw("Daily patient capacity cannot be negative")
    
    def on_update(self):
        if self.head_of_department:
            # Update doctor's department
            doctor = frappe.get_doc("Doctor", self.head_of_department)
            doctor.department = self.name
            doctor.save()
        self.update_doctor_departments()
        self.update_appointment_slots()
    
    def update_doctor_departments(self):
        # Update department field for all doctors in this department
        doctors = frappe.get_all("Doctor", filters={"department": self.name})
        for doctor in doctors:
            doc = frappe.get_doc("Doctor", doctor.name)
            doc.save()
    
    def update_appointment_slots(self):
        # Update available appointment slots based on department capacity
        frappe.publish_realtime('department_capacity_updated', {
            'department': self.name,
            'capacity': self.capacity
        })
    
    def get_available_slots(self, date):
        # Get available appointment slots for a specific date
        total_appointments = frappe.db.count("Appointment", {
            "department": self.name,
            "appointment_date": date,
            "status": ["!=", "Cancelled"]
        })
        
        available_slots = self.capacity - total_appointments
        return max(0, available_slots) 