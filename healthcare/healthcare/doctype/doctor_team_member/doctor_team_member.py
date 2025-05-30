import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime
from frappe.permissions import has_permission

class DoctorTeamMember(Document):
    def validate(self):
        self.validate_doctor()
        self.validate_role()
        self.validate_duplicate()
        self.validate_department()
        self.validate_specialization()
        self.validate_working_hours()
        self.validate_max_team_size()
    
    def validate_doctor(self):
        """Validate that the doctor exists and is active"""
        if not frappe.db.exists("Doctor", self.doctor):
            frappe.throw(_("Doctor {0} does not exist").format(self.doctor))
        
        if not frappe.db.exists("Doctor", self.team_member):
            frappe.throw(_("Team member {0} does not exist").format(self.team_member))
        
        # Check if team member is active
        team_member = frappe.get_doc("Doctor", self.team_member)
        if not team_member.is_active:
            frappe.throw(_("Team member {0} is not active").format(self.team_member))
        
        # Check if doctor has permission to manage team
        if not self.has_team_management_permission(self.doctor):
            frappe.throw(_("You don't have permission to manage team members"))
    
    def validate_role(self):
        """Validate that the role exists and is valid"""
        if not frappe.db.exists("Team Role", self.role):
            frappe.throw(_("Role {0} does not exist").format(self.role))
        
        # Validate role permissions
        role = frappe.get_doc("Team Role", self.role)
        if not role.can_manage_team:
            frappe.throw(_("Selected role does not have team management permissions"))
    
    def validate_duplicate(self):
        """Validate that the team member is not already added"""
        existing = frappe.db.exists("Doctor Team Member", {
            "doctor": self.doctor,
            "team_member": self.team_member,
            "name": ["!=", self.name]
        })
        if existing:
            frappe.throw(_("Team member {0} is already added to this team").format(self.team_member))
    
    def validate_department(self):
        """Validate department compatibility"""
        doctor = frappe.get_doc("Doctor", self.doctor)
        team_member = frappe.get_doc("Doctor", self.team_member)
        
        if doctor.department != team_member.department:
            frappe.throw(_("Team member must belong to the same department as the doctor"))
    
    def validate_specialization(self):
        """Validate specialization compatibility"""
        doctor = frappe.get_doc("Doctor", self.doctor)
        team_member = frappe.get_doc("Doctor", self.team_member)
        
        if doctor.specialization != team_member.specialization:
            frappe.throw(_("Team member must have the same specialization as the doctor"))
    
    def validate_working_hours(self):
        """Validate working hours compatibility"""
        doctor_schedule = frappe.get_all("Doctor Schedule",
            filters={"doctor": self.doctor},
            fields=["from_time", "to_time"]
        )
        member_schedule = frappe.get_all("Doctor Schedule",
            filters={"doctor": self.team_member},
            fields=["from_time", "to_time"]
        )
        
        if not self.has_overlapping_schedule(doctor_schedule, member_schedule):
            frappe.throw(_("Team member's working hours must overlap with doctor's schedule"))
    
    def validate_max_team_size(self):
        """Validate maximum team size"""
        max_team_size = frappe.db.get_single_value("Healthcare Settings", "max_team_size") or 5
        current_team_size = frappe.db.count("Doctor Team Member", {"doctor": self.doctor})
        
        if current_team_size >= max_team_size:
            frappe.throw(_("Maximum team size limit reached"))
    
    def before_save(self):
        """Set default values before saving"""
        if not self.join_date:
            self.join_date = getdate()
        
        # Set last modified timestamp
        self.last_modified = now_datetime()
    
    def after_insert(self):
        """Actions after inserting a new team member"""
        self.create_team_notification()
        self.update_team_metrics()
    
    def on_trash(self):
        """Actions before deleting a team member"""
        if not self.has_team_management_permission(self.doctor):
            frappe.throw(_("You don't have permission to remove team members"))
        
        self.create_removal_notification()
        self.update_team_metrics()
    
    def has_team_management_permission(self, doctor):
        """Check if user has team management permission"""
        if frappe.session.user == "Administrator":
            return True
        
        return has_permission("Doctor Team Member", "write", user=frappe.session.user)
    
    def has_overlapping_schedule(self, schedule1, schedule2):
        """Check if two schedules overlap"""
        for s1 in schedule1:
            for s2 in schedule2:
                if (s1.from_time <= s2.to_time and s1.to_time >= s2.from_time):
                    return True
        return False
    
    def create_team_notification(self):
        """Create notification for team member addition"""
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Team Update",
            "title": "New Team Member Added",
            "message": f"New team member {self.team_member} has been added to your team",
            "for_user": self.doctor
        }).insert()
    
    def create_removal_notification(self):
        """Create notification for team member removal"""
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Team Update",
            "title": "Team Member Removed",
            "message": f"Team member {self.team_member} has been removed from your team",
            "for_user": self.doctor
        }).insert()
    
    def update_team_metrics(self):
        """Update team performance metrics"""
        frappe.get_doc("Doctor Workspace Settings", self.doctor).update_team_metrics()
    
    @frappe.whitelist()
    def get_team_members(doctor):
        """Get all team members for a doctor"""
        try:
            members = frappe.get_all("Doctor Team Member",
                filters={"doctor": doctor},
                fields=["name", "team_member", "role", "join_date", "status", "notes"],
                order_by="join_date desc"
            )
            
            # Get additional details for each member
            for member in members:
                doctor_doc = frappe.get_doc("Doctor", member.team_member)
                member.name = f"{doctor_doc.first_name} {doctor_doc.last_name}"
                member.specialization = doctor_doc.specialization
                member.department = doctor_doc.department
                member.performance = self.get_member_performance(member.team_member)
            
            return members
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Team Members Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def update_member_status(team_member, status):
        """Update team member status"""
        try:
            if status not in ["Active", "Inactive", "On Leave"]:
                frappe.throw(_("Invalid status"))
            
            doc = frappe.get_doc("Doctor Team Member", team_member)
            doc.status = status
            doc.save()
            
            # Create status update notification
            frappe.get_doc({
                "doctype": "Notification",
                "type": "Status Update",
                "title": "Team Member Status Updated",
                "message": f"Team member {doc.team_member}'s status has been updated to {status}",
                "for_user": doc.doctor
            }).insert()
            
            return {"message": "Status updated successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Update Team Member Status Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_member_permissions(team_member):
        """Get permissions for a team member"""
        try:
            member = frappe.get_doc("Doctor Team Member", team_member)
            role = frappe.get_doc("Team Role", member.role)
            
            return {
                "can_view_patients": role.can_view_patients,
                "can_edit_patients": role.can_edit_patients,
                "can_view_schedule": role.can_view_schedule,
                "can_edit_schedule": role.can_edit_schedule,
                "can_view_medical_records": role.can_view_medical_records,
                "can_edit_medical_records": role.can_edit_medical_records,
                "can_manage_appointments": role.can_manage_appointments,
                "can_manage_team": role.can_manage_team
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Team Member Permissions Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_member_performance(team_member):
        """Get performance metrics for a team member"""
        try:
            # Get appointments handled
            appointments = frappe.get_all("Appointment",
                filters={"doctor": team_member},
                fields=["status", "appointment_date"]
            )
            
            # Get patient feedback
            feedback = frappe.get_all("Patient Feedback",
                filters={"doctor": team_member},
                fields=["rating"]
            )
            
            # Calculate metrics
            total_appointments = len(appointments)
            completed_appointments = len([a for a in appointments if a.status == "Completed"])
            satisfaction_rating = sum(f.rating for f in feedback) / len(feedback) if feedback else 0
            
            return {
                "total_appointments": total_appointments,
                "completed_appointments": completed_appointments,
                "completion_rate": (completed_appointments / total_appointments * 100) if total_appointments else 0,
                "satisfaction_rating": satisfaction_rating
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Team Member Performance Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_team_availability(date):
        """Get team availability for a specific date"""
        try:
            team_members = frappe.get_all("Doctor Team Member",
                filters={"status": "Active"},
                fields=["team_member"]
            )
            
            availability = []
            for member in team_members:
                schedule = frappe.get_all("Doctor Schedule",
                    filters={
                        "doctor": member.team_member,
                        "schedule_date": date
                    },
                    fields=["from_time", "to_time"]
                )
                
                if schedule:
                    availability.append({
                        "doctor": member.team_member,
                        "schedule": schedule
                    })
            
            return availability
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Team Availability Error")
            frappe.throw(str(e)) 