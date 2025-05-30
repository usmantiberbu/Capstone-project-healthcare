frappe.ui.form.on('Waitlist', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('Check Availability'), function() {
            frm.call({
                method: 'check_availability',
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Available slots found. Patient has been notified.'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.show_alert({
                            message: __('No available slots found.'),
                            indicator: 'orange'
                        });
                    }
                }
            });
        }, __('Actions'));
        
        // Add view buttons
        if (frm.doc.patient) {
            frm.add_custom_button(__('View Patient'), function() {
                frappe.set_route('Form', 'Patient', frm.doc.patient);
            });
        }
        
        if (frm.doc.doctor) {
            frm.add_custom_button(__('View Doctor'), function() {
                frappe.set_route('Form', 'Doctor', frm.doc.doctor);
            });
        }
    },
    
    patient: function(frm) {
        if (frm.doc.patient) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Patient',
                    name: frm.doc.patient
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('patient_name', `${r.message.first_name} ${r.message.last_name}`);
                    }
                }
            });
        }
    },
    
    doctor: function(frm) {
        if (frm.doc.doctor) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Doctor',
                    name: frm.doc.doctor
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('specialization', r.message.specialization);
                        frm.set_value('department', r.message.department);
                    }
                }
            });
        }
    },
    
    department: function(frm) {
        if (frm.doc.department && !frm.doc.doctor) {
            // Clear specialization if no doctor is selected
            frm.set_value('specialization', '');
        }
    },
    
    status: function(frm) {
        if (frm.doc.status === 'Notified') {
            frappe.show_alert({
                message: __('Patient will be notified about available slots.'),
                indicator: 'blue'
            });
        }
    }
}); 