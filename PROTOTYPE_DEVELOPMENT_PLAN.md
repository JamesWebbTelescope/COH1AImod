# Prototype Development Plan: CoH1 × Mistral AI Mod

## Document Information
- **Project Name**: CoH1 × Mistral AI Mod
- **Version**: 1.0
- **Date**: 2026-10-04
- **Author**: Generated via planner skill
- **Source**: AI_Architecture.txt

---

## Executive Summary

### Project Overview
Replace the macro-level decision-making of the stock Company of Heroes 1 (CoH1) skirmish AI with a Mistral AI model, while maintaining smooth gameplay despite cloud latency and API costs. The system features a two-tier architecture with a local reflex layer for high-frequency decisions and a Mistral-powered strategist for macro-level planning.

### Total Estimated Effort
- **Phase 0 (Spike)**: 2-3 weeks
- **Phase 1 (Read-only)**: 3-4 weeks
- **Phase 2 (Reflex)**: 4-5 weeks
- **Phase 3 (Strategist)**: 5-6 weeks
- **Phase 4 (Evaluation)**: 3-4 weeks
- **Phase 5 (Polish)**: 2-3 weeks
- **Total**: ~20-25 weeks (5-6 months)

### Key Dependencies
| Dependency | Type | Criticality | Fallback Plan |
|------------|------|-------------|----------------|
| CoH1 SCAR Modding Framework | Technical | HIGH | Use alternative modding approach |
| Python 3.10+ | Runtime | HIGH | N/A |
| Mistral API Access | Service | HIGH | Local mock server for development |
| File I/O permissions in CoH1 | Technical | HIGH | Memory IPC or console relay |
| pydantic (JSON validation) | Library | MEDIUM | Manual validation |
| pytest (testing) | Library | MEDIUM | Manual testing |

### Critical Path
**Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5**

The IPC channel (Phase 0) is the critical path dependency - all subsequent phases depend on successful communication between SCAR and the external service.

---

## Confirmed Features

### Category 1: Core Infrastructure (Phase 0)

#### Feature 1.1: SCAR Mod Framework
- **Description**: Base mod that loads in CoH1 skirmish mode and provides the foundation for all AI components
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: CoH1 game installation, SCAR modding tools
- **Acceptance Criteria**: 
  - Empty mod loads successfully in CoH1 skirmish
  - Mod can be packaged as .sga file
  - Mod executes custom SCAR/Lua code
  - No crashes or errors on load

#### Feature 1.2: IPC Channel Implementation
- **Description**: Communication channel between SCAR and external Python service using file polling, shared memory, or console-log relay
- **Priority**: HIGH
- **Complexity**: HIGH
- **Dependencies**: 1.1 (SCAR Mod Framework)
- **Acceptance Criteria**:
  - Data can be sent from SCAR to external process
  - Commands can be received from external process to SCAR
  - Round-trip latency <200ms
  - Reliable under game load

#### Feature 1.3: Latency Verification
- **Description**: Performance testing to verify IPC round-trip meets latency targets
- **Priority**: HIGH
- **Complexity**: LOW
- **Dependencies**: 1.1, 1.2
- **Acceptance Criteria**:
  - Measured round-trip time <200ms
  - Latency consistent across multiple test runs
  - Documentation of latency measurements

### Category 2: State Collection & Serialization (Phase 1)

#### Feature 2.1: Game State Collector
- **Description**: Gathers per-player snapshot every tick (~1s): manpower/fuel/munitions income and stock, squad list (type, health, vet, position), capture points owned, visible enemy units, tech tree state, current build queue
- **Priority**: HIGH
- **Complexity**: HIGH
- **Dependencies**: 1.1, 1.2
- **Acceptance Criteria**:
  - All specified data points collected accurately
  - Collection completes within tick time budget
  - No performance impact on game
  - Handles edge cases (no units, no enemies visible)

#### Feature 2.2: Compact JSON Serializer
- **Description**: Converts collected game state to compact, schema-valid JSON format optimized for transmission
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 2.1
- **Acceptance Criteria**:
  - JSON schema defined and documented
  - Serialization produces valid JSON
  - Size optimized for transmission efficiency
  - Deserialization works correctly on receiving end

