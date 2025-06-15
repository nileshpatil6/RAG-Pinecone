import logging
import structlog
from structlog.stdlib import LoggerFactory
import sys
from typing import Optional

from app.core.config import settings


def setup_logging():
    """Configure structured logging with optional OpenTelemetry"""
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )
    
    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON or console renderer based on format
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup OpenTelemetry if configured
    if settings.otel_exporter_otlp_endpoint:
        setup_opentelemetry()


def setup_opentelemetry():
    """Configure OpenTelemetry tracing"""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        
        # Create resource
        resource = Resource.create({
            "service.name": settings.otel_service_name,
            "service.version": settings.app_version,
        })
        
        # Setup tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Auto-instrument libraries
        FastAPIInstrumentor.instrument()
        HTTPXClientInstrumentor.instrument()
        SQLAlchemyInstrumentor.instrument()
        
        logger = structlog.get_logger()
        logger.info("opentelemetry_configured", endpoint=settings.otel_exporter_otlp_endpoint)
        
    except ImportError:
        logger = structlog.get_logger()
        logger.warning("opentelemetry_not_available", 
                      message="OpenTelemetry dependencies not installed")