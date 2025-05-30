# Healthcare Appointment Scheduling System

A comprehensive healthcare management system built on the Frappe Framework, designed to streamline appointment scheduling, patient management, and medical record keeping for healthcare facilities.

## Features

### 1. Patient Management
- Patient registration and profile management
- Document management (ID proofs, insurance cards)
- Patient portal access
- Medical history tracking
- Appointment history

### 2. Doctor Management
- Doctor profiles with specialization details
- Schedule management
- Performance metrics dashboard
- Leave management system
- Department-wise organization

### 3. Appointment Scheduling
- Real-time appointment booking
- Conflict-free scheduling
- Waitlist management
- Appointment reminders
- Status tracking (Scheduled, Confirmed, Completed, Cancelled)

### 4. Medical Records
- Secure medical record management
- Version control and audit trail
- Document attachments
- Access control based on roles
- Patient history tracking

### 5. Notifications
- Email notifications
- SMS alerts
- Appointment reminders
- Status updates
- Custom notification templates

### 6. Security Features
- Role-based access control
- Field-level permissions
- Audit logging
- Data encryption
- HIPAA compliance features

## Installation

1. **Prerequisites**
   - Python 3.10+
   - Node.js 16+
   - MariaDB 10.6+
   - Redis

2. **Install Frappe Bench**
   ```bash
   pip install frappe-bench
   ```

3. **Create a new bench**
   ```bash
   bench init healthcare-bench
   cd healthcare-bench
   ```

4. **Create a new site**
   ```bash
   bench new-site mysite.local
   ```

5. **Install the Healthcare app**
   ```bash
   bench get-app healthcare
   bench --site mysite.local install-app healthcare
   ```

6. **Start the development server**
   ```bash
   bench start
   ```

## Configuration

1. **Healthcare Settings**
   - Configure working hours
   - Set appointment duration
   - Configure notification settings
   - Set up departments

2. **User Roles**
   - Healthcare Administrator
   - Doctor
   - Patient
   - Receptionist

3. **Email Settings**
   - Configure SMTP settings
   - Set up email templates

4. **SMS Settings**
   - Configure SMS gateway
   - Set up SMS templates

## Usage

1. **Patient Registration**
   - Go to Desk > Healthcare > Patient > New
   - Fill in required information
   - Upload necessary documents

2. **Doctor Management**
   - Create doctor profiles
   - Set up schedules
   - Assign departments

3. **Appointment Booking**
   - Select doctor and date
   - Choose available time slot
   - Confirm booking

4. **Medical Records**
   - Create new records
   - Attach documents
   - Track patient history

## Development

1. **Code Structure**
   ```
   healthcare/
   ├── healthcare/
   │   ├── doctype/
   │   │   ├── patient/
   │   │   ├── doctor/
   │   │   ├── appointment/
   │   │   └── medical_record/
   │   ├── www/
   │   │   └── doctor-portal/
   │   └── tests/
   ```

2. **Running Tests**
   ```bash
   bench --site mysite.local run-tests --app healthcare
   ```

3. **Development Guidelines**
   - Follow PEP 8 style guide
   - Write unit tests for new features
   - Document API endpoints
   - Update documentation

## API Documentation

### Patient APIs
- `get_patient_details`
- `get_patient_appointments`
- `update_patient_profile`

### Doctor APIs
- `get_doctor_details`
- `get_doctor_schedule`
- `get_doctor_metrics`

### Appointment APIs
- `create_appointment`
- `update_appointment_status`
- `get_available_slots`

### Medical Record APIs
- `create_medical_record`
- `get_record_details`
- `add_attachment`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## Acknowledgments

- Frappe Framework
- Healthcare community
- Contributors and maintainers 