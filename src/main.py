from application.use_cases.guanacos_spits import GuanacosSpits
from infrastructure.repositories.sql_guanacos_repository import SQLGuanacosRepository
from infrastructure.database.sqlite_manager import SqliteManager
from infrastructure.repositories.zulip_bot_manager import ZulipBotManager
from prometheus_client import start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from typing import Dict, List
import sqlite3
import time

HR_BOT_NAME = "Recursos Humanos"
HR_BOT_SHORT_NAME = "rh"

def setup_telemetry():
    """Sets up OpenTelemetry tracing exporting to Arize Phoenix"""
    resource = Resource(attributes={
        "service.name": "donmingo-agent"
    })
    
    provider = TracerProvider(resource=resource)
    
    # Phoenix OTLP HTTP receiver is on port 4318, trace endpoint is /v1/traces
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))
    
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    
    print("[INFO] OpenTelemetry tracing to Phoenix enabled on localhost:4318")

def _get_all_zulip_bots(bot_manager: ZulipBotManager) -> List[Dict]:
    users_response = bot_manager.client.get_users()
    if users_response.get("result") != "success":
        raise RuntimeError(f"Zulip API error retrieving users: {users_response.get('msg')}")
    return [m for m in users_response.get("members", []) if m.get("is_bot") is True]

def _get_db_bots(guanacos_repository) -> List[Dict]:
    bots: List[Dict] = []
    with guanacos_repository.db_manager.get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bots")
        rows = cursor.fetchall()
        for row in rows:
            bots.append(dict(row))
    return bots

def _delete_db_bot_by_short_name(guanacos_repository, short_name: str) -> None:
    guanacos_repository.delete_guanaco(short_name=short_name)

def _deactivate_zulip_bot(bot_manager: ZulipBotManager, user: Dict) -> None:
    user_id = user.get("user_id") or user.get("id")
    if not user_id:
        print(f"[WARNING] Cannot deactivate bot without user_id: {user.get('email')}")
        return
    response = bot_manager.client.deactivate_user_by_id(int(user_id))
    if response.get("result") != "success":
        msg = response.get("msg", "")
        if "No such user" in msg:
            print(f"[INFO] Bot already absent in Zulip: {user.get('email')}")
            return
        print(f"[WARNING] Could not deactivate bot {user.get('email')}: {msg}")
    else:
        print(f"[INFO] Deactivated orphan/duplicate bot: {user.get('full_name')} ({user.get('email')})")

def _enforce_single_hr_bot(guanacos_repository, bot_manager: ZulipBotManager) -> None:
    print("[INFO] Enforcing single HR bot policy...")
    db_bots = _get_db_bots(guanacos_repository)
    zulip_bots = _get_all_zulip_bots(bot_manager)

    db_hr_bots = [b for b in db_bots if b.get("bot_type") == "hr"]
    canonical_db_hr = None
    if db_hr_bots:
        canonical_db_hr = next((b for b in db_hr_bots if b.get("short_name") == HR_BOT_SHORT_NAME), db_hr_bots[0])

        for hr in db_hr_bots:
            if hr["id"] == canonical_db_hr["id"]:
                continue
            _delete_db_bot_by_short_name(guanacos_repository, hr["short_name"])
            print(f"[INFO] Removed duplicate HR bot from DB: {hr['name']} ({hr['short_name']})")

    hr_like_zulip = [
        b for b in zulip_bots
        if (b.get("full_name", "").strip().lower().startswith(HR_BOT_NAME.lower())
            or b.get("email", "").split("@")[0].startswith(HR_BOT_SHORT_NAME))
    ]

    canonical_email = canonical_db_hr["email"].lower() if canonical_db_hr else None
    for zb in hr_like_zulip:
        zb_email = (zb.get("email") or "").lower()
        if canonical_email and zb_email == canonical_email:
            continue
        _deactivate_zulip_bot(bot_manager, zb)

    if canonical_db_hr is None:
        bot_data = bot_manager.create_bot(full_name=HR_BOT_NAME, short_name=HR_BOT_SHORT_NAME)
        bot_email = bot_data.get("email") or f"{HR_BOT_SHORT_NAME}-bot@donmingo.zulipchat.com"
        guanacos_repository.save_guanaco(
            name=HR_BOT_NAME,
            short_name=HR_BOT_SHORT_NAME,
            email=bot_email,
            api_key=bot_data["api_key"],
            bot_type="hr"
        )
        print(f"[INFO] HR bot created and registered: {bot_email}")
    else:
        print(f"[INFO] HR bot already registered and unique: {canonical_db_hr['email']}")

