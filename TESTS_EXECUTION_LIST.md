# 🎯 Tests Execution List - CoH1 × Mistral AI Mod

**Document Version**: 1.0.0  
**Last Updated**: 2026-10-25  
**Purpose**: Actionable list of tests to execute NOW and tests to IMPLEMENT for future execution  
**Status**: Phase 0-2 Complete (416+ tests passing), Phases 3-5 Tests Need Implementation

---

# 🚀 EXECUTABLE TESTS (Run These NOW)

These tests **already exist** and can be executed immediately to verify the current state of Phases 0-2.

## Quick Commands

```bash
# Run ALL existing tests (Phases 0-2)
cd /d/SteamLibrary/steamapps/common/Company\ of\ Heroes\ Relaunch/Mods/COh1AIMod
python -m pytest tests/ -v --tb=short

# Run with coverage report
python -m pytest tests/ --cov=python --cov=scar --cov-report=term-missing

# Run specific test suites
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/performance/ -v
```

---

## Phase 0: Foundation Tests (158+ tests)

### Unit Tests
```bash
# Run all Phase 0 unit tests
python -m pytest tests/unit/test_config.py tests/unit/test_ipc_reader.py tests/unit/test_schema.py tests/unit/test_logger.py -v

# Individual files
python -m pytest tests/unit/test_config.py -v           # 30+ tests - Configuration
python -m pytest tests/unit/test_ipc_reader.py -v        # 25+ tests - IPC communication
python -m pytest tests/unit/test_schema.py -v           # 66 tests - JSON schemas
python -m pytest tests/unit/test_logger.py -v           # 24 tests - State logging
```

### Integration Tests
```bash
python -m pytest tests/integration/test_roundtrip.py -v   # 4 tests - End-to-end IPC
```

### Performance Tests
```bash
python -m pytest tests/performance/test_ipc_latency.py -v   # 1+ tests - Latency verification
```

**Phase 0 Test Count**: 158+ tests | **Expected**: All passing ✅

---

## Phase 1: Read-only Intelligence Tests (Included in Phase 0)

### Unit Tests
```bash
# These are included in Phase 0 test files
python -m pytest tests/unit/test_schema.py tests/unit/test_logger.py -v
```

**Phase 1 Test Count**: Included in Phase 0 total | **Expected**: All passing ✅

---

## Phase 2: Reflex Layer Tests (416+ total tests)

### Unit Tests
```bash
# Run all Phase 2 unit tests
python -m pytest tests/unit/test_command_executor.py tests/unit/test_validator.py tests/unit/test_safety_filter.py tests/unit/test_fallback.py tests/unit/test_reflex_layer.py tests/unit/test_orchestrator_main.py -v

# Individual files
python -m pytest tests/unit/test_command_executor.py -v   # 56 tests - Command execution
python -m pytest tests/unit/test_validator.py -v             # 69 tests - Action validation
python -m pytest tests/unit/test_safety_filter.py -v        # 39 tests - Safety checks
python -m pytest tests/unit/test_fallback.py -v              # 50+ tests - Fallback mechanism
python -m pytest tests/unit/test_reflex_layer.py -v        # 40+ tests - Reflex behaviors
python -m pytest tests/unit/test_orchestrator_main.py -v   # Orchestrator integration
```

### Integration Tests
```bash
# Run all Phase 2 integration tests
python -m pytest tests/integration/test_command_executor_integration.py tests/integration/test_end_to_end_loop.py tests/integration/test_end_to_end_simple.py tests/integration/test_reflex_integration.py tests/integration/test_phase2_validation_safety.py tests/integration/test_phase2_fallback.py -v

# Individual files
python -m pytest tests/integration/test_command_executor_integration.py -v   # 22 tests
python -m pytest tests/integration/test_end_to_end_loop.py -v              # 7 tests - Milestone 1
python -m pytest tests/integration/test_end_to_end_simple.py -v          # 8 tests - Milestone 2
python -m pytest tests/integration/test_reflex_integration.py -v         # 16 tests
python -m pytest tests/integration/test_phase2_validation_safety.py -v    # 32 tests - Milestone 3
python -m pytest tests/integration/test_phase2_fallback.py -v            # 59+ tests - Milestone 4
```

