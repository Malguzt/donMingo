from application.use_cases.guanacos_spits import GuanacosSpits
from infrastructure.repositories.local_guanacos_repository import LocalGuanacosRepository
from infrastructure.repositories.zulip_bot_manager import ZulipBotManager
from prometheus_client import start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

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

def bootstrap_required_bots():
    """Ensures that required bots for the systems auto-management exist in Zulip."""
    print("[INFO] Bootstrapping system dependencies: Checking required bots...")
    bot_manager = ZulipBotManager()
    hr_bot_name = "Recursos Humanos"
    
    try:
        if not bot_manager.bot_exists(hr_bot_name):
            print(f"[INFO] '{hr_bot_name}' not found. Creating it...")
            bot_manager.create_bot(full_name=hr_bot_name, short_name="rh")
            print(f"[INFO] Successfully created '{hr_bot_name}' bot.")
        else:
            print(f"[INFO] '{hr_bot_name}' bot already exists.")
    except Exception as e:
        print(f"[ERROR] Failed to bootstrap bots: {e}")

def main():
    # Bootstrap dependencies
    bootstrap_required_bots()
    
    # Initialize repository and use case following dependency injection principle
    guanacos_repository = LocalGuanacosRepository()
    guanacos_spits = GuanacosSpits(guanacos_repository, sleep_time=10)
    
    # Start Prometheus metrics server
    print("[INFO] Starting Prometheus metrics server on port 8000")
    start_http_server(8000)
    
    # Configure Traces
    setup_telemetry()
    
    # Start the workers and run until shutdown
    guanacos_spits.run()

if __name__ == "__main__":
    main()