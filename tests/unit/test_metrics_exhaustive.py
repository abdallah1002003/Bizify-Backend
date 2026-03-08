import pytest
import time
from prometheus_client import Histogram
from app.core.metrics import (
    REGISTRY,
    MetricsTimer,
    record_http_request,
    record_db_query,
    record_cache_operation,
    record_auth_attempt,
    record_ai_request,
    record_email_sent,
    record_error,
    http_requests_total,
    http_request_duration_seconds,
    db_query_duration_seconds,
    db_query_errors_total,
    cache_hits_total,
    cache_misses_total,
    auth_attempts_total,
    ai_requests_total,
    ai_request_duration_seconds,
    emails_sent_total,
    errors_total,
)

def test_metrics_timer():
    metric = Histogram("test_hist", "test", ["l1"], registry=REGISTRY)
    labels = {"l1": "v1"}
    
    with MetricsTimer(metric, labels):
        time.sleep(0.01)
        
    # Verify observation
    sample = REGISTRY.get_sample_value("test_hist_sum", labels={"l1": "v1"})
    assert sample > 0

def test_record_http_request():
    record_http_request("GET", "/test", 200, 0.1)
    
    count = REGISTRY.get_sample_value(
        "bizify_http_requests_total", 
        labels={"method": "GET", "endpoint": "/test", "status": "200"}
    )
    assert count == 1
    
    duration = REGISTRY.get_sample_value(
        "bizify_http_request_duration_seconds_sum",
        labels={"method": "GET", "endpoint": "/test"}
    )
    assert duration >= 0.1

def test_record_db_query():
    # Case: success
    record_db_query("SELECT", "users", 0.05, error=False)
    duration = REGISTRY.get_sample_value(
        "bizify_db_query_duration_seconds_sum",
        labels={"operation": "SELECT", "table": "users"}
    )
    assert duration >= 0.05
    
    # Case: error
    record_db_query("INSERT", "users", 0.01, error=True)
    err_count = REGISTRY.get_sample_value(
        "bizify_db_query_errors_total",
        labels={"operation": "INSERT", "table": "users", "error_type": "query_error"}
    )
    assert err_count == 1

def test_record_cache_operation():
    # Hit
    record_cache_operation("redis", hit=True)
    assert REGISTRY.get_sample_value("bizify_cache_hits_total", labels={"cache_backend": "redis"}) == 1
    
    # Miss
    record_cache_operation("memory", hit=False)
    assert REGISTRY.get_sample_value("bizify_cache_misses_total", labels={"cache_backend": "memory"}) == 1

def test_record_auth_attempt():
    record_auth_attempt("jwt", success=True)
    assert REGISTRY.get_sample_value("bizify_auth_attempts_total", labels={"method": "jwt", "success": "True"}) == 1
    
    record_auth_attempt("password", success=False)
    assert REGISTRY.get_sample_value("bizify_auth_attempts_total", labels={"method": "password", "success": "False"}) == 1

def test_record_ai_request():
    record_ai_request("openai", "gpt-4", 2.5, success=True)
    assert REGISTRY.get_sample_value("bizify_ai_requests_total", labels={"provider": "openai", "model": "gpt-4", "status": "success"}) == 1
    
    record_ai_request("anthropic", "claude-3", 1.0, success=False)
    assert REGISTRY.get_sample_value("bizify_ai_requests_total", labels={"provider": "anthropic", "model": "claude-3", "status": "error"}) == 1

def test_record_email_sent():
    record_email_sent("welcome", success=True)
    assert REGISTRY.get_sample_value("bizify_emails_sent_total", labels={"template": "welcome", "status": "success"}) == 1
    
    record_email_sent("reset", success=False)
    assert REGISTRY.get_sample_value("bizify_emails_sent_total", labels={"template": "reset", "status": "error"}) == 1

def test_record_error():
    record_error("ValueError", "UserService")
    assert REGISTRY.get_sample_value("bizify_errors_total", labels={"error_type": "ValueError", "service": "UserService"}) == 1
