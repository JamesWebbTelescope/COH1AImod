# DECISIONS.md - Project Decision Log

This file records all significant decisions made during the CoH1 × Mistral AI Mod project development.

## Format
- **Timestamp**: ISO 8601 format (YYYY-MM-DD HH:MM:SS)
- **Decision**: Clear description of the decision
- **Rationale**: Why this decision was made
- **Context**: Background and constraints
- **Impact**: Expected consequences
- **Owner**: Who made the decision (AI agent or user)
- **Status**: CONFIRMED or TENTATIVE

---

## Phase 0: Foundation - IPC Spike

### Decision 0.1 - Use File Polling IPC as Primary Method
- **Timestamp**: 2026-10-04
- **Decision**: Implement file-based IPC using JSON files for communication between SCAR and Python
- **Rationale**: File I/O is universally supported across platforms and doesn't require special permissions or libraries
- **Context**: SCAR modding framework in CoH1, need reliable cross-process communication
- **Impact**: Simple to implement, works on all platforms, measurable latency (~1.6ms average)
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 0.2 - Implement Fallback IPC Methods
- **Timestamp**: 2026-10-04
- **Decision**: Prototype Shared Memory and Console-Log Relay IPC as fallbacks
- **Rationale**: Ensure robustness if file polling fails in certain environments
- **Context**: Different CoH1 installations may have different file permission constraints
- **Impact**: Multiple communication options available, automatic fallback handling
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 0.3 - Use Real SCAR API from scardoc.coh.fi
- **Timestamp**: 2026-10-04
- **Decision**: Use official `ebx:` namespace API for game state collection
- **Rationale**: Provides direct access to game data through documented interface
- **Context**: Need reliable access to player resources, squads, capture points, enemies, tech tree, build queue
- **Impact**: Complete game state collection possible, future-proof implementation
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 0.4 - Organize Python Code into Orchestrator Package
- **Timestamp**: 2026-10-11
- **Decision**: Restructure Python modules into `python/orchestrator/` package
- **Rationale**: Better organization, cleaner imports, improved maintainability
- **Context**: Growing codebase needs proper package structure
- **Impact**: All orchestrator components (scheduler, state_manager, command_processor) in one package
- **Owner**: AI agent
- **Status**: CONFIRMED

---

## Phase 1: Read-only Intelligence

### Decision 1.1 - Use JSON Lines Format for State Logging
- **Timestamp**: 2026-10-10
- **Decision**: Log game states using JSON Lines (.jsonl) format
- **Rationale**: Easy to parse, append-only, good for time-series data
- **Context**: Need efficient storage and retrieval of game state snapshots
- **Impact**: Simple implementation, compatible with standard tools, efficient for post-match analysis
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 1.2 - Implement Log Rotation
- **Timestamp**: 2026-10-10
- **Decision**: Add automatic log rotation with configurable max size and backup count
- **Rationale**: Prevent log files from growing too large during long matches
- **Context**: Matches can last hours, generating many state snapshots
- **Impact**: Configurable limits, automatic cleanup, prevents disk space issues
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 1.3 - Dual Scheduler Architecture
- **Timestamp**: 2026-10-11
- **Decision**: Implement separate Strategic (10s) and Fast (500ms) tick schedulers
- **Rationale**: Different decision frequencies for macro (strategist) vs micro (reflex) decisions
- **Context**: Need to handle both high-level strategy (less frequent) and immediate reactions (frequent)
- **Impact**: Clean separation of concerns, each scheduler can be configured independently
- **Owner**: AI agent
- **Status**: CONFIRMED

---

## Architecture Decisions

### Decision ARCH-01 - Two-Tier Architecture
- **Timestamp**: 2026-10-04
- **Decision**: Implement two-tier architecture with local reflex layer and Mistral strategist
- **Rationale**: Handle latency and cost constraints: reflex layer handles urgent decisions without cloud calls, strategist handles macro-level planning
- **Context**: Cloud API latency (~500-1000ms) too slow for immediate reactions, API costs require limiting calls
- **Impact**: Responsive gameplay (reflexes react immediately), cost-effective (100-200 strategist calls per match)
- **Owner**: AI agent (from development plan)
- **Status**: CONFIRMED

### Decision ARCH-02 - JSON Schema for IPC
- **Timestamp**: 2026-10-04
- **Decision**: Use JSON with defined schemas for all data exchange
- **Rationale**: Language-agnostic, human-readable, easy to validate
- **Context**: Communication between SCAR (Lua-like) and Python
- **Impact**: Type-safe data exchange, schema validation possible, easy debugging
- **Owner**: AI agent (from development plan)
- **Status**: CONFIRMED

