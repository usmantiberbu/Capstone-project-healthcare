import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, add_days, date_diff, now_datetime
from frappe.core.doctype.communication.email import make

class DoctorLeave(Document):
    def validate(self):
        self.validate_dates()
        self.validate_leave_balance()
        self.validate_overlap()
        self.set_status()
    
    def validate_dates(self):
        """Validate leave dates"""
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_("From date cannot be after to date"))
        
        if getdate(self.from_date) < getdate():
            frappe.throw(_("Cannot apply for leave in the past"))
        
        if self.half_day and not self.half_day_date:
            frappe.throw(_("Please select half day date"))
        
        if self.half_day and self.half_day_date:
            if not (getdate(self.from_date) <= getdate(self.half_day_date) <= getdate(self.to_date)):
                frappe.throw(_("Half day date must be between from date and to date"))
    
    def validate_leave_balance(self):
        """Validate leave balance"""
        if self.status == "Draft":
            return
        
        leave_balance = self.get_leave_balance()
        total_days = self.get_total_days()
        
        if leave_balance < total_days:
            frappe.throw(_("Insufficient leave balance. Available: {0}, Required: {1}").format(
                leave_balance, total_days))
    
    def validate_overlap(self):
        """Validate overlapping leaves"""
        if self.status == "Draft":
            return
        
        overlapping_leaves = frappe.get_all("Doctor Leave",
            filters={
                "doctor": self.doctor,
                "status": ["in", ["Pending", "Approved"]],
                "from_date": ["<=", self.to_date],
                "to_date": [">=", self.from_date],
                "name": ["!=", self.name]
            }
        )
        
        if overlapping_leaves:
            frappe.throw(_("Leave application overlaps with existing leave"))
    
    def set_status(self):
        """Set initial status"""
        if self.is_new():
            self.status = "Draft"
    
    def get_total_days(self):
        """Calculate total leave days"""
        total_days = date_diff(self.to_date, self.from_date) + 1
        
        if self.half_day:
            total_days -= 0.5
        
        return total_days
    
    def get_leave_balance(self):
        """Get leave balance for the doctor"""
        # Get leave allocation
        allocation = frappe.get_all("Leave Allocation",
            filters={
                "employee": self.doctor,
                "leave_type": self.leave_type,
                "from_date": ["<=", self.from_date],
                "to_date": [">=", self.to_date]
            },
            fields=["total_leaves_allocated"]
        )
        
        if not allocation:
            return 0
        
        # Get leaves taken
        leaves_taken = frappe.get_all("Doctor Leave",
            filters={
                "doctor": self.doctor,
                "leave_type": self.leave_type,
                "status": "Approved",
                "from_date": [">=", allocation[0].from_date],
                "to_date": ["<=", allocation[0].to_date]
            },
            fields=["SUM(total_days) as total_days"]
        )
        
        return allocation[0].total_leaves_allocated - (leaves_taken[0].total_days or 0)
    
    def before_save(self):
        """Actions before saving"""
        if self.is_new():
            self.set_status()
    
    def on_update(self):
        """Actions on update"""
        if self.has_value_changed("status"):
            self.handle_status_change()
    
    def handle_status_change(self):
        """Handle status changes"""
        if self.status == "Pending":
            self.send_approval_request()
        elif self.status == "Approved":
            self.handle_approval()
        elif self.status == "Rejected":
            self.handle_rejection()
        elif self.status == "Cancelled":
            self.handle_cancellation()
    
    def send_approval_request(self):
        """Send leave approval request"""
        # Get approver
        approver = frappe.get_value("Healthcare Settings", "Healthcare Settings", "leave_approver")
        if not approver:
            frappe.throw(_("Leave approver not set in Healthcare Settings"))
        
        # Create notification
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Leave Request",
            "title": "Leave Approval Request",
            "message": f"Leave request from {self.doctor} needs your approval",
            "for_user": approver
        }).insert()
        
        # Send email
        make(
            recipients=[approver],
            subject=f"Leave Approval Request - {self.name}",
            content=self.get_approval_email_content(),
            doctype=self.doctype,
            name=self.name
        )
    
    def handle_approval(self):
        """Handle leave approval"""
        self.approver = frappe.session.user
        self.approval_date = now_datetime()
        
        # Update doctor's schedule
        self.update_doctor_schedule()
        
        # Send approval notification
        self.send_approval_notification()
    
    def handle_rejection(self):
        """Handle leave rejection"""
        self.approver = frappe.session.user
        self.approval_date = now_datetime()
        
        # Send rejection notification
        self.send_rejection_notification()
    
    def handle_cancellation(self):
        """Handle leave cancellation"""
        # Send cancellation notification
        self.send_cancellation_notification()
    
    def update_doctor_schedule(self):
        """Update doctor's schedule for leave period"""
        # Get all appointments in leave period
        appointments = frappe.get_all("Appointment",
            filters={
                "doctor": self.doctor,
                "appointment_date": ["between", [self.from_date, self.to_date]],
                "status": ["in", ["Scheduled", "Confirmed"]]
            }
        )
        
        # Cancel or reschedule appointments
        for appointment in appointments:
            apt = frappe.get_doc("Appointment", appointment.name)
            apt.status = "Cancelled"
            apt.notes = f"Cancelled due to doctor leave: {self.name}"
            apt.save()
    
    def get_approval_email_content(self):
        """Get email content for approval request"""
        return f"""
        Dear {self.approver},
        
        A leave request requires your approval:
        
        Doctor: {self.doctor}
        Leave Type: {self.leave_type}
        From Date: {self.from_date}
        To Date: {self.to_date}
        Reason: {self.reason}
        
        Please review and take appropriate action.
        
        Best regards,
        Healthcare Team
        """
    
    def send_approval_notification(self):
        """Send approval notification"""
        # Create notification
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Leave Request",
            "title": "Leave Request Approved",
            "message": f"Your leave request {self.name} has been approved",
            "for_user": self.doctor
        }).insert()
        
        # Send email
        make(
            recipients=[self.doctor],
            subject=f"Leave Request Approved - {self.name}",
            content=self.get_approval_notification_content(),
            doctype=self.doctype,
            name=self.name
        )
    
    def send_rejection_notification(self):
        """Send rejection notification"""
        # Create notification
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Leave Request",
            "title": "Leave Request Rejected",
            "message": f"Your leave request {self.name} has been rejected",
            "for_user": self.doctor
        }).insert()
        
        # Send email
        make(
            recipients=[self.doctor],
            subject=f"Leave Request Rejected - {self.name}",
            content=self.get_rejection_notification_content(),
            doctype=self.doctype,
            name=self.name
        )
    
    def send_cancellation_notification(self):
        """Send cancellation notification"""
        # Create notification
        frappe.get_doc({
            "doctype": "Notification",
            "type": "Leave Request",
            "title": "Leave Request Cancelled",
            "message": f"Your leave request {self.name} has been cancelled",
            "for_user": self.doctor
        }).insert()
        
        # Send email
        make(
            recipients=[self.doctor],
            subject=f"Leave Request Cancelled - {self.name}",
            content=self.get_cancellation_notification_content(),
            doctype=self.doctype,
            name=self.name
        )
    
    def get_approval_notification_content(self):
        """Get email content for approval notification"""
        return f"""
        Dear {self.doctor},
        
        Your leave request has been approved:
        
        Leave Type: {self.leave_type}
        From Date: {self.from_date}
        To Date: {self.to_date}
        Reason: {self.reason}
        
        Best regards,
        Healthcare Team
        """
    
    def get_rejection_notification_content(self):
        """Get email content for rejection notification"""
        return f"""
        Dear {self.doctor},
        
        Your leave request has been rejected:
        
        Leave Type: {self.leave_type}
        From Date: {self.from_date}
        To Date: {self.to_date}
        Reason: {self.reason}
        Rejection Remarks: {self.approval_remarks}
        
        Best regards,
        Healthcare Team
        """
    
    def get_cancellation_notification_content(self):
        """Get email content for cancellation notification"""
        return f"""
        Dear {self.doctor},
        
        Your leave request has been cancelled:
        
        Leave Type: {self.leave_type}
        From Date: {self.from_date}
        To Date: {self.to_date}
        Reason: {self.reason}
        
        Best regards,
        Healthcare Team
        """
    
    @frappe.whitelist()
    def get_leave_balance(doctor, leave_type):
        """Get leave balance for a doctor"""
        try:
            # Get leave allocation
            allocation = frappe.get_all("Leave Allocation",
                filters={
                    "employee": doctor,
                    "leave_type": leave_type,
                    "from_date": ["<=", getdate()],
                    "to_date": [">=", getdate()]
                },
                fields=["total_leaves_allocated"]
            )
            
            if not allocation:
                return 0
            
            # Get leaves taken
            leaves_taken = frappe.get_all("Doctor Leave",
                filters={
                    "doctor": doctor,
                    "leave_type": leave_type,
                    "status": "Approved",
                    "from_date": [">=", allocation[0].from_date],
                    "to_date": ["<=", allocation[0].to_date]
                },
                fields=["SUM(total_days) as total_days"]
            )
            
            return allocation[0].total_leaves_allocated - (leaves_taken[0].total_days or 0)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Leave Balance Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_leave_history(doctor):
        """Get leave history for a doctor"""
        try:
            leaves = frappe.get_all("Doctor Leave",
                filters={"doctor": doctor},
                fields=["name", "leave_type", "from_date", "to_date", 
                       "status", "reason", "approver", "approval_date"],
                order_by="from_date desc"
            )
            
            return leaves
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Leave History Error")
            frappe.throw(str(e)) 