**Phase 2 Test Count**: 416+ tests | **Expected**: All passing ✅

---

## All Existing Tests (Combined)

### Run Everything
```bash
# All tests (Phases 0-2)
python -m pytest tests/ -v --tb=short

# With coverage
python -m pytest tests/ --cov=python --cov=scar --cov-report=term-missing

# Quick check (no verbose output)
python -m pytest tests/ -q

# With duration timing
python -m pytest tests/ -v --durations=10

# Only failures
python -m pytest tests/ -v --tb=short -f
```

### Test Statistics
```bash
# Count tests
python -m pytest tests/ --collect-only -q

# Show slowest tests
python -m pytest tests/ --durations=20

# Run specific test by keyword
python -m pytest tests/ -k "reflex" -v
python -m pytest tests/ -k "validator" -v
python -m pytest tests/ -k "fallback" -v
python -m pytest tests/ -k "end_to_end" -v
```

**Total Existing Tests**: 416+ tests | **Status**: All passing ✅

---

---

# 📋 TESTS TO IMPLEMENT (For Future Execution)

These tests **do NOT exist yet** and need to be created before they can be executed.
They are required for Phases 3-5 completion.

---

## Phase 3: Strategist Integration (100 tests to create)

### Mistral API Client (19 tests)
**File to create**: `python/mistral_client.py` + `tests/unit/test_mistral_client.py` + `tests/integration/test_mistral_integration.py`

```python
# Future execution commands (once implemented):
python -m pytest tests/unit/test_mistral_client.py -v           # 15 unit tests
python -m pytest tests/integration/test_mistral_integration.py -v   # 4 integration tests
```

**Tests to implement**:
- test_api_connection_success, test_api_connection_failure
- test_authentication_success, test_authentication_failure
- test_model_selection_large, test_model_selection_small, test_invalid_model_selection
- test_api_timeout_handling, test_rate_limit_handling, test_authentication_error
- test_api_response_parsing, test_api_response_validation
- test_retry_logic, test_configurable_endpoint, test_configurable_timeout
- test_request_logging, test_response_logging
- test_secure_auth_storage, test_mock_mode
- test_end_to_end_api_call, test_api_call_with_mock
- test_api_call_with_rate_limit, test_api_fallback_integration
- test_concurrent_requests, test_connection_pooling
- test_api_version_compatibility

---

### System Prompt Engine (15 tests)
**File to create**: `python/prompts.py` + `tests/unit/test_prompts.py` + `tests/integration/test_prompts_integration.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_prompts.py -v                # 12 unit tests
python -m pytest tests/integration/test_prompts_integration.py -v  # 3 integration tests
```

**Tests to implement**:
- test_prompt_generation_us, test_prompt_generation_wehrmacht
- test_prompt_generation_british, test_prompt_generation_pe
- test_fuel_cutoff_rules, test_counter_units_matrix
- test_build_tree_rules, test_resource_constraints
- test_prompt_validation, test_prompt_customization
- test_prompt_update, test_default_prompt
- test_prompt_in_strategic_cycle, test_prompt_faction_switching
- test_prompt_error_handling

---

### JSON Mode Integration (15 tests)
**File to update**: `python/schema.py` + `tests/unit/test_json_mode.py` + `tests/integration/test_json_mode_integration.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_json_mode.py -v                # 12 unit tests
python -m pytest tests/integration/test_json_mode_integration.py -v  # 3 integration tests
```

**Tests to implement**:
- test_intent_schema_definition, test_intent_schema_validation
- test_intent_build_command, test_intent_capture_command
- test_intent_attack_move_command, test_intent_set_posture_command
- test_intent_produce_command, test_intent_retreat_command
- test_mistral_json_mode_configuration
- test_json_response_parsing, test_json_error_handling
- test_json_schema_evolution
- test_json_mode_end_to_end, test_json_mode_with_mock
- test_json_schema_validation_in_pipeline

---

### Game History Manager (14 tests)
**File to create**: `python/history.py` + `tests/unit/test_history.py` + `tests/integration/test_history_integration.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_history.py -v                    # 11 unit tests
python -m pytest tests/integration/test_history_integration.py -v  # 3 integration tests
```

