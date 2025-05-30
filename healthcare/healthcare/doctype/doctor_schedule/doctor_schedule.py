import frappe
from frappe.model.document import Document
from frappe.utils import getdate, get_time, add_days, add_to_date
from datetime import datetime, timedelta

class DoctorSchedule(Document):
    def validate(self):
        self.validate_schedule_date()
        self.validate_doctor_availability()
        self.validate_time_slots()
        self.set_doctor_name()
    
    def validate_schedule_date(self):
        if getdate(self.schedule_date) < getdate():
            frappe.throw("Schedule date cannot be in the past")
    
    def validate_doctor_availability(self):
        # Check if doctor is on leave
        leave_records = frappe.get_all("Doctor Leave",
            filters={
                "doctor": self.doctor,
                "from_date": ["<=", self.schedule_date],
                "to_date": [">=", self.schedule_date],
                "status": "Approved"
            }
        )
        if leave_records:
            frappe.throw("Doctor is on leave for the selected date")
        
        # Check for existing schedule
        existing_schedule = frappe.get_all("Doctor Schedule",
            filters={
                "doctor": self.doctor,
                "schedule_date": self.schedule_date,
                "name": ["!=", self.name],
                "status": "Active"
            }
        )
        if existing_schedule:
            frappe.throw("Doctor already has a schedule for this date")
    
    def validate_time_slots(self):
        for slot in self.schedule_times:
            if slot.start_time >= slot.end_time:
                frappe.throw("Start time must be before end time")
            
            # Calculate duration
            start = datetime.strptime(str(slot.start_time), "%H:%M:%S")
            end = datetime.strptime(str(slot.end_time), "%H:%M:%S")
            duration = (end - start).total_seconds() / 60
            slot.duration = int(duration)
            
            # Validate maximum appointments
            if slot.max_appointments < 1:
                frappe.throw("Maximum appointments must be at least 1")
            
            # Check for overlapping appointments
            self.check_overlapping_appointments(slot)
    
    def check_overlapping_appointments(self, slot):
        overlapping = frappe.get_all("Appointment",
            filters={
                "doctor": self.doctor,
                "appointment_date": self.schedule_date,
                "appointment_time": ["between", [slot.start_time, slot.end_time]],
                "status": ["!=", "Cancelled"]
            }
        )
        if overlapping:
            frappe.throw(f"Time slot {slot.start_time} to {slot.end_time} has overlapping appointments")
    
    def set_doctor_name(self):
        if self.doctor:
            doctor = frappe.get_doc("Doctor", self.doctor)
            self.doctor_name = f"{doctor.first_name} {doctor.last_name}"
    
    def on_update(self):
        self.update_doctor_availability()
        self.notify_doctor()
    
    def update_doctor_availability(self):
        frappe.publish_realtime('doctor_schedule_updated', {
            'doctor': self.doctor,
            'date': self.schedule_date,
            'status': self.status
        })
    
    def notify_doctor(self):
        if self.status == "Active":
            doctor = frappe.get_doc("Doctor", self.doctor)
            if doctor.email:
                frappe.sendmail(
                    recipients=[doctor.email],
                    subject="Schedule Update",
                    message=f"Your schedule for {self.schedule_date} has been updated.",
                    now=True
                )
    
    def get_available_slots(self, date):
        """Get available time slots for a specific date"""
        slots = []
        for slot in self.schedule_times:
            if slot.is_available and slot.appointments_booked < slot.max_appointments:
                slots.append({
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'duration': slot.duration,
                    'available_slots': slot.max_appointments - slot.appointments_booked
                })
        return slots 