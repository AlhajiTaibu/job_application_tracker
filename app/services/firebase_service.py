import base64
import json

import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
from app.core.config import settings
from app.core.logging_config import logger


class FireBaseService:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        cred_path = BASE_DIR / "serviceAccountKey.json"
        self.cred = None
        if settings.firebase_credentials_base64:
            cred_string = base64.b64decode(settings.firebase_credentials_base64)
            cred_dict = json.loads(cred_string)
            self.cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(self.cred)
        else:
            self.cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(self.cred)

    def send_unified_push(self, tokens: list, title: str, body: str, data_payload: dict = None):
        """
        Sends notifications to multiple device tokens (Mobile + Web).
        """
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data_payload,  # Optional: Send stock IDs or deep links
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        for idx, send_response in enumerate(response.responses):
            if send_response.success:
                logger.info(f"FCM sent to token[{idx}]: message_id={send_response.message_id}")
            else:
                logger.error(f"FCM failed for token[{idx}]: {send_response.exception}")

        logger.info(f"FCM summary: {response.success_count} sent, {response.failure_count} failed")

        # Pro-Tip: Clean up expired tokens
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    logger.error(f"Token {tokens[idx]} failed: {resp.exception}")
                    # Logic to delete invalid tokens from your DB


firebase_service = FireBaseService()
