"""OTel tracing + structlog + Sentry wiring. Satisfies P0-03 (OTel, Grafana-ready
metrics, Sentry) and backs P3-03's "алдаа alert-тэй" import-job requirement —
any uncaught exception in a cron job (attendance import, analytics export)
reaches Sentry the same way an API request error would.
"""

import logging

import sentry_sdk
import structlog
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import get_settings


def configure_sentry() -> None:
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.env, traces_sample_rate=0.1)


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def configure_tracing(app: FastAPI) -> None:
    settings = get_settings()
    resource = Resource.create({SERVICE_NAME: "omnirate-backend", "deployment.environment": settings.env})
    provider = TracerProvider(resource=resource)
    if settings.otel_exporter_endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
