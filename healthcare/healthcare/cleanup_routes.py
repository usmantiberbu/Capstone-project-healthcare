import frappe

def cleanup_routes():
    """Clean up website routes for patient portal"""
    try:
        # Delete existing routes
        frappe.db.sql("DELETE FROM `tabWebsite Route` WHERE route LIKE 'patient-portal%'")
        frappe.db.commit()
        print("Successfully cleaned up website routes")
    except Exception as e:
        print(f"Error cleaning up routes: {str(e)}")
        frappe.db.rollback()

if __name__ == "__main__":
    cleanup_routes() 