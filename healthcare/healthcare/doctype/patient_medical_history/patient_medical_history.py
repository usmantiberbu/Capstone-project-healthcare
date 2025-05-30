import frappe
from frappe.model.document import Document

class PatientMedicalHistory(Document):
    def validate(self):
        self.validate_date()
        self.validate_patient()
    
    def validate_date(self):
        if self.date:
            if frappe.utils.getdate(self.date) > frappe.utils.today():
                frappe.throw("Date cannot be in the future")
    
    def validate_patient(self):
        if self.patient:
            if not frappe.db.exists("Patient", self.patient):
                frappe.throw("Patient does not exist")
    
    def on_submit(self):
        self.update_patient_record()
    
    def update_patient_record(self):
        if self.patient:
            patient = frappe.get_doc("Patient", self.patient)
            patient.append("medical_history_table", {
                "date": self.date,
                "description": self.description,
                "diagnosis": self.diagnosis,
                "treatment": self.treatment,
                "prescription": self.prescription
            })
            patient.save() 