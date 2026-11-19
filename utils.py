import requests
from config import Config

def send_approval_email(email, first_name, application_id):
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {Config.RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    link = f"{Config.DOMAIN}/collect-payment/{application_id}"
    data = {
        "from": "Hope Bridge Foundation <grants@hopebridge.org>",
        "to": [email],
        "subject": "Your Hope Bridge Grant is Approved!",
        "html": f"""
        <h2>Congratulations, {first_name}!</h2>
        <p>Your grant application has been <strong>approved</strong>.</p>
        <p>Click the link below to submit your payment details:</p>
        <a href="{link}">{link}</a>
        <br><br>
        <p>Best,<br>Hope Bridge Foundation Team</p>
        """
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.status_code == 200
    except:
        return False