#### Feature 2.3: State Logging
- **Description**: Logs game state snapshots for post-match analysis and debugging
- **Priority**: MEDIUM
- **Complexity**: LOW
- **Dependencies**: 2.1, 2.2
- **Acceptance Criteria**:
  - Snapshots logged to file with timestamps
  - Logs include all relevant state data
  - Log rotation implemented for long matches
  - Logs can be parsed and analyzed post-match

### Category 3: Command Execution Layer

#### Feature 3.1: Command Executor API
- **Description**: Exposes command API to bridge: BUILD(engineer, tier2), CAPTURE(point), ATTACK_MOVE(squad, location), SET_POSTURE(defend), PRODUCE(unit_type)
- **Priority**: HIGH
- **Complexity**: HIGH
- **Dependencies**: 1.1, 1.2
- **Acceptance Criteria**:
  - All command types implemented
  - Commands execute successfully in game
  - Error handling for invalid commands
  - Command results can be verified

#### Feature 3.2: Local Reflex Layer
- **Description**: Autonomous heuristics that must never wait for cloud: retreat low-health squads under fire, respond to artillery, basic capture micro, keep build queues non-empty
- **Priority**: HIGH
- **Complexity**: HIGH
- **Dependencies**: 2.1, 3.1
- **Acceptance Criteria**:
  - Retreat behavior triggers at configured health threshold
  - Artillery response implemented
  - Capture point micro works
  - Build queues kept active
  - All reflexes work without strategist input

### Category 4: Orchestrator Service (Python)

#### Feature 4.1: Strategic Tick Scheduler
- **Description**: Triggers strategist every 10-15 seconds, managing the timing of macro-level decisions
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 1.2, 2.1, 2.2
- **Acceptance Criteria**:
  - Configurable tick interval (10-15s)
  - Reliable scheduling without drift
  - Handles game pause/resume correctly
  - Events logged for debugging

#### Feature 4.2: Fast Tick Scheduler
- **Description**: Handles reflex layer needs and urgent events every ≤1 second
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 1.2, 2.1, 3.2
- **Acceptance Criteria**:
  - Sub-second tick timing verified
  - Urgent events processed immediately
  - No conflict with strategic scheduler
  - Performance meets requirements

#### Feature 4.3: Game History Manager
- **Description**: Maintains rolling log of last N snapshots and decisions for strategist continuity
- **Priority**: MEDIUM
- **Complexity**: MEDIUM
- **Dependencies**: 2.1, 2.2, 4.1
- **Acceptance Criteria**:
  - Configurable history depth (N snapshots)
  - Efficient storage (memory/disk)
  - History included in strategist prompts
  - History can be persisted and loaded

#### Feature 4.4: Cost/Rate Limiter
- **Description**: Budget management for API calls with max 100-200 strategist calls per match
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 4.1
- **Acceptance Criteria**:
  - Configurable call budget
  - Urgent calls draw from same budget
  - Rate limiting enforced
  - Budget usage logged

### Category 5: Mistral Integration

#### Feature 5.1: Mistral API Client
- **Description**: Python client for connecting to Mistral API with support for Large and Small models
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: None (external service)
- **Acceptance Criteria**:
  - Successful API connection
  - Model selection works (Large/Small)
  - Error handling for API failures
  - Authentication handled securely

#### Feature 5.2: System Prompt Engine
- **Description**: Generates CoH1-specific system prompts with domain knowledge, hard rules (fuel cutoffs, counter-units matrix)
- **Priority**: HIGH
- **Complexity**: HIGH
- **Dependencies**: 5.1
- **Acceptance Criteria**:
  - System prompt includes all CoH1 rules
  - Faction-specific prompts available
  - Hard rules properly encoded
  - Prompts validated for correctness

#### Feature 5.3: JSON Mode Integration
- **Description**: Ensures Mistral returns structured macro intents in JSON format
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 5.1, 5.2
- **Acceptance Criteria**:
  - JSON schema defined for intents
  - Mistral configured for JSON mode
  - Output always valid JSON
  - Schema validation implemented

