frappe.ui.form.on('Department Schedule', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Department'), function() {
            frappe.set_route('Form', 'Department', frm.doc.department);
        });
        
        frm.add_custom_button(__('View Schedule'), function() {
            frappe.set_route('Calendar', 'Appointment', {'department': frm.doc.department});
        });
    },
    
    department: function(frm) {
        if (frm.doc.department) {
            frappe.db.get_value('Department', frm.doc.department, ['department_name', 'capacity'], function(r) {
                if (r) {
                    frappe.show_alert({
                        message: `Department: ${r.department_name} (Capacity: ${r.capacity})`,
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    
    start_time: function(frm) {
        calculateDuration(frm);
    },
    
    end_time: function(frm) {
        calculateDuration(frm);
    },
    
    break_time: function(frm) {
        if (frm.doc.break_time && frm.doc.start_time && frm.doc.end_time) {
            let break_time = frappe.datetime.str_to_obj(frm.doc.break_time);
            let start_time = frappe.datetime.str_to_obj(frm.doc.start_time);
            let end_time = frappe.datetime.str_to_obj(frm.doc.end_time);
            
            if (break_time < start_time || break_time > end_time) {
                frappe.msgprint('Break time must be between start and end time');
                frm.set_value('break_time', '');
            }
        }
    },
    
    break_duration: function(frm) {
        if (frm.doc.break_duration && frm.doc.duration) {
            if (frm.doc.break_duration > frm.doc.duration) {
                frappe.msgprint('Break duration cannot be greater than total duration');
                frm.set_value('break_duration', '');
            }
        }
    },
    
    max_appointments: function(frm) {
        if (frm.doc.max_appointments) {
            // Calculate available slots for today
            frappe.call({
                method: 'healthcare.healthcare.doctype.department_schedule.department_schedule.get_available_slots',
                args: {
                    department: frm.doc.department,
                    date: frappe.datetime.get_today()
                },
                callback: function(r) {
                    if (r.message !== null) {
                        frappe.show_alert({
                            message: `Available slots today: ${r.message}`,
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    }
});

function calculateDuration(frm) {
    if (frm.doc.start_time && frm.doc.end_time) {
        let start = frappe.datetime.str_to_obj(frm.doc.start_time);
        let end = frappe.datetime.str_to_obj(frm.doc.end_time);
        let duration = (end - start) / (1000 * 60); // in minutes
        frm.set_value('duration', Math.round(duration));
    }
} 