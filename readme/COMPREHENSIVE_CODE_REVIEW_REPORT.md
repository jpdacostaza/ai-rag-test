COMPREHENSIVE CODE REVIEW REPORT
==================================================
Generated: 2025-06-20 21:55:59
Project: e:\Projects\opt\backend
Files analyzed: 46

SUMMARY
--------------------
Total issues found: 199
Files with issues: 46 of 46

ISSUE BREAKDOWN BY SEVERITY
------------------------------
ERROR: 23 issues
STYLE: 176 issues
  - 1: 51
  - 121: 18
  - 15: 10
  - 17: 5
  - 9: 5

FLAKE8 ISSUES
--------------------

ai_tools.py:
  - e:\Projects\opt\backend\ai_tools.py:91:17: E999 SyntaxError: unterminated f-string literal (detected at line 93)

demo-test\comprehensive_code_review.py:
  - e:\Projects\opt\backend\demo-test\comprehensive_code_review.py:80:25: F541 f-string is missing placeholders

demo-test\demo_adaptive_learning.py:
  - e:\Projects\opt\backend\demo-test\demo_adaptive_learning.py:49:121: E501 line too long (121 > 120 characters)
  - e:\Projects\opt\backend\demo-test\demo_adaptive_learning.py:86:9: F841 local variable '___________result' is assigned to but never used
  - e:\Projects\opt\backend\demo-test\demo_adaptive_learning.py:154:17: F841 local variable '___________avg_time' is assigned to but never used

demo-test\demo_cache_manager.py:
  - e:\Projects\opt\backend\demo-test\demo_cache_manager.py:83:121: E501 line too long (246 > 120 characters)
  - e:\Projects\opt\backend\demo-test\demo_cache_manager.py:85:121: E501 line too long (232 > 120 characters)
  - e:\Projects\opt\backend\demo-test\demo_cache_manager.py:87:121: E501 line too long (232 > 120 characters)
  - e:\Projects\opt\backend\demo-test\demo_cache_manager.py:89:121: E501 line too long (139 > 120 characters)

demo-test\duplicate_code_detector.py:
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:23:1: F401 'typing.Dict' imported but unused
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:26:1: F401 'typing.Set' imported but unused
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:27:1: F401 'typing.Tuple' imported but unused
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:253:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:287:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:326:121: E501 line too long (125 > 120 characters)
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:329:121: E501 line too long (125 > 120 characters)
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:355:121: E501 line too long (125 > 120 characters)
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:358:121: E501 line too long (125 > 120 characters)
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:410:121: E501 line too long (128 > 120 characters)
  - e:\Projects\opt\backend\demo-test\duplicate_code_detector.py:416:121: E501 line too long (130 > 120 characters)

demo-test\duplicate_code_fixer.py:
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:101:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:104:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:127:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:130:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:136:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:143:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:150:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:154:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:160:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:163:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:168:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:206:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:212:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:218:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:221:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:225:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:227:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:232:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:237:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:245:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:252:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:255:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:269:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:278:22: W291 trailing whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:282:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:285:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:288:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:295:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:336:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:342:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:355:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:366:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:371:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:379:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:396:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:398:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:405:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:416:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:420:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:430:1: W293 blank line contains whitespace
  - e:\Projects\opt\backend\demo-test\duplicate_code_fixer.py:433:1: W293 blank line contains whitespace

demo-test\final_cleanup.py:
  - e:\Projects\opt\backend\demo-test\final_cleanup.py:6:1: F401 'typing.List' imported but unused
  - e:\Projects\opt\backend\demo-test\final_cleanup.py:281:21: F841 local variable '____________after_msg' is assigned to but never used

demo-test\final_code_fixer.py:
  - e:\Projects\opt\backend\demo-test\final_code_fixer.py:11:1: F401 'typing.Dict' imported but unused
  - e:\Projects\opt\backend\demo-test\final_code_fixer.py:12:1: F401 'typing.List' imported but unused
  - e:\Projects\opt\backend\demo-test\final_code_fixer.py:204:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\final_code_fixer.py:209:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\final_code_fixer.py:215:9: E722 do not use bare 'except'

demo-test\iterative_code_fixer.py:
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:7:1: F401 'os' imported but unused
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:14:1: F401 'typing.List' imported but unused
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:15:1: F401 'typing.Set' imported but unused
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:57:9: F841 local variable '________import_fixes' is assigned to but never used
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:474:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:483:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:491:19: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\iterative_code_fixer.py:498:15: F541 f-string is missing placeholders