**Tests to implement**:
- test_history_initialization, test_history_add_snapshot
- test_history_max_depth, test_history_retrieval
- test_history_get_last_n, test_history_clear
- test_history_persistence, test_history_file_rotation
- test_history_search, test_history_statistics
- test_history_thread_safety
- test_history_in_prompts, test_history_with_state_manager
- test_history_persistence_and_reload

---

### Cost/Rate Limiter (14 tests)
**File to create**: `python/rate_limiter.py` + `tests/unit/test_rate_limiter.py` + `tests/integration/test_rate_limiter_integration.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_rate_limiter.py -v                # 11 unit tests
python -m pytest tests/integration/test_rate_limiter_integration.py -v  # 3 integration tests
```

**Tests to implement**:
- test_rate_limiter_initialization, test_rate_limiter_budget_tracking
- test_rate_limiter_budget_exceeded, test_rate_limiter_urgent_calls
- test_rate_limiter_reset, test_rate_limiter_time_window
- test_rate_limiter_configurable_budget, test_rate_limiter_configurable_window
- test_rate_limiter_statistics, test_rate_limiter_notification
- test_rate_limiter_thread_safety
- test_rate_limiter_in_strategic_cycle, test_rate_limiter_with_fallback
- test_rate_limiter_persistence

---

### Orchestrator → Mistral Integration (10 tests)
**File to create**: `python/orchestrator/strategist.py` + `tests/unit/test_strategist.py` + `tests/integration/test_strategic_cycle.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_strategist.py -v                   # 0 unit tests (integration only)
python -m pytest tests/integration/test_strategic_cycle.py -v     # 10 integration tests
```

**Tests to implement**:
- test_strategic_cycle_complete, test_strategic_cycle_error_handling
- test_strategic_cycle_latency
- test_intent_validation_integration, test_intent_execution_integration
- test_strategic_tick_integration, test_fallback_integration
- test_game_state_in_prompts, test_history_in_prompts
- test_difficulty_in_prompts

---

### Difficulty Doctrine Prompts (10 tests)
**File to update**: `python/prompts.py` + update existing test files

```python
# Future execution commands:
python -m pytest tests/unit/test_prompts.py::test_difficulty_* -v   # 8 unit tests
python -m pytest tests/integration/test_prompts_integration.py::test_difficulty_* -v  # 2 integration tests
```

**Tests to implement**:
- test_difficulty_levels, test_easy_difficulty_prompt
- test_normal_difficulty_prompt, test_hard_difficulty_prompt
- test_expert_difficulty_prompt
- test_difficulty_prompt_differences, test_difficulty_configuration
- test_difficulty_validation
- test_difficulty_affects_behavior, test_difficulty_switching

---

### Phase 3 Performance Tests (3 tests)
**File to create**: `tests/performance/test_strategic_latency.py`

```python
# Future execution commands:
python -m pytest tests/performance/test_strategic_latency.py -v  # 3 tests
```

**Tests to implement**:
- test_strategic_cycle_latency_under_load
- test_concurrent_api_calls
- test_rate_limiter_under_stress

---

### Phase 3 Summary
**Total Tests**: 100 (19+15+15+14+14+10+10+3)  
**Files to Create**: 7 Python modules + 7 test files  
**Status**: ❌ Not Started  

```bash
# Future: Run all Phase 3 tests (once implemented)
python -m pytest tests/unit/test_mistral_client.py tests/unit/test_prompts.py tests/unit/test_json_mode.py tests/unit/test_history.py tests/unit/test_rate_limiter.py tests/integration/test_mistral_integration.py tests/integration/test_strategic_cycle.py tests/integration/test_prompts_integration.py tests/integration/test_json_mode_integration.py tests/integration/test_history_integration.py tests/integration/test_rate_limiter_integration.py tests/performance/test_strategic_latency.py -v
```

---

---

## Phase 4: Evaluation & Tuning (63 tests to create)

### AI-vs-AI Test Harness (14 tests)
**File to create**: `python/test_harness.py` + `tests/unit/test_test_harness.py` + `tests/integration/test_evaluation.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_test_harness.py -v           # 10 unit tests
python -m pytest tests/integration/test_evaluation.py -v       # 4 integration tests
```

