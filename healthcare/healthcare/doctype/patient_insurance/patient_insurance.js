frappe.ui.form.on('Patient Insurance', {
    refresh: function(frm) {
        // Add custom buttons
        frm.add_custom_button(__('View Patient'), function() {
            frappe.set_route('Form', 'Patient', frm.doc.patient);
        });
        
        frm.add_custom_button(__('View Insurance Provider'), function() {
            frappe.set_route('Form', 'Insurance Provider', frm.doc.insurance_provider);
        });
        
        // Add status change buttons for Healthcare Manager
        if (frappe.user.has_role('Healthcare Manager')) {
            frm.add_custom_button(__('Mark as Active'), function() {
                frm.set_value('status', 'Active');
                frm.save();
            });
            
            frm.add_custom_button(__('Mark as Expired'), function() {
                frm.set_value('status', 'Expired');
                frm.save();
            });
            
            frm.add_custom_button(__('Mark as Cancelled'), function() {
                frm.set_value('status', 'Cancelled');
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
    
    insurance_provider: function(frm) {
        if (frm.doc.insurance_provider) {
            frappe.db.get_value('Insurance Provider', frm.doc.insurance_provider, ['contact_person', 'contact_number'], function(r) {
                if (r) {
                    frappe.show_alert({
                        message: `Contact: ${r.contact_person} (${r.contact_number})`,
                        indicator: 'blue'
                    });
                }
            });
        }
    },
    
    coverage_type: function(frm) {
        if (frm.doc.coverage_type) {
            // Set default coverage details based on coverage type
            let coverage_details = {
                'Basic': [
                    { 'service_type': 'Consultation', 'coverage_percentage': 80 },
                    { 'service_type': 'Basic Tests', 'coverage_percentage': 70 }
                ],
                'Comprehensive': [
                    { 'service_type': 'Consultation', 'coverage_percentage': 90 },
                    { 'service_type': 'Basic Tests', 'coverage_percentage': 85 },
                    { 'service_type': 'Specialized Tests', 'coverage_percentage': 80 }
                ],
                'Premium': [
                    { 'service_type': 'Consultation', 'coverage_percentage': 100 },
                    { 'service_type': 'Basic Tests', 'coverage_percentage': 100 },
                    { 'service_type': 'Specialized Tests', 'coverage_percentage': 90 },
                    { 'service_type': 'Surgery', 'coverage_percentage': 85 }
                ],
                'Specialized': [
                    { 'service_type': 'Specialized Tests', 'coverage_percentage': 100 },
                    { 'service_type': 'Surgery', 'coverage_percentage': 90 },
                    { 'service_type': 'Rehabilitation', 'coverage_percentage': 80 }
                ]
            };
            
            if (coverage_details[frm.doc.coverage_type]) {
                frm.set_value('coverage_details', []);
                coverage_details[frm.doc.coverage_type].forEach(detail => {
                    let row = frappe.model.add_child(frm.doc, 'Insurance Coverage Detail', 'coverage_details');
                    row.service_type = detail.service_type;
                    row.coverage_percentage = detail.coverage_percentage;
                });
                frm.refresh_field('coverage_details');
            }
        }
    }
}); 