demo-test\simple_duplicate_detector.py:
  - e:\Projects\opt\backend\demo-test\simple_duplicate_detector.py:240:15: F541 f-string is missing placeholders
  - e:\Projects\opt\backend\demo-test\simple_duplicate_detector.py:275:15: F541 f-string is missing placeholders

demo-test\test_adaptive_learning.py:
  - e:\Projects\opt\backend\demo-test\test_adaptive_learning.py:357:9: F841 local variable '____________overall_status' is assigned to but never used

error_handler.py:
  - e:\Projects\opt\backend\error_handler.py:43:121: E501 line too long (122 > 120 characters)

human_logging.py:
  - e:\Projects\opt\backend\human_logging.py:71:13: F841 local variable '___________reset' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:71:31: F841 local variable '___________bold' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:71:48: F841 local variable '___________dim' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:77:13: F841 local variable '____________level_color' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:77:39: F841 local variable '____________reset' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:77:59: F841 local variable '____________bold' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:77:78: F841 local variable '____________dim' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:80:9: F841 local variable '____________timestamp' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:192:5: F841 local variable '____________tools_info' is assigned to but never used
  - e:\Projects\opt\backend\human_logging.py:193:5: F841 local variable '____________req_id_info' is assigned to but never used

init_cache.py:
  - e:\Projects\opt\backend\init_cache.py:32:121: E501 line too long (166 > 120 characters)

main.py:
  - e:\Projects\opt\backend\main.py:44:1: F401 'human_logging.init_logging' imported but unused
  - e:\Projects\opt\backend\main.py:49:20: F821 undefined name 'model_manager_router'
  - e:\Projects\opt\backend\main.py:52:20: F821 undefined name 'upload_router'
  - e:\Projects\opt\backend\main.py:54:20: F821 undefined name 'enhanced_router'
  - e:\Projects\opt\backend\main.py:55:20: F821 undefined name 'feedback_router'
  - e:\Projects\opt\backend\main.py:68:5: F841 local variable '___spinner' is assigned to but never used
  - e:\Projects\opt\backend\main.py:92:23: F821 undefined name 'initialize_storage'
  - e:\Projects\opt\backend\main.py:120:33: F821 undefined name 'ensure_model_available'
  - e:\Projects\opt\backend\main.py:152:11: F821 undefined name 'refresh_model_cache'
  - e:\Projects\opt\backend\main.py:157:26: F821 undefined name 'initialize_cache_management'
  - e:\Projects\opt\backend\main.py:170:23: F821 undefined name 'start_watchdog_service'
  - e:\Projects\opt\backend\main.py:174:11: F821 undefined name 'start_enhanced_background_tasks'
  - e:\Projects\opt\backend\main.py:188:5: F841 local variable '___health' is assigned to but never used
  - e:\Projects\opt\backend\main.py:248:21: F821 undefined name 'get_cache_manager'
  - e:\Projects\opt\backend\main.py:286:27: F821 undefined name 'get_health_status'
  - e:\Projects\opt\backend\main.py:319:16: F821 undefined name 'get_watchdog'
  - e:\Projects\opt\backend\main.py:330:16: F821 undefined name 'get_watchdog'
  - e:\Projects\opt\backend\main.py:353:16: F821 undefined name 'get_watchdog'
  - e:\Projects\opt\backend\main.py:368:20: F821 undefined name 'StorageManager'
  - e:\Projects\opt\backend\main.py:371:19: F821 undefined name 'StorageManager'
  - e:\Projects\opt\backend\main.py:746:121: E501 line too long (125 > 120 characters)
  - e:\Projects\opt\backend\main.py:752:121: E501 line too long (154 > 120 characters)
  - e:\Projects\opt\backend\main.py:781:28: F821 undefined name 'get_time_from_timeanddate'
  - e:\Projects\opt\backend\main.py:989:121: E501 line too long (132 > 120 characters)
  - e:\Projects\opt\backend\main.py:1009:121: E501 line too long (181 > 120 characters)
  - e:\Projects\opt\backend\main.py:1013:33: F821 undefined name 'get_cache_manager'
  - e:\Projects\opt\backend\main.py:1094:17: F841 local variable '___chunks_stored' is assigned to but never used
  - e:\Projects\opt\backend\main.py:1130:23: F821 undefined name '_model_cache'
  - e:\Projects\opt\backend\main.py:1130:54: F821 undefined name '_model_cache'
  - e:\Projects\opt\backend\main.py:1132:15: F821 undefined name 'refresh_model_cache'
  - e:\Projects\opt\backend\main.py:1134:19: F821 undefined name '_model_cache'
  - e:\Projects\opt\backend\main.py:1206:17: F841 local variable '___data' is assigned to but never used
  - e:\Projects\opt\backend\main.py:1260:21: F821 undefined name 'get_cache_manager'
  - e:\Projects\opt\backend\main.py:1272:21: F821 undefined name 'get_cache_manager'
  - e:\Projects\opt\backend\main.py:1290:21: F821 undefined name 'get_cache_manager'
  - e:\Projects\opt\backend\main.py:1296:121: E501 line too long (154 > 120 characters)