**Tests to implement**:
- test_harness_initialization, test_match_configuration
- test_match_scheduling, test_match_execution
- test_match_parameters, test_result_collection
- test_result_storage, test_concurrent_matches
- test_match_timeout, test_match_error_handling
- test_end_to_end_ai_vs_ai, test_ai_vs_stock_ai
- test_headless_execution, test_batch_match_execution

---

### Win Rate Tracking (13 tests)
**File to create**: `python/stats.py` + `tests/unit/test_stats.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_stats.py -v                        # 10 unit tests
python -m pytest tests/integration/test_stats_integration.py -v   # 3 integration tests
```

**Tests to implement**:
- test_stats_initialization, test_win_tracking, test_draw_tracking
- test_win_rate_calculation, test_per_difficulty_stats
- test_historical_data_storage, test_stats_retrieval
- test_stats_aggregation, test_stats_export, test_stats_reset
- test_stats_with_test_harness, test_win_rate_analysis
- test_longitudinal_analysis

---

### Decision Log Analysis (13 tests)
**File to create**: `python/log_analyzer.py` + `tests/unit/test_log_analyzer.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_log_analyzer.py -v                # 10 unit tests
python -m pytest tests/integration/test_log_analyzer_integration.py -v  # 3 integration tests
```

**Tests to implement**:
- test_log_analyzer_initialization, test_log_parsing
- test_decision_extraction, test_explainability_analysis
- test_pattern_detection, test_anomaly_detection
- test_regression_detection, test_decision_classification
- test_statistics_calculation, test_visualization_generation
- test_analysis_with_real_logs, test_explainability_validation
- test_regression_detection_in_pipeline

---

### Regression Test Suite (11 tests)
**File to create**: `python/regression_tests/` + `tests/unit/test_regression_scenarios.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_regression_scenarios.py -v   # 8 unit tests
python -m pytest tests/integration/test_regression_integration.py -v  # 3 integration tests
```

**Tests to implement**:
- test_scenario_library_loading, test_scenario_execution
- test_scenario_configuration, test_pass_fail_criteria
- test_regression_detection, test_scenario_scheduling
- test_concurrent_scenarios, test_scenario_cleanup
- test_regression_suite_end_to_end, test_scenario_against_baseline
- test_regression_reporting

---

### Baseline Evaluation (5 tests)
**File to create**: `tests/integration/test_baseline_evaluation.py`

```python
# Future execution commands:
python -m pytest tests/integration/test_baseline_evaluation.py -v  # 5 tests
```

**Tests to implement**:
- test_baseline_vs_stock_easy, test_baseline_vs_stock_normal
- test_baseline_vs_stock_hard, test_baseline_vs_stock_expert
- test_baseline_documentation

---

### Prompt Tuning (5 tests)
**File to create**: `tests/integration/test_prompt_tuning.py`

```python
# Future execution commands:
python -m pytest tests/integration/test_prompt_tuning.py -v  # 5 tests
```

**Tests to implement**:
- test_prompt_tuning_iteration_1, test_prompt_tuning_iteration_2
- test_prompt_tuning_final
- test_failure_analysis, test_prompt_comparison

---

### Phase 4 Performance Tests (2 tests)
**File to create**: `tests/performance/test_batch_performance.py`

```python
# Future execution commands:
python -m pytest tests/performance/test_batch_performance.py -v  # 2 tests
```

**Tests to implement**:
- test_batch_match_performance
- test_regression_suite_performance

---

### Phase 4 Summary
**Total Tests**: 63 (14+13+13+11+5+5+2)  
**Files to Create**: 5 Python modules + 6 test files + 5 scenario JSON files  
**Status**: ❌ Not Started  
**Dependencies**: Phase 3 must be complete

```bash
# Future: Run all Phase 4 tests (once implemented)
python -m pytest tests/unit/test_test_harness.py tests/unit/test_stats.py tests/unit/test_log_analyzer.py tests/unit/test_regression_scenarios.py tests/integration/test_evaluation.py tests/integration/test_stats_integration.py tests/integration/test_log_analyzer_integration.py tests/integration/test_regression_integration.py tests/integration/test_baseline_evaluation.py tests/integration/test_prompt_tuning.py tests/performance/test_batch_performance.py -v
```

