import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate
from frappe.core.doctype.communication.email import make

class AppointmentWaitlist(Document):
    def validate(self):
        self.validate_patient()
        self.validate_department()
        self.validate_doctor()
        self.validate_preferred_date()
        self.set_patient_details()
        self.set_doctor_details()
    
    def validate_patient(self):
        """Validate patient details"""
        if not frappe.db.exists("Patient", self.patient):
            frappe.throw(_("Patient {0} does not exist").format(self.patient))
        
        patient = frappe.get_doc("Patient", self.patient)
        if not patient.is_active:
            frappe.throw(_("Patient {0} is not active").format(self.patient))
    
    def validate_department(self):
        """Validate department"""
        if not frappe.db.exists("Medical Department", self.department):
            frappe.throw(_("Department {0} does not exist").format(self.department))
    
    def validate_doctor(self):
        """Validate doctor details"""
        if self.doctor:
            if not frappe.db.exists("Doctor", self.doctor):
                frappe.throw(_("Doctor {0} does not exist").format(self.doctor))
            
            doctor = frappe.get_doc("Doctor", self.doctor)
            if not doctor.is_active:
                frappe.throw(_("Doctor {0} is not active").format(self.doctor))
            
            if doctor.department != self.department:
                frappe.throw(_("Doctor {0} does not belong to department {1}").format(
                    self.doctor, self.department))
    
    def validate_preferred_date(self):
        """Validate preferred date"""
        if getdate(self.preferred_date) < getdate():
            frappe.throw(_("Preferred date cannot be in the past"))
    
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
        if self.doctor:
            doctor = frappe.get_doc("Doctor", self.doctor)
            self.doctor_name = f"{doctor.first_name} {doctor.last_name}"
            self.specialization = doctor.specialization
    
    def before_save(self):
        """Actions before saving"""
        if self.is_new():
            self.status = "Pending"
    
    def on_update(self):
        """Actions on update"""
        if self.has_value_changed("status"):
            self.handle_status_change()
    
    def handle_status_change(self):
        """Handle status changes"""
        if self.status == "Notified":
            self.send_availability_notification()
        elif self.status == "Booked":
            self.handle_booking()
        elif self.status == "Cancelled":
            self.handle_cancellation()
    
    def send_availability_notification(self):
        """Send notification about available slot"""
        if not self.send_notification:
            return
        
        try:
            # Get available slots
            available_slots = self.get_available_slots()
            
            if not available_slots:
                return
            
            # Send notification through selected channels
            for channel in self.notification_channels:
                if channel == "Email":
                    self.send_email_notification(available_slots)
                elif channel == "SMS":
                    self.send_sms_notification(available_slots)
                elif channel == "WhatsApp":
                    self.send_whatsapp_notification(available_slots)
            
            self.last_notification_sent = now_datetime()
            self.save()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Send Availability Notification Error")
    
    def get_available_slots(self):
        """Get available appointment slots"""
        try:
            if self.doctor:
                # Get slots for specific doctor
                return frappe.get_doc("Appointment").get_available_slots(
                    self.doctor, self.preferred_date)
            else:
                # Get slots for department
                doctors = frappe.get_all("Doctor",
                    filters={"department": self.department, "is_active": 1},
                    fields=["name"]
                )
                
                available_slots = []
                for doctor in doctors:
                    slots = frappe.get_doc("Appointment").get_available_slots(
                        doctor.name, self.preferred_date)
                    available_slots.extend(slots)
                
                return available_slots
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Available Slots Error")
            return []
    
    def send_email_notification(self, available_slots):
        """Send email notification"""
        try:
            message = self.get_notification_message(available_slots)
            
            make(
                recipients=[self.patient_email],
                subject="Appointment Slot Available",
                content=message,
                doctype=self.doctype,
                name=self.name
            )
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Email Notification Error")
    
    def send_sms_notification(self, available_slots):
        """Send SMS notification"""
        try:
            # Implement SMS sending logic here
            pass
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "SMS Notification Error")
    
    def send_whatsapp_notification(self, available_slots):
        """Send WhatsApp notification"""
        try:
            # Implement WhatsApp sending logic here
            pass
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "WhatsApp Notification Error")
    
    def get_notification_message(self, available_slots):
        """Get notification message"""
        message = f"""
        Dear {self.patient_name},
        
        Appointment slots are now available for your waitlist request:
        
        Department: {self.department}
        Preferred Date: {self.preferred_date}
        
        Available Slots:
        """
        
        for slot in available_slots:
            message += f"\n- {slot}"
        
        message += """
        
        Please book your appointment as soon as possible to secure your preferred time.
        
        Best regards,
        Healthcare Team
        """
        
        return message
    
    def handle_booking(self):
        """Handle waitlist booking"""
        try:
            # Create appointment
            appointment = frappe.get_doc({
                "doctype": "Appointment",
                "patient": self.patient,
                "doctor": self.doctor,
                "department": self.department,
                "appointment_date": self.preferred_date,
                "appointment_time": self.preferred_time,
                "status": "Scheduled",
                "notes": f"Booked from waitlist {self.name}"
            })
            
            appointment.insert()
            
            # Send booking confirmation
            if self.send_notification:
                self.send_booking_confirmation(appointment)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Handle Booking Error")
    
    def handle_cancellation(self):
        """Handle waitlist cancellation"""
        try:
            # Send cancellation notification
            if self.send_notification:
                self.send_cancellation_notification()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Handle Cancellation Error")
    
    @frappe.whitelist()
    def check_availability(self):
        """Check for available slots"""
        try:
            available_slots = self.get_available_slots()
            
            if available_slots:
                self.status = "Notified"
                self.save()
                return {"message": "Available slots found", "slots": available_slots}
            else:
                return {"message": "No available slots found"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Check Availability Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def book_appointment(self, appointment_time):
        """Book appointment from waitlist"""
        try:
            if self.status != "Notified":
                frappe.throw(_("Cannot book appointment. Waitlist status must be 'Notified'"))
            
            self.preferred_time = appointment_time
            self.status = "Booked"
            self.save()
            
            return {"message": "Appointment booked successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Book Appointment Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def cancel_waitlist(self, reason=None):
        """Cancel waitlist entry"""
        try:
            if self.status == "Booked":
                frappe.throw(_("Cannot cancel booked waitlist entry"))
            
            self.status = "Cancelled"
            if reason:
                self.notes = f"Cancellation reason: {reason}"
            
            self.save()
            
            return {"message": "Waitlist entry cancelled successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Cancel Waitlist Error")
            frappe.throw(str(e)) 