frappe.ui.form.on('Department', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.head_of_department) {
            frm.add_custom_button(__('View Head of Department'), function() {
                frappe.set_route('Form', 'Doctor', frm.doc.head_of_department);
            });
        }
        
        frm.add_custom_button(__('View Doctors'), function() {
            frappe.set_route('List', 'Doctor', { department: frm.doc.name });
        });
        
        frm.add_custom_button(__('View Appointments'), function() {
            frappe.set_route('List', 'Appointment', { department: frm.doc.name });
        });
        
        frm.add_custom_button(__('Department Schedule'), function() {
            frappe.set_route('Report', 'Department Schedule', {'department': frm.doc.name});
        });
    },
    
    head_of_department: function(frm) {
        if (frm.doc.head_of_department) {
            frappe.db.get_value('Doctor', frm.doc.head_of_department, ['first_name', 'last_name', 'email', 'mobile'], function(r) {
                if (r) {
                    frappe.show_alert({
                        message: `Contact: ${r.first_name} ${r.last_name} (${r.mobile || r.email})`,
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    
    is_active: function(frm) {
        if (!frm.doc.is_active) {
            frappe.show_alert({
                message: 'Department is now inactive. New appointments cannot be scheduled.',
                indicator: 'orange'
            });
        } else {
            frappe.show_alert({
                message: 'Department is now active and available for appointments.',
                indicator: 'green'
            });
        }
    },
    
    operating_hours: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.start_time && row.end_time) {
            // Calculate duration
            let start = frappe.datetime.str_to_obj(row.start_time);
            let end = frappe.datetime.str_to_obj(row.end_time);
            let duration = (end - start) / (1000 * 60); // in minutes
            row.duration = duration;
            frm.refresh_field('operating_hours');
        }
    },
    
    capacity: function(frm) {
        if (frm.doc.capacity) {
            // Check current appointments
            frappe.call({
                method: 'healthcare.healthcare.doctype.department.department.get_available_slots',
                args: {
                    department: frm.doc.name,
                    date: frappe.datetime.get_today()
                },
                callback: function(r) {
                    if (r.message !== null) {
                        frappe.show_alert({
                            message: `Available slots today: ${r.message}`,
                            indicator: 'blue'
                        });
                    }
                }
            });
        }
    }
}); 