# Phase 2 Testing Plan: Reflex Layer

## Document Information
- **Phase**: 2 - Reflex Layer
- **Version**: 1.0
- **Date**: 2026-10-18
- **Author**: Generated via developer skill
- **Status**: ACTIVE

---

## Overview

This document outlines the comprehensive testing plan for **Phase 2: Reflex Layer** of the CoH1 × Mistral AI Mod project. 

**Phase 2 Goal:** Implement local heuristics that replace part of the stock AI decision loop without requiring cloud model calls. The reflex layer must handle urgent, time-sensitive decisions autonomously.

**Duration:** 4-5 weeks (estimated)
**Priority:** HIGH

---

## Testing Strategy

### 1. Test-Driven Development (TDD) Approach
All features will be implemented using TDD:
1. Write unit tests first (RED)
2. Implement feature (GREEN)
3. Refactor (REFACTOR)
4. Verify all tests pass

### 2. Test Coverage Requirements
- **Minimum Code Coverage**: 80% for all new modules
- **Test Types**: Unit tests, Integration tests, Manual verification
- **Edge Cases**: Must be explicitly tested

### 3. Test Execution
- **Unit Tests**: Run with `pytest tests/unit/ -v`
- **Integration Tests**: Run with `pytest tests/integration/ -v`
- **Performance Tests**: Run with `pytest tests/performance/ -v`
- **All Tests**: Run with `pytest tests/ -v`

---

## Phase 2 Features & Test Requirements

---

## Feature 3.1: Command Executor API

**Description:** Exposes command API to bridge: BUILD, CAPTURE, ATTACK_MOVE, SET_POSTURE, PRODUCE, RETREAT, STOP, HOLD

**Priority:** HIGH | **Complexity:** HIGH | **Dependencies:** 1.1, 1.2

### Acceptance Criteria
- [ ] All command types implemented
- [ ] Commands execute successfully in game
- [ ] Error handling for invalid commands
- [ ] Command results can be verified

### Test Requirements

#### Unit Tests (`tests/unit/test_command_executor.py`)

**Test Command Creation:**
```python
- test_create_build_command_valid()
- test_create_build_command_invalid_type()
- test_create_build_command_missing_position()
- test_create_capture_command_valid()
- test_create_capture_command_invalid_point_id()
- test_create_attack_move_command_valid()
- test_create_attack_move_command_invalid_squad()
- test_create_attack_move_command_invalid_location()
- test_create_set_posture_command_valid()
- test_create_set_posture_command_invalid_posture()
- test_create_produce_command_valid()
- test_create_produce_command_invalid_unit_type()
- test_create_retreat_command_valid()
- test_create_stop_command_valid()
- test_create_hold_command_valid()
```

**Test Command Serialization:**
```python
- test_command_to_json_valid()
- test_command_from_json_valid()
- test_command_roundtrip()
- test_command_serialization_edge_cases()
```

**Test Command Validation:**
```python
- test_validate_command_valid_build()
- test_validate_command_invalid_build()
- test_validate_command_valid_capture()
- test_validate_command_valid_attack_move()
- test_validate_command_valid_set_posture()
- test_validate_command_valid_produce()
- test_validate_command_unknown_type()
- test_validate_command_missing_fields()
```

**Test Error Handling:**
```python
- test_execute_invalid_command_error()
- test_execute_command_with_invalid_target()
- test_execute_command_without_prerequisites()
- test_command_timeout_handling()
```

**Total Unit Tests:** 30+ tests

#### Integration Tests (`tests/integration/test_command_execution.py`)

```python
- test_end_to_end_command_execution()
- test_multiple_commands_sequential()
- test_multiple_commands_parallel()
- test_command_execution_with_state_update()
- test_command_failure_recovery()
- test_command_queue_overflow_handling()
```

**Total Integration Tests:** 6+ tests

#### Manual Verification
- [ ] BUILD command executes in CoH1
- [ ] CAPTURE command executes in CoH1
- [ ] ATTACK_MOVE command executes in CoH1
- [ ] SET_POSTURE command executes in CoH1
- [ ] PRODUCE command executes in CoH1
- [ ] RETREAT command executes in CoH1
- [ ] STOP command executes in CoH1
- [ ] HOLD command executes in CoH1

---

## Feature 3.2: Local Reflex Layer

