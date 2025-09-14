import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

email_user = os.getenv('EMAIL_USER')
email_password = os.getenv('EMAIL_PASSWORD')
def generate_otp() -> str:
    return str(random.randint(100000, 999999))
def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg["Subject"] = "Your OTP Verification Code - Sufi Pulse"
    msg["From"] = "contact@sufipulse.com"
    msg["To"] = to_email

    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: #ffffff; border-radius: 12px; 
                    padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
          <div style="text-align: center; margin-bottom: 20px;">
            <h2 style="color: #065f46; margin: 0;">Sufi Pulse</h2>
            <p style="color: #555; margin: 5px 0;">Your trusted spiritual companion</p>
          </div>
          
          <p style="color: #333; font-size: 15px;">
            Dear User,<br><br>
            Please use the following One-Time Password (OTP) to complete your verification:
          </p>
          
          <div style="text-align: center; margin: 25px 0;">
            <span style="display: inline-block; background: #065f46; color: #ffffff; 
                         font-size: 24px; font-weight: bold; letter-spacing: 3px; 
                         padding: 12px 20px; border-radius: 8px;">
              {otp}
            </span>
          </div>
          
          <p style="color: #555; font-size: 14px;">
            This OTP will expire in <b>5 minutes</b>. Please do not share it with anyone.
          </p>
          
          <p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
            © {datetime.now().year} Sufi Pulse. All rights reserved.
          </p>
        </div>
      </body>
    </html>
    """

    msg.set_content(f"Your OTP is: {otp}. It expires in 5 minutes.")  # Fallback plain text
    msg.add_alternative(html_content, subtype="html")

    with smtplib.SMTP("smtp.ionos.com", 587) as server:
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)

def get_otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=5)