model_manager.py:
  - e:\Projects\opt\backend\model_manager.py:27:5: F824 `global _model_cache` is unused: name is never assigned in scope

storage\openwebui\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\train_script.py:
  - e:\Projects\opt\backend\storage\openwebui\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\train_script.py:0:1: E902 OSError: [Errno 22] Invalid argument: 'e:\\Projects\\opt\\backend\\storage\\openwebui\\cache\\embedding\\models\\models--sentence-transformers--all-MiniLM-L6-v2\\snapshots\\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\\train_script.py'

watchdog.py:
  - e:\Projects\opt\backend\watchdog.py:687:17: F841 local variable '____________status_emoji' is assigned to but never used

BLACK ISSUES
--------------------

adaptive_learning.py:
  - Black formatting issues found

ai_tools.py:
  - Black formatting issues found

app.py:
  - Black formatting issues found

cache_manager.py:
  - Black formatting issues found

comprehensive_cleanup.py:
  - Black formatting issues found

database.py:
  - Black formatting issues found

database_manager.py:
  - Black formatting issues found

debug_models.py:
  - Black formatting issues found

demo-test\auto_code_fix.py:
  - Black formatting issues found

demo-test\comprehensive_code_review.py:
  - Black formatting issues found

demo-test\demo_adaptive_learning.py:
  - Black formatting issues found

demo-test\demo_ai_tools.py:
  - Black formatting issues found

demo-test\demo_cache_manager.py:
  - Black formatting issues found

demo-test\duplicate_code_detector.py:
  - Black formatting issues found

demo-test\duplicate_code_fixer.py:
  - Black formatting issues found

demo-test\enhanced_auto_fix.py:
  - Black formatting issues found

demo-test\final_cleanup.py:
  - Black formatting issues found

demo-test\final_code_fixer.py:
  - Black formatting issues found

demo-test\iterative_code_fixer.py:
  - Black formatting issues found

demo-test\multi_pass_fixer.py:
  - Black formatting issues found

demo-test\quality_summary.py:
  - Black formatting issues found

demo-test\simple_cache_test.py:
  - Black formatting issues found

demo-test\simple_duplicate_detector.py:
  - Black formatting issues found

demo-test\targeted_import_fixer.py:
  - Black formatting issues found

demo-test\test_adaptive_learning.py:
  - Black formatting issues found

demo-test\test_cache_manager.py:
  - Black formatting issues found

enhanced_document_processing.py:
  - Black formatting issues found

enhanced_integration.py:
  - Black formatting issues found

error_handler.py:
  - Black formatting issues found

feedback_router.py:
  - Black formatting issues found

force_refresh.py:
  - Black formatting issues found

human_logging.py:
  - Black formatting issues found

init_cache.py:
  - Black formatting issues found

main.py:
  - Black formatting issues found

model_manager.py:
  - Black formatting issues found

rag.py:
  - Black formatting issues found

refresh-models.py:
  - Black formatting issues found

simple_cleanup.py:
  - Black formatting issues found

storage\openwebui\cache\embedding\models\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf\train_script.py:
  - Black formatting issues found

storage_manager.py:
  - Black formatting issues found

upload.py:
  - Black formatting issues found

utils\__init__.py:
  - Black formatting issues found

utils\error_handling.py:
  - Black formatting issues found

utils\file_validator.py:
  - Black formatting issues found

utils\logging_setup.py:
  - Black formatting issues found

watchdog.py:
  - Black formatting issues found

PYLINT ISSUES
--------------------