**Description:** Autonomous heuristics that must never wait for cloud: retreat low-health squads under fire, respond to artillery, basic capture micro, keep build queues non-empty

**Priority:** HIGH | **Complexity:** HIGH | **Dependencies:** 2.1, 3.1

### Acceptance Criteria
- [ ] Retreat behavior triggers at configured health threshold
- [ ] Artillery response implemented
- [ ] Capture point micro works
- [ ] Build queues kept active
- [ ] All reflexes work without strategist input

### Test Requirements

#### Unit Tests (`tests/unit/test_reflex_layer.py`)

**Test Retreat Logic:**
```python
- test_retreat_triggered_at_health_threshold()
- test_retreat_not_triggered_above_threshold()
- test_retreat_under_fire_priority()
- test_retreat_suppressed_priority()
- test_retreat_location_selection()
- test_retreat_pathfinding_safety()
```

**Test Artillery Response:**
```python
- test_artillery_detected()
- test_artillery_response_move_away()
- test_artillery_response_spread_squads()
- test_artillery_response_use_cover()
- test_artillery_response_no_false_positives()
```

**Test Capture Point Micro:**
```python
- test_capture_point_detected()
- test_capture_point_assign_squad()
- test_capture_point_priority_calculation()
- test_capture_point_abandon_low_health()
- test_capture_point_reinforce_under_attack()
- test_capture_point_neutral_preference()
```

**Test Build Queue Management:**
```python
- test_build_queue_empty_detected()
- test_build_queue_select_next_unit()
- test_build_queue_resource_awareness()
- test_build_queue_priority_system()
- test_build_queue_tech_requirements()
- test_build_queue_pop_cap_awareness()
```

**Test Reflex Configuration:**
```python
- test_load_reflex_config_defaults()
- test_load_reflex_config_custom()
- test_update_reflex_thresholds()
- test_reflex_enabled_disabled()
```

**Test Reflex Timing:**
```python
- test_reflex_execution_time_budget()
- test_reflex_no_blocking()
- test_reflex_concurrent_execution()
```

**Total Unit Tests:** 30+ tests

#### Integration Tests (`tests/integration/test_reflex_integration.py`)

```python
- test_reflex_layer_with_state_updates()
- test_reflex_layer_with_command_execution()
- test_reflex_layer_priority_order()
- test_reflex_layer_urgent_events()
- test_reflex_layer_resource_constraints()
- test_reflex_layer_with_multiple_squads()
- test_reflex_layer_with_enemy_presence()
```

**Total Integration Tests:** 7+ tests

#### Manual Verification
- [ ] Retreat behavior observed when squad health < 30%
- [ ] Artillery response triggers when under artillery fire
- [ ] Capture point micro captures neutral points
- [ ] Capture point micro reinforces contested points
- [ ] Build queue never empty when resources available
- [ ] Build queue respects resource constraints
- [ ] Build queue respects tech tree requirements
- [ ] All reflexes work without Mistral connection

---

## Feature 6.1: Action Validator

**Description:** Enforces whitelist of legal commands before execution

**Priority:** HIGH | **Complexity:** MEDIUM | **Dependencies:** 3.1

### Acceptance Criteria
- [ ] Whitelist of all legal commands defined
- [ ] Invalid commands rejected
- [ ] Validation happens before execution
- [ ] Validation errors logged

### Test Requirements

#### Unit Tests (`tests/unit/test_validator.py`)

**Test Whitelist Validation:**
```python
- test_validate_command_whitelist_all_commands()
- test_validate_command_not_in_whitelist()
- test_validate_command_empty_command()
- test_validate_command_none_command()
```

**Test Field Validation:**
```python
- test_validate_build_command_required_fields()
- test_validate_capture_command_required_fields()
- test_validate_attack_move_command_required_fields()
- test_validate_set_posture_command_required_fields()
- test_validate_produce_command_required_fields()
- test_validate_retreat_command_required_fields()
- test_validate_stop_command_required_fields()
- test_validate_hold_command_required_fields()
```

**Test Type Validation:**
```python
- test_validate_command_type_string()
- test_validate_command_type_invalid()
- test_validate_position_format()
- test_validate_squad_id_format()
- test_validate_unit_type_format()
```

**Test Validation Logic:**
```python
- test_validation_before_execution()
- test_validation_error_logging()
- test_validation_stats_tracking()
- test_validation_performance()
```

