frappe.ui.form.on('Patient Medical History', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Patient'), function() {
            frappe.set_route('Form', 'Patient', frm.doc.patient);
        });
        
        frm.add_custom_button(__('Print Record'), function() {
            frappe.print({
                doctype: frm.doctype,
                name: frm.docname,
                print_format: 'Patient Medical History'
            });
        });
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
    
    date: function(frm) {
        if (frm.doc.date) {
            // Set default description if empty
            if (!frm.doc.description) {
                frm.set_value('description', 'Medical consultation on ' + frm.doc.date);
            }
        }
    }
}); 