import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_days, add_to_date
from frappe.core.doctype.communication.email import make

class AppointmentReminder(Document):
    def validate(self):
        self.validate_appointment()
        self.validate_notification_channels()
    
    def validate_appointment(self):
        """Validate appointment details"""
        if not frappe.db.exists("Appointment", self.appointment):
            frappe.throw(_("Appointment {0} does not exist").format(self.appointment))
        
        appointment = frappe.get_doc("Appointment", self.appointment)
        if appointment.status in ["Completed", "Cancelled", "No Show"]:
            frappe.throw(_("Cannot send reminders for completed, cancelled, or no-show appointments"))
    
    def validate_notification_channels(self):
        """Validate notification channels"""
        if not self.notification_channels:
            frappe.throw(_("Please select at least one notification channel"))
    
    def before_save(self):
        """Actions before saving"""
        if self.is_new():
            self.status = "Pending"
    
    def on_update(self):
        """Actions on update"""
        if self.has_value_changed("status") and self.status == "Pending":
            self.send_reminders()
    
    def send_reminders(self):
        """Send reminders through selected channels"""
        try:
            # Get appointment and patient details
            appointment = frappe.get_doc("Appointment", self.appointment)
            patient = frappe.get_doc("Patient", self.patient)
            
            # Send through each selected channel
            for channel in self.notification_channels:
                if channel == "Email" and not self.email_sent:
                    self.send_email_reminder(appointment, patient)
                elif channel == "SMS" and not self.sms_sent:
                    self.send_sms_reminder(appointment, patient)
                elif channel == "WhatsApp" and not self.whatsapp_sent:
                    self.send_whatsapp_reminder(appointment, patient)
            
            # Update status
            if all([self.email_sent, self.sms_sent, self.whatsapp_sent]):
                self.status = "Sent"
            else:
                self.status = "Failed"
            
            self.last_sent = now_datetime()
            self.save()
        except Exception as e:
            self.status = "Failed"
            self.error_log = str(e)
            self.save()
            frappe.log_error(frappe.get_traceback(), "Send Reminders Error")
    
    def send_email_reminder(self, appointment, patient):
        """Send email reminder"""
        try:
            make(
                recipients=[patient.email],
                subject=f"Appointment Reminder - {appointment.name}",
                content=self.message,
                doctype=self.doctype,
                name=self.name
            )
            self.email_sent = 1
        except Exception as e:
            self.error_log = f"Email Error: {str(e)}"
            frappe.log_error(frappe.get_traceback(), "Email Reminder Error")
    
    def send_sms_reminder(self, appointment, patient):
        """Send SMS reminder"""
        try:
            # Implement SMS sending logic here
            # For now, just mark as sent
            self.sms_sent = 1
        except Exception as e:
            self.error_log = f"SMS Error: {str(e)}"
            frappe.log_error(frappe.get_traceback(), "SMS Reminder Error")
    
    def send_whatsapp_reminder(self, appointment, patient):
        """Send WhatsApp reminder"""
        try:
            # Implement WhatsApp sending logic here
            # For now, just mark as sent
            self.whatsapp_sent = 1
        except Exception as e:
            self.error_log = f"WhatsApp Error: {str(e)}"
            frappe.log_error(frappe.get_traceback(), "WhatsApp Reminder Error")
    
    @frappe.whitelist()
    def resend_reminder(self):
        """Resend reminder"""
        try:
            self.status = "Pending"
            self.email_sent = 0
            self.sms_sent = 0
            self.whatsapp_sent = 0
            self.error_log = ""
            self.save()
            
            return {"message": "Reminder queued for resending"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Resend Reminder Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_reminder_status(self):
        """Get reminder status"""
        return {
            "status": self.status,
            "email_sent": self.email_sent,
            "sms_sent": self.sms_sent,
            "whatsapp_sent": self.whatsapp_sent,
            "last_sent": self.last_sent,
            "error_log": self.error_log
        } 