**Test Custom Validators:**
```python
- test_add_custom_validator()
- test_remove_custom_validator()
- test_custom_validator_execution()
- test_multiple_custom_validators()
```

**Total Unit Tests:** 25+ tests

#### Integration Tests (`tests/integration/test_validation_integration.py`)

```python
- test_validation_in_command_pipeline()
- test_validation_error_handling_in_pipeline()
- test_validation_with_state_awareness()
- test_validation_performance_impact()
```

**Total Integration Tests:** 4+ tests

#### Manual Verification
- [ ] Invalid BUILD command rejected
- [ ] Invalid CAPTURE command rejected
- [ ] Invalid ATTACK_MOVE command rejected
- [ ] Invalid SET_POSTURE command rejected
- [ ] Invalid PRODUCE command rejected
- [ ] Validation errors appear in logs

---

## Feature 6.2: Safety Filter

**Description:** Sanity checks for affordability, pop cap, pathfinding, and legality

**Priority:** HIGH | **Complexity:** HIGH | **Dependencies:** 2.1, 3.1, 6.1

### Acceptance Criteria
- [ ] Resource checks implemented
- [ ] Population cap enforced
- [ ] Pathfinding validation works
- [ ] All safety checks pass before execution

### Test Requirements

#### Unit Tests (`tests/unit/test_safety_filter.py`)

**Test Resource Checks:**
```python
- test_check_affordability_manpower()
- test_check_affordability_fuel()
- test_check_affordability_munitions()
- test_check_affordability_combined()
- test_check_affordability_exact_cost()
- test_check_affordability_insufficient()
- test_check_affordability_edge_cases()
```

**Test Population Cap:**
```python
- test_check_pop_cap_under_limit()
- test_check_pop_cap_at_limit()
- test_check_pop_cap_over_limit()
- test_check_pop_cap_unit_cost()
- test_check_pop_cap_multiple_units()
```

**Test Pathfinding:**
```python
- test_check_pathfinding_valid_path()
- test_check_pathfinding_blocked()
- test_check_pathfinding_out_of_bounds()
- test_check_pathfinding_distance_limits()
- test_check_pathfinding_terrain_costs()
```

**Test Legality:**
```python
- test_check_command_legality_valid()
- test_check_command_legality_invalid_target()
- test_check_command_legality_building_requirements()
- test_check_command_legality_tech_requirements()
- test_check_command_legality_faction_restrictions()
```

**Test Combined Checks:**
```python
- test_safety_check_all_pass()
- test_safety_check_resource_fail()
- test_safety_check_pop_cap_fail()
- test_safety_check_pathfinding_fail()
- test_safety_check_legality_fail()
- test_safety_check_multiple_failures()
```

**Test Safety Filter Configuration:**
```python
- test_safety_filter_enabled_disabled()
- test_safety_filter_strict_mode()
- test_safety_filter_warning_mode()
- test_safety_filter_custom_thresholds()
```

**Total Unit Tests:** 30+ tests

#### Integration Tests (`tests/integration/test_safety_integration.py`)

```python
- test_safety_filter_in_command_pipeline()
- test_safety_filter_with_validation()
- test_safety_filter_state_awareness()
- test_safety_filter_performance()
- test_safety_filter_error_handling()
```

**Total Integration Tests:** 5+ tests

#### Manual Verification
- [ ] Command rejected when insufficient resources
- [ ] Command rejected when pop cap reached
- [ ] Command rejected when path blocked
- [ ] Command rejected when target invalid
- [ ] Safety check failures logged
- [ ] All checks pass for valid commands

---

## Feature 6.3: Fallback Mechanism

**Description:** Graceful degradation to stock AI if Mistral model is unreachable

**Priority:** HIGH | **Complexity:** MEDIUM | **Dependencies:** 3.2, 5.1

### Acceptance Criteria
- [ ] Detects model unavailability
- [ ] Switches to stock/heuristic behavior
- [ ] No game freeze or crash
- [ ] Fallback logged for debugging

### Test Requirements

#### Unit Tests (`tests/unit/test_fallback.py`)

**Test Detection:**
```python
- test_detect_model_unavailable_timeout()
- test_detect_model_unavailable_connection_error()
- test_detect_model_unavailable_auth_error()
- test_detect_model_unavailable_rate_limit()
- test_detect_model_available()
```

