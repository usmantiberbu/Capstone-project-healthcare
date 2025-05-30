import frappe
from frappe import _
from frappe.model.document import Document

class TeamRole(Document):
    def validate(self):
        self.validate_permissions()
    
    def validate_permissions(self):
        """Validate that at least one permission is enabled"""
        permissions = [
            self.can_view_patients,
            self.can_edit_patients,
            self.can_view_schedule,
            self.can_edit_schedule,
            self.can_view_medical_records,
            self.can_edit_medical_records,
            self.can_manage_appointments,
            self.can_manage_team
        ]
        
        if not any(permissions):
            frappe.throw(_("At least one permission must be enabled"))
    
    @frappe.whitelist()
    def get_roles():
        """Get all team roles"""
        try:
            roles = frappe.get_all("Team Role",
                fields=["name", "role_name", "description"],
                order_by="role_name"
            )
            return roles
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Team Roles Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_role_permissions(role):
        """Get permissions for a specific role"""
        try:
            role_doc = frappe.get_doc("Team Role", role)
            return {
                "can_view_patients": role_doc.can_view_patients,
                "can_edit_patients": role_doc.can_edit_patients,
                "can_view_schedule": role_doc.can_view_schedule,
                "can_edit_schedule": role_doc.can_edit_schedule,
                "can_view_medical_records": role_doc.can_view_medical_records,
                "can_edit_medical_records": role_doc.can_edit_medical_records,
                "can_manage_appointments": role_doc.can_manage_appointments,
                "can_manage_team": role_doc.can_manage_team
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Role Permissions Error")
            frappe.throw(str(e)) 