# Post-Cleanup Verification Report
Generated: verify_cleanup.py

## Summary
- Duplicate file groups found: 33
- Potential import issues: 60
- Files with API endpoints: 22
- Critical file issues: 0
- Errors encountered: 2

## 🔍 Duplicate Files Found
### Hash: bc0ce1e161e8
- `tools\global_date_time_filter.py`
- `memory\functions\global_date_time_filter.py`

### Hash: 4aa670c14c91
- `utilities\ai_tools.py`
- `storage\openwebui\utilities\ai_tools.py`

### Hash: 0b94be740ef3
- `utilities\alert_manager.py`
- `storage\openwebui\utilities\alert_manager.py`

### Hash: f46b91618613
- `utilities\api_key_manager.py`
- `storage\openwebui\utilities\api_key_manager.py`

### Hash: b4785d8427c9
- `utilities\async_context_managers.py`
- `storage\openwebui\utilities\async_context_managers.py`

### Hash: 2e9934c9478d
- `utilities\auth_validator_migration_guide.py`
- `storage\openwebui\utilities\auth_validator_migration_guide.py`

### Hash: 311f1e72bcd9
- `utilities\cache_manager.py`
- `storage\openwebui\utilities\cache_manager.py`

### Hash: 0cedca8fe356
- `utilities\circuit_breaker.py`
- `storage\openwebui\utilities\circuit_breaker.py`

### Hash: b5df04abcb95
- `utilities\connection_factory.py`
- `storage\openwebui\utilities\connection_factory.py`

### Hash: 1043877eda55
- `utilities\cpu_enforcer.py`
- `storage\openwebui\utilities\cpu_enforcer.py`

### Hash: c4b89800b513
- `utilities\database_types.py`
- `storage\openwebui\utilities\database_types.py`

### Hash: f38a5efaaaa2
- `utilities\endpoint_validator.py`
- `storage\openwebui\utilities\endpoint_validator.py`

### Hash: 0564c09bd59d
- `utilities\enhanced_connection_pooling.py`
- `storage\openwebui\utilities\enhanced_connection_pooling.py`

### Hash: 2e69b29ece75
- `utilities\enhanced_web_search.py`
- `storage\openwebui\utilities\enhanced_web_search.py`

### Hash: d54175235b85
- `utilities\error_patterns.py`
- `storage\openwebui\utilities\error_patterns.py`

### Hash: c1bd5fef6219
- `utilities\error_patterns_examples.py`
- `storage\openwebui\utilities\error_patterns_examples.py`

### Hash: 5c5fdf6a7f35
- `utilities\error_patterns_migration_guide.py`
- `storage\openwebui\utilities\error_patterns_migration_guide.py`

### Hash: b73a99706eb9
- `utilities\feature_registry.py`
- `storage\openwebui\utilities\feature_registry.py`

### Hash: f21ecc3f6afd
- `utilities\fix_unicode.py`
- `storage\openwebui\utilities\fix_unicode.py`

### Hash: 39fb9445c863
- `utilities\focused_endpoint_validator.py`
- `storage\openwebui\utilities\focused_endpoint_validator.py`

### Hash: fb8f635bd42b
- `utilities\force_refresh.py`
- `storage\openwebui\utilities\force_refresh.py`

### Hash: 1b12274746c5
- `utilities\inspect_chromadb.py`
- `storage\openwebui\utilities\inspect_chromadb.py`

### Hash: 2c8d2efd655d
- `utilities\memory_monitor.py`
- `storage\openwebui\utilities\memory_monitor.py`

### Hash: 39397fb9eeaa
- `utilities\memory_pool.py`
- `storage\openwebui\utilities\memory_pool.py`

### Hash: 3fe49bab348f
- `utilities\performance_monitoring.py`
- `storage\openwebui\utilities\performance_monitoring.py`

### Hash: 95b42e1369c7
- `utilities\rag.py`
- `storage\openwebui\utilities\rag.py`

### Hash: a643e733c256
- `utilities\simple_error_handling.py`
- `storage\openwebui\utilities\simple_error_handling.py`

### Hash: c9feb693e87e
- `utilities\smart_outlet_implementation.py`
- `storage\openwebui\utilities\smart_outlet_implementation.py`

### Hash: af8841d16765
- `utilities\smart_web_search_trigger.py`
- `storage\openwebui\utilities\smart_web_search_trigger.py`

### Hash: 3ec43413db8a
- `utilities\validation.py`
- `storage\openwebui\utilities\validation.py`

### Hash: c2106580d6a3
- `utilities\watchdog.py`
- `storage\openwebui\utilities\watchdog.py`

### Hash: bb60e4922252
- `utilities\web_search_metrics.py`
- `storage\openwebui\utilities\web_search_metrics.py`

### Hash: d5a6d0b15ee0
- `utilities\__init__.py`
- `storage\openwebui\utilities\__init__.py`

