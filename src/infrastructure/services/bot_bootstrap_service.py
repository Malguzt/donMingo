from typing import Dict, List
import sqlite3
import time
from infrastructure.repositories.zulip_bot_manager import ZulipBotManager


class BotBootstrapService:
    """Coordinates required bot bootstrap and cleanup policies."""

    HR_BOT_NAME = "Recursos Humanos"
    HR_BOT_SHORT_NAME = "rh"

    def __init__(self, guanacos_repository):
        self.guanacos_repository = guanacos_repository
        self.bot_manager = ZulipBotManager()

    def _get_all_zulip_bots(self) -> List[Dict]:
        users_response = self.bot_manager.client.get_users()
        if users_response.get("result") != "success":
            raise RuntimeError(f"Zulip API error retrieving users: {users_response.get('msg')}")
        return [m for m in users_response.get("members", []) if m.get("is_bot") is True]

    def _get_db_bots(self) -> List[Dict]:
        bots: List[Dict] = []
        with self.guanacos_repository.db_manager.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bots")
            rows = cursor.fetchall()
            for row in rows:
                bots.append(dict(row))
        return bots

    def _delete_db_bot_by_short_name(self, short_name: str) -> None:
        self.guanacos_repository.delete_guanaco(short_name=short_name)

    def _deactivate_zulip_bot(self, user: Dict) -> None:
        user_id = user.get("user_id") or user.get("id")
        if not user_id:
            print(f"[WARNING] Cannot deactivate bot without user_id: {user.get('email')}")
            return
        response = self.bot_manager.client.deactivate_user_by_id(int(user_id))
        if response.get("result") != "success":
            msg = response.get("msg", "")
            if "No such user" in msg:
                print(f"[INFO] Bot already absent in Zulip: {user.get('email')}")
                return
            print(f"[WARNING] Could not deactivate bot {user.get('email')}: {msg}")
        else:
            print(f"[INFO] Deactivated orphan/duplicate bot: {user.get('full_name')} ({user.get('email')})")

    def _enforce_single_hr_bot(self) -> None:
        print("[INFO] Enforcing single HR bot policy...")
        db_bots = self._get_db_bots()
        zulip_bots = self._get_all_zulip_bots()

        db_hr_bots = [b for b in db_bots if b.get("bot_type") == "hr"]
        canonical_db_hr = None
        if db_hr_bots:
            canonical_db_hr = next((b for b in db_hr_bots if b.get("short_name") == self.HR_BOT_SHORT_NAME), db_hr_bots[0])

            for hr in db_hr_bots:
                if hr["id"] == canonical_db_hr["id"]:
                    continue
                self._delete_db_bot_by_short_name(hr["short_name"])
                print(f"[INFO] Removed duplicate HR bot from DB: {hr['name']} ({hr['short_name']})")

        hr_like_zulip = [
            b for b in zulip_bots
            if (b.get("full_name", "").strip().lower().startswith(self.HR_BOT_NAME.lower())
                or b.get("email", "").split("@")[0].startswith(self.HR_BOT_SHORT_NAME))
        ]

        canonical_email = canonical_db_hr["email"].lower() if canonical_db_hr else None
        for zb in hr_like_zulip:
            zb_email = (zb.get("email") or "").lower()
            if canonical_email and zb_email == canonical_email:
                continue
            self._deactivate_zulip_bot(zb)

        if canonical_db_hr is None:
            bot_data = self.bot_manager.create_bot(full_name=self.HR_BOT_NAME, short_name=self.HR_BOT_SHORT_NAME)
            bot_email = bot_data.get("email") or f"{self.HR_BOT_SHORT_NAME}-bot@donmingo.zulipchat.com"
            self.guanacos_repository.save_guanaco(
                name=self.HR_BOT_NAME,
                short_name=self.HR_BOT_SHORT_NAME,
                email=bot_email,
                api_key=bot_data["api_key"],
                bot_type="hr"
            )
            print(f"[INFO] HR bot created and registered: {bot_email}")
        else:
            print(f"[INFO] HR bot already registered and unique: {canonical_db_hr['email']}")

    def _ensure_required_non_hr_bots(self) -> None:
        required = [
            {"name": "Pancho", "short_name": "pancho", "type": "guanaco"},
        ]

        db_bots = self._get_db_bots()
        db_emails = {b["email"].lower() for b in db_bots}
        zulip_bots = self._get_all_zulip_bots()

        for bot_info in required:
            exists_in_db = any(
                (
                    b["short_name"] == bot_info["short_name"]
                    or b["name"].strip().lower() == bot_info["name"].lower()
                )
                and b["bot_type"] == bot_info["type"]
                for b in db_bots
            )
            if exists_in_db:
                print(f"[INFO] Required bot '{bot_info['name']}' already exists in DB.")
                continue

            conflicting = []
            for b in zulip_bots:
                full_name = b.get("full_name", "").strip().lower()
                email_prefix = (b.get("email", "").split("@")[0]).lower()
                is_same_candidate = (
                    full_name == bot_info["name"].lower()
                    or email_prefix.startswith(bot_info["short_name"])
                )
                if is_same_candidate and (b.get("email", "").lower() not in db_emails):
                    conflicting.append(b)

            for user in conflicting:
                self._deactivate_zulip_bot(user)

            active_name = bot_info["name"]
            active_short_name = bot_info["short_name"]
            try:
                bot_data = self.bot_manager.create_bot(full_name=active_name, short_name=active_short_name)
            except Exception as e:
                err = str(e)
                if "Email is already in use" in err or "Name is already in use" in err:
                    active_short_name = f"{bot_info['short_name']}-{int(time.time())}"
                    if "Name is already in use" in err:
                        active_name = f"{bot_info['name']} New"
                    print(
                        f"[WARNING] Conflict creating '{bot_info['name']}'. "
                        f"Retrying with name='{active_name}', short_name='{active_short_name}'."
                    )
                    bot_data = self.bot_manager.create_bot(full_name=active_name, short_name=active_short_name)
                else:
                    raise

            bot_email = bot_data.get("email") or f"{active_short_name}-bot@donmingo.zulipchat.com"
            self.guanacos_repository.save_guanaco(
                name=active_name,
                short_name=active_short_name,
                email=bot_email,
                api_key=bot_data["api_key"],
                bot_type=bot_info["type"]
            )
            print(f"[INFO] Required bot created and registered: {active_name} ({bot_email})")

    def _cleanup_zulip_bots_not_in_db(self) -> None:
        print("[INFO] Cleaning Zulip bots that are not present in DB...")
        db_bots = self._get_db_bots()
        db_emails = {b["email"].lower() for b in db_bots}

        for user in self._get_all_zulip_bots():
            email = (user.get("email") or "").lower()
            if email and email not in db_emails:
                self._deactivate_zulip_bot(user)

    def bootstrap_required_bots(self) -> None:
        print("[INFO] Bootstrapping system dependencies: Checking required bots...")
        self._enforce_single_hr_bot()
        self._ensure_required_non_hr_bots()
        self._cleanup_zulip_bots_not_in_db()
