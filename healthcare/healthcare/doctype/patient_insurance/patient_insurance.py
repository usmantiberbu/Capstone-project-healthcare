import frappe
from frappe.model.document import Document
from datetime import datetime

class PatientInsurance(Document):
    def validate(self):
        self.validate_dates()
        self.validate_coverage()
        self.set_names()
        self.check_expiry()
    
    def validate_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                frappe.throw("Start Date cannot be after End Date")
            
            if self.start_date < datetime.now().date():
                frappe.throw("Cannot set start date in the past")
    
    def validate_coverage(self):
        if self.coverage_amount and self.deductible_amount:
            if self.deductible_amount >= self.coverage_amount:
                frappe.throw("Deductible Amount cannot be greater than or equal to Coverage Amount")
        
        if self.co_pay_percentage and self.co_pay_percentage > 100:
            frappe.throw("Co-pay Percentage cannot be greater than 100%")
    
    def set_names(self):
        if self.patient:
            patient = frappe.get_doc("Patient", self.patient)
            self.patient_name = f"{patient.first_name} {patient.last_name}"
    
    def check_expiry(self):
        if self.end_date and self.end_date < datetime.now().date():
            self.status = "Expired"
    
    def on_submit(self):
        self.update_patient_insurance()
        self.send_notification()
    
    def update_patient_insurance(self):
        # Update patient's insurance information
        patient = frappe.get_doc("Patient", self.patient)
        patient.append("insurance_details", {
            "insurance_provider": self.insurance_provider,
            "policy_number": self.policy_number,
            "policy_type": self.policy_type,
            "coverage_type": self.coverage_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status
        })
        patient.save()
    
    def send_notification(self):
        # Notify patient about insurance status
        if self.patient:
            patient = frappe.get_doc("Patient", self.patient)
            if patient.email:
                frappe.sendmail(
                    recipients=patient.email,
                    subject=f"Insurance Policy {self.status} - {self.name}",
                    message=f"Your insurance policy {self.policy_number} has been {self.status.lower()}"
                ) 