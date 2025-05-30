frappe.ui.form.on('Doctor', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Schedule'), function() {
            frappe.set_route('Calendar', 'Appointment', {'doctor': frm.doc.name});
        });
        
        frm.add_custom_button(__('View Appointments'), function() {
            frappe.set_route('List', 'Appointment', {'doctor': frm.doc.name});
        });
        
        frm.add_custom_button(__('View Performance'), function() {
            frappe.set_route('Report', 'Doctor Performance', {'doctor': frm.doc.name});
        });
    },
    
    specialization: function(frm) {
        if (frm.doc.specialization) {
            // Update department based on specialization
            let department_map = {
                'Cardiology': 'Cardiology Department',
                'Neurology': 'Neurology Department',
                'Pediatrics': 'Pediatrics Department',
                'Orthopedics': 'Orthopedics Department',
                'Dermatology': 'Dermatology Department',
                'Ophthalmology': 'Ophthalmology Department',
                'ENT': 'ENT Department',
                'Gynecology': 'Gynecology Department',
                'Dentistry': 'Dental Department'
            };
            
            if (department_map[frm.doc.specialization]) {
                frm.set_value('department', department_map[frm.doc.specialization]);
            }
        }
    },
    
    working_hours: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.start_time && row.end_time) {
            // Calculate duration
            let start = frappe.datetime.str_to_obj(row.start_time);
            let end = frappe.datetime.str_to_obj(row.end_time);
            let duration = (end - start) / (1000 * 60); // in minutes
            row.duration = duration;
            frm.refresh_field('working_hours');
        }
    }
}); 