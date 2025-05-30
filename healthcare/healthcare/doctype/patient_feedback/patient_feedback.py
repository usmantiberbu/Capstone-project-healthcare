import frappe
from frappe.model.document import Document

class PatientFeedback(Document):
    def validate(self):
        self.validate_rating()
        self.set_names()
        self.validate_appointment()
    
    def validate_rating(self):
        if self.rating and (self.rating < 1 or self.rating > 5):
            frappe.throw("Rating must be between 1 and 5")
    
    def set_names(self):
        if self.patient:
            patient = frappe.get_doc("Patient", self.patient)
            self.patient_name = f"{patient.first_name} {patient.last_name}"
        
        if self.doctor:
            doctor = frappe.get_doc("Doctor", self.doctor)
            self.doctor_name = f"{doctor.first_name} {doctor.last_name}"
    
    def validate_appointment(self):
        if self.appointment:
            appointment = frappe.get_doc("Appointment", self.appointment)
            if appointment.patient != self.patient:
                frappe.throw("Appointment does not belong to the selected patient")
            if appointment.doctor != self.doctor:
                frappe.throw("Appointment does not belong to the selected doctor")
    
    def on_submit(self):
        self.update_doctor_rating()
        self.send_notification()
    
    def update_doctor_rating(self):
        # Update doctor's average rating
        doctor = frappe.get_doc("Doctor", self.doctor)
        
        # Get all approved feedback for this doctor
        feedbacks = frappe.get_all("Patient Feedback",
            filters={
                "doctor": self.doctor,
                "status": "Approved",
                "name": ["!=", self.name]
            },
            fields=["rating"]
        )
        
        # Calculate new average rating
        total_rating = sum(f.rating for f in feedbacks) + self.rating
        count = len(feedbacks) + 1
        average_rating = total_rating / count
        
        # Update doctor's rating
        doctor.average_rating = round(average_rating, 2)
        doctor.save()
    
    def send_notification(self):
        if self.status == "Approved":
            # Notify doctor about new feedback
            if self.doctor:
                doctor = frappe.get_doc("Doctor", self.doctor)
                if doctor.email:
                    frappe.sendmail(
                        recipients=doctor.email,
                        subject=f"New Patient Feedback - {self.name}",
                        message=f"You have received new feedback from {self.patient_name} with rating {self.rating}/5"
                    ) 