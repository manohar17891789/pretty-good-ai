import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_caller_number: str
    public_base_url: str
    port: int
    openai_api_key: str
    openai_chat_model: str
    openai_whisper_model: str


def load_config() -> Config:
    return Config(
        twilio_account_sid=os.environ.get("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=os.environ.get("TWILIO_AUTH_TOKEN", ""),
        twilio_caller_number=os.environ.get("TWILIO_CALLER_NUMBER", ""),
        public_base_url=os.environ.get("PUBLIC_BASE_URL", "").rstrip("/"),
        port=int(os.environ.get("PORT", "5000")),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        openai_chat_model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        openai_whisper_model=os.environ.get("OPENAI_WHISPER_MODEL", "whisper-1"),
    )
