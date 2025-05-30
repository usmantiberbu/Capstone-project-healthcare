import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, add_to_date

class DepartmentSchedule(Document):
    def validate(self):
        self.validate_timings()
        self.calculate_duration()
        self.validate_break_time()
        self.validate_max_appointments()
    
    def validate_timings(self):
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                frappe.throw("Start time must be before end time")
    
    def calculate_duration(self):
        if self.start_time and self.end_time:
            start = get_datetime(self.start_time)
            end = get_datetime(self.end_time)
            self.duration = int((end - start).total_seconds() / 60)
    
    def validate_break_time(self):
        if self.break_time and self.start_time and self.end_time:
            if not (self.start_time <= self.break_time <= self.end_time):
                frappe.throw("Break time must be between start and end time")
            
            if self.break_duration and self.break_duration > self.duration:
                frappe.throw("Break duration cannot be greater than total duration")
    
    def validate_max_appointments(self):
        if self.max_appointments and self.max_appointments < 0:
            frappe.throw("Maximum appointments cannot be negative")
    
    def on_update(self):
        self.update_department_schedule()
    
    def update_department_schedule(self):
        # Update department's operating hours
        department = frappe.get_doc("Department", self.department)
        department.save()
        
        # Notify about schedule changes
        frappe.publish_realtime('department_schedule_updated', {
            'department': self.department,
            'day': self.day_of_week,
            'schedule': {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'is_working_day': self.is_working_day
            }
        })
    
    def get_available_slots(self, date):
        if not self.is_working_day:
            return 0
        
        # Calculate available slots considering break time
        total_duration = self.duration
        if self.break_duration:
            total_duration -= self.break_duration
        
        # Get existing appointments for the day
        existing_appointments = frappe.get_all("Appointment",
            filters={
                "department": self.department,
                "appointment_date": date,
                "status": ["!=", "Cancelled"]
            },
            fields=["appointment_time", "duration"]
        )
        
        # Calculate used time slots
        used_slots = sum(apt.duration for apt in existing_appointments)
        
        # Calculate available slots
        available_slots = (total_duration - used_slots) // 30  # Assuming 30-minute slots
        return max(0, min(available_slots, self.max_appointments)) 