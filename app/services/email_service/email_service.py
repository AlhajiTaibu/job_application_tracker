import base64
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import find_dotenv, set_key
from fastapi.templating import Jinja2Templates
import logging
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.core.config import settings
from app.core.logging_config import logger


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
        try:
            creds = None

            if settings.gmail_token_json_b64:
                cred_string = base64.b64decode(settings.gmail_token_json_b64)
                cred_dict = json.loads(cred_string)
                creds = Credentials.from_authorized_user_info(cred_dict)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_config(
                        self.client_secret_config, self.scopes)
                    # run_local_server handles the old tools.run_flow logic automatically
                    creds = flow.run_local_server(port=settings.api_port, host=settings.api_host, access_type="offline",
                                                  prompt="consent")
                self.encode_json_to_env("GMAIL_TOKEN_JSON_B64", creds.to_json())

            return creds
        except Exception as error:
            logger.error(str(error))

    def get_service(self, api_name='gmail', version='v1'):
        """Helper to directly return the API service object"""
        try:
            creds = self.get_credentials()
            return build(api_name, version, credentials=creds)
        except Exception as error:
            logger.error(error)

    def encode_json_to_env(self, key_name, data_dict):
        encoded_bytes = base64.b64encode(data_dict.encode('utf-8'))
        base64_string = encoded_bytes.decode('utf-8')
        env_file_string = ".env" if settings.is_prod else ".env.local"
        env_path = find_dotenv(env_file_string)
        if not env_path:
            with open(".env", "w") as f: pass
            env_path = ".env"
        set_key(env_path, key_name, base64_string)
        with open(env_path, "r") as file:
            lines = file.readlines()

        with open(env_path, "w") as file:
            for line in lines:
                if line.startswith(f"{key_name}="):
                    raw_value = line.split("=", 1)[1].strip().strip('"').strip("'")
                    line = f"{key_name}={raw_value}\n"
                file.write(line)
        logger.info(f"Successfully wrote {key_name} to .env")


SCOPES = ["https://www.googleapis.com/auth/gmail.send", "openid", "https://www.googleapis.com/auth/userinfo.email"]
CLIENT_SECRET_CONFIG = {
    "installed": {
        "client_id": settings.client_id,
        "project_id": settings.project_id,
        "auth_uri": settings.auth_uri,
        "token_uri": settings.token_uri,
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": settings.client_secret,
        "redirect_uris": list(settings.redirect_uris.split(','))
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
            logger(f'An error occurred: {error}')


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
            sender='',
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
    message = send_message_instance.create_message(
        to="alhabdutaib@gmail.com",
        sender='alhaji@gmail.com',
        subject="Demo demo 2",
        message_text="hello peeps"

    )
    send_message_instance.send_message(
        'me',
        message
    )


if __name__ == '__main__':
    send_otp()