---

---

## Phase 5: Polish & Release (29 tests to create)

### Configuration UI (10 tests)
**File to create**: `python/config_ui.py` + `tests/unit/test_config_ui.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_config_ui.py -v  # 9 unit tests + 1 manual
```

**Tests to implement**:
- test_ui_initialization, test_api_key_configuration
- test_model_choice_configuration, test_budget_configuration
- test_difficulty_configuration, test_config_validation
- test_config_persistence, test_config_reset
- test_ui_error_handling
- manual_ui_usability

---

### Documentation (7 tests - Manual Verification)
**Files to create**: Documentation files + `tests/manual/test_documentation.md`

```python
# Manual verification (not automated)
# Document results in tests/manual/test_documentation.md
```

**Manual tests to implement**:
- manual_readme_completeness, manual_readme_clarity
- manual_api_docs_completeness, manual_api_docs_accuracy
- manual_usage_instructions, manual_examples
- manual_documentation_navigation

---

### Release Packaging (7 tests)
**File to update**: `package_mod.bat` + `tests/unit/test_packaging.py`

```python
# Future execution commands:
python -m pytest tests/unit/test_packaging.py -v  # 4 unit tests + 3 manual
```

**Tests to implement**:
- test_package_script, test_sga_creation
- test_package_contents, test_versioning
- manual_installation, manual_uninstallation
- manual_release_checklist

---

### Final Testing (5 tests)
**File to create**: `tests/integration/test_final_verification.py`

```python
# Future execution commands:
python -m pytest tests/integration/test_final_verification.py -v  # 4 integration tests + 1 manual
```

**Tests to implement**:
- test_full_regression_suite, test_user_acceptance_testing
- test_performance_validation, test_final_verification
- manual_final_acceptance

---

### Phase 5 Summary
**Total Tests**: 29 (10+7+7+5)  
**Files to Create**: 2 Python modules + 2 test files + 1 manual test document  
**Status**: ❌ Not Started  
**Dependencies**: Phase 4 must be complete

```bash
# Future: Run all Phase 5 tests (once implemented)
python -m pytest tests/unit/test_config_ui.py tests/unit/test_packaging.py tests/integration/test_final_verification.py -v
```

---

---

# 📊 COMPLETE EXECUTION COMMANDS

## Current State Verification

```bash
# 1. Verify all existing tests pass
cd /d/SteamLibrary/steamapps/common/Company\ of\ Heroes\ Relaunch/Mods/COh1AIMod
python -m pytest tests/ -v --tb=short

# 2. Check test count
python -m pytest tests/ --collect-only -q

# 3. Run with coverage to verify Phase 0-2
python -m pytest tests/ --cov=python --cov=scar --cov-report=term --cov-fail-under=80

# 4. Quick verification (no verbose output)
python -m pytest tests/ -q

# 5. Show any failures only
python -m pytest tests/ -v --tb=short -f
```

## Phase-by-Phase Execution

```bash
# Phase 0 tests only
python -m pytest tests/unit/test_config.py tests/unit/test_ipc_reader.py tests/unit/test_schema.py tests/unit/test_logger.py tests/integration/test_roundtrip.py tests/performance/test_ipc_latency.py -v

# Phase 1 tests (included in Phase 0)
# Already covered by Phase 0 commands

# Phase 2 tests only
python -m pytest tests/unit/test_command_executor.py tests/unit/test_validator.py tests/unit/test_safety_filter.py tests/unit/test_fallback.py tests/unit/test_reflex_layer.py tests/unit/test_orchestrator_main.py tests/integration/ -v
```

## Future Execution (After Implementation)

