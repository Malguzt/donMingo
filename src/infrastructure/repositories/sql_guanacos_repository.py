from domain.ports.guanacos_repository import GuanacosRepository
from domain.entities.guanaco.guanaco import Guanaco
from domain.entities.user import User
from infrastructure.database.sqlite_manager import SqliteManager
from infrastructure.repositories.zulip_chat_message_repository import ZulipChatMessageRepository
from infrastructure.repositories.http_think_repository import HttpThinkRepository
from infrastructure.repositories.hr_think_repository import HRThinkRepository
from typing import List
import sqlite3

class SQLGuanacosRepository(GuanacosRepository):
    def __init__(self, db_manager: SqliteManager):
        self.db_manager = db_manager

    def get_guanacos(self) -> List[Guanaco]:
        guanacos = []
        with self.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bots")
            rows = cursor.fetchall()
            
            for row in rows:
                # Create a dedicated repository for each bot using its own API key
                chat_repo = ZulipChatMessageRepository()
                # Override config with specific bot credentials
                chat_repo.config.email = row["email"]
                chat_repo.config.api_key = row["api_key"]
                # Re-initialize client with bot credentials
                import zulip
                chat_repo.client = zulip.Client(
                    email=chat_repo.config.email,
                    api_key=chat_repo.config.api_key,
                    site=chat_repo.config.site
                )
                
                # Assign think repository based on type
                http_think_repo = HttpThinkRepository()
                if row["bot_type"] == "hr":
                    think_repo = HRThinkRepository(self, nlp_engine=http_think_repo)
                else:
                    think_repo = http_think_repo
                
                # Mock user for the bot (Zulip bots act as users)
                bot_user = User(platform_id=row["id"], platform="zulip", name=row["name"])
                bot_user.email = row["email"] # Dynamically adding email since we saw it's used
                
                guanacos.append(Guanaco(
                    name=row["name"],
                    user=bot_user,
                    chat_message_repository=chat_repo,
                    think_repository=think_repo
                ))
        return guanacos

    def save_guanaco(self, name: str, short_name: str, email: str, api_key: str, bot_type: str = "guanaco"):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO bots (name, short_name, email, api_key, bot_type)
                VALUES (?, ?, ?, ?, ?)
            """, (name, short_name, email, api_key, bot_type))
            conn.commit()

    def delete_guanaco(self, short_name: str):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bots WHERE short_name = ?", (short_name,))
            conn.commit()