ai_tools.py:
  - ai_tools.py:91:16: E0001: Parsing failed: 'unterminated f-string literal (detected at line 93) (ai_tools, line 91)' (syntax-error)

database.py:
  - database.py:4:0: E0001: Cannot import 'ai_tools' due to 'unterminated f-string literal (detected at line 93) (ai_tools, line 91)' (syntax-error)

demo-test\demo_adaptive_learning.py:
  - demo-test\demo_adaptive_learning.py:7:0: E0401: Unable to import 'adaptive_learning' (import-error)

demo-test\demo_cache_manager.py:
  - demo-test\demo_cache_manager.py:12:0: E0401: Unable to import 'cache_manager' (import-error)

demo-test\simple_cache_test.py:
  - demo-test\simple_cache_test.py:11:0: E0401: Unable to import 'cache_manager' (import-error)

demo-test\test_adaptive_learning.py:
  - demo-test\test_adaptive_learning.py:9:0: E0401: Unable to import 'adaptive_learning' (import-error)
  - demo-test\test_adaptive_learning.py:10:0: E0401: Unable to import 'adaptive_learning' (import-error)
  - demo-test\test_adaptive_learning.py:11:0: E0401: Unable to import 'adaptive_learning' (import-error)
  - demo-test\test_adaptive_learning.py:12:0: E0401: Unable to import 'adaptive_learning' (import-error)

enhanced_integration.py:
  - enhanced_integration.py:68:16: W0707: Consider explicitly re-raising using 'except ValueError as exc' and 'raise HTTPException(status_code=400, detail='Invalid chunking strategy. Options: {[s.value for s in ChunkingStrategy]}') from exc' (raise-missing-from)
  - enhanced_integration.py:177:12: W0707: Consider explicitly re-raising using 'except ValueError as exc' and 'raise HTTPException(status_code=400, detail=f'Invalid feedback type. Options: {[f.value for f in FeedbackType]}') from exc' (raise-missing-from)

error_handler.py:
  - error_handler.py:249:11: W0718: Catching too general exception Exception (broad-exception-caught)
  - error_handler.py:264:19: W0718: Catching too general exception Exception (broad-exception-caught)

main.py:
  - main.py:26:0: E0001: Cannot import 'ai_tools' due to 'unterminated f-string literal (detected at line 93) (ai_tools, line 91)' (syntax-error)
  - main.py:27:0: E0001: Cannot import 'ai_tools' due to 'unterminated f-string literal (detected at line 93) (ai_tools, line 91)' (syntax-error)
  - main.py:28:0: E0001: Cannot import 'ai_tools' due to 'unterminated f-string literal (detected at line 93) (ai_tools, line 91)' (syntax-error)

utils\error_handling.py:
  - utils\error_handling.py:40:15: W0718: Catching too general exception Exception (broad-exception-caught)
  - utils\error_handling.py:75:24: W1203: Use lazy % formatting in logging functions (logging-fstring-interpolation)
  - utils\error_handling.py:79:24: C0415: Import outside toplevel (time) (import-outside-toplevel)
  - utils\error_handling.py:83:24: W1203: Use lazy % formatting in logging functions (logging-fstring-interpolation)
  - utils\error_handling.py:98:35: W0621: Redefining name 'logger' from outer scope (line 14) (redefined-outer-name)
  - utils\error_handling.py:114:12: W1203: Use lazy % formatting in logging functions (logging-fstring-interpolation)

utils\file_validator.py:
  - utils\file_validator.py:56:18: W0612: Unused variable 'error' (unused-variable)

RECOMMENDATIONS
--------------------
1. Fix critical errors first (F-codes, syntax errors)
2. Address style issues with automated tools (black, isort)
3. Fix line length and whitespace issues
4. Remove unused imports and variables
5. Add proper type hints where missing
6. Consider adding docstrings for public functions

PRIORITY FILES (most issues)
------------------------------
demo-test\duplicate_code_fixer.py: 42 issues
main.py: 40 issues
demo-test\duplicate_code_detector.py: 12 issues
human_logging.py: 11 issues
demo-test\iterative_code_fixer.py: 9 issues
utils\error_handling.py: 7 issues
demo-test\demo_cache_manager.py: 6 issues
demo-test\final_code_fixer.py: 6 issues
demo-test\test_adaptive_learning.py: 6 issues
demo-test\demo_adaptive_learning.py: 5 issues