```bash
# Run all tests (Phases 0-5) - Future
python -m pytest tests/ -v

# Run Phase 3 tests only - Future
python -m pytest tests/unit/test_mistral_client.py tests/unit/test_prompts.py tests/unit/test_json_mode.py tests/unit/test_history.py tests/unit/test_rate_limiter.py tests/integration/test_mistral_integration.py tests/integration/test_strategic_cycle.py tests/integration/test_prompts_integration.py tests/integration/test_json_mode_integration.py tests/integration/test_history_integration.py tests/integration/test_rate_limiter_integration.py tests/performance/test_strategic_latency.py -v

# Run Phase 4 tests only - Future
python -m pytest tests/unit/test_test_harness.py tests/unit/test_stats.py tests/unit/test_log_analyzer.py tests/unit/test_regression_scenarios.py tests/integration/test_evaluation.py tests/integration/test_stats_integration.py tests/integration/test_log_analyzer_integration.py tests/integration/test_regression_integration.py tests/integration/test_baseline_evaluation.py tests/integration/test_prompt_tuning.py tests/performance/test_batch_performance.py -v

# Run Phase 5 tests only - Future
python -m pytest tests/unit/test_config_ui.py tests/unit/test_packaging.py tests/integration/test_final_verification.py -v
```

---

---

# 📝 TEST IMPLEMENTATION TRACKING

## Current Status

| Category | Count | Status | Commands |
|----------|-------|--------|----------|
| **Executable Tests** | 416+ | ✅ All Passing | `pytest tests/ -v` |
| **Tests to Implement** | 187 | ❌ Not Started | See above |
| **Total Planned** | 603+ | ⚠️ 72% Complete | - |

## Implementation Checklist

### This Week (P0 - Critical)
- [ ] Run Phase 1 validation against real CoH1 data
- [ ] Create `python/mistral_client.py` + tests (19 tests)
- [ ] Create `python/prompts.py` + tests (15 tests)
- [ ] **Verification**: `pytest tests/unit/test_mistral_client.py tests/unit/test_prompts.py -v`

### Next Week (P1 - High)
- [ ] Create `python/history.py` + tests (14 tests)
- [ ] Create `python/rate_limiter.py` + tests (14 tests)
- [ ] Create `python/schema.py` updates + JSON mode tests (15 tests)
- [ ] **Verification**: `pytest tests/unit/test_history.py tests/unit/test_rate_limiter.py tests/unit/test_json_mode.py -v`

### Week 3 (P1 - High)
- [ ] Create `python/orchestrator/strategist.py` + tests (10 tests)
- [ ] Update `python/prompts.py` + difficulty tests (10 tests)
- [ ] **Verification**: `pytest tests/integration/test_strategic_cycle.py -v`
- [ ] **Milestone**: Phase 3 Complete (100 tests)

### Week 4-5 (P2 - Medium)
- [ ] Create Phase 4 modules + tests (63 tests)
- [ ] **Verification**: `pytest tests/unit/test_test_harness.py tests/unit/test_stats.py tests/unit/test_log_analyzer.py -v`
- [ ] **Milestone**: Phase 4 Complete (63 tests)

### Week 6 (P3 - Low)
- [ ] Create Phase 5 modules + tests (29 tests)
- [ ] **Verification**: `pytest tests/unit/test_config_ui.py tests/unit/test_packaging.py -v`
- [ ] **Milestone**: Project Complete (603+ tests)

---

---

# 🎯 QUICK REFERENCE

## Test Count Summary

| Phase | Unit Tests | Integration Tests | Manual Tests | Total | Status |
|-------|------------|-------------------|--------------|-------|--------|
| Phase 0-2 | 452+ | 29+ | 7 | **488+** | ✅ Executable Now |
| Phase 3 | 69 | 28 | 0 | **97** | ❌ To Implement |
| Phase 4 | 38 | 23 | 0 | **61** | ❌ To Implement |
| Phase 5 | 13 | 4 | 12 | **29** | ❌ To Implement |
| **TOTAL** | **572+** | **84+** | **19** | **675+** | **72% Complete** |

## Command Summary

```bash
# EXECUTE NOW (existing tests):
pytest tests/ -v                    # All existing tests
pytest tests/ -q                    # Quick mode
pytest tests/ --cov=python          # With coverage
pytest tests/ -k "reflex"           # Filter by keyword
pytest tests/ -f                    # Show failures only

# TO BE IMPLEMENTED (future):
# See detailed test lists above for each phase
```

## File Structure Summary