**Test Fallback Activation:**
```python
- test_activate_fallback_on_unavailable()
- test_activate_fallback_manual_override()
- test_activate_fallback_automatic()
- test_activate_fallback_threshold()
```

**Test Fallback Behavior:**
```python
- test_fallback_uses_reflex_layer()
- test_fallback_uses_heuristics()
- test_fallback_no_mistral_calls()
- test_fallback_maintains_state()
- test_fallback_recovery()
```

**Test Fallback Logging:**
```python
- test_fallback_activation_logged()
- test_fallback_deactivation_logged()
- test_fallback_errors_logged()
- test_fallback_stats_tracked()
```

**Test Fallback Configuration:**
```python
- test_fallback_enabled_default()
- test_fallback_disabled()
- test_fallback_timeout_configuration()
- test_fallback_retry_logic()
```

**Total Unit Tests:** 20+ tests

#### Integration Tests (`tests/integration/test_fallback_integration.py`)

```python
- test_fallback_in_full_pipeline()
- test_fallback_with_reflex_layer()
- test_fallback_with_state_updates()
- test_fallback_recovery_to_normal()
- test_fallback_performance_impact()
```

**Total Integration Tests:** 5+ tests

#### Manual Verification
- [ ] Fallback activates when Mistral API unreachable
- [ ] Fallback activates when API key invalid
- [ ] Fallback activates when rate limit exceeded
- [ ] Game continues with reflex-only behavior
- [ ] Fallback deactivates when Mistral available
- [ ] Fallback events logged correctly

---

## Feature 4.2: Fast Tick Scheduler

**Description:** Handles reflex layer needs and urgent events every ≤1 second

**Priority:** HIGH | **Complexity:** MEDIUM | **Dependencies:** 1.2, 2.1, 3.2
**Status:** Already implemented in orchestrator/scheduler.py - needs verification

### Acceptance Criteria
- [ ] Sub-second tick timing verified
- [ ] Urgent events processed immediately
- [ ] No conflict with strategic scheduler
- [ ] Performance meets requirements

### Test Requirements

#### Unit Tests (`tests/unit/test_fast_scheduler.py`)

**Test Timing:**
```python
- test_fast_scheduler_interval_200ms()
- test_fast_scheduler_interval_500ms()
- test_fast_scheduler_interval_1000ms()
- test_fast_scheduler_interval_custom()
```

**Test Urgent Events:**
```python
- test_fast_scheduler_urgent_event_processing()
- test_fast_scheduler_urgent_event_priority()
- test_fast_scheduler_multiple_urgent_events()
```

**Test Scheduler Lifecycle:**
```python
- test_fast_scheduler_start()
- test_fast_scheduler_stop()
- test_fast_scheduler_pause()
- test_fast_scheduler_resume()
- test_fast_scheduler_restart()
```

**Test Integration:**
```python
- test_fast_scheduler_with_strategic_scheduler()
- test_fast_scheduler_no_conflicts()
- test_fast_scheduler_shared_state()
```

**Total Unit Tests:** 15+ tests

#### Integration Tests
- Verify existing tests cover fast scheduler integration

#### Manual Verification
- [ ] Fast tick executes every 500ms
- [ ] Fast tick executes every 200ms (configurable)
- [ ] Urgent events processed immediately
- [ ] No conflict with strategic scheduler (10s interval)

---

## Test Environment Setup

### Required Files
```
COh1AIMod/
├── python/
│   ├── validator.py                    # NEW - Action validator
│   ├── safety_filter.py                # NEW - Safety filter
│   ├── fallback.py                     # NEW - Fallback mechanism
│   ├── orchestrator/
│   │   ├── fast_scheduler.py           # VERIFY - Fast tick scheduler
│   │   └── ...
│   └── ...
├── scar/
│   ├── command_executor.scar          # NEW - Command executor
│   ├── reflex_layer.scar               # NEW - Reflex layer
│   └── ...
└── tests/
    ├── unit/
    │   ├── test_command_executor.py    # NEW
    │   ├── test_reflex_layer.py         # NEW
    │   ├── test_validator.py            # NEW
    │   ├── test_safety_filter.py        # NEW
    │   ├── test_fallback.py             # NEW
    │   ├── test_fast_scheduler.py       # NEW
    │   └── ...
    └── integration/
        ├── test_command_execution.py   # NEW
        ├── test_reflex_integration.py   # NEW
        ├── test_validation_integration.py # NEW
        ├── test_safety_integration.py   # NEW
        ├── test_fallback_integration.py  # NEW
        └── ...
```

