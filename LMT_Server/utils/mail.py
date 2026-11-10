import smtplib
from email.mime.text import MIMEText
from email.header import Header
from .db import config

def send_verification_code(to_email, code):
    mail_config = config.get('QQ_Mail', {})
    sender = mail_config.get('SENDER', '')
    api_key = mail_config.get('API_KEY', '')

    if not sender or not api_key:
        print("Missing QQ_Mail config (SENDER or API_KEY). Please check your config.yaml.")
        return False

    from email.utils import formataddr
    message = MIMEText(f'Your Caseplay verification code is: {code}', 'plain', 'utf-8')
    message['From'] = formataddr(('Caseplay', sender))
    message['To'] = Header(to_email, 'utf-8')
    message['Subject'] = Header('LMT Registration Verification Code', 'utf-8')

    try:
        # Use QQ Mail SMTP server
        smtpObj = smtplib.SMTP_SSL("smtp.qq.com", 465)
        smtpObj.login(sender, api_key)
        smtpObj.sendmail(sender, [to_email], message.as_string())
        smtpObj.quit()
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
