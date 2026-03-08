import zulip
from infrastructure.config.zulip_config import ZulipConfig
from typing import Optional

class ZulipBotManager:
    """Handles the creation and deletion of bots in Zulip."""
    def __init__(self):
        self.config = ZulipConfig()
        self.client = zulip.Client(
            email=self.config.email,
            api_key=self.config.api_key,
            site=self.config.site,
        )

    def create_bot(self, full_name: str, short_name: str, bot_type: int = 1) -> str:
        """
        Creates a new bot in the Zulip organization.
        bot_type: 1 for Generic bot.
        Returns the API key of the created bot or raises an Exception.
        """
        request_paylod = {
            "full_name": full_name,
            "short_name": short_name,
            "bot_type": bot_type,
        }
        
        response = self.client.call_endpoint(
            url="bots",
            method="POST",
            request=request_paylod
        )
        
        if response.get("result") != "success":
            raise RuntimeError(f"Error creating bot {full_name}: {response.get('msg')}")
            
        return response.get("api_key", "")

    def deactivate_bot(self, email: str) -> bool:
        """
        Deactivates an existing bot in the Zulip organization.
        Returns True if successful, raises an Exception otherwise.
        """
        # Find the user ID dynamically based on the email
        user_id = self._find_user_id_by_email(email)
        if user_id is None:
             raise ValueError(f"Bot with email {email} not found")
             
        response = self.client.call_endpoint(
            url=f"users/{user_id}",
            method="DELETE"
        )
        
        if response.get("result") != "success":
            raise RuntimeError(f"Error deactivating bot {email}: {response.get('msg')}")
            
        return True

    def bot_exists(self, full_name: str) -> bool:
        """
        Checks if a bot with the given full_name already exists in the organization.
        """
        users_response = self.client.get_users()
        if users_response.get("result") != "success":
            raise RuntimeError(f"Zulip API error retrieving users: {users_response.get('msg')}")
            
        for member in users_response.get("members", []):
            if member.get("full_name", "").lower() == full_name.lower():
                return True
        return False

    def _find_user_id_by_email(self, email: str) -> Optional[int]:
        users_response = self.client.get_users()
        if users_response.get("result") != "success":
            raise RuntimeError(f"Zulip API error retrieving users: {users_response.get('msg')}")
            
        for member in users_response.get("members", []):
            if member.get("email") == email:
                user_id_value = member.get("user_id") or member.get("id")
                return int(user_id_value) if user_id_value is not None else None
        return None