#### Feature 5.4: Difficulty Doctrine Prompts
- **Description**: Per-difficulty tuning via prompt engineering for AI difficulty levels
- **Priority**: MEDIUM
- **Complexity**: MEDIUM
- **Dependencies**: 5.2
- **Acceptance Criteria**:
  - Multiple difficulty levels supported
  - Prompts adjusted per difficulty
  - Difficulty affects AI behavior
  - Configurable difficulty settings

### Category 6: Safety & Validation

#### Feature 6.1: Action Validator
- **Description**: Enforces whitelist of legal commands before execution
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 3.1
- **Acceptance Criteria**:
  - Whitelist of all legal commands defined
  - Invalid commands rejected
  - Validation happens before execution
  - Validation errors logged

#### Feature 6.2: Safety Filter
- **Description**: Sanity checks for affordability, pop cap, pathfinding, and legality
- **Priority**: HIGH
- **Complexity**: HIGH
- **Dependencies**: 2.1, 3.1, 6.1
- **Acceptance Criteria**:
  - Resource checks implemented
  - Population cap enforced
  - Pathfinding validation works
  - All safety checks pass before execution

#### Feature 6.3: Fallback Mechanism
- **Description**: Graceful degradation to stock AI if Mistral model is unreachable
- **Priority**: HIGH
- **Complexity**: MEDIUM
- **Dependencies**: 3.2, 5.1
- **Acceptance Criteria**:
  - Detects model unavailability
  - Switches to stock/heuristic behavior
  - No game freeze or crash
  - Fallback logged for debugging

### Category 7: Testing & Evaluation

#### Feature 7.1: AI-vs-AI Test Harness
- **Description**: Automated headless match execution for testing AI vs AI
- **Priority**: MEDIUM
- **Complexity**: HIGH
- **Dependencies**: 1.1, 3.1, 3.2
- **Acceptance Criteria**:
  - Headless match execution works
  - Configurable match parameters
  - Automated match scheduling
  - Results collection and storage

#### Feature 7.2: Win Rate Tracking
- **Description**: Metrics collection for AI performance vs stock AI across difficulty levels
- **Priority**: MEDIUM
- **Complexity**: MEDIUM
- **Dependencies**: 7.1
- **Acceptance Criteria**:
  - Win/loss tracking implemented
  - Per-difficulty statistics
  - Historical data stored
  - Visualization/reporting available

#### Feature 7.3: Decision Log Analysis
- **Description**: Post-match analysis of AI decisions for explainability
- **Priority**: MEDIUM
- **Complexity**: MEDIUM
- **Dependencies**: 2.3, 4.3
- **Acceptance Criteria**:
  - Decision logs captured
  - Logs parseable and analyzable
  - "Why did it do that" explanations possible
  - Regression detection from logs

#### Feature 7.4: Regression Test Suite
- **Description**: Fixed replay scenarios (e.g., respond to early bike rush) to catch strategist regressions
- **Priority**: MEDIUM
- **Complexity**: HIGH
- **Dependencies**: 7.1
- **Acceptance Criteria**:
  - Scenario library created
  - Automated scenario execution
  - Pass/fail criteria defined
  - Regression detection works

### Category 8: Polish & Configuration

#### Feature 8.1: Configuration UI
- **Description**: User interface for API key, model choice, budget configuration
- **Priority**: LOW
- **Complexity**: MEDIUM
- **Dependencies**: 4.4, 5.1
- **Acceptance Criteria**:
  - All config options exposed
  - Configuration persists between sessions
  - Validation of input values
  - User-friendly interface

#### Feature 8.2: Documentation
- **Description**: README, API docs, usage instructions for mod
- **Priority**: MEDIUM
- **Complexity**: LOW
- **Dependencies**: None
- **Acceptance Criteria**:
  - README complete and accurate
  - API documentation generated
  - Usage instructions clear
  - Examples provided

#### Feature 8.3: Release Packaging
- **Description**: Mod .sga packaging and distribution preparation
- **Priority**: LOW
- **Complexity**: LOW
- **Dependencies**: 1.1, 8.2
- **Acceptance Criteria**:
  - .sga file creation works
  - Installation instructions provided
  - Versioning implemented
  - Release checklist completed

