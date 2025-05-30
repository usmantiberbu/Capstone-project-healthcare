frappe.ui.form.on('Doctor Schedule', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.doctor) {
            frm.add_custom_button(__('View Doctor'), function() {
                frappe.set_route('Form', 'Doctor', frm.doc.doctor);
            });
        }
        
        if (frm.doc.department) {
            frm.add_custom_button(__('View Department'), function() {
                frappe.set_route('Form', 'Department', frm.doc.department);
            });
        }
        
        frm.add_custom_button(__('View Appointments'), function() {
            frappe.set_route('List', 'Appointment', {
                'doctor': frm.doc.doctor,
                'appointment_date': frm.doc.schedule_date
            });
        });
        
        // Add calendar view button
        frm.add_custom_button(__('Calendar View'), function() {
            frappe.set_route('Calendar', 'Doctor Schedule', {
                'doctor': frm.doc.doctor
            });
        });
    },
    
    doctor: function(frm) {
        if (frm.doc.doctor) {
            frappe.db.get_value('Doctor', frm.doc.doctor, ['department', 'email', 'mobile'], function(r) {
                if (r) {
                    frm.set_value('department', r.department);
                    frappe.show_alert({
                        message: `Contact: ${r.mobile || r.email}`,
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    
    schedule_date: function(frm) {
        if (frm.doc.schedule_date && frm.doc.doctor) {
            // Check doctor's availability
            frappe.call({
                method: 'healthcare.healthcare.doctype.doctor_schedule.doctor_schedule.check_doctor_availability',
                args: {
                    doctor: frm.doc.doctor,
                    date: frm.doc.schedule_date
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: r.message,
                            indicator: 'orange'
                        });
                    }
                }
            });
        }
    }
});

// Handle Schedule Time Slot child table
frappe.ui.form.on('Schedule Time Slot', {
    start_time: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.start_time && row.end_time) {
            calculate_duration(frm, row);
        }
    },
    
    end_time: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.start_time && row.end_time) {
            calculate_duration(frm, row);
        }
    },
    
    max_appointments: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.max_appointments < 1) {
            frappe.throw("Maximum appointments must be at least 1");
        }
    }
});

function calculate_duration(frm, row) {
    let start = frappe.datetime.str_to_obj(row.start_time);
    let end = frappe.datetime.str_to_obj(row.end_time);
    let duration = (end - start) / (1000 * 60); // in minutes
    
    if (duration <= 0) {
        frappe.throw("End time must be after start time");
    }
    
    row.duration = duration;
    frm.refresh_field('schedule_times');
} 