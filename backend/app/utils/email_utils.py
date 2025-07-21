import smtplib
from email.mime.text import MIMEText
from flask import current_app

def send_email(to_email, subject, body):
    smtp_server = current_app.config['SMTP_SERVER']
    smtp_port = current_app.config['SMTP_PORT']
    smtp_user = current_app.config['SMTP_USER']
    smtp_password = current_app.config['SMTP_PASSWORD']
    smtp_use_tls = current_app.config['SMTP_USE_TLS']
    smtp_from = current_app.config['SMTP_FROM']

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = smtp_from
    msg['To'] = to_email

    if smtp_use_tls:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [to_email], msg.as_string())
    else:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_from, [to_email], msg.as_string()) 