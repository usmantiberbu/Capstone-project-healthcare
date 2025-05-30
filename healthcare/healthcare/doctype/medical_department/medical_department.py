import frappe
from frappe import _
from frappe.model.document import Document

class MedicalDepartment(Document):
    def validate(self):
        self.validate_department_name()
        self.validate_head_doctor()
    
    def validate_department_name(self):
        """Validate department name"""
        if not self.department_name:
            frappe.throw(_("Department name is required"))
        
        # Check for duplicate department names
        existing = frappe.get_all("Medical Department",
            filters={"department_name": self.department_name, "name": ["!=", self.name]},
            fields=["name"]
        )
        
        if existing:
            frappe.throw(_("Department with name {0} already exists").format(self.department_name))
    
    def validate_head_doctor(self):
        """Validate head doctor"""
        if self.head_doctor and not frappe.db.exists("Doctor", self.head_doctor):
            frappe.throw(_("Head doctor {0} does not exist").format(self.head_doctor))
    
    @frappe.whitelist()
    def get_departments():
        """Get all active departments"""
        try:
            departments = frappe.get_all("Medical Department",
                filters={"is_active": 1},
                fields=["name", "department_name", "description", "head_doctor"],
                order_by="department_name"
            )
            
            # Get head doctor names
            for dept in departments:
                if dept.head_doctor:
                    doctor = frappe.get_doc("Doctor", dept.head_doctor)
                    dept.head_doctor_name = f"{doctor.first_name} {doctor.last_name}"
            
            return departments
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Departments Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_department_details(department):
        """Get department details"""
        try:
            department = frappe.get_doc("Medical Department", department)
            
            # Get head doctor details
            head_doctor = None
            if department.head_doctor:
                doctor = frappe.get_doc("Doctor", department.head_doctor)
                head_doctor = {
                    "name": doctor.name,
                    "first_name": doctor.first_name,
                    "last_name": doctor.last_name,
                    "specialization": doctor.specialization,
                    "email": doctor.email,
                    "phone": doctor.phone
                }
            
            # Get department doctors
            doctors = frappe.get_all("Doctor",
                filters={"department": department.name, "is_active": 1},
                fields=["name", "first_name", "last_name", "specialization", "email", "phone"]
            )
            
            return {
                "name": department.name,
                "department_name": department.department_name,
                "description": department.description,
                "head_doctor": head_doctor,
                "doctors": doctors
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Department Details Error")
            frappe.throw(str(e)) 