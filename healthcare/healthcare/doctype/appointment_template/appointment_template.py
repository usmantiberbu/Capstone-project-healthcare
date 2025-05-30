import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_days

class AppointmentTemplate(Document):
    def validate(self):
        self.validate_department()
        self.validate_reminder_days()
        self.validate_permissions()
    
    def validate_department(self):
        """Validate department"""
        if not frappe.db.exists("Medical Department", self.department):
            frappe.throw(_("Department {0} does not exist").format(self.department))
    
    def validate_reminder_days(self):
        """Validate reminder days"""
        if self.send_reminders and not self.reminder_days:
            frappe.throw(_("Please select at least one reminder day"))
    
    def validate_permissions(self):
        """Validate permissions"""
        if not self.allowed_roles:
            frappe.throw(_("Please select at least one allowed role"))
    
    @frappe.whitelist()
    def create_appointment(self, patient, doctor, appointment_date, appointment_time):
        """Create appointment from template"""
        try:
            # Validate template permissions
            if not self.has_permission("read"):
                frappe.throw(_("You don't have permission to use this template"))
            
            # Create appointment
            appointment = frappe.get_doc({
                "doctype": "Appointment",
                "patient": patient,
                "doctor": doctor,
                "department": self.department,
                "appointment_type": self.appointment_type,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "duration": self.duration,
                "notes": self.description,
                "payment_status": "Pending" if self.payment_required else "Paid",
                "payment_amount": self.base_price if self.payment_required else 0,
                "send_notification": self.send_reminders,
                "notification_channels": ["Email", "SMS", "WhatsApp"]
            })
            
            appointment.insert()
            
            # Set up reminders if enabled
            if self.send_reminders:
                self.setup_reminders(appointment)
            
            return {"message": "Appointment created successfully", "appointment": appointment.name}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Create Appointment from Template Error")
            frappe.throw(str(e))
    
    def setup_reminders(self, appointment):
        """Set up appointment reminders"""
        try:
            for day in self.reminder_days:
                reminder_date = add_days(getdate(appointment.appointment_date), -int(day))
                
                # Create reminder
                frappe.get_doc({
                    "doctype": "Appointment Reminder",
                    "appointment": appointment.name,
                    "patient": appointment.patient,
                    "doctor": appointment.doctor,
                    "reminder_date": reminder_date,
                    "message": self.get_reminder_message(appointment),
                    "status": "Pending"
                }).insert()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Setup Reminders Error")
    
    def get_reminder_message(self, appointment):
        """Get formatted reminder message"""
        try:
            message = self.reminder_message or """
            Dear {patient_name},
            
            This is a reminder for your upcoming appointment:
            
            Date: {appointment_date}
            Time: {appointment_time}
            Doctor: {doctor_name}
            Department: {department}
            
            Please arrive 15 minutes before your scheduled time.
            
            Best regards,
            Healthcare Team
            """
            
            # Get appointment details
            appointment_doc = frappe.get_doc("Appointment", appointment.name)
            patient = frappe.get_doc("Patient", appointment.patient)
            doctor = frappe.get_doc("Doctor", appointment.doctor)
            
            # Format message
            return message.format(
                patient_name=f"{patient.first_name} {patient.last_name}",
                appointment_date=appointment_doc.appointment_date,
                appointment_time=appointment_doc.appointment_time,
                doctor_name=f"{doctor.first_name} {doctor.last_name}",
                department=appointment_doc.department
            )
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Reminder Message Error")
            return str(e)
    
    @frappe.whitelist()
    def get_available_templates(patient=None, department=None):
        """Get available appointment templates"""
        try:
            filters = {"is_active": 1}
            
            if department:
                filters["department"] = department
            
            templates = frappe.get_all("Appointment Template",
                filters=filters,
                fields=["name", "template_name", "appointment_type", "department", 
                       "duration", "description", "base_price", "insurance_coverage"]
            )
            
            # Filter by permissions
            allowed_templates = []
            for template in templates:
                template_doc = frappe.get_doc("Appointment Template", template.name)
                if template_doc.has_permission("read"):
                    allowed_templates.append(template)
            
            return allowed_templates
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Available Templates Error")
            frappe.throw(str(e)) 