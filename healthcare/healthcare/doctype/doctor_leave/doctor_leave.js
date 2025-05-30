frappe.ui.form.on('Doctor Leave', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.doctor) {
            frm.add_custom_button(__('View Doctor'), function() {
                frappe.set_route('Form', 'Doctor', frm.doc.doctor);
            });
        }
        
        // Add approve/reject buttons for Healthcare Manager
        if (frm.doc.status === 'Pending' && 
            (frappe.user.has_role('Healthcare Manager') || frappe.user.has_role('Administrator'))) {
            frm.add_custom_button(__('Approve'), function() {
                frappe.confirm(
                    'Are you sure you want to approve this leave application?',
                    function() {
                        frm.call({
                            method: 'approve_leave',
                            callback: function(r) {
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }, __('Actions'));
            
            frm.add_custom_button(__('Reject'), function() {
                frappe.confirm(
                    'Are you sure you want to reject this leave application?',
                    function() {
                        frm.call({
                            method: 'reject_leave',
                            callback: function(r) {
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }, __('Actions'));
        }
        
        // Add calendar view button
        frm.add_custom_button(__('Calendar View'), function() {
            frappe.set_route('Calendar', 'Doctor Leave', {
                'doctor': frm.doc.doctor
            });
        });
    },
    
    doctor: function(frm) {
        if (frm.doc.doctor) {
            frappe.db.get_value('Doctor', frm.doc.doctor, ['department', 'email', 'mobile'], function(r) {
                if (r) {
                    frappe.show_alert({
                        message: `Contact: ${r.mobile || r.email}`,
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    
    from_date: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date) {
            calculate_total_days(frm);
        }
    },
    
    to_date: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date) {
            calculate_total_days(frm);
        }
    },
    
    status: function(frm) {
        if (frm.doc.status === 'Approved') {
            frappe.show_alert({
                message: 'Leave has been approved. All schedules during this period will be cancelled.',
                indicator: 'green'
            });
        } else if (frm.doc.status === 'Rejected') {
            frappe.show_alert({
                message: 'Leave has been rejected.',
                indicator: 'red'
            });
        }
    }
});

function calculate_total_days(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        let from_date = frappe.datetime.str_to_obj(frm.doc.from_date);
        let to_date = frappe.datetime.str_to_obj(frm.doc.to_date);
        let diff = frappe.datetime.get_day_diff(to_date, from_date) + 1;
        frm.set_value('total_days', diff);
    }
} 