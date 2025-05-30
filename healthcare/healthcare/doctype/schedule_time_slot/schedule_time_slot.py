import frappe
from frappe.model.document import Document

class ScheduleTimeSlot(Document):
    def validate(self):
        self.validate_times()
        self.validate_appointments()
    
    def validate_times(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                frappe.throw("Start time must be before end time")
            
            # Calculate duration
            start = frappe.utils.get_time(self.start_time)
            end = frappe.utils.get_time(self.end_time)
            duration = (end - start).total_seconds() / 60
            self.duration = int(duration)
    
    def validate_appointments(self):
        if self.max_appointments and self.appointments_booked:
            if self.appointments_booked > self.max_appointments:
                frappe.throw("Appointments booked cannot be greater than maximum appointments")
            
            if self.appointments_booked == self.max_appointments:
                self.is_available = 0 