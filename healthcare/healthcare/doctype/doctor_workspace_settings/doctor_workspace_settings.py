import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class DoctorWorkspaceSettings(Document):
    def validate(self):
        self.validate_metrics()
        self.validate_team_roles()
        self.validate_notifications()
    
    def validate_metrics(self):
        """Validate selected metrics"""
        if self.enable_performance_metrics and not self.metrics_to_show:
            frappe.throw(_("Please select at least one metric to show"))
    
    def validate_team_roles(self):
        """Validate team roles configuration"""
        if self.enable_team_management and not self.team_roles:
            frappe.throw(_("Please add at least one team role"))
    
    def validate_notifications(self):
        """Validate notification settings"""
        if self.enable_notifications and not self.notification_channels:
            frappe.throw(_("Please select at least one notification channel"))
    
    @frappe.whitelist()
    def get_workspace_url(self):
        """Get the URL for the doctor workspace"""
        return frappe.utils.get_url("/doctor-workspace")
    
    @frappe.whitelist()
    def get_doctor_metrics(self, doctor):
        """Get doctor's performance metrics"""
        try:
            metrics = {}
            
            # Appointments Completed
            if "Appointments Completed" in self.metrics_to_show:
                metrics["appointments_completed"] = self.get_appointments_completed(doctor)
            
            # Patient Satisfaction
            if "Patient Satisfaction" in self.metrics_to_show:
                metrics["patient_satisfaction"] = self.get_patient_satisfaction(doctor)
            
            # Wait Time
            if "Wait Time" in self.metrics_to_show:
                metrics["wait_time"] = self.get_average_wait_time(doctor)
            
            # Revenue
            if "Revenue" in self.metrics_to_show:
                metrics["revenue"] = self.get_doctor_revenue(doctor)
            
            # Team Performance
            if "Team Performance" in self.metrics_to_show:
                metrics["team_performance"] = self.get_team_performance(doctor)
            
            return metrics
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Doctor Metrics Error")
            frappe.throw(str(e))
    
    def get_appointments_completed(self, doctor):
        """Get number of completed appointments"""
        return frappe.db.count("Appointment", {
            "doctor": doctor,
            "status": "Completed",
            "appointment_date": [">=", getdate()]
        })
    
    def get_patient_satisfaction(self, doctor):
        """Get patient satisfaction rating"""
        ratings = frappe.get_all("Patient Feedback",
            filters={"doctor": doctor},
            fields=["rating"]
        )
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)
    
    def get_average_wait_time(self, doctor):
        """Get average patient wait time"""
        appointments = frappe.get_all("Appointment",
            filters={
                "doctor": doctor,
                "status": "Completed",
                "appointment_date": [">=", getdate()]
            },
            fields=["wait_time"]
        )
        if not appointments:
            return 0
        return sum(a.wait_time for a in appointments) / len(appointments)
    
    def get_doctor_revenue(self, doctor):
        """Get doctor's revenue"""
        return frappe.db.sql("""
            SELECT SUM(amount)
            FROM `tabPayment Entry`
            WHERE doctor = %s
            AND payment_date >= %s
        """, (doctor, getdate()))[0][0] or 0
    
    def get_team_performance(self, doctor):
        """Get team performance metrics"""
        team_members = frappe.get_all("Doctor Team Member",
            filters={"doctor": doctor},
            fields=["team_member"]
        )
        
        performance = {
            "total_appointments": 0,
            "completed_appointments": 0,
            "average_satisfaction": 0
        }
        
        for member in team_members:
            # Get member's appointments
            appointments = frappe.get_all("Appointment",
                filters={"doctor": member.team_member},
                fields=["status"]
            )
            performance["total_appointments"] += len(appointments)
            performance["completed_appointments"] += len([a for a in appointments if a.status == "Completed"])
            
            # Get member's satisfaction rating
            ratings = frappe.get_all("Patient Feedback",
                filters={"doctor": member.team_member},
                fields=["rating"]
            )
            if ratings:
                performance["average_satisfaction"] += sum(r.rating for r in ratings) / len(ratings)
        
        if team_members:
            performance["average_satisfaction"] /= len(team_members)
        
        return performance
    
    @frappe.whitelist()
    def get_patient_queue(self, doctor):
        """Get current patient queue"""
        try:
            queue = frappe.get_all("Appointment",
                filters={
                    "doctor": doctor,
                    "appointment_date": getdate(),
                    "status": ["in", ["Scheduled", "In Progress"]]
                },
                fields=["name", "patient", "appointment_time", "status"],
                order_by="appointment_time"
            )
            
            # Get patient details
            for item in queue:
                patient = frappe.get_doc("Patient", item.patient)
                item.patient_name = f"{patient.first_name} {patient.last_name}"
                item.patient_age = patient.age
                item.patient_gender = patient.gender
            
            return queue
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Patient Queue Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_team_members(self, doctor):
        """Get doctor's team members"""
        try:
            team_members = frappe.get_all("Doctor Team Member",
                filters={"doctor": doctor},
                fields=["team_member", "role"]
            )
            
            # Get member details
            for member in team_members:
                doctor = frappe.get_doc("Doctor", member.team_member)
                member.name = f"{doctor.first_name} {doctor.last_name}"
                member.specialization = doctor.specialization
                member.department = doctor.department
            
            return team_members
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Team Members Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def add_team_member(self, doctor, team_member, role):
        """Add a team member"""
        try:
            if not self.enable_team_management:
                frappe.throw(_("Team management is not enabled"))
            
            # Validate role
            valid_roles = [r.role_name for r in self.team_roles]
            if role not in valid_roles:
                frappe.throw(_("Invalid role selected"))
            
            # Add team member
            team_member = frappe.get_doc({
                "doctype": "Doctor Team Member",
                "doctor": doctor,
                "team_member": team_member,
                "role": role
            })
            team_member.insert()
            
            return {"message": "Team member added successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Add Team Member Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def remove_team_member(self, doctor, team_member):
        """Remove a team member"""
        try:
            if not self.enable_team_management:
                frappe.throw(_("Team management is not enabled"))
            
            # Remove team member
            frappe.delete_doc("Doctor Team Member", {
                "doctor": doctor,
                "team_member": team_member
            })
            
            return {"message": "Team member removed successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Remove Team Member Error")
            frappe.throw(str(e)) 