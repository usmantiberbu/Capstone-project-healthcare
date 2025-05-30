import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, add_days, date_diff
from frappe.core.doctype.file.file import File
from frappe.permissions import has_permission

class MedicalRecord(Document):
    def validate(self):
        self.validate_patient()
        self.validate_appointment()
        self.validate_permissions()
        self.set_patient_details()
        self.validate_attachments()
    
    def validate_patient(self):
        """Validate patient exists and is active"""
        if not frappe.db.exists("Patient", self.patient):
            frappe.throw(_("Patient {0} does not exist").format(self.patient))
        
        if not frappe.get_value("Patient", self.patient, "is_active"):
            frappe.throw(_("Patient {0} is not active").format(self.patient))
    
    def validate_appointment(self):
        """Validate linked appointment exists"""
        if self.appointment and not frappe.db.exists("Appointment", self.appointment):
            frappe.throw(_("Appointment {0} does not exist").format(self.appointment))
    
    def validate_permissions(self):
        """Validate access permissions"""
        if self.access_level == "Restricted":
            if not self.allowed_roles:
                frappe.throw(_("Please specify allowed roles for restricted access"))
    
    def set_patient_details(self):
        """Set patient details from Patient DocType"""
        if self.patient:
            patient = frappe.get_doc("Patient", self.patient)
            self.patient_name = patient.patient_name
            self.patient_age = date_diff(getdate(), patient.dob) / 365
            self.patient_gender = patient.gender
    
    def validate_attachments(self):
        """Validate attachments exist"""
        if self.attachments:
            for attachment in self.attachments:
                if not frappe.db.exists("File", attachment.file):
                    frappe.throw(_("File {0} does not exist").format(attachment.file))
    
    def before_save(self):
        """Actions before saving"""
        self.handle_versioning()
    
    def handle_versioning(self):
        """Handle record versioning"""
        if not self.is_new():
            # Create history entry
            self.create_history_entry()
            
            # Update version
            self.version = (self.version or 0) + 1
    
    def create_history_entry(self):
        """Create history entry for changes"""
        changes = self.get_changes()
        if changes:
            self.append("history", {
                "version": self.version,
                "action": "Updated",
                "user": frappe.session.user,
                "timestamp": now_datetime(),
                "changes": changes
            })
    
    def get_changes(self):
        """Get changes made in current version"""
        changes = []
        for field in self.meta.get("fields"):
            if self.has_value_changed(field.fieldname):
                changes.append({
                    "field": field.fieldname,
                    "old_value": self.get_doc_before_save().get(field.fieldname),
                    "new_value": self.get(field.fieldname)
                })
        return str(changes)
    
    def on_trash(self):
        """Actions on deletion"""
        # Archive attachments
        if self.attachments:
            for attachment in self.attachments:
                file = frappe.get_doc("File", attachment.file)
                file.archive()
    
    @frappe.whitelist()
    def get_patient_records(patient):
        """Get all medical records for a patient"""
        try:
            records = frappe.get_all("Medical Record",
                filters={"patient": patient},
                fields=["name", "record_type", "record_date", "version", 
                       "access_level", "created_by", "creation"],
                order_by="record_date desc, creation desc"
            )
            
            # Filter based on permissions
            filtered_records = []
            for record in records:
                if record.access_level == "Public":
                    filtered_records.append(record)
                elif record.access_level == "Restricted":
                    if frappe.has_permission("Medical Record", "read", record.name):
                        filtered_records.append(record)
            
            return filtered_records
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Patient Records Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def get_record_details(name):
        """Get detailed information about a medical record"""
        try:
            record = frappe.get_doc("Medical Record", name)
            
            # Check permissions
            if record.access_level == "Restricted":
                if not frappe.has_permission("Medical Record", "read", name):
                    frappe.throw(_("You don't have permission to access this record"))
            
            # Get attachments
            attachments = []
            if record.attachments:
                for attachment in record.attachments:
                    file = frappe.get_doc("File", attachment.file)
                    attachments.append({
                        "name": file.name,
                        "file_name": file.file_name,
                        "file_url": file.file_url,
                        "file_size": file.file_size,
                        "content_type": file.content_type
                    })
            
            # Get history
            history = []
            if record.history:
                for entry in record.history:
                    history.append({
                        "version": entry.version,
                        "action": entry.action,
                        "user": entry.user,
                        "timestamp": entry.timestamp,
                        "changes": entry.changes
                    })
            
            return {
                "name": record.name,
                "patient": record.patient,
                "patient_name": record.patient_name,
                "record_type": record.record_type,
                "record_date": record.record_date,
                "version": record.version,
                "access_level": record.access_level,
                "attachments": attachments,
                "history": history,
                "created_by": record.created_by,
                "creation": record.creation
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Get Record Details Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def add_attachment(self, file_name, file_url, content_type=None):
        """Add attachment to record"""
        try:
            # Create folder if not exists
            folder = f"Medical Records/{self.patient}"
            if not frappe.db.exists("File", {"is_folder": 1, "file_name": folder}):
                folder_doc = frappe.get_doc({
                    "doctype": "File",
                    "file_name": folder,
                    "is_folder": 1,
                    "folder": "Home"
                })
                folder_doc.insert()
            
            # Create file
            file = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "file_url": file_url,
                "content_type": content_type,
                "folder": folder,
                "is_private": self.access_level == "Restricted"
            })
            file.insert()
            
            # Add to attachments
            self.append("attachments", {
                "file": file.name,
                "file_name": file_name,
                "file_url": file_url
            })
            self.save()
            
            return {"message": "Attachment added successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Add Attachment Error")
            frappe.throw(str(e))
    
    @frappe.whitelist()
    def remove_attachment(self, file_name):
        """Remove attachment from record"""
        try:
            # Find attachment
            attachment = None
            for att in self.attachments:
                if att.file_name == file_name:
                    attachment = att
                    break
            
            if not attachment:
                frappe.throw(_("Attachment {0} not found").format(file_name))
            
            # Archive file
            file = frappe.get_doc("File", attachment.file)
            file.archive()
            
            # Remove from attachments
            self.remove(attachment)
            self.save()
            
            return {"message": "Attachment removed successfully"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Remove Attachment Error")
            frappe.throw(str(e)) 