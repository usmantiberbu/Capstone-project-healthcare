import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_days, date_diff, get_datetime
from datetime import datetime, timedelta

class Doctor(Document):
    def validate(self):
        self.validate_department()
        self.validate_specialization()
        self.validate_contact_details()
    
    def validate_department(self):
        """Validate department exists"""
        if self.department and not frappe.db.exists("Medical Department", self.department):
            frappe.throw(_("Department {0} does not exist").format(self.department))
    
    def validate_specialization(self):
        """Validate specialization"""
        if not self.specialization:
            frappe.throw(_("Specialization is required"))
    
    def validate_contact_details(self):
        """Validate contact details"""
        if not self.email and not self.phone:
            frappe.throw(_("Either email or phone is required"))
    
    @frappe.whitelist()
    def get_doctor_metrics(self, date_range="month"):
        """Get doctor performance metrics"""
        try:
            # Get date range
            start_date, end_date = self.get_date_range(date_range)
            
            # Get appointments
            appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": ["between", [start_date, end_date]]
                },
                fields=["name", "status", "appointment_date", "appointment_time"]
            )
            
            # Get previous period for comparison
            prev_start_date, prev_end_date = self.get_date_range(date_range, previous=True)
            prev_appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": ["between", [prev_start_date, prev_end_date]]
                },
                fields=["name", "status"]
            )
            
            # Calculate metrics
            total_appointments = len(appointments)
            completed_appointments = len([a for a in appointments if a.status == "Completed"])
            prev_total = len(prev_appointments)
            
            # Calculate trends
            appointment_trend = self.calculate_trend(total_appointments, prev_total)
            
            # Get patient ratings
            ratings = frappe.get_all("Patient Feedback",
                filters={
                    "doctor": self.name,
                    "creation": ["between", [start_date, end_date]]
                },
                fields=["rating"]
            )
            
            avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else 0
            
            # Get wait times
            wait_times = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": ["between", [start_date, end_date]],
                    "status": "Completed"
                },
                fields=["wait_time"]
            )
            
            avg_wait_time = sum(w.wait_time for w in wait_times) / len(wait_times) if wait_times else 0
            
            return {
                "total_appointments": total_appointments,
                "patients_seen": completed_appointments,
                "average_rating": avg_rating,
                "average_wait_time": round(avg_wait_time, 1),
                "appointment_trend": appointment_trend,
                "patients_trend": self.calculate_trend(completed_appointments, len([a for a in prev_appointments if a.status == "Completed"])),
                "rating_trend": self.calculate_trend(avg_rating, self.get_previous_rating(prev_start_date, prev_end_date)),
                "wait_time_trend": self.calculate_trend(avg_wait_time, self.get_previous_wait_time(prev_start_date, prev_end_date))
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Doctor Metrics Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_appointment_distribution(self):
        """Get appointment distribution by status"""
        try:
            # Get appointments for current month
            start_date = getdate().replace(day=1)
            end_date = getdate()
            
            appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": ["between", [start_date, end_date]]
                },
                fields=["status"]
            )
            
            # Count by status
            status_counts = {}
            for appointment in appointments:
                status_counts[appointment.status] = status_counts.get(appointment.status, 0) + 1
            
            return {
                "labels": list(status_counts.keys()),
                "data": list(status_counts.values())
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Appointment Distribution Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_patient_demographics(self):
        """Get patient demographics"""
        try:
            # Get appointments for current month
            start_date = getdate().replace(day=1)
            end_date = getdate()
            
            appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": ["between", [start_date, end_date]]
                },
                fields=["patient"]
            )
            
            # Get patient details
            patient_ages = []
            for appointment in appointments:
                patient = frappe.get_doc("Patient", appointment.patient)
                age = date_diff(getdate(), patient.dob) / 365
                patient_ages.append(age)
            
            # Group by age ranges
            age_ranges = {
                "0-18": 0,
                "19-30": 0,
                "31-50": 0,
                "51-70": 0,
                "70+": 0
            }
            
            for age in patient_ages:
                if age <= 18:
                    age_ranges["0-18"] += 1
                elif age <= 30:
                    age_ranges["19-30"] += 1
                elif age <= 50:
                    age_ranges["31-50"] += 1
                elif age <= 70:
                    age_ranges["51-70"] += 1
                else:
                    age_ranges["70+"] += 1
            
            return {
                "labels": list(age_ranges.keys()),
                "data": list(age_ranges.values())
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Patient Demographics Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_today_schedule(self):
        """Get today's schedule"""
        try:
            today = getdate()
            
            appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": today
                },
                fields=["name", "patient", "appointment_time", "appointment_type", "status"],
                order_by="appointment_time"
            )
            
            schedule = []
            for appointment in appointments:
                schedule.append({
                    "time": get_datetime(appointment.appointment_time).strftime("%I:%M %p"),
                    "patient": frappe.get_value("Patient", appointment.patient, "patient_name"),
                    "type": appointment.appointment_type,
                    "status": appointment.status
                })
            
            return schedule
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Today Schedule Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_recent_activity(self):
        """Get recent activity"""
        try:
            # Get recent appointments
            appointments = frappe.get_all("Appointment",
                filters={
                    "doctor": self.name,
                    "appointment_date": ["<=", getdate()]
                },
                fields=["name", "patient", "appointment_date", "appointment_time", "status"],
                order_by="appointment_date desc, appointment_time desc",
                limit=5
            )
            
            # Get recent feedback
            feedback = frappe.get_all("Patient Feedback",
                filters={"doctor": self.name},
                fields=["name", "patient", "rating", "creation"],
                order_by="creation desc",
                limit=5
            )
            
            # Combine and sort activities
            activities = []
            
            for appointment in appointments:
                activities.append({
                    "icon": "fa-calendar-check",
                    "text": f"Appointment with {frappe.get_value('Patient', appointment.patient, 'patient_name')} - {appointment.status}",
                    "time": get_datetime(appointment.appointment_date).strftime("%Y-%m-%d %I:%M %p")
                })
            
            for item in feedback:
                activities.append({
                    "icon": "fa-star",
                    "text": f"Received {item.rating} star rating from {frappe.get_value('Patient', item.patient, 'patient_name')}",
                    "time": get_datetime(item.creation).strftime("%Y-%m-%d %I:%M %p")
                })
            
            # Sort by time
            activities.sort(key=lambda x: get_datetime(x["time"]), reverse=True)
            
            return activities[:5]
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Recent Activity Error")
            frappe.throw(str(e))
    
    def get_date_range(self, date_range, previous=False):
        """Get date range for metrics"""
        today = getdate()
        
        if date_range == "today":
            start_date = today
            end_date = today
        elif date_range == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif date_range == "month":
            start_date = today.replace(day=1)
            end_date = today
        else:  # year
            start_date = today.replace(month=1, day=1)
            end_date = today
        
        if previous:
            days = (end_date - start_date).days + 1
            start_date = start_date - timedelta(days=days)
            end_date = start_date + timedelta(days=days-1)
        
        return start_date, end_date
    
    def calculate_trend(self, current, previous):
        """Calculate trend percentage"""
        if not previous:
            return 0
        return round(((current - previous) / previous) * 100, 1)
    
    def get_previous_rating(self, start_date, end_date):
        """Get average rating for previous period"""
        ratings = frappe.get_all("Patient Feedback",
            filters={
                "doctor": self.name,
                "creation": ["between", [start_date, end_date]]
            },
            fields=["rating"]
        )
        
        return sum(r.rating for r in ratings) / len(ratings) if ratings else 0
    
    def get_previous_wait_time(self, start_date, end_date):
        """Get average wait time for previous period"""
        wait_times = frappe.get_all("Appointment",
            filters={
                "doctor": self.name,
                "appointment_date": ["between", [start_date, end_date]],
                "status": "Completed"
            },
            fields=["wait_time"]
        )
        
        return sum(w.wait_time for w in wait_times) / len(wait_times) if wait_times else 0
    
    @frappe.whitelist()
    def get_doctors(department=None):
        """Get doctors by department"""
        try:
            filters = {"is_active": 1}
            if department:
                filters["department"] = department
            
            doctors = frappe.get_all("Doctor",
                filters=filters,
                fields=["name", "first_name", "last_name", "specialization", 
                       "department", "email", "phone", "availability"],
                order_by="first_name, last_name"
            )
            
            # Get department names
            for doctor in doctors:
                department = frappe.get_doc("Medical Department", doctor.department)
                doctor.department_name = department.department_name
            
            return doctors
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Doctors Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_doctor_details(doctor):
        """Get doctor details"""
        try:
            doctor = frappe.get_doc("Doctor", doctor)
            
            # Get department details
            department = frappe.get_doc("Medical Department", doctor.department)
            
            # Get doctor's schedule
            schedule = frappe.get_all("Doctor Schedule",
                filters={"doctor": doctor.name},
                fields=["day", "start_time", "end_time", "duration"]
            )
            
            return {
                "name": doctor.name,
                "first_name": doctor.first_name,
                "last_name": doctor.last_name,
                "specialization": doctor.specialization,
                "department": {
                    "name": department.name,
                    "department_name": department.department_name,
                    "description": department.description
                },
                "email": doctor.email,
                "phone": doctor.phone,
                "availability": doctor.availability,
                "schedule": schedule
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Doctor Details Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_doctor_schedule(doctor, date):
        """Get doctor's schedule for a specific date"""
        try:
            # Get doctor's schedule for the day
            day = frappe.utils.getdate(date).strftime("%A")
            schedule = frappe.get_all("Doctor Schedule",
                filters={
                    "doctor": doctor,
                    "day": day
                },
                fields=["start_time", "end_time", "duration"]
            )
            
            if not schedule:
                return []
            
            # Get booked appointments
            booked_slots = frappe.get_all("Appointment",
                filters={
                    "doctor": doctor,
                    "appointment_date": date,
                    "status": ["in", ["Scheduled", "Confirmed"]]
                },
                fields=["appointment_time"]
            )
            
            booked_times = [slot.appointment_time for slot in booked_slots]
            
            # Generate available slots
            available_slots = []
            for slot in schedule:
                current_time = slot.start_time
                while current_time + slot.duration <= slot.end_time:
                    if current_time not in booked_times:
                        available_slots.append({
                            "time": current_time.strftime("%H:%M"),
                            "duration": slot.duration
                        })
                    current_time = add_to_date(current_time, minutes=slot.duration)
            
            return available_slots
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Doctor Schedule Error")
            frappe.throw(str(e))
    
    def on_update(self):
        self.update_availability()
    
    def update_availability(self):
        # Update doctor's availability in the system
        frappe.publish_realtime('doctor_availability_updated', {
            'doctor': self.name,
            'availability': self.get_availability()
        })
    
    def get_availability(self):
        # Get doctor's current availability
        availability = {
            'working_hours': self.working_hours,
            'leave_records': self.leave_records
        }
        return availability 