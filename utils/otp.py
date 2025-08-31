import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from datetime import timezone

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}. It expires in 5 minutes.")
    msg["Subject"] = "Your OTP Verification Code"
    msg["From"] = "talhaadil48@gmail.com"
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("talhaadil48@gmail.com", "ozgcstcgwwjeuvss")
        server.send_message(msg)



def get_otp_expiry() -> datetime:

    return datetime.now(timezone.utc) + timedelta(minutes=5)