def _ensure_required_non_hr_bots(guanacos_repository, bot_manager: ZulipBotManager) -> None:
    required = [
        {"name": "Pancho", "short_name": "pancho", "type": "guanaco"},
    ]

    db_bots = _get_db_bots(guanacos_repository)
    db_emails = {b["email"].lower() for b in db_bots}
    zulip_bots = _get_all_zulip_bots(bot_manager)

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
            _deactivate_zulip_bot(bot_manager, user)

        active_name = bot_info["name"]
        active_short_name = bot_info["short_name"]
        try:
            bot_data = bot_manager.create_bot(full_name=active_name, short_name=active_short_name)
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
                bot_data = bot_manager.create_bot(full_name=active_name, short_name=active_short_name)
            else:
                raise

        bot_email = bot_data.get("email") or f"{active_short_name}-bot@donmingo.zulipchat.com"
        guanacos_repository.save_guanaco(
            name=active_name,
            short_name=active_short_name,
            email=bot_email,
            api_key=bot_data["api_key"],
            bot_type=bot_info["type"]
        )
        print(f"[INFO] Required bot created and registered: {active_name} ({bot_email})")

def _cleanup_zulip_bots_not_in_db(guanacos_repository, bot_manager: ZulipBotManager) -> None:
    print("[INFO] Cleaning Zulip bots that are not present in DB...")
    db_bots = _get_db_bots(guanacos_repository)
    db_emails = {b["email"].lower() for b in db_bots}

    for user in _get_all_zulip_bots(bot_manager):
        email = (user.get("email") or "").lower()
        if email and email not in db_emails:
            _deactivate_zulip_bot(bot_manager, user)

def bootstrap_required_bots(guanacos_repository):
    """Ensures required bots exist, enforces single HR bot, and cleans orphan Zulip bots."""
    print("[INFO] Bootstrapping system dependencies: Checking required bots...")
    bot_manager = ZulipBotManager()
    _enforce_single_hr_bot(guanacos_repository, bot_manager)
    _ensure_required_non_hr_bots(guanacos_repository, bot_manager)
    _cleanup_zulip_bots_not_in_db(guanacos_repository, bot_manager)

def main():
    # Initialize infrastructure
    db_manager = SqliteManager()
    guanacos_repository = SQLGuanacosRepository(db_manager)
    
    # Bootstrap dependencies
    bootstrap_required_bots(guanacos_repository)
    
    # Initialize use case following dependency injection principle
    guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=10)
    
    # Inject repository into HRThinkRepository if any bot uses it
    # (SQLGuanacosRepository already does this in its get_guanacos mapper, 
    # but we might need to ensure the instance is shared if we had a more complex setup)
    
    # 3. Start Metrics Server (conditional)
    try:
        start_http_server(8000)
        print("[INFO] Starting Prometheus metrics server on port 8000")
    except OSError:
        print("[WARNING] Metrics server on port 8000 already running or address in use. Skipping...")
    
    # Configure Traces
    setup_telemetry()
    
    # Preload models in background before workers start
    from infrastructure.transformers_engine.models_handler import ModelsHandler
    models_handler = ModelsHandler()
    models_handler.preload_models()
    print("[INFO] Model preload started in background...")
    
    # Start the workers and run until shutdown
    guanacos_spits.run()

if __name__ == "__main__":
    main()
