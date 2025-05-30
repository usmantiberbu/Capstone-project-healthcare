frappe.ui.form.on('Appointment', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Patient'), function() {
            frappe.set_route('Form', 'Patient', frm.doc.patient);
        });
        
        frm.add_custom_button(__('View Doctor'), function() {
            frappe.set_route('Form', 'Doctor', frm.doc.doctor);
        });
        
        if (frm.doc.status === 'Scheduled') {
            frm.add_custom_button(__('Mark as Completed'), function() {
                frm.set_value('status', 'Completed');
                frm.save();
            });
            
            frm.add_custom_button(__('Cancel Appointment'), function() {
                frm.set_value('status', 'Cancelled');
                frm.save();
            });
        }
    },
    
    patient: function(frm) {
        if (frm.doc.patient) {
            frappe.db.get_value('Patient', frm.doc.patient, ['first_name', 'last_name'], function(r) {
                if (r) {
                    frm.set_value('patient_name', r.first_name + ' ' + r.last_name);
                }
            });
        }
    },
    
    doctor: function(frm) {
        if (frm.doc.doctor) {
            frappe.db.get_value('Doctor', frm.doc.doctor, ['first_name', 'last_name', 'department'], function(r) {
                if (r) {
                    frm.set_value('doctor_name', r.first_name + ' ' + r.last_name);
                    frm.set_value('department', r.department);
                }
            });
        }
    },
    
    appointment_date: function(frm) {
        if (frm.doc.appointment_date && frm.doc.doctor) {
            // Check doctor's availability
            frappe.call({
                method: 'healthcare.healthcare.doctype.doctor.doctor.get_doctor_availability',
                args: {
                    doctor: frm.doc.doctor,
                    date: frm.doc.appointment_date
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_df_property('appointment_time', 'options', r.message);
                    }
                }
            });
        }
    }
}); 