### Test Data Requirements

#### Mock Game States
- `tests/test_data/mock_states/`
  - `early_game.json` - Early game state with few units
  - `mid_game.json` - Mid game state with multiple squads
  - `late_game.json` - Late game state with full army
  - `low_resources.json` - State with minimal resources
  - `max_pop_cap.json` - State at population limit
  - `under_attack.json` - State with squads under fire
  - `artillery_incoming.json` - State with artillery fire
  - `empty_state.json` - Edge case: no units

#### Mock Commands
- `tests/test_data/mock_commands/`
  - `valid_build.json`
  - `invalid_build.json`
  - `valid_capture.json`
  - `invalid_capture.json`
  - `valid_attack_move.json`
  - `invalid_attack_move.json`
  - ... (all command types)

#### Test Scenarios
- `tests/test_data/scenarios/`
  - `retreat_scenario.json` - Squad needs to retreat
  - `artillery_scenario.json` - Artillery incoming
  - `capture_scenario.json` - Capture point available
  - `build_queue_scenario.json` - Build queue empty
  - `fallback_scenario.json` - Mistral unavailable

---

## Test Execution Plan

### Week 1-2: Command Executor & Validation
1. Implement `scar/command_executor.scar`
2. Write unit tests for command executor
3. Implement `python/validator.py`
4. Write unit tests for validator
5. Write integration tests for command pipeline

### Week 3-4: Safety Filter & Reflex Layer
1. Implement `python/safety_filter.py`
2. Write unit tests for safety filter
3. Implement `scar/reflex_layer.scar`
4. Write unit tests for reflex layer
5. Write integration tests for safety + reflex

### Week 5: Fallback Mechanism & Integration
1. Implement `python/orchestrator/fallback.py`
2. Write unit tests for fallback
3. Verify fast scheduler implementation
4. Write all remaining integration tests
5. Run full test suite

---

## Test Coverage Targets

| Module | Unit Tests | Integration Tests | Total Tests | Coverage Target |
|--------|------------|-------------------|-------------|-----------------|
| command_executor.scar | 30+ | 6+ | 36+ | >80% |
| reflex_layer.scar | 30+ | 7+ | 37+ | >80% |
| validator.py | 25+ | 4+ | 29+ | >80% |
| safety_filter.py | 30+ | 5+ | 35+ | >80% |
| fallback.py | 20+ | 5+ | 25+ | >80% |
| fast_scheduler.py | 15+ | 0 | 15+ | >80% |
| **TOTAL** | **150+** | **27+** | **177+** | **>80%** |

---

## Test Quality Gates

Before Phase 2 is considered complete:

1. **All Acceptance Criteria Met**
   - [ ] All command types execute in game
   - [ ] All reflex behaviors implemented and working
   - [ ] Reflex layer works without strategist input
   - [ ] Safety and validation in place
   - [ ] Fallback mechanism working

2. **All Tests Passing**
   - [ ] All unit tests pass (100% pass rate)
   - [ ] All integration tests pass (100% pass rate)
   - [ ] No tests skipped or ignored without justification

3. **Code Quality**
   - [ ] All modules have >80% test coverage
   - [ ] Code follows existing style conventions
   - [ ] Proper error handling implemented
   - [ ] Documentation updated

4. **Manual Verification**
   - [ ] All manual verification steps completed
   - [ ] Behavior verified in actual CoH1 environment (if possible)
   - [ ] Performance meets requirements

---

## Test Automation

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run Phase 2 unit tests only
python -m pytest tests/unit/test_command_executor.py tests/unit/test_reflex_layer.py tests/unit/test_validator.py tests/unit/test_safety_filter.py tests/unit/test_fallback.py tests/unit/test_fast_scheduler.py -v

# Run Phase 2 integration tests only
python -m pytest tests/integration/test_command_execution.py tests/integration/test_reflex_integration.py tests/integration/test_validation_integration.py tests/integration/test_safety_integration.py tests/integration/test_fallback_integration.py -v

