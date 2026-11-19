import requests
from flask import render_template
from config import Config

def send_templated_email(to_email, subject, template_name, **context):
    """
    Renders an HTML email template inside templates/emails/ 
    and sends it via the Resend API.
    """
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {Config.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Provide an absolute logo URL for the email header (email clients need absolute URLs)
    domain = getattr(Config, 'DOMAIN', 'http://localhost:5000').rstrip('/')
    context.setdefault('logo_url', f"{domain}/static/images/logo.png")

    # Render the Jinja2 template into an HTML string
    html_body = render_template(f"emails/{template_name}", **context)
    
    data = {
        # Note: Make sure hopebridge.org is verified in Resend, 
        # or switch to "Hope Bridge Foundation <onboarding@resend.dev>" while testing
        "from": "Hope Bridge Foundation <grants@hopebridge.org>",
        "to": [to_email] if isinstance(to_email, str) else to_email,
        "subject": subject,
        "html": html_body
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if not response.ok:
            print(f"Resend API Error ({response.status_code}): {response.text}")
        return response.ok
    except Exception as e:
        print(f"Email request failed: {e}")
        return False

def send_approval_email(email, first_name, application_id):
    """
    Sends the grant approval email with the payment collection link.
    """
    domain = getattr(Config, 'DOMAIN', 'http://localhost:5000').rstrip('/')
    link = f"{domain}/collect-payment/{application_id}"
    
    return send_templated_email(
        to_email=email,
        subject="Your Hope Bridge Grant is Approved!",
        template_name="approval.html",
        first_name=first_name,
        link=link
    )