---

## Development Roadmap

### Phase 0: Foundation - IPC Spike (Weeks 1-3)
**Goal**: Prove core feasibility - mod loads and IPC channel works with <200ms latency

#### Infrastructure Setup
- [ ] **Step 0.1**: Set up project repository structure - LOW - None
  - Create directory structure for mod files
  - Set up Python project with requirements.txt
  - Configure version control
  - **Acceptance**: Repository ready for development

- [ ] **Step 0.2**: Research CoH1 SCAR modding - MEDIUM - None
  - Investigate SCAR modding tools and documentation
  - Identify file I/O capabilities in SCAR
  - Test basic SCAR script execution
  - **Acceptance**: Understanding of SCAR capabilities documented

- [ ] **Step 0.3**: Create empty SCAR mod (Feature 1.1) - MEDIUM - Step 0.2
  - Develop minimal SCAR script that loads in CoH1
  - Test in skirmish mode
  - Package as .sga
  - **Acceptance**: Mod loads without errors

#### IPC Channel Implementation
- [ ] **Step 0.4**: Implement file polling IPC (Feature 1.2) - HIGH - Step 0.3
  - Create SCAR script to write test data to file
  - Create Python service to read from file
  - Implement round-trip: Python writes command, SCAR reads and executes
  - **Files**: `scar/ipc_writer.scar`, `python/ipc_reader.py`
  - **Acceptance**: Round-trip latency measured <200ms

- [ ] **Step 0.5**: Verify latency (Feature 1.3) - LOW - Step 0.4
  - Implement timing measurements
  - Run 100+ test cycles
  - Document results
  - **Acceptance**: Latency report with <200ms average

- [ ] **Step 0.6**: Fallback IPC methods - MEDIUM - Step 0.4
  - Prototype shared memory approach
  - Prototype console-log relay approach
  - Compare performance
  - **Acceptance**: Documentation of all approaches

**Phase 0 Exit Criteria**:
- [ ] Empty mod loads in CoH1 skirmish
- [ ] IPC round-trip proven with <200ms latency
- [ ] At least one working IPC method

---

### Phase 1: Read-only Intelligence (Weeks 4-7)
**Goal**: Full snapshot pipeline with logging, stock AI untouched

#### State Collection
- [ ] **Step 1.1**: Implement game state collector (Feature 2.1) - HIGH - Phase 0
  - Collect player resources (manpower, fuel, munitions)
  - Collect squad data (type, health, vet, position)
  - Collect capture points owned
  - Collect visible enemy units
  - Collect tech tree state and build queue
  - **Files**: `scar/state_collector.scar`
  - **Acceptance**: All data points collected accurately in test

- [ ] **Step 1.2**: Implement JSON serializer (Feature 2.2) - MEDIUM - Step 1.1
  - Define JSON schema for game state
  - Implement serialization in SCAR
  - Implement deserialization in Python
  - **Files**: `scar/serializer.scar`, `python/schema.py`
  - **Acceptance**: Valid JSON produced and consumed

- [ ] **Step 1.3**: Implement state logging (Feature 2.3) - LOW - Step 1.2
  - Log snapshots to file with timestamps
  - Implement log rotation
  - Add log parsing utility
  - **Files**: `python/logger.py`, `python/log_parser.py`
  - **Acceptance**: Logs work and are parseable

#### Orchestrator Setup
- [ ] **Step 1.4**: Create orchestrator service skeleton - MEDIUM - Step 1.2
  - Python service that reads state files
  - Basic configuration management
  - Service lifecycle (start/stop)
  - **Files**: `python/orchestrator/__init__.py`, `python/config.py`
  - **Acceptance**: Service runs and reads state

- [ ] **Step 1.5**: Implement strategic tick scheduler (Feature 4.1) - MEDIUM - Step 1.4
  - Configurable tick interval
  - Scheduling without drift
  - Pause/resume handling
  - **Files**: `python/orchestrator/scheduler.py`
  - **Acceptance**: Scheduler works correctly

