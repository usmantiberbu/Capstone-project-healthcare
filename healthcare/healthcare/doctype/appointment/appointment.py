import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_days, add_to_date
from frappe.core.doctype.communication.email import make
from frappe.desk.form.load import get_attachments
from frappe.permissions import has_permission

class Appointment(Document):
    def validate(self):
        self.validate_patient()
        self.validate_doctor()
        self.validate_department()
        self.validate_appointment_datetime()
        self.validate_insurance()
        self.validate_payment()
        self.set_patient_details()
        self.set_doctor_details()
    
    def validate_patient(self):
        """Validate patient details"""
        if not frappe.db.exists("Patient", self.patient):
            frappe.throw(_("Patient {0} does not exist").format(self.patient))
        
        patient = frappe.get_doc("Patient", self.patient)
        if not patient.is_active:
            frappe.throw(_("Patient {0} is not active").format(self.patient))
    
    def validate_doctor(self):
        """Validate doctor details"""
        if not frappe.db.exists("Doctor", self.doctor):
            frappe.throw(_("Doctor {0} does not exist").format(self.doctor))
        
        doctor = frappe.get_doc("Doctor", self.doctor)
        if not doctor.is_active:
            frappe.throw(_("Doctor {0} is not active").format(self.doctor))
        
        # Check if doctor belongs to selected department
        if doctor.department != self.department:
            frappe.throw(_("Doctor {0} does not belong to department {1}").format(
                self.doctor, self.department))
    
    def validate_department(self):
        """Validate department"""
        if not frappe.db.exists("Medical Department", self.department):
            frappe.throw(_("Department {0} does not exist").format(self.department))
    
    def validate_appointment_datetime(self):
        """Validate appointment date and time"""
        if getdate(self.appointment_date) < getdate():
            frappe.throw(_("Appointment date cannot be in the past"))
        
        # Check doctor's schedule
        if not self.is_doctor_available():
            frappe.throw(_("Doctor is not available at the selected time"))
        
        # Check for scheduling conflicts
        if self.has_scheduling_conflict():
            frappe.throw(_("There is a scheduling conflict at the selected time"))
    
    def validate_insurance(self):
        """Validate insurance details"""
        if self.insurance_provider and not frappe.db.exists("Insurance Provider", self.insurance_provider):
            frappe.throw(_("Insurance provider {0} does not exist").format(self.insurance_provider))
    
    def validate_payment(self):
        """Validate payment details"""
        if self.payment_status == "Paid" and not self.payment_amount:
            frappe.throw(_("Payment amount is required when status is Paid"))
    
    def set_patient_details(self):
        """Set patient details from Patient DocType"""
        patient = frappe.get_doc("Patient", self.patient)
        self.patient_name = f"{patient.first_name} {patient.last_name}"
        self.patient_age = patient.age
        self.patient_gender = patient.gender
        self.patient_contact = patient.phone
        self.patient_email = patient.email
    
    def set_doctor_details(self):
        """Set doctor details from Doctor DocType"""
        doctor = frappe.get_doc("Doctor", self.doctor)
        self.doctor_name = f"{doctor.first_name} {doctor.last_name}"
        self.specialization = doctor.specialization
    
    def is_doctor_available(self):
        """Check if doctor is available at the appointment time"""
        schedule = frappe.get_all("Doctor Schedule",
            filters={
                "doctor": self.doctor,
                "schedule_date": self.appointment_date
            },
            fields=["from_time", "to_time"]
        )
        
        if not schedule:
            return False
        
        appointment_time = self.appointment_time
        for s in schedule:
            if s.from_time <= appointment_time <= s.to_time:
                return True
        
        return False
    
    def has_scheduling_conflict(self):
        """Check for scheduling conflicts"""
        # Get all appointments for the doctor at the same time
        appointments = frappe.get_all("Appointment",
            filters={
                "doctor": self.doctor,
                "appointment_date": self.appointment_date,
                "appointment_time": self.appointment_time,
                "status": ["in", ["Scheduled", "Confirmed"]],
                "name": ["!=", self.name]
            }
        )
        
        return len(appointments) > 0
    
    def before_save(self):
        """Actions before saving"""
        if self.is_new():
            self.status = "Scheduled"
    
    def after_insert(self):
        """Actions after inserting"""
        self.create_notification()
        self.send_appointment_confirmation()
    
    def on_update(self):
        """Actions on update"""
        if self.has_value_changed("status"):
            self.handle_status_change()
    
    def on_trash(self):
        """Actions before deleting"""
        if self.status in ["Completed", "Checked In"]:
            frappe.throw(_("Cannot delete completed or checked-in appointments"))
    
    def create_notification(self):
        """Create notification for the appointment"""
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Appointment",
            "title": "New Appointment Created",
            "message": f"Appointment {self.name} has been created for {self.patient_name}",
            "for_user": self.doctor
        }).insert()
    
    def send_appointment_confirmation(self):
        """Send appointment confirmation"""
        if not self.send_notification:
            return
        
        if "Email" in self.notification_channels:
            self.send_email_confirmation()
        
        if "SMS" in self.notification_channels:
            self.send_sms_confirmation()
        
        if "WhatsApp" in self.notification_channels:
            self.send_whatsapp_confirmation()
    
    def send_email_confirmation(self):
        """Send email confirmation"""
        try:
            make(
                recipients=[self.patient_email],
                subject=f"Appointment Confirmation - {self.name}",
                content=self.get_email_content(),
                doctype=self.doctype,
                name=self.name
            )
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Appointment Email Error")
    
    def send_sms_confirmation(self):
        """Send SMS confirmation"""
        try:
            # Implement SMS sending logic here
            pass
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Appointment SMS Error")
    
    def send_whatsapp_confirmation(self):
        """Send WhatsApp confirmation"""
        try:
            # Implement WhatsApp sending logic here
            pass
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Appointment WhatsApp Error")
    
    def get_email_content(self):
        """Get email content for appointment confirmation"""
        return f"""
        Dear {self.patient_name},
        
        Your appointment has been confirmed:
        
        Appointment ID: {self.name}
        Date: {self.appointment_date}
        Time: {self.appointment_time}
        Doctor: {self.doctor_name}
        Department: {self.department}
        
        Please arrive 15 minutes before your scheduled time.
        
        Best regards,
        Healthcare Team
        """
    
    def handle_status_change(self):
        """Handle appointment status changes"""
        if self.status == "Confirmed":
            self.send_appointment_confirmation()
        elif self.status == "Cancelled":
            self.handle_cancellation()
        elif self.status == "Completed":
            self.handle_completion()
    
    def handle_cancellation(self):
        """Handle appointment cancellation"""
        # Create cancellation notification
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Appointment",
            "title": "Appointment Cancelled",
            "message": f"Appointment {self.name} has been cancelled",
            "for_user": self.doctor
        }).insert()
        
        # Send cancellation notification
        if self.send_notification:
            self.send_cancellation_notification()
    
    def handle_completion(self):
        """Handle appointment completion"""
        # Create completion notification
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Appointment",
            "title": "Appointment Completed",
            "message": f"Appointment {self.name} has been completed",
            "for_user": self.doctor
        }).insert()
        
        # Create follow-up appointment if needed
        if self.is_follow_up and self.follow_up_date:
            self.create_follow_up_appointment()
    
    def create_follow_up_appointment(self):
        """Create follow-up appointment"""
        follow_up = frappe.get_doc({
            "doctype": "Appointment",
            "patient": self.patient,
            "doctor": self.doctor,
            "department": self.department,
            "appointment_type": "Follow Up",
            "appointment_date": self.follow_up_date,
            "appointment_time": self.appointment_time,
            "duration": self.duration,
            "notes": self.follow_up_notes,
            "is_follow_up": 1
        })
        follow_up.insert()
    
    @frappe.whitelist()
    def get_available_slots(doctor, date):
        """Get available appointment slots for a doctor on a specific date"""
        try:
            # Get doctor's schedule
            schedule = frappe.get_all("Doctor Schedule",
                filters={
                    "doctor": doctor,
                    "schedule_date": date
                },
                fields=["from_time", "to_time"]
            )
            
            if not schedule:
                return []
            
            # Get booked appointments
            appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": doctor,
                    "appointment_date": date,
                    "status": ["in", ["Scheduled", "Confirmed"]]
                },
                fields=["appointment_time", "duration"]
            )
            
            # Calculate available slots
            available_slots = []
            for s in schedule:
                current_time = s.from_time
                while current_time < s.to_time:
                    slot_available = True
                    for apt in appointments:
                        if current_time == apt.appointment_time:
                            slot_available = False
                            break
                    
                    if slot_available:
                        available_slots.append(current_time)
                    
                    current_time = add_to_date(current_time, minutes=30)
            
            return available_slots
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Available Slots Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def reschedule_appointment(new_date, new_time):
        """Reschedule appointment to a new date and time"""
        try:
            self.appointment_date = new_date
            self.appointment_time = new_time
            
            if not self.is_doctor_available():
                frappe.throw(_("Doctor is not available at the selected time"))
            
            if self.has_scheduling_conflict():
                frappe.throw(_("There is a scheduling conflict at the selected time"))
            
            self.save()
            
            # Send rescheduling notification
            if self.send_notification:
                self.send_rescheduling_notification()
            
            return {"message": "Appointment rescheduled successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Reschedule Appointment Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def cancel_appointment(reason=None):
        """Cancel appointment with optional reason"""
        try:
            if self.status in ["Completed", "Checked In"]:
                frappe.throw(_("Cannot cancel completed or checked-in appointments"))
            
            self.status = "Cancelled"
            if reason:
                self.notes = f"Cancellation reason: {reason}"
            
            self.save()
            
            return {"message": "Appointment cancelled successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Cancel Appointment Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def check_in():
        """Check in patient for appointment"""
        try:
            if self.status != "Confirmed":
                frappe.throw(_("Only confirmed appointments can be checked in"))
            
            self.status = "Checked In"
            self.save()
            
            # Create check-in notification
            frappe.get_doc({
                "doctype": "Notification",
                "type": "Appointment",
                "title": "Patient Checked In",
                "message": f"Patient {self.patient_name} has checked in for appointment {self.name}",
                "for_user": self.doctor
            }).insert()
            
            return {"message": "Patient checked in successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Check In Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def complete_appointment():
        """Mark appointment as completed"""
        try:
            if self.status != "Checked In":
                frappe.throw(_("Only checked-in appointments can be completed"))
            
            self.status = "Completed"
            self.save()
            
            # Create completion notification
            frappe.get_doc({
                "doctype": "Notification",
                "type": "Appointment",
                "title": "Appointment Completed",
                "message": f"Appointment {self.name} has been completed",
                "for_user": self.doctor
            }).insert()
            
            return {"message": "Appointment completed successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Complete Appointment Error")
            frappe.throw(str(e))

    @frappe.whitelist()
    def get_patient_appointments():
        """Get patient's appointments"""
        try:
            appointments = frappe.get_all("Appointment",
                filters={"patient": frappe.session.user},
                fields=["name", "appointment_date", "appointment_time", "doctor_name",
                       "department", "appointment_type", "status", "notes"],
                order_by="appointment_date desc, appointment_time desc"
            )
            
            return appointments
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Patient Appointments Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_appointment_details(appointment):
        """Get appointment details"""
        try:
            appointment = frappe.get_doc("Appointment", appointment)
            
            # Check permissions
            if appointment.patient != frappe.session.user:
                frappe.throw(_("You don't have permission to view this appointment"))
            
            return {
                "name": appointment.name,
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.appointment_time,
                "doctor_name": appointment.doctor_name,
                "department": appointment.department,
                "appointment_type": appointment.appointment_type,
                "status": appointment.status,
                "notes": appointment.notes
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Appointment Details Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def cancel_appointment(appointment):
        """Cancel appointment"""
        try:
            appointment = frappe.get_doc("Appointment", appointment)
            
            # Check permissions
            if appointment.patient != frappe.session.user:
                frappe.throw(_("You don't have permission to cancel this appointment"))
            
            # Check if cancellation is allowed
            if appointment.status not in ["Scheduled", "Confirmed"]:
                frappe.throw(_("Cannot cancel appointment in current status"))
            
            appointment.status = "Cancelled"
            appointment.save()
            
            return {"message": "Appointment cancelled successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Cancel Appointment Error")
            frappe.throw(str(e)) 