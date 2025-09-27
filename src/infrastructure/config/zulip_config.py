import os
from dotenv import load_dotenv

load_dotenv()


class ZulipConfig:
    def __init__(self):
        self.api_key = os.getenv("ZULIP_API_KEY")
        self.email = os.getenv("ZULIP_EMAIL")
        self.site = os.getenv("ZULIP_API_URL") or os.getenv("ZULIP_SITE")

        missing = [name for name, value in [
            ("ZULIP_API_KEY", self.api_key),
            ("ZULIP_EMAIL", self.email),
            ("ZULIP_API_URL or ZULIP_SITE", self.site),
        ] if not value]
        if missing:
            missing_keys = ", ".join(missing)
            raise ValueError(
                f"Missing required environment variables: {missing_keys}. "
                f"Create a .env or set them in the environment."
            )