**Phase 1 Exit Criteria**:
- [ ] Full state collection working
- [ ] Snapshots serialized to JSON
- [ ] Orchestrator reads and logs state
- [ ] Post-match analysis possible

---

### Phase 2: Reflex Layer (Weeks 8-12)
**Goal**: Local heuristics replace part of stock AI decision loop without model calls

#### Command Execution
- [ ] **Step 2.1**: Implement command executor API (Feature 3.1) - HIGH - Phase 1
  - Implement BUILD command
  - Implement CAPTURE command
  - Implement ATTACK_MOVE command
  - Implement SET_POSTURE command
  - Implement PRODUCE command
  - **Files**: `scar/command_executor.scar`
  - **Acceptance**: All commands execute in game

- [ ] **Step 2.2**: Implement action validator (Feature 6.1) - MEDIUM - Step 2.1
  - Define whitelist of legal commands
  - Implement validation logic
  - **Files**: `python/validator.py`
  - **Acceptance**: Invalid commands rejected

- [ ] **Step 2.3**: Implement safety filter (Feature 6.2) - HIGH - Step 2.1, Step 2.2
  - Resource affordability checks
  - Population cap validation
  - Pathfinding validation
  - **Files**: `python/safety_filter.py`
  - **Acceptance**: All safety checks pass before execution

#### Reflex Layer
- [ ] **Step 2.4**: Implement local reflex layer (Feature 3.2) - HIGH - Step 2.1
  - Retreat low-health squads
  - Respond to artillery
  - Basic capture micro
  - Build queue management
  - **Files**: `scar/reflex_layer.scar`
  - **Acceptance**: All reflexes work autonomously

- [ ] **Step 2.5**: Implement fast tick scheduler (Feature 4.2) - MEDIUM - Step 2.4
  - Sub-second timing
  - Urgent event handling
  - Integration with reflex layer
  - **Files**: `python/orchestrator/fast_scheduler.py`
  - **Acceptance**: Fast tick works correctly

- [ ] **Step 2.6**: Implement fallback mechanism (Feature 6.3) - MEDIUM - Step 2.4
  - Detect model unavailability
  - Switch to reflex-only mode
  - Graceful degradation
  - **Files**: `python/orchestrator/fallback.py`
  - **Acceptance**: Fallback works when model unavailable

**Phase 2 Exit Criteria**:
- [ ] Command execution API working
- [ ] All reflex behaviors implemented
- [ ] Reflex layer works without strategist
- [ ] Safety and validation in place

---

### Phase 3: Strategist Integration (Weeks 13-18)
**Goal**: Mistral macro intents driving build/tech/posture through validator

#### Mistral Integration
- [ ] **Step 3.1**: Implement Mistral API client (Feature 5.1) - MEDIUM - Phase 2
  - API connection and authentication
  - Model selection (Large/Small)
  - Error handling
  - **Files**: `python/mistral_client.py`
  - **Acceptance**: API calls work correctly

- [ ] **Step 3.2**: Implement system prompt engine (Feature 5.2) - HIGH - Step 3.1
  - CoH1 domain knowledge encoding
  - Faction-specific prompts
  - Hard rules (fuel cutoffs, counter-units)
  - **Files**: `python/prompts.py`
  - **Acceptance**: Prompts validated for correctness

- [ ] **Step 3.3**: Implement JSON mode integration (Feature 5.3) - MEDIUM - Step 3.2
  - Define intent schema
  - Configure Mistral for JSON output
  - Validate JSON responses
  - **Files**: `python/schema.py` (updated)
  - **Acceptance**: Always valid JSON intents

- [ ] **Step 3.4**: Implement game history manager (Feature 4.3) - MEDIUM - Step 3.2
  - Rolling log of snapshots
  - History included in prompts
  - Persistence
  - **Files**: `python/history.py`
  - **Acceptance**: History works correctly

- [ ] **Step 3.5**: Implement cost/rate limiter (Feature 4.4) - MEDIUM - Step 3.1
  - Configurable call budget
  - Urgent call handling
  - Rate limiting
  - **Files**: `python/rate_limiter.py`
  - **Acceptance**: Budget enforced correctly

