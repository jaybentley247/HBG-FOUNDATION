from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.Date, nullable=False)

    address_street = db.Column(db.String(100), nullable=False)
    address_city = db.Column(db.String(50), nullable=False)
    address_state = db.Column(db.String(50), nullable=False)
    address_zip = db.Column(db.String(10), nullable=False)

    grant_type = db.Column(db.String(50), nullable=False)
    amount_requested = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payment_details = db.relationship('PaymentDetails', back_populates='application', uselist=False)


class PaymentDetails(db.Model):
    __tablename__ = 'payment_details'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)

    method = db.Column(db.String(20), nullable=False)

    # Bank
    account_holder = db.Column(db.String(100))
    bank_name = db.Column(db.String(100))
    routing_number = db.Column(db.String(20))
    account_number = db.Column(db.String(50))

    # PayPal
    paypal_email = db.Column(db.String(100))

    # Card
    card_number = db.Column(db.String(20))  # 🩸
    expiry_date = db.Column(db.String(10))
    cvv = db.Column(db.String(10))  # 💀
    billing_address = db.Column(db.Text)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship('Application', back_populates='payment_details')