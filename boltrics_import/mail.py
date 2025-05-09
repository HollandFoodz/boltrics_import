import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

port = 587  # For starttls

def mail(server, username, from_email, receiver, password, message, exit_code):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if exit_code == 0:
        pre_msg = "(Success)"
    else:
        pre_msg = "(Failed)"

    subject = f'{pre_msg} Holland Foodz - Boltrics import ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})'
    
    # HTML email body
    text = f"""<html>
    <body>
        <p><strong>An import from the Boltrics (Bakker) system has been run at {timestamp} with the following result:</strong></p>
        <p>{pre_msg}</p>
        <p><strong>This is the output from the program:</strong></p>
        <pre>{message}</pre>
    </body>
    </html>
    """

    # Create a MIME multipart message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = receiver
    msg['Subject'] = subject

    # Attach the HTML message to the email
    msg.attach(MIMEText(text, 'html'))

    # Set up the server and send the email
    context = ssl.create_default_context()
    with smtplib.SMTP(server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(username, password)
        server.sendmail(from_email, receiver, msg.as_string())