#### Integration
- [ ] **Step 3.6**: Connect orchestrator to Mistral - HIGH - Step 3.1, Step 3.5
  - Full strategic cycle
  - Intent validation and execution
  - Error handling
  - **Files**: `python/orchestrator/strategist.py`
  - **Acceptance**: Full cycle works end-to-end

- [ ] **Step 3.7**: Implement difficulty doctrine prompts (Feature 5.4) - MEDIUM - Step 3.2
  - Per-difficulty prompt variations
  - Difficulty configuration
  - **Files**: `python/prompts.py` (updated)
  - **Acceptance**: Difficulty affects AI behavior

**Phase 3 Exit Criteria**:
- [ ] Mistral integration working
- [ ] Full strategic cycle complete
- [ ] Difficulty tuning implemented
- [ ] Intents validated and executed

---

### Phase 4: Evaluation & Tuning (Weeks 19-22)
**Goal**: AI-vs-AI win-rate measurement, iteration, and refinement

#### Testing Infrastructure
- [ ] **Step 4.1**: Implement AI-vs-AI test harness (Feature 7.1) - HIGH - Phase 3
  - Headless match execution
  - Automated match scheduling
  - Results collection
  - **Files**: `python/test_harness.py`
  - **Acceptance**: Automated matches work

- [ ] **Step 4.2**: Implement win rate tracking (Feature 7.2) - MEDIUM - Step 4.1
  - Win/loss tracking
  - Per-difficulty statistics
  - Historical data storage
  - **Files**: `python/stats.py`
  - **Acceptance**: Statistics collected correctly

- [ ] **Step 4.3**: Implement decision log analysis (Feature 7.3) - MEDIUM - Step 4.1
  - Decision log parsing
  - Explainability analysis
  - Regression detection
  - **Files**: `python/log_analyzer.py`
  - **Acceptance**: Analysis provides useful insights

- [ ] **Step 4.4**: Create regression test suite (Feature 7.4) - HIGH - Step 4.1
  - Scenario library
  - Automated scenario execution
  - Pass/fail criteria
  - **Files**: `python/regression_tests/`
  - **Acceptance**: Regression tests work

#### Iteration
- [ ] **Step 4.5**: Run baseline evaluation - MEDIUM - Step 4.1, Step 4.2
  - Test vs stock AI at all difficulties
  - Collect baseline metrics
  - **Acceptance**: Baseline results documented

- [ ] **Step 4.6**: Tune prompts based on results - HIGH - Step 4.5
  - Analyze failures
  - Adjust prompts and heuristics
  - Re-test
  - **Acceptance**: Improved performance vs baseline

**Phase 4 Exit Criteria**:
- [ ] Test harness working
- [ ] Baseline metrics collected
- [ ] Regression suite in place
- [ ] Tuned performance > stock AI

---

### Phase 5: Polish & Release (Weeks 23-25)
**Goal**: Configuration, documentation, and release preparation

#### Configuration & UI
- [ ] **Step 5.1**: Implement configuration UI (Feature 8.1) - MEDIUM - Phase 4
  - API key configuration
  - Model choice
  - Budget settings
  - **Files**: `python/config_ui.py` or web interface
  - **Acceptance**: All options configurable

- [ ] **Step 5.2**: Create comprehensive documentation (Feature 8.2) - LOW - Phase 4
  - README.md
  - API documentation
  - Usage instructions
  - Examples
  - **Files**: `README.md`, `docs/`
  - **Acceptance**: Documentation complete and accurate

#### Packaging & Release
- [ ] **Step 5.3**: Implement release packaging (Feature 8.3) - LOW - Step 5.2
  - .sga file creation
  - Installation instructions
  - Versioning
  - **Files**: `package.sh`, `INSTALL.md`
  - **Acceptance**: Package works for distribution

- [ ] **Step 5.4**: Final testing - MEDIUM - Step 5.3
  - Full regression test suite
  - User acceptance testing
  - Performance validation
  - **Acceptance**: All tests pass

