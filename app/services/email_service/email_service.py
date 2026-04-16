import logging
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
from fastapi.templating import Jinja2Templates

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Auth:
    def __init__(self, scopes, client_secret_config, application_name):
        self.scopes = scopes
        self.client_secret_config = client_secret_config
        self.application_name = application_name
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.token_path = os.path.join(BASE_DIR, ".credentials", "token.json")

    def get_credentials(self):
        """
        Retrieves valid user credentials from storage or
        runs the local flow to generate new ones.
        """
        creds = None

        # Ensure the directory exists

        credential_dir = os.path.dirname(self.token_path)
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        # Check for existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

        # If there are no (valid) credentials, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    self.client_secret_config, self.scopes)
                # run_local_server handles the old tools.run_flow logic automatically
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return creds

    def get_service(self, api_name='gmail', version='v1'):
        """Helper to directly return the API service object"""
        creds = self.get_credentials()
        return build(api_name, version, credentials=creds)


SCOPES=["https://www.googleapis.com/auth/gmail.send","openid", "https://www.googleapis.com/auth/userinfo.email"]
CLIENT_SECRET_CONFIG = {
  "installed": {
    "client_id": settings.client_id,
    "project_id": settings.project_id,
    "auth_uri": settings.auth_uri,
    "token_uri": settings.token_uri,
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": settings.client_secret,
    "redirect_uris": [
      settings.redirect_uris
    ]
  }
}

APPLICATION_NAME = 'Gmail API Python Quickstart'
authInst = Auth(
    SCOPES,
    CLIENT_SECRET_CONFIG,
    APPLICATION_NAME
)

service = authInst.get_service()


class SendEmail:
    def __init__(self, email_service):
        self.service = email_service

    def create_message(self, sender, to, subject, message_text):
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        message.attach(MIMEText(message_text, 'html'))
        return {
            'raw': base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()}

    def send_message(self, user_id, message):
        """Send an email message.

      Args:
        service: Authorized Gmail API service instance.
        user_id: User's email address. The special value "me"
        can be used to indicate the authenticated user.
        message: Message to be sent.

      Returns:
        Sent Message.
      """
        try:
            message = (
                self.service.users().messages().send(
                    userId=user_id,
                    body=message
                ).execute()
            )
            return message
        except Exception as error:
            print(f'An error occurred: {error}')

send_message_instance = SendEmail(service)

def send_email(html: str, recipient: str, subject: str, context=None):
    templates = Jinja2Templates(directory="templates")
    if context is None:
        context = {}
    try:
        send_email_instance = SendEmail(service)
        raw_mail_body = templates.get_template(
            html
        )
        body = raw_mail_body.render(context)
        message = send_email_instance.create_message(
            to=recipient,
            sender='alhajitaibu1992@gmail.com',
            subject=subject,
            message_text=body

        )
        send_message_instance.send_message(
            'me',
            message
        )
        logger.info(f"Email sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False

def send_otp():
    templates = Jinja2Templates(directory="templates")
    raw_mail_body = templates.get_template(
        'auth/verification_email.html'
    )
    body = raw_mail_body.render()
    message = send_message_instance.create_message(
        to="alhabdutaib@gmail.com",
        sender='alhajitaibu1992@gmail.com',
        subject="Demo demo 2",
        message_text=body

    )
    send_message_instance.send_message(
        'me',
        message
    )

if __name__ == '__main__':
    send_otp()