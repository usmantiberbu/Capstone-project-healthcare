import frappe
from frappe import _

def get_context(context):
    """Get context for patient portal pages"""
    context.title = _("Patient Portal")
    context.brand_html = "Healthcare"
    context.no_cache = 1

    # Add navigation items
    context.nav_items = [
        {"label": "Home", "url": "/patient-portal"},
        {"label": "Register", "url": "/patient-portal/registration"},
        {"label": "Login", "url": "/patient-portal/login"}
    ]

    return context

# Define routes directly
def get_portal_routes():
    """Define portal routes"""
    return {
        "patient-portal": {
            "title": "Patient Portal",
            "template": "www/patient-portal/index.html",
            "context": get_context,
            "allow_guest": True
        },
        "patient-portal/registration": {
            "title": "Patient Registration",
            "template": "www/patient-portal/registration.html",
            "context": get_context,
            "allow_guest": True
        },
        "patient-portal/login": {
            "title": "Patient Login",
            "template": "www/patient-portal/login.html",
            "context": get_context,
            "allow_guest": True
        }
    }

# Register routes on app install
def after_install():
    """Register routes after app installation"""
    try:
        # Create Website Settings if not exists
        if not frappe.db.exists("Website Settings"):
            frappe.get_doc({
                "doctype": "Website Settings",
                "home_page": "patient-portal",
                "brand_html": "Healthcare",
                "top_bar_items": [
                    {"label": "Home", "url": "/patient-portal"},
                    {"label": "Register", "url": "/patient-portal/registration"},
                    {"label": "Login", "url": "/patient-portal/login"}
                ]
            }).insert(ignore_permissions=True)
            
        # Register routes
        routes = get_portal_routes()
        for route, config in routes.items():
            if not frappe.db.exists("Website Route", route):
                frappe.get_doc({
                    "doctype": "Website Route",
                    "route": route,
                    "template": config["template"],
                    "title": config["title"],
                    "allow_guest": config.get("allow_guest", True)
                }).insert(ignore_permissions=True)
                
        frappe.db.commit()
        print("Successfully registered website routes")
    except Exception as e:
        frappe.log_error(f"Error registering routes: {str(e)}")
        frappe.db.rollback()

# No need for database operations
# The routes will be handled by Frappe's website module 