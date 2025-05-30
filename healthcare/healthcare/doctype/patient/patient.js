frappe.ui.form.on('Patient', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Medical History'), function() {
            frappe.set_route('List', 'Patient Medical History', {'patient': frm.doc.name});
        });
        
        frm.add_custom_button(__('Schedule Appointment'), function() {
            frappe.new_doc('Appointment', {
                patient: frm.doc.name,
                patient_name: frm.doc.first_name + ' ' + frm.doc.last_name
            });
        });
    },
    
    date_of_birth: function(frm) {
        if (frm.doc.date_of_birth) {
            let age = frappe.datetime.get_diff(frappe.datetime.now_date(), frm.doc.date_of_birth, 'years');
            frm.set_value('age', age);
        }
    },
    
    mobile_no: function(frm) {
        if (frm.doc.mobile_no) {
            // Format mobile number
            frm.set_value('mobile_no', frm.doc.mobile_no.replace(/[^0-9]/g, ''));
        }
    }
}); 