# 🧹 MEMORY SYSTEM CLEANUP PLAN

## STEP 1: Remove Conflicting Function Files
- Keep ONLY: enhanced_memory_function_filter_v5_1_final.py
- Delete: All v4, v5, v5_minimal, v5_fixed versions

## STEP 2: Fix Threshold Conflicts
- Docker Compose: Change MEMORY_RETRIEVAL_THRESHOLD from 2.0 to -0.5
- Environment: Align all thresholds to negative values
- Config: Update settings.py memory_threshold to -0.5
- Function: Change similarity_threshold from 0.3 to -0.5

## STEP 3: Container Cache Clear
- Restart memory-api container
- Restart backend-openwebui container
- Clear any persisted vector cache

## STEP 4: Test Clean Import
- Import ONLY the v5.1 final function
- Test with clean identity introduction
- Verify cross-session persistence

## CONFLICTS IDENTIFIED:
1. Function v4: -0.3 (negative)
2. Function v5.1: 0.3 (positive) ❌
3. Docker: 2.0 (very high) ❌  
4. Environment: 0.2 (positive) ❌
5. Config: 2.0 (very high) ❌

## TARGET STATE:
- All thresholds: -0.5 (consistent negative)
- One function file only
- Clean cache
- No conflicts