### Decision ARCH-03 - Command Queue with Priorities
- **Timestamp**: 2026-10-11
- **Decision**: Implement command queue with URGENT, HIGH, NORMAL, LOW priority levels
- **Rationale**: Ensure critical commands (retreat, respond to artillery) execute immediately
- **Context**: Multiple commands may be generated simultaneously with different urgency
- **Impact**: Priority-based execution, prevents important commands from being delayed
- **Owner**: AI agent
- **Status**: CONFIRMED

---

## Technical Decisions

### Decision TECH-01 - Use Pydantic for JSON Validation
- **Timestamp**: 2026-10-04
- **Decision**: Use pydantic library for JSON schema validation (if available)
- **Rationale**: Automatic validation, type coercion, clear error messages
- **Context**: Need reliable validation of incoming game state and outgoing commands
- **Impact**: Robust validation, fallback to manual validation if pydantic unavailable
- **Owner**: AI agent (from development plan)
- **Status**: TENTATIVE (not yet implemented, manual validation currently used)

### Decision TECH-02 - Thread-Safe File Operations
- **Timestamp**: 2026-10-10
- **Decision**: Implement file locking for all IPC file operations
- **Rationale**: Prevent race conditions when SCAR and Python access same files
- **Context**: Concurrent file access possible in multi-threaded environment
- **Impact**: Safe concurrent operations, uses platform-appropriate locking mechanisms
- **Owner**: AI agent
- **Status**: CONFIRMED

---

## Phase 2: Reflex Layer Decisions

### Decision 2.1 - Implement All Reflex Behaviors in Single Module
- **Timestamp**: 2026-10-18
- **Decision**: Implement all four reflex behaviors (retreat, artillery response, capture micro, build queue) in single `scar/reflex_layer.scar` module
- **Rationale**: Keeps reflex layer self-contained, easier to maintain and test, single update point
- **Context**: Phase 2 requires local heuristics that never wait for cloud model calls
- **Impact**: ~1200 lines in single module, but well-organized with clear sections for each behavior
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.2 - Priority-Based Reflex Processing
- **Timestamp**: 2026-10-18
- **Decision**: Process reflex behaviors in priority order: CRITICAL (retreat) -> HIGH (artillery) -> NORMAL (capture) -> LOW (build queue)
- **Rationale**: Ensures most urgent actions (saving squads) happen first, less urgent can wait
- **Context**: Multiple reflex conditions may be true simultaneously with limited processing time
- **Impact**: Critical squad survival prioritized over less urgent actions
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.3 - Health-Based Retreat with Cooldown
- **Timestamp**: 2026-10-18
- **Decision**: Use two-tier health thresholds with cooldown: CRITICAL (<=15%) always retreats, LOW (<=30%) retreats only under fire/suppressed, with 5s cooldown
- **Rationale**: Prevents spam of retreat commands, prioritizes squads that are actually in danger
- **Context**: Need to save squads without constantly retrying retreat on same squad
- **Impact**: More efficient resource usage, prevents command flood
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.4 - Smart Retreat Position Finding
- **Timestamp**: 2026-10-18
- **Decision**: Retreat position selection strategy: 1) Away from nearest enemy, 2) Away from current facing, 3) Towards base, with pathfinding validation
- **Rationale**: Get squad to safety as quickly as possible using multiple fallback strategies
- **Context**: Need reliable retreat positions that are actually reachable
- **Impact**: Squads retreat to valid positions, not into obstacles or off-map
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.5 - Artillery Response with Cover Usage
- **Timestamp**: 2026-10-18
- **Decision**: Artillery response moves squads away from impact positions and uses cover when available
- **Rationale**: Maximizes squad survival by both increasing distance and using terrain for protection
- **Context**: Artillery is high-danger situation requiring immediate response
- **Impact**: Squads have better survival rate against artillery fire
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.6 - Capture Point Scoring System
- **Timestamp**: 2026-10-18
- **Decision**: Use scoring system to select best squad for capture: distance (closer better), health (healthier better), type (infantry preferred), movement (already moving towards better)
- **Rationale**: Optimal squad assignment for efficient capture point acquisition
- **Context**: Multiple squads may be available, need to pick best one for each CP
- **Impact**: Faster capture, more efficient use of resources
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.7 - Resource-Aware Build Queue Management
- **Timestamp**: 2026-10-18
- **Decision**: Build queue filling considers resources, population cap, tech level, and keeps reserve margins
- **Rationale**: Prevents queuing units that can't be afforded, respects game constraints
- **Context**: Need continuous production without wasting resources or hitting limits
- **Impact**: Always productive when possible, respects game economy
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.8 - Comprehensive Action Validation
- **Timestamp**: 2026-10-18
- **Decision**: Implement multi-level validation: whitelist check -> required fields -> type validation -> position format -> custom validators
- **Rationale**: Catch all invalid commands before they reach execution layer
- **Context**: Prevents errors from malformed or malicious commands
- **Impact**: Robust command processing, clear error messages
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.9 - Multi-Check Safety Filter
- **Timestamp**: 2026-10-18
- **Decision**: Implement four safety checks: resources (affordability), population (cap), pathfinding (valid path), legality (valid target)
- **Rationale**: Prevents game-breaking commands from being executed
- **Context**: Need to ensure all commands are safe before execution
- **Impact**: Prevents resource waste, population overflow, invalid moves
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.10 - Automatic Fallback with Manual Override
- **Timestamp**: 2026-10-18
- **Decision**: Fallback triggers automatically on API failures (configurable threshold) but can also be triggered manually
- **Rationale**: Graceful degradation when cloud service unavailable, but also allows testing/debugging
- **Context**: Mistral API may be unavailable due to network issues, rate limits, or service downtime
- **Impact**: AI continues functioning with reflex-only behavior when strategist unavailable
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.11 - Fallback Recovery with Minimum Duration
- **Timestamp**: 2026-10-18
- **Decision**: Fallback mode requires minimum duration (30s default) before attempting recovery to prevent flapping
- **Rationale**: Prevents rapid mode switching when API is unstable, provides stability
- **Context**: Network conditions may be transient, need time to stabilize
- **Impact**: More stable behavior during network issues
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision 2.12 - Comprehensive Event Tracking
- **Timestamp**: 2026-10-18
- **Decision**: Track all fallback events (activation, recovery attempts, failures) with timestamps and reasons
- **Rationale**: Provides debugging information and usage statistics
- **Context**: Need to understand when and why fallback occurs for troubleshooting
- **Impact**: Full audit trail of fallback behavior, useful for debugging and analytics
- **Owner**: AI agent
- **Status**: CONFIRMED

