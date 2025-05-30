import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_days, date_diff

class LeaveAllocation(Document):
    def validate(self):
        self.validate_dates()
        self.validate_overlap()
        self.calculate_leave_balance()
    
    def validate_dates(self):
        """Validate allocation dates"""
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_("From date cannot be after to date"))
        
        if getdate(self.from_date) < getdate():
            frappe.throw(_("Cannot allocate leaves in the past"))
    
    def validate_overlap(self):
        """Validate overlapping allocations"""
        overlapping = frappe.get_all("Leave Allocation",
            filters={
                "employee": self.employee,
                "leave_type": self.leave_type,
                "from_date": ["<=", self.to_date],
                "to_date": [">=", self.from_date],
                "name": ["!=", self.name]
            }
        )
        
        if overlapping:
            frappe.throw(_("Leave allocation overlaps with existing allocation"))
    
    def calculate_leave_balance(self):
        """Calculate leave balance"""
        # Get leaves taken
        leaves_taken = frappe.get_all("Doctor Leave",
            filters={
                "doctor": self.employee,
                "leave_type": self.leave_type,
                "status": "Approved",
                "from_date": [">=", self.from_date],
                "to_date": ["<=", self.to_date]
            },
            fields=["SUM(total_days) as total_days"]
        )
        
        self.leaves_taken = leaves_taken[0].total_days or 0
        self.leaves_remaining = self.total_leaves_allocated - self.leaves_taken
    
    def before_save(self):
        """Actions before saving"""
        self.calculate_leave_balance()
    
    def on_update(self):
        """Actions on update"""
        if self.has_value_changed("total_leaves_allocated"):
            self.calculate_leave_balance()
    
    @frappe.whitelist()
    def get_leave_balance(employee, leave_type):
        """Get leave balance for an employee"""
        try:
            # Get current allocation
            allocation = frappe.get_all("Leave Allocation",
                filters={
                    "employee": employee,
                    "leave_type": leave_type,
                    "from_date": ["<=", getdate()],
                    "to_date": [">=", getdate()]
                },
                fields=["total_leaves_allocated", "leaves_taken", "leaves_remaining"]
            )
            
            if not allocation:
                return 0
            
            return allocation[0].leaves_remaining
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Leave Balance Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_leave_history(employee):
        """Get leave history for an employee"""
        try:
            # Get all allocations
            allocations = frappe.get_all("Leave Allocation",
                filters={"employee": employee},
                fields=["name", "leave_type", "from_date", "to_date", 
                       "total_leaves_allocated", "leaves_taken", "leaves_remaining"],
                order_by="from_date desc"
            )
            
            # Get all leaves
            leaves = frappe.get_all("Doctor Leave",
                filters={"doctor": employee},
                fields=["name", "leave_type", "from_date", "to_date", 
                       "status", "reason", "approver", "approval_date"],
                order_by="from_date desc"
            )
            
            return {
                "allocations": allocations,
                "leaves": leaves
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Leave History Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def carry_forward_leaves():
        """Carry forward leaves to next year"""
        try:
            current_year = getdate().year
            next_year = current_year + 1
            
            # Get all allocations with carry forward
            allocations = frappe.get_all("Leave Allocation",
                filters={
                    "carry_forward": 1,
                    "to_date": ["<=", f"{current_year}-12-31"]
                }
            )
            
            for allocation in allocations:
                alloc = frappe.get_doc("Leave Allocation", allocation.name)
                
                # Create new allocation for next year
                new_allocation = frappe.get_doc({
                    "doctype": "Leave Allocation",
                    "employee": alloc.employee,
                    "leave_type": alloc.leave_type,
                    "from_date": f"{next_year}-01-01",
                    "to_date": f"{next_year}-12-31",
                    "total_leaves_allocated": alloc.carry_forward_leaves,
                    "carry_forward": 0
                })
                new_allocation.insert()
            
            return {"message": "Leaves carried forward successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Carry Forward Leaves Error")
            frappe.throw(str(e)) 