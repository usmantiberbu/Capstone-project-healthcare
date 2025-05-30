frappe.ui.form.on('Medical Record', {
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
        
        frm.add_custom_button(__('Print Record'), function() {
            frappe.print({
                doctype: frm.doctype,
                name: frm.docname,
                print_format: 'Medical Record'
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
    
    doctor: function(frm) {
        if (frm.doc.doctor) {
            frappe.db.get_value('Doctor', frm.doc.doctor, ['first_name', 'last_name'], function(r) {
                if (r) {
                    frm.set_value('doctor_name', r.first_name + ' ' + r.last_name);
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
    
    height: function(frm) {
        calculateBMI(frm);
    },
    
    weight: function(frm) {
        calculateBMI(frm);
    }
});

function calculateBMI(frm) {
    if (frm.doc.height && frm.doc.weight) {
        // Convert height from cm to meters
        let height_in_meters = frm.doc.height / 100;
        // Calculate BMI
        let bmi = frm.doc.weight / (height_in_meters * height_in_meters);
        frm.set_value('bmi', Math.round(bmi * 100) / 100);
    }
} 