# Run with coverage
python -m pytest tests/ --cov=python --cov=scar --cov-report=html

# Run specific test
python -m pytest tests/unit/test_command_executor.py::TestBuildCommand::test_create_build_command_valid -v
```

### Continuous Integration
All tests should be run before any commit:
```bash
# Pre-commit hook (recommended)
pytest tests/ -v --tb=short
```

---

## Test Data Generation

### Generating Mock States
```python
# Example: Generate mock game state for testing
from schema import GameState, ResourceData, SquadData, Position, TechTreeData, PopulationData

mock_state = GameState(
    player_id=1,
    game_time=300.0,
    resources={
        "manpower": ResourceData(current=1000, income=10, max=5000),
        "fuel": ResourceData(current=500, income=5, max=3000),
        "munitions": ResourceData(current=300, income=3, max=2000)
    },
    squads=[
        SquadData(
            id=1,
            type="riflemen",
            health=80,
            max_health=100,
            vet_level=1,
            position=Position(x=100, y=200, z=0),
            posture="aggressive"
        )
    ],
    # ... more fields
)
```

### Test Scenario Templates
All test scenarios should follow this structure:
```json
{
  "name": "retreat_scenario",
  "description": "Squad needs to retreat due to low health",
  "state": {
    "player_id": 1,
    "game_time": 600,
    "squads": [
      {
        "id": 1,
        "type": "riflemen",
        "health": 25,
        "max_health": 100,
        "under_fire": true,
        "position": [100, 200, 0]
      }
    ],
    "resources": {...},
    "enemies": [...]
  },
  "expected_actions": [
    {
      "type": "RETREAT",
      "squad_id": 1,
      "reason": "low_health"
    }
  ]
}
```

---

## Risk Mitigation for Testing

### Risk: SCAR Environment Limitations
- **Mitigation**: Use mock game state for unit tests
- **Contingency**: Test SCAR code separately in CoH1 environment
- **Fallback**: Create simulation environment for SCAR testing

### Risk: Test Data Complexity
- **Mitigation**: Generate comprehensive mock data covering all edge cases
- **Contingency**: Use recorded game states from actual matches
- **Fallback**: Manually create test scenarios

### Risk: Integration Complexity
- **Mitigation**: Test components independently before integration
- **Contingency**: Use dependency injection for easier testing
- **Fallback**: Create test doubles (mocks/stubs)

### Risk: Performance Testing
- **Mitigation**: Include performance tests in CI
- **Contingency**: Profile slow tests and optimize
- **Fallback**: Mark performance tests as optional

---

## Test Review Process

### Code Review Checklist
For each test file, verify:
- [ ] Tests cover all acceptance criteria
- [ ] Tests cover all edge cases
- [ ] Tests are independent (no order dependency)
- [ ] Tests use proper assertions
- [ ] Tests have descriptive names
- [ ] Tests include docstrings
- [ ] Tests handle errors properly
- [ ] Tests clean up after themselves

### Test Maintenance
- [ ] Update tests when requirements change
- [ ] Add regression tests for fixed bugs
- [ ] Remove obsolete tests
- [ ] Keep test data up to date

---

## Success Criteria

Phase 2 Testing is **COMPLETE** when:

1. ✅ All acceptance criteria for Phase 2 features are met
2. ✅ All unit tests pass (100% pass rate)
3. ✅ All integration tests pass (100% pass rate)
4. ✅ Code coverage >80% for all new modules
5. ✅ All manual verification steps completed
6. ✅ No critical bugs open
7. ✅ Documentation updated

---

## Next Steps

1. **Implement Features** (in order):
   - Command Executor API
   - Action Validator
   - Safety Filter
   - Local Reflex Layer
   - Fast Tick Scheduler (verify)
   - Fallback Mechanism

2. **Write Tests** (in parallel with implementation):
   - Unit tests for each feature
   - Integration tests for feature interactions
   - Manual verification scripts

3. **Run Full Test Suite**:
   - Verify all tests pass
   - Fix any failures
   - Optimize slow tests

4. **Update Documentation**:
   - Update MEMORY.md with all changes
   - Update DECISIONS.md with decisions made
   - Update CHANGELOG.md with new features

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-18 | AI Agent | Initial release |

---

*This testing plan will be updated as Phase 2 implementation progresses.*
