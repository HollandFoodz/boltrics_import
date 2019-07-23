import smtplib, ssl

port = 587  # For starttls

def mail(server, sender, receiver, password, error):
    SUBJECT = 'Holland Foodz - import failed'
    TEXT = 'An import from the Boltrics (Zeewolde/Bakker) system failed.\n\nPlease contact IT to review the following error:\n\n{}'.format(error)
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)

    context = ssl.create_default_context()
    with smtplib.SMTP(server, port) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.sendmail(sender, receiver, message)
