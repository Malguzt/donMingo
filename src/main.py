from application.use_cases.guanacos_spits import GuanacosSpits
from infrastructure.repositories.sql_guanacos_repository import SQLGuanacosRepository
from infrastructure.database.sqlite_manager import SqliteManager
from infrastructure.services.bot_bootstrap_service import BotBootstrapService
from infrastructure.workers.guanaco_worker_factory import GuanacoWorkerFactory
from prometheus_client import start_http_server
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry():
    """Sets up OpenTelemetry tracing exporting to Arize Phoenix."""
    resource = Resource(attributes={
        "service.name": "donmingo-agents"
    })

    provider = TracerProvider(resource=resource)

    # Phoenix OTLP HTTP receiver is on port 4318, trace endpoint is /v1/traces
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces"))

    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    print("[INFO] OpenTelemetry tracing to Phoenix enabled on localhost:4318")


def main():
    # Initialize infrastructure.
    db_manager = SqliteManager()
    guanacos_repository = SQLGuanacosRepository(db_manager)

    # Bootstrap dependencies.
    BotBootstrapService(guanacos_repository).bootstrap_required_bots()

    # Initialize use case using explicit worker factory injection.
    guanacos_spits = GuanacosSpits(
        guanacos_repository,
        sleep_time=10,
        worker_factory=GuanacoWorkerFactory(),
    )

    # Start Metrics Server (conditional).
    try:
        start_http_server(8000)
        print("[INFO] Starting Prometheus metrics server on port 8000")
    except OSError:
        print("[WARNING] Metrics server on port 8000 already running or address in use. Skipping...")

    # Configure traces.
    setup_telemetry()

    print("[INFO] donMingo linked to Yaguarete Proxy")

    # Start the workers and run until shutdown.
    guanacos_spits.run()


if __name__ == "__main__":
    main()
