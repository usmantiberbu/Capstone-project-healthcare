import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class Waitlist(Document):
    def validate(self):
        self.validate_dates()
        self.validate_doctor()
        self.set_patient_name()
    
    def validate_dates(self):
        if self.preferred_date and getdate(self.preferred_date) < getdate():
            frappe.throw("Preferred date cannot be in the past")
    
    def validate_doctor(self):
        if self.doctor:
            doctor = frappe.get_doc("Doctor", self.doctor)
            if doctor.specialization != self.specialization:
                frappe.throw("Selected doctor's specialization does not match the required specialization")
    
    def set_patient_name(self):
        if self.patient:
            patient = frappe.get_doc("Patient", self.patient)
            self.patient_name = f"{patient.first_name} {patient.last_name}"
    
    def on_submit(self):
        if self.status == "Notified":
            self.notify_patient()
    
    def notify_patient(self):
        patient = frappe.get_doc("Patient", self.patient)
        if patient.email:
            frappe.sendmail(
                recipients=[patient.email],
                subject="Appointment Slot Available",
                message=f"""
                Dear {patient.first_name},
                
                An appointment slot is now available for your requested specialization.
                Please log in to your patient portal to schedule your appointment.
                
                Department: {self.department}
                Specialization: {self.specialization}
                Preferred Date: {self.preferred_date}
                Preferred Time: {self.preferred_time}
                
                Best regards,
                Healthcare Team
                """,
                now=True
            )
    
    @frappe.whitelist()
    def check_availability(self):
        """Check for available slots and notify patient if found"""
        if self.status != "Pending":
            frappe.throw("Can only check availability for pending waitlist entries")
        
        # Get available slots
        available_slots = frappe.get_all("Doctor Schedule",
            filters={
                "department": self.department,
                "specialization": self.specialization,
                "schedule_date": [">=", getdate()],
                "status": "Active"
            },
            fields=["name", "doctor", "schedule_date", "time_slots"]
        )
        
        if available_slots:
            self.status = "Notified"
            self.save()
            self.notify_patient()
            return True
        
        return False
    
    @frappe.whitelist()
    def schedule_appointment(self, schedule_name, time_slot):
        """Schedule an appointment from the waitlist"""
        if self.status != "Notified":
            frappe.throw("Can only schedule appointments for notified waitlist entries")
        
        schedule = frappe.get_doc("Doctor Schedule", schedule_name)
        
        # Create new appointment
        appointment = frappe.new_doc("Appointment")
        appointment.patient = self.patient
        appointment.doctor = schedule.doctor
        appointment.appointment_date = schedule.schedule_date
        appointment.appointment_time = time_slot
        appointment.status = "Scheduled"
        appointment.save()
        
        # Update waitlist status
        self.status = "Scheduled"
        self.save()
        
        return appointment.name 