## ⚠️ Potential Import Issues
- tests\test_bulk_memory_query.py:3 - from core.main import app
- tests\test_chroma_metrics.py:5 - from core.metrics import METRICS_ENABLED, chroma_operation_latency_seconds
- tests\test_chroma_metrics.py:6 - from services.database_manager import db_manager
- tests\test_circuit_breaker.py:6 - from core.main import app
- tests\test_circuit_breaker.py:7 - from utilities.circuit_breaker import get_llm_breaker
- tests\test_circuit_breaker.py:10 - import services.llm_service as llm_service
- tests\test_circuit_breaker_metrics.py:3 - from utilities.circuit_breaker import CircuitBreaker
- tests\test_circuit_breaker_metrics.py:4 - from core.metrics import METRICS_ENABLED, generate_latest
- tests\test_embedding_latency_metric.py:6 - from services.embedding_provider import HuggingFaceEmbeddingProvider
- tests\test_embedding_latency_metric.py:7 - from core.metrics import embedding_latency_seconds, METRICS_ENABLED
- tests\test_embedding_latency_metric.py:20 - from core.main import app
- tests\test_environment_validation_warnings.py:2 - from core.security import validate_environment, perform_environment_validation
- tests\test_fixes_verification.py:52 - from utilities.ai_tools import calculate
- tests\test_fixes_verification.py:79 - from services.memory_service import APIMemoryProvider
- tests\test_fixes_verification.py:97 - from utilities.watchdog import SystemWatchdog
- tests\test_fixes_verification.py:116 - from memory.api.main import app
- tests\test_fixes_verification.py:130 - from utilities.ai_tools import (
- tests\test_fixes_verification.py:173 - from utilities.rag import extract_text_from_pdf, chunk_text
- tests\test_fixes_verification.py:191 - from services.llm_service import OllamaService
- tests\test_gateway_correlation.py:7 - from core.main import app
- tests\test_gateway_correlation.py:8 - from core.enhanced_api_gateway import EnhancedAPIGateway
- tests\test_gateway_correlation.py:9 - from core.metrics import METRICS_ENABLED, generate_latest
- tests\test_gateway_latency_histogram.py:3 - from core.main import app
- tests\test_gateway_latency_histogram.py:4 - from core.metrics import METRICS_ENABLED
- tests\test_health_breaker.py:6 - from core.main import app
- tests\test_issues_3_and_5.py:28 - from utilities.enhanced_connection_pooling import get_enhanced_redis_pool, pool_manager
- tests\test_issues_3_and_5.py:29 - from utilities.performance_monitoring import performance_monitor, record_operation_performance
- tests\test_issues_3_and_5.py:30 - from utilities.async_context_managers import redis_connection
- tests\test_issues_3_and_5.py:31 - from utilities.simple_error_handling import handle_database_errors, handle_errors
- tests\test_issues_3_and_5.py:32 - from core.unified_logging import get_logger, log_service_status
- tests\test_memory_degraded_mode.py:9 - import services.database_manager as dm
- tests\test_memory_degraded_mode.py:13 - from core.main import get_memory_service_or_legacy
- tests\test_memory_injection_sanitization.py:2 - from services.memory_service import MemoryEntry, MemoryMetadata, MemoryService
- tests\test_memory_metrics.py:29 - from services.memory_service import MemoryService, MemoryEntry, MemoryMetadata
- tests\test_memory_metrics.py:30 - from core.metrics import (
- tests\test_metrics_basic.py:6 - from core.main import app
- tests\test_metrics_basic.py:25 - from services.embedding_provider import HuggingFaceEmbeddingProvider
- tests\test_metrics_basic.py:26 - from core.metrics import embedding_latency_seconds, embedding_errors_total, METRICS_ENABLED
- tests\test_phase1_quickwins.py:11 - from core.security import SecurityHeadersMiddleware
- tests\test_phase1_quickwins.py:12 - from core.error_handler import ErrorHandler
- tests\test_phase1_quickwins.py:13 - from core.metrics import generate_latest, METRICS_ENABLED
- tests\test_phase1_quickwins.py:14 - from core.enhanced_api_gateway import EnhancedAPIGateway
- tests\test_phase1_quickwins.py:15 - from core.error_handler import RedisConnectionHandler
- tests\test_phase2_environment_validation.py:1 - from core.security import validate_environment
- tests\test_phase2_rate_circuit.py:4 - from core.main import app
- tests\test_phase2_rate_circuit.py:5 - from utilities.circuit_breaker import CircuitBreaker
- tests\test_phase2_security_circuit_metrics.py:8 - from core.security import SecurityHeadersMiddleware
- tests\test_phase2_security_circuit_metrics.py:9 - from utilities.circuit_breaker import CircuitBreaker, circuit_breaker_state_total
- tests\test_phase2_security_circuit_metrics.py:10 - from core.metrics import METRICS_ENABLED, generate_latest
- tests\test_rate_limit.py:6 - from core.main import app
- tests\test_rate_limit_scope.py:4 - from core.main import app
- tests\test_rate_limit_scope.py:22 - import services.llm_service as llm_mod
- tests\test_rate_limit_scope.py:78 - import services.llm_service as llm_mod
- tests\test_rate_limit_with_correlation.py:4 - from core.security import SecurityHeadersMiddleware
- tests\test_readiness_and_version.py:3 - from core.main import app
- tests\test_redis_metrics.py:5 - from core.metrics import METRICS_ENABLED, redis_operation_latency_seconds
- tests\test_redis_metrics.py:6 - from services.database_manager import db_manager
- tests\test_security_headers_snapshot.py:5 - from core.security import SecurityHeadersMiddleware
- tests\test_web_search_ddgs_only.py:4 - from utilities.enhanced_web_search import search_web
- tests\test_web_search_structured.py:2 - from utilities.enhanced_web_search import search_web, should_trigger_web_search

## 🌐 API Endpoints Found
### core\main.py
- FastAPI(
- app.get(
- app.post(

### routes\chat.py
- APIRouter(

### routes\debug.py
- APIRouter(

### routes\gateway.py
- APIRouter(

### routes\health.py
- APIRouter(

### routes\memory.py
- APIRouter(

### routes\models.py
- APIRouter(

### routes\tools.py
- APIRouter(

### routes\upload.py
- APIRouter(

### scripts\integrated_memory_startup.py
- FastAPI(
- app.get(
- app.post(

### scripts\verify_cleanup.py
- @app.route
- @router.get
- @router.post
- @router.put
- @router.delete
- FastAPI(
- APIRouter(
- app.get(
- app.post(
- app.put(
- app.delete(

### services\feedback_router.py
- APIRouter(

### services\model_manager.py
- @router.get
- @router.post
- @router.delete
- APIRouter(

### tests\test_phase1_quickwins.py
- FastAPI(
- app.get(

### tests\test_phase2_security_circuit_metrics.py
- FastAPI(
- app.get(

### tests\test_rate_limit_middleware.py
- FastAPI(
- app.post(

### tests\test_rate_limit_with_correlation.py
- FastAPI(
- app.post(

### tests\test_security_headers_snapshot.py
- FastAPI(
- app.get(

### utilities\endpoint_validator.py
- @router.get
- app.post(

### memory\api\enhanced_memory_api.py
- FastAPI(
- app.get(
- app.post(

### memory\api\main.py
- FastAPI(
- app.get(
- app.post(
- app.delete(

### storage\openwebui\utilities\endpoint_validator.py
- @router.get
- app.post(

## ✅ All Critical Files Present

## ❌ Errors Encountered
- Failed to hash E:\Projects\opt\backend\storage\openwebui\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\train_script.py: [Errno 22] Invalid argument: 'E:\\Projects\\opt\\backend\\storage\\openwebui\\cache\\embedding\\models\\models--sentence-transformers--all-MiniLM-L6-v2\\snapshots\\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\\train_script.py'
- Failed to scan endpoints in E:\Projects\opt\backend\storage\openwebui\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\train_script.py: [Errno 22] Invalid argument: 'E:\\Projects\\opt\\backend\\storage\\openwebui\\cache\\embedding\\models\\models--sentence-transformers--all-MiniLM-L6-v2\\snapshots\\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\\train_script.py'

## 📁 Current Directory Structure
```
backend/
  data/

config/
  __init__.py
  __pycache__/
  config_unified.py
  deprecated_personas/
  function_template.json
  ... and 12 more items

core/
  __pycache__/
  auth.py
  config_validation.py
  enhanced_api_gateway.py
  error_handler.py
  ... and 7 more items

data/

deprecated/
  knmi_api_service/

docs/
  KNMI_WEATHER_INTEGRATION.md

handlers/
  __init__.py
  exceptions.py

logs/
  rag_validation_report.json

memory/
  api/
  functions/

middleware/
  __init__.py
  performance_middleware.py
  rate_limit_middleware.py
  security_middleware.py

models/
  __init__.py
  __pycache__/
  models.py

pipelines/
  anti_hallucination_module/
  anti_hallucination_pipeline.py
  enhanced_memory_pipeline.py
  health_check.py
  memory_system/
  ... and 2 more items

routes/
  __init__.py
  chat.py
  debug.py
  gateway.py
  health.py
  ... and 4 more items

scripts/
  add-model.sh
  auto_install_function.py
  auto_install_pipeline.py
  clean-rebuild.ps1
  clean-rebuild.sh
  ... and 43 more items

services/
  __init__.py
  __pycache__/
  adaptive_learning.py
  auth_validator.py
  chat_service.py
  ... and 16 more items

setup/
  openwebui_api_keys.example.json
  secure_deployment.sh
  setup-api-keys.ps1
  setup-api-keys.sh
  setup-github.ps1
  ... and 3 more items

storage/
  .cache/
  backend/
  chroma/
  gateway/
  installer/
  ... and 5 more items

tests/
  helpers/
  investigate_function_calling_search.py
  test_bulk_memory_query.py
  test_chroma_metrics.py
  test_circuit_breaker.py
  ... and 38 more items

tools/
  __init__.py
  __pycache__/
  generate_metrics_doc.py
  global_date_time_filter.py
  integration_enhancements.py
  ... and 1 more items

utilities/
  __init__.py
  __pycache__/
  ai_tools.py
  alert_manager.py
  api_key_manager.py
  ... and 28 more items

```