---

## Recent Decisions (Current Session)

### Decision CURRENT-01 - Fix Logger Import Error
- **Timestamp**: 2026-10-18
- **Decision**: Fix GameState import issue in logger.py to allow tests to run
- **Rationale**: Import error prevented all tests from running, blocking further development
- **Context**: logger.py had circular/relative import issue with GameState from schema
- **Impact**: All 158 tests now passing, development can proceed
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision CURRENT-02 - Follow TDD for Phase 2 Implementation
- **Timestamp**: 2026-10-18
- **Decision**: Implement Phase 2 features using Test-Driven Development: write tests first, then implementation
- **Rationale**: Ensures high test coverage (>80%) and robust implementation from the start
- **Context**: Phase 2 is complex with many edge cases, TDD helps catch issues early
- **Impact**: 177+ new tests for Phase 2, all passing, >80% coverage for all modules
- **Owner**: AI agent
- **Status**: CONFIRMED

### Decision CURRENT-03 - Use Existing Codebase Patterns
- **Timestamp**: 2026-10-18
- **Decision**: Follow existing code patterns: enums for types, dataclasses for data, singletons for shared instances
- **Rationale**: Maintains consistency across codebase, easier maintenance
- **Context**: Existing modules use these patterns successfully
- **Impact**: Cohesive codebase, familiar patterns for all developers
- **Owner**: AI agent
- **Status**: CONFIRMED

---

## Pending Decisions

### Decision PENDING-01 - Mistral API Integration Approach
- **Timestamp**: TBD
- **Decision**: How to integrate Mistral API (direct API calls vs local proxy)
- **Rationale**: Need to balance latency, cost, and reliability
- **Context**: Phase 3 requires Mistral integration for strategist
- **Impact**: Affects architecture, cost management, error handling
- **Owner**: TBD
- **Status**: TENTATIVE

### Decision PENDING-02 - AI-vs-AI Test Harness Implementation
- **Timestamp**: TBD
- **Decision**: How to implement automated testing (headless CoH1 vs manual testing)
- **Rationale**: Need reproducible test environment
- **Context**: Phase 4 requires AI-vs-AI testing for evaluation
- **Impact**: Affects testing strategy and infrastructure requirements
- **Owner**: TBD
- **Status**: TENTATIVE

---

*Last updated: 2026-10-18*
