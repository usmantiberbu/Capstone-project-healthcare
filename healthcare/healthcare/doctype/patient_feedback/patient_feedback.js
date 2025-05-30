frappe.ui.form.on('Patient Feedback', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Patient'), function() {
            frappe.set_route('Form', 'Patient', frm.doc.patient);
        });
        
        frm.add_custom_button(__('View Doctor'), function() {
            frappe.set_route('Form', 'Doctor', frm.doc.doctor);
        });
        
        if (frm.doc.appointment) {
            frm.add_custom_button(__('View Appointment'), function() {
                frappe.set_route('Form', 'Appointment', frm.doc.appointment);
            });
        }
        
        // Add approve/reject buttons for Healthcare Manager
        if (frm.doc.status === 'Pending' && frappe.user.has_role('Healthcare Manager')) {
            frm.add_custom_button(__('Approve'), function() {
                frm.set_value('status', 'Approved');
                frm.save();
            });
            
            frm.add_custom_button(__('Reject'), function() {
                frm.set_value('status', 'Rejected');
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
            frappe.db.get_value('Doctor', frm.doc.doctor, ['first_name', 'last_name', 'average_rating'], function(r) {
                if (r) {
                    frm.set_value('doctor_name', r.first_name + ' ' + r.last_name);
                    frappe.show_alert({
                        message: `Doctor's current average rating: ${r.average_rating || 'No ratings yet'}`,
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    
    appointment: function(frm) {
        if (frm.doc.appointment) {
            frappe.db.get_value('Appointment', frm.doc.appointment, ['patient', 'doctor', 'appointment_date'], function(r) {
                if (r) {
                    frm.set_value('patient', r.patient);
                    frm.set_value('doctor', r.doctor);
                    frm.set_value('date', r.appointment_date);
                }
            });
        }
    },
    
    rating: function(frm) {
        if (frm.doc.rating) {
            // Show rating description
            let rating_desc = {
                1: 'Poor',
                2: 'Fair',
                3: 'Good',
                4: 'Very Good',
                5: 'Excellent'
            };
            
            frappe.show_alert({
                message: `Rating: ${rating_desc[frm.doc.rating]}`,
                indicator: 'green'
            });
        }
    }
}); 