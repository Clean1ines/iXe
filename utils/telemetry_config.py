"""Configuration for OpenTelemetry tracing."""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource


def configure_telemetry(service_name: str = "ixe-api") -> None:
    """
    Configure OpenTelemetry tracing for the application.

    Args:
        service_name: Name of the service for telemetry purposes
    """
    # Set up a basic tracer provider
    provider = TracerProvider(
        resource=Resource.create({"service.name": service_name})
    )
    
    # Choose exporter based on environment
    if os.getenv("OTLP_EXPORTER_ENDPOINT"):
        # Use OTLP exporter to send to collector (Jaeger, Zipkin, etc.)
        otlp_exporter = OTLPSpanExporter(
            endpoint=os.getenv("OTLP_EXPORTER_ENDPOINT"),
            headers=(("Authorization", f"Bearer {os.getenv('OTLP_TOKEN')}"),) if os.getenv("OTLP_TOKEN") else ()
        )
        processor = BatchSpanProcessor(otlp_exporter)
    else:
        # Use console exporter for development
        console_exporter = ConsoleSpanExporter()
        processor = BatchSpanProcessor(console_exporter)
    
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def instrument_app(app):
    """
    Instrument the FastAPI app with OpenTelemetry.

    Args:
        app: FastAPI application instance
    """
    FastAPIInstrumentor.instrument_app(app)
    return app