**Phase 5 Exit Criteria**:
- [ ] Configuration UI working
- [ ] Documentation complete
- [ ] Release package ready
- [ ] All tests passing

---

## Testing Matrix

| Feature | Unit Tests | Integration Tests | Manual Verification |
|---------|------------|-------------------|---------------------|
| 1.1 SCAR Mod Framework | SCAR syntax validation, load testing | Integration with CoH1 | Manual load test in game |
| 1.2 IPC Channel | File I/O unit tests, latency measurement | End-to-end round-trip | Manual timing verification |
| 1.3 Latency Verification | Statistical analysis of measurements | N/A | Manual observation |
| 2.1 Game State Collector | Data collection unit tests, edge cases | Full snapshot pipeline | Manual state verification |
| 2.2 Compact JSON Serializer | Schema validation, round-trip tests | Serialization/deserialization | Manual JSON inspection |
| 2.3 State Logging | Log writing tests, rotation tests | Log parsing | Manual log review |
| 3.1 Command Executor API | Command validation tests | Full command execution | Manual command testing in game |
| 3.2 Local Reflex Layer | Reflex trigger tests, edge cases | Reflex integration with game | Manual observation of reflexes |
| 4.1 Strategic Tick Scheduler | Scheduling logic tests | Full strategic cycle | Manual timing verification |
| 4.2 Fast Tick Scheduler | Fast scheduling tests | Reflex + urgent event handling | Manual observation |
| 4.3 Game History Manager | History storage/retrieval tests | History in prompts | Manual log review |
| 4.4 Cost/Rate Limiter | Budget tracking tests | Rate limiting in action | Manual budget monitoring |
| 5.1 Mistral API Client | API call mocking, error handling | Real API integration | Manual API testing |
| 5.2 System Prompt Engine | Prompt generation tests | Prompt in strategic cycle | Manual prompt review |
| 5.3 JSON Mode Integration | JSON validation tests | JSON output from Mistral | Manual JSON inspection |
| 5.4 Difficulty Doctrine Prompts | Prompt variation tests | Difficulty in action | Manual behavior observation |
| 6.1 Action Validator | Whitelist tests, validation logic | Full validation pipeline | Manual validation testing |
| 6.2 Safety Filter | Safety check tests | Full safety pipeline | Manual safety verification |
| 6.3 Fallback Mechanism | Fallback detection tests | Fallback in action | Manual fallback testing |
| 7.1 AI-vs-AI Test Harness | Test scheduling tests | Full harness execution | Manual match observation |
| 7.2 Win Rate Tracking | Statistics calculation tests | Full tracking system | Manual stats review |
| 7.3 Decision Log Analysis | Log parsing tests | Full analysis pipeline | Manual analysis review |
| 7.4 Regression Test Suite | Scenario tests | Full regression suite | Manual regression verification |
| 8.1 Configuration UI | UI functionality tests | Full configuration system | Manual configuration testing |
| 8.2 Documentation | N/A | N/A | Manual documentation review |
| 8.3 Release Packaging | Package creation tests | Full packaging pipeline | Manual installation test |

---

## Testing Strategy Details

### Unit Test Requirements
Each module must have comprehensive unit tests with >80% code coverage:
- **SCAR modules**: Test with mock game state
- **Python modules**: Use pytest with mocking for external dependencies
- **Edge cases**: Test with empty state, invalid inputs, network failures

### Integration Test Requirements
- **End-to-end pipeline**: State collection → serialization → Mistral call → validation → execution
- **Performance testing**: Verify all latency requirements
- **Stress testing**: High-frequency events, many units
- **Failure testing**: Network failures, invalid responses

### Test Data Requirements
- Sample game states from actual matches
- Edge case scenarios (no resources, max pop cap, etc.)
- Historical match data for regression testing

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation Strategy | Contingency Plan |
|------|-------------|--------|---------------------|-------------------|
| SCAR cannot write files at runtime | HIGH | CRITICAL | Test early in Phase 0 | Use memory IPC or console relay |
| IPC latency exceeds 200ms | MEDIUM | HIGH | Optimize serialization, test multiple methods | Accept higher latency, adjust design |
| SCAR lacks required game data access | MEDIUM | HIGH | Research thoroughly in Phase 0 | Use memory scanning for missing data |
| Mistral API rate limits too restrictive | LOW | MEDIUM | Implement caching, budget carefully | Use local mock, request limit increase |
| JSON parsing fails in SCAR | LOW | MEDIUM | Use simple, validated schemas | Implement fallback parser |

