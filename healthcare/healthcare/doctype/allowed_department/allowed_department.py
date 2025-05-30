import frappe
from frappe import _
from frappe.model.document import Document

class AllowedDepartment(Document):
    def validate(self):
        self.validate_department()
        self.validate_permissions()
    
    def validate_department(self):
        """Validate that the department exists and is active"""
        if not frappe.db.exists("Department", self.department):
            frappe.throw(_("Department {0} does not exist").format(self.department))
        
        department = frappe.get_doc("Department", self.department)
        if not department.is_active:
            frappe.throw(_("Department {0} is not active").format(self.department))
    
    def validate_permissions(self):
        """Validate that at least one permission is enabled"""
        permissions = [
            self.allow_appointment_booking,
            self.allow_medical_history_view,
            self.allow_document_upload
        ]
        
        if not any(permissions):
            frappe.throw(_("At least one permission must be enabled"))
    
    @frappe.whitelist()
    def get_allowed_departments():
        """Get all allowed departments"""
        try:
            departments = frappe.get_all("Allowed Department",
                fields=["name", "department", "allow_appointment_booking", 
                       "allow_medical_history_view", "allow_document_upload"],
                order_by="department"
            )
            return departments
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Allowed Departments Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def is_department_allowed(department):
        """Check if a department is allowed"""
        try:
            return frappe.db.exists("Allowed Department", {
                "department": department
            })
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Check Department Allowed Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_department_permissions(department):
        """Get permissions for a specific department"""
        try:
            dept = frappe.get_doc("Allowed Department", {
                "department": department
            })
            return {
                "allow_appointment_booking": dept.allow_appointment_booking,
                "allow_medical_history_view": dept.allow_medical_history_view,
                "allow_document_upload": dept.allow_document_upload
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Department Permissions Error")
            frappe.throw(str(e)) 