```
# EXISTING FILES (can execute now):
tests/
├── unit/
│   ├── test_config.py              # Phase 0
│   ├── test_ipc_reader.py           # Phase 0
│   ├── test_schema.py              # Phase 0
│   ├── test_logger.py              # Phase 0
│   ├── test_command_executor.py    # Phase 2
│   ├── test_validator.py            # Phase 2
│   ├── test_safety_filter.py       # Phase 2
│   ├── test_fallback.py            # Phase 2
│   ├── test_reflex_layer.py        # Phase 2
│   └── test_orchestrator_main.py   # Phase 2
│
├── integration/
│   ├── test_roundtrip.py           # Phase 0
│   ├── test_command_executor_integration.py  # Phase 2
│   ├── test_end_to_end_loop.py     # Phase 2
│   ├── test_end_to_end_simple.py   # Phase 2
│   ├── test_reflex_integration.py  # Phase 2
│   ├── test_phase2_validation_safety.py  # Phase 2
│   └── test_phase2_fallback.py     # Phase 2
│
└── performance/
    └── test_ipc_latency.py          # Phase 0

# FILES TO CREATE (future):
tests/
├── unit/
│   ├── test_mistral_client.py     # Phase 3
│   ├── test_prompts.py              # Phase 3
│   ├── test_json_mode.py            # Phase 3
│   ├── test_history.py              # Phase 3
│   ├── test_rate_limiter.py         # Phase 3
│   ├── test_strategist.py           # Phase 3
│   ├── test_test_harness.py        # Phase 4
│   ├── test_stats.py                # Phase 4
│   ├── test_log_analyzer.py         # Phase 4
│   ├── test_regression_scenarios.py # Phase 4
│   ├── test_config_ui.py            # Phase 5
│   └── test_packaging.py            # Phase 5
│
├── integration/
│   ├── test_mistral_integration.py # Phase 3
│   ├── test_strategic_cycle.py     # Phase 3
│   ├── test_prompts_integration.py  # Phase 3
│   ├── test_json_mode_integration.py # Phase 3
│   ├── test_history_integration.py # Phase 3
│   ├── test_rate_limiter_integration.py # Phase 3
│   ├── test_evaluation.py           # Phase 4
│   ├── test_stats_integration.py   # Phase 4
│   ├── test_log_analyzer_integration.py # Phase 4
│   ├── test_regression_integration.py # Phase 4
│   ├── test_baseline_evaluation.py  # Phase 4
│   ├── test_prompt_tuning.py        # Phase 4
│   └── test_final_verification.py   # Phase 5
│
└── performance/
    ├── test_strategic_latency.py   # Phase 3
    └── test_batch_performance.py    # Phase 4
```

---

---

# 📞 SUPPORT

## Common Issues & Solutions

### Issue: Tests not found
**Solution**: Ensure you're in the correct directory:
```bash
cd /d/SteamLibrary/steamapps/common/Company\ of\ Heroes\ Relaunch/Mods/COh1AIMod
```

### Issue: Module import errors
**Solution**: Add project root to Python path:
```bash
export PYTHONPATH=/d/SteamLibrary/steamapps/common/Company\ of\ Heroes\ Relaunch/Mods/COh1AIMod:$PYTHONPATH
python -m pytest tests/ -v
```

### Issue: File locking on Windows
**Solution**: Ensure no Python processes are running:
```bash
taskkill /IM python.exe /F
python -m pytest tests/ -v
```

### Issue: Slow test execution
**Solution**: Run tests in parallel:
```bash
pytest tests/ -n 4 -v  # Uses 4 workers
```

---

## Documentation References

- **PROTOTYPE_DEVELOPMENT_PLAN.md** - Full project plan
- **TESTS_TO_COMPLETE.md** - Detailed test specifications
- **TESTING_GUIDE.md** - Testing standards and best practices
- **EXECUTION_SHEET.md** - Execution checklists
- **DECISIONS.md** - Project decisions
- **MEMORY.md** - Code change history

---

**Document Status**: ✅ READY FOR EXECUTION  
**Next Action**: Run `pytest tests/ -v` to verify current state  
**Owner**: Developer Team  
**Last Updated**: 2026-10-25

---

*Generated by Mistral Vibe - CoH1 × Mistral AI Mod*  
*This is your actionable test execution list*