### Dependency Risks

| Dependency | Risk | Mitigation | Contingency |
|------------|------|------------|-------------|
| CoH1 SCAR framework | May not support file I/O | Test early | Use alternative IPC methods |
| Python libraries | Version conflicts | Use virtualenv, lock versions | Manual dependency management |
| Mistral API | Service changes, downtime | Monitor API updates | Local mock server, fallback to stock AI |

### Timeline Risks

| Risk | Mitigation | Contingency |
|------|------------|-------------|
| Phase 0 takes longer than expected | Start Phase 0 immediately, allocate buffer | Extend timeline, reduce scope |
| IPC method 1 fails, need to try method 2 | Test all methods in parallel | Use best available method |
| Mistral API changes during development | Use API versioning | Update client, use mock for development |

---

## Quality Gates

- [ ] Every feature has unit test requirements defined
- [ ] Every feature has integration test requirements defined
- [ ] All dependencies documented with fallback plans
- [ ] Every step has clear acceptance criteria
- [ ] User has confirmed the final feature set (COMPLETED)
- [ ] Risk assessment includes mitigation strategies (COMPLETED)
- [ ] Timeline estimates are realistic with buffers (COMPLETED)

---

## Directory Structure

```
COH1AImod/
├── README.md
├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── USAGE_GUIDE.md
│   └── ARCHITECTURE.md
├── scar/
│   ├── mod.scar                 # Main SCAR entry point
│   ├── ipc.scar                 # IPC communication
│   ├── state_collector.scar     # Game state collection
│   ├── serializer.scar          # JSON serialization
│   ├── command_executor.scar    # Command execution
│   ├── reflex_layer.scar        # Local reflex heuristics
│   └── config.scar              # Configuration
├── python/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── main.py              # Main orchestrator service
│   │   ├── scheduler.py         # Tick schedulers
│   │   ├── strategist.py        # Strategist integration
│   │   └── fallback.py          # Fallback mechanism
│   ├── mistral_client.py        # Mistral API client
│   ├── prompts.py               # System prompt engine
│   ├── validator.py             # Action validator
│   ├── safety_filter.py         # Safety checks
│   ├── history.py               # Game history manager
│   ├── rate_limiter.py          # Cost/rate limiting
│   ├── logger.py                # State logging
│   ├── log_parser.py            # Log parsing
│   ├── schema.py                # JSON schemas
│   ├── config.py                # Configuration
│   ├── config_ui.py             # Configuration UI
│   ├── stats.py                 # Statistics tracking
│   ├── log_analyzer.py          # Decision log analysis
│   └── test_harness.py          # AI-vs-AI test harness
├── tests/
│   ├── unit/
│   │   ├── test_state_collector.py
│   │   ├── test_serializer.py
│   │   ├── test_commands.py
│   │   └── ...
│   ├── integration/
│   │   ├── test_roundtrip.py
│   │   ├── test_strategic_cycle.py
│   │   └── ...
│   └── regression/
│       ├── test_bike_rush.py
│       └── ...
├── regression_tests/
│   └── scenarios/
│       ├── bike_rush.json
│       └── ...
└── package.sh                  # Release packaging script
```

---

## Next Steps

1. **Immediate**: Begin Phase 0 - Set up project structure and start SCAR mod research
2. **This Week**: Complete Step 0.1-0.3 (project setup, SCAR research, empty mod)
3. **Next Week**: Complete Step 0.4-0.6 (IPC implementation and latency verification)

---

## Approval

**User Confirmation**: All features confirmed for inclusion as-is on 2026-10-04

**Plan Status**: APPROVED - Ready for execution

**Next Review**: After Phase 0 completion

---

*Generated by planner skill - CoH1 × Mistral AI Mod Prototype Development Plan*
