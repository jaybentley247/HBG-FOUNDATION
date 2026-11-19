from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models import db, Application, PaymentDetails
from datetime import datetime
import hmac
import json
import os
from utils import send_approval_email
from config import Config

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/grants')
def grants():
    return render_template('grants.html')

@bp.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@bp.route('/apply', methods=['GET', 'POST'])
def apply():
    if request.method == 'POST':
        step = request.form.get('step')

        # Step 1: Personal Info
        if step == '1':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            dob = request.form.get('dob', '').strip()
            address_street = request.form.get('address_street', '').strip()
            address_city = request.form.get('address_city', '').strip()
            address_state = request.form.get('address_state', '').strip()
            address_zip = request.form.get('address_zip', '').strip()

            # Validate required fields
            if not all([first_name, last_name, email, phone, dob, address_street, address_city, address_state, address_zip]):
                return jsonify({'error': 'All fields are required.'}), 400

            if '@' not in email or '.' not in email:
                return jsonify({'error': 'Invalid email address.'}), 400

            # Validate DOB format
            try:
                datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format.'}), 400

            # Save to session
            session.update({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'dob': dob,
                'address_street': address_street,
                'address_city': address_city,
                'address_state': address_state,
                'address_zip': address_zip,
            })
            return jsonify({'redirect': '/apply?step=2'})

        # Step 2: Grant Details
        elif step == '2':
            grant_type = request.form.get('grant_type', '').strip()
            amount_requested = request.form.get('amount_requested', '').strip()
            description = request.form.get('description', '').strip()

            if not grant_type or not amount_requested or not description:
                return jsonify({'error': 'All grant fields are required.'}), 400

            try:
                amount_requested = float(amount_requested)
                if amount_requested <= 0:
                    raise ValueError
            except:
                return jsonify({'error': 'Amount must be a positive number.'}), 400

            session.update({
                'grant_type': grant_type,
                'amount_requested': amount_requested,
                'description': description,
            })
            return jsonify({'redirect': '/apply?step=3'})

        # Step 3: Submit Final
        elif step == '3':
            if not session.get('first_name') or not session.get('grant_type'):
                return jsonify({'error': 'Session expired. Please restart.'}), 400

            if not request.form.get('certify'):
                return jsonify({'error': 'You must certify the information.'}), 400

            try:
                # Create Application
                app = Application(
                    first_name=session['first_name'],
                    last_name=session['last_name'],
                    email=session['email'],
                    phone=session['phone'],
                    dob=datetime.strptime(session['dob'], '%Y-%m-%d').date(),
                    address_street=session['address_street'],
                    address_city=session['address_city'],
                    address_state=session['address_state'],
                    address_zip=session['address_zip'],
                    grant_type=session['grant_type'],
                    amount_requested=session['amount_requested'],
                    description=session['description'],
                    status='pending'  # Ensures status defaults to pending for the dashboard
                )
                db.session.add(app)
                db.session.commit()

                # Clear session
                session.clear()

                # Redirect to success
                return jsonify({'redirect': url_for('main.success')})

            except Exception as e:
                db.session.rollback()
                print(f"Database error on submit: {e}") # Prints exact error to your terminal window
                return jsonify({'error': 'Application failed. Please try again.'}), 500

        else:
            return jsonify({'error': 'Invalid step.'}), 400

    else:
        # GET request — render template
        step = request.args.get('step', '1')
        if step not in ['1', '2', '3']:
            return redirect(url_for('main.apply'))
        return render_template('apply.html', step=step)

@bp.route('/success')
def success():
    return render_template('success.html')

# --- Admin Authentication & Dashboard Routes ---

@bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        # Credentials come from ADMIN_USERNAME / ADMIN_PASSWORD in .env
        expected_user = os.getenv('ADMIN_USERNAME', '')
        expected_pass = os.getenv('ADMIN_PASSWORD', '')
        if (expected_user and expected_pass
                and hmac.compare_digest(username, expected_user)
                and hmac.compare_digest(password, expected_pass)):
            session['is_admin'] = True
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid username or password.')
    return render_template('admin/login.html')

@bp.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('main.admin_login'))
    
    # Fetch all applications from the database
    applications = Application.query.order_by(Application.id.desc()).all()
    
    # Compute analytics stats for your dashboard cards
    total = len(applications)
    pending = sum(1 for a in applications if getattr(a, 'status', 'pending') == 'pending')
    funds_requested = sum(float(a.amount_requested or 0) for a in applications)
    
    return render_template(
        'admin/dashboard.html', 
        applications=applications, 
        total=total, 
        pending=pending, 
        funds_requested=funds_requested
    )

@bp.route('/admin/application/<int:app_id>')
def admin_application_detail(app_id):
    if not session.get('is_admin'):
        return redirect(url_for('main.admin_login'))
    
    app = Application.query.get_or_404(app_id)
    return render_template('admin/detail.html', app=app)

@bp.route('/admin/approve/<int:app_id>', methods=['POST'])
def admin_approve(app_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    app = Application.query.get_or_404(app_id)
    app.status = 'approved'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/admin/reject/<int:app_id>', methods=['POST'])
def admin_reject(app_id):
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    app = Application.query.get_or_404(app_id)
    app.status = 'rejected'
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('main.admin_login'))

@bp.route('/collect-payment/<int:app_id>', methods=['GET', 'POST'])
def collect_payment(app_id):
    # Fetch the application so we know who is submitting payment info
    app = Application.query.get_or_404(app_id)
    
    if request.method == 'POST':
        # Capture form fields from collect_payment.html
        account_name = request.form.get('account_name', '').strip()
        account_number = request.form.get('account_number', '').strip()
        bank_name = request.form.get('bank_name', '').strip()
        routing_number = request.form.get('routing_number', '').strip()
        
        if not all([account_name, account_number, bank_name]):
            flash('Please fill in all required payment details.', 'danger')
            return render_template('collect_payment.html', app=app)
            
        try:
            # Save or update payment details linked to this application
            # (Assumes a PaymentDetails model exists as imported in your routes)
            payment = PaymentDetails.query.filter_by(application_id=app.id).first()
            if not payment:
                payment = PaymentDetails(application_id=app.id)
                db.session.add(payment)
                
            payment.account_name = account_name
            payment.account_number = account_number
            payment.bank_name = bank_name
            payment.routing_number = routing_number
            
            db.session.commit()
            
            flash('Payment details submitted successfully!', 'success')
            # Redirect to admin detail view or a confirmation screen
            return redirect(url_for('main.admin_application_detail', app_id=app.id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving payment details. Please try again.', 'danger')
            
    return render_template('collect_payment.html', app=app)