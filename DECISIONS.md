# Design Decisions Documentation

## Overview

This document records all major design decisions made during the development of the CoH1 × Mistral AI Mod project.

---

## Decision Index

| Decision ID | Date | Area | Summary | Status |
|-------------|------|------|---------|--------|
| [D-001](#d-001-data-structure-choice) | 2026-10-26 | History | Data structure choice for history entries | ✅ Final |
| [D-002](#d-002-rolling-vs-full-history) | 2026-10-26 | History | Rolling vs full history storage | ✅ Final |
| [D-003](#d-003-context-generation-strategy) | 2026-10-26 | History | Context generation strategy | ✅ Final |
| [D-004](#d-004-persistence-format) | 2026-10-26 | History | Persistence format selection | ✅ Final |
| [D-005](#d-005-thread-safety-approach) | 2026-10-26 | History | Thread safety approach | ✅ Final |
| [D-006](#d-006-rate-limiting-granularity) | 2026-10-26 | Rate Limiter | Rate limiting granularity | ✅ Final |
| [D-007](#d-007-budget-sharing) | 2026-10-26 | Rate Limiter | Budget sharing between call types | ✅ Final |
| [D-008](#d-008-adaptive-rate-limiting) | 2026-10-26 | Rate Limiter | Adaptive rate limiting implementation | ✅ Final |
| [D-009](#d-009-statistics-tracking) | 2026-10-26 | Rate Limiter | Statistics tracking granularity | ✅ Final |
| [D-010](#d-010-integration-architecture) | 2026-10-26 | Architecture | Integration architecture for both features | ✅ Final |

---

## History Manager Design Decisions

### D-001: Data Structure Choice

**Decision**: Use dataclasses for history entries and records

**Rationale**:
- Dataclasses provide automatic `__init__`, `__repr__`, and `__eq__` methods
- Type hints are built-in with dataclasses
- Immutable by default (frozen=True) for data integrity
- Easy serialization/deserialization
- Better performance than dict-based structures for attribute access

**Alternatives Considered**:
1. **Plain classes**: More verbose, manual implementation of common methods
2. **Named tuples**: Immutable but less flexible, no default values
3. **Dictionaries**: Less type-safe, harder to maintain
4. **Pydantic models**: External dependency, overkill for simple data structures

**Trade-offs**:
- ✅ Clean, type-safe code
- ✅ Good performance
- ✅ Easy to maintain
- ❌ Requires Python 3.7+ (already satisfied)

**Impact**: All history data structures use dataclasses with frozen=True

---

### D-002: Rolling vs Full History Storage

**Decision**: Implement rolling history with configurable max size

**Rationale**:
- Memory efficiency: CoH1 matches can be long, unlimited history would consume too much memory
- Performance: Rolling history has O(1) add operations with fixed-size storage
- Strategist continuity: Recent history is more relevant than ancient history
- Flexibility: Configurable size allows tuning based on available resources

**Alternatives Considered**:
1. **Full history**: Store everything, provide pruning as separate operation
2. **Time-based rolling**: Keep history from last N minutes/seconds
3. **Priority-based**: Keep most "important" entries, drop less important ones

**Trade-offs**:
- ✅ Predictable memory usage
- ✅ Fast operations
- ✅ Recent context for strategist
- ❌ Loses old data that might be useful for analysis
- ❌ Requires tuning of max size parameter

**Impact**:
- `max_entries` parameter controls history size
- Oldest entries are automatically pruned when limit is reached
- Persistence includes all stored entries

---

### D-003: Context Generation Strategy

**Decision**: Generate context from most recent N entries plus summary statistics

**Rationale**:
- Most recent context is most relevant for current decisions
- Summary statistics provide long-term trends without excessive data
- Configurable context window allows tuning for different use cases
- Balances detail with token efficiency (Mistral API has token limits)

**Alternatives Considered**:
1. **Full history in context**: Too many tokens, might exceed API limits
2. **Sampling**: Random sampling might miss important patterns
3. **Clustering**: Complex to implement, might not preserve important details
4. **Feature extraction**: Only extract specific features, might lose nuance

**Trade-offs**:
- ✅ Balances recency and completeness
- ✅ Token-efficient
- ✅ Configurable for different needs
- ❌ Might miss patterns that span beyond context window
- ❌ Requires careful tuning of context window

**Impact**:
- `context_window` parameter controls number of recent entries in context
- Context includes both raw data and summary statistics
- Multiple context generation methods available

---

### D-004: Persistence Format

**Decision**: Use JSON format for persistence

**Rationale**:
- Human-readable for debugging
- Standard library support (no external dependencies)
- Good balance of size and readability
- Easy to integrate with other tools
- Schema validation available

**Alternatives Considered**:
1. **Pickle**: Binary format, not human-readable, security concerns
2. **MessagePack**: Binary, more compact, but external dependency
3. **SQLite**: Relational database, overkill for this use case
4. **Custom binary**: Complex to implement, not maintainable

**Trade-offs**:
- ✅ Human-readable
- ✅ No external dependencies
- ✅ Standard library support
- ❌ Larger file size than binary formats
- ❌ Slower than binary formats for large datasets

**Impact**:
- History persisted as JSON files
- Compression available for large histories
- Easy to inspect and debug

---

### D-005: Thread Safety Approach

**Decision**: Use threading.Lock for synchronization with async support

**Rationale**:
- CoH1 runs in single thread, but Python orchestrator might use threads
- threading.Lock is standard library, no external dependencies
- Works with both synchronous and async code (via asyncio.to_thread)
- Simple and well-understood pattern

**Alternatives Considered**:
1. **No locking**: Risk of race conditions
2. **RLock**: Reentrant locks, but more complex, not needed here
3. **Semaphore**: Overkill for simple mutual exclusion
4. **asyncio.Lock**: Would require all code to be async

**Trade-offs**:
- ✅ Simple and reliable
- ✅ Works with both sync and async code
- ✅ Standard library, no external dependencies
- ❌ Small performance overhead
- ❌ Need to be careful with deadlocks

**Impact**:
- All public methods are thread-safe
- Internal state protected by locks
- Async support via async wrapper methods

---

## Rate Limiter Design Decisions

### D-006: Rate Limiting Granularity

**Decision**: Implement multi-level rate limiting (per-call, per-second, per-minute, per-match)

**Rationale**:
- Per-match budget: Prevents exceeding Mistral API limits per match
- Per-second limit: Prevents overwhelming the game with rapid calls
- Per-minute limit: Prevents exceeding Mistral rate limits
- Per-call minimum interval: Ensures minimum time between calls

**Alternatives Considered**:
1. **Single-level limiting**: Too restrictive or not restrictive enough
2. **Token bucket algorithm**: Complex, hard to tune, overkill for this use case
3. **Leaky bucket algorithm**: Similar issues to token bucket
4. **Fixed window**: Might allow bursts at window boundaries

**Trade-offs**:
- ✅ Flexible and configurable
- ✅ Prevents multiple types of abuse
- ✅ Easy to understand and tune
- ❌ More complex implementation
- ❌ Multiple parameters to configure

**Impact**:
- Configurable limits at multiple levels
- All checks are performed before allowing a call
- Comprehensive protection against rate limit issues

---

### D-007: Budget Sharing

**Decision**: Make budget sharing configurable (default: urgent calls share budget)

**Rationale**:
- Mistral API has a global limit, not per-type limits
- Urgent calls are still API calls, should count toward limit
- Configurable for flexibility in different scenarios
- Default behavior matches Mistral API reality

**Alternatives Considered**:
1. **Always share budget**: Less flexible, might not suit all use cases
2. **Never share budget**: Could exceed API limits if both types used heavily
3. **Separate budgets**: Would require separate Mistral accounts/API keys

**Trade-offs**:
- ✅ Flexible configuration
- ✅ Default behavior prevents API limit issues
- ✅ Matches Mistral API reality
- ❌ Configurable complexity
- ❌ Need to understand implications

**Impact**:
- `urgent_calls_share_budget` configuration parameter
- Default is True (urgent calls count toward main budget)
- Can be set to False for separate tracking

---

### D-008: Adaptive Rate Limiting

**Decision**: Implement adaptive rate limiting with cooldown factor

**Rationale**:
- Mistral API might rate limit unexpectedly
- Need to back off when rate limited
- Should gradually resume when rate limit clears
- Cooldown factor provides exponential backoff

**Alternatives Considered**:
1. **Fixed backoff**: Too rigid, doesn't adapt to changing conditions
2. **No backoff**: Would immediately retry and likely hit rate limit again
3. **Random backoff**: Unpredictable, might not be optimal
4. **Exponential backoff**: Standard approach, but we implemented a simpler version

**Trade-offs**:
- ✅ Adapts to changing conditions
- ✅ Prevents repeated rate limit hits
- ✅ Simple implementation
- ❌ Might wait longer than necessary
- ❌ More complex than fixed backoff

**Impact**:
- Rate limiter tracks rate limit status
- Cooldown period applied when rate limited
- Cooldown factor controls backoff speed
- Clear rate limit method to reset

---

### D-009: Statistics Tracking

**Decision**: Track comprehensive statistics for monitoring and debugging

**Rationale**:
- Need to monitor API usage for cost control
- Debugging requires detailed information
- Performance analysis benefits from comprehensive data
- Lightweight enough to always collect

**Alternatives Considered**:
1. **Minimal tracking**: Only count calls, not detailed stats
2. **No tracking**: Save memory, but lose valuable information
3. **External monitoring**: Separate monitoring system, overkill for this use case
4. ** Sampling**: Only track some calls, might miss important patterns

**Trade-offs**:
- ✅ Comprehensive debugging information
- ✅ Performance analysis capability
- ✅ Cost monitoring
- ❌ Slightly more memory usage
- ❌ Small performance overhead

**Impact**:
- Detailed call records with timestamps, tokens, latency, etc.
- Aggregated statistics (total calls, total tokens, success rate, etc.)
- Call history with search and filtering capabilities
- All statistics available via API

---

## Integration Design Decisions

### D-010: Integration Architecture

**Decision**: Loose coupling with explicit integration points

**Rationale**:
- History manager and rate limiter are independent modules
- Orchestrator integrates both via explicit method calls
- Clear interfaces between components
- Easy to test components independently
- Flexible for future changes

**Alternatives Considered**:
1. **Tight coupling**: History manager and rate limiter directly reference each other
2. **Event bus**: Components communicate via events, more complex
3. **Dependency injection**: Framework-level complexity, overkill for this use case
4. **Singleton pattern**: Global state, harder to test and maintain

**Trade-offs**:
- ✅ Clear separation of concerns
- ✅ Easy to test
- ✅ Flexible for changes
- ✅ Easy to understand
- ❌ Slightly more boilerplate code
- ❌ Need to manually wire components together

**Impact**:
- Orchestrator creates and manages both components
- Explicit method calls for integration
- No direct dependencies between history manager and rate limiter
- Easy to mock components for testing

---

## Configuration Design Decisions

### D-011: Configuration Format

**Decision**: Use configuration objects with defaults and validation

**Rationale**:
- Type-safe configuration
- Default values for all parameters
- Validation of configuration values
- Easy to create from different sources (dict, file, etc.)

**Alternatives Considered**:
1. **Plain dictionaries**: Less type-safe, no validation
2. **JSON files**: Good, but requires file I/O
3. **Environment variables**: Hard to manage many parameters
4. **Command line arguments**: Not suitable for many parameters

**Trade-offs**:
- ✅ Type-safe
- ✅ Default values
- ✅ Validation
- ✅ Flexible creation
- ❌ Slightly more code

**Impact**:
- `HistoryConfig` and `RateLimitConfig` classes
- Default values for all parameters
- Validation of configuration values
- Can be created from dict, config object, or file

---

## Testing Design Decisions

### D-012: Testing Strategy

**Decision**: Comprehensive unit and integration testing

**Rationale**:
- Unit tests for individual components
- Integration tests for component interactions
- High code coverage (>80%)
- Tests for edge cases and error conditions

**Alternatives Considered**:
1. **Only unit tests**: Might miss integration issues
2. **Only integration tests**: Harder to isolate issues
3. **Manual testing**: Not reproducible, hard to maintain
4. **No testing**: Unacceptable for production code

**Trade-offs**:
- ✅ High confidence in code quality
- ✅ Reproducible tests
- ✅ Easy to maintain
- ❌ More development time
- ❌ Need to keep tests up to date

**Impact**:
- Unit tests for all public methods
- Integration tests for component interactions
- Edge case and error condition tests
- Test coverage >80%

---

## Documentation Design Decisions

### D-013: Documentation Approach

**Decision**: Comprehensive inline documentation + separate docs

**Rationale**:
- Inline documentation (docstrings) for API reference
- Separate files for architectural and design documentation
- Examples in both inline and separate docs
- Easy to maintain and keep up to date

**Alternatives Considered**:
1. **Only inline docs**: Hard to see big picture
2. **Only separate docs**: Might get out of sync with code
3. **No docs**: Unacceptable for maintainability
4. **External docs**: Overkill for this project

**Trade-offs**:
- ✅ Comprehensive documentation
- ✅ Easy to maintain
- ✅ API reference built into code
- ❌ More work to maintain
- ❌ Need to keep docs up to date

**Impact**:
- All public methods have docstrings
- Separate MEMORY.md, DECISIONS.md, TODO.md files
- Examples in docstrings
- Architecture documentation in separate files

---

## Recent Decisions (Features 4.3 and 4.4)

### History Manager (Feature 4.3)

**Key Decisions**:
1. ✅ Use dataclasses for all data structures (D-001)
2. ✅ Implement rolling history with configurable size (D-002)
3. ✅ Generate context from recent entries + summary (D-003)
4. ✅ Use JSON for persistence (D-004)
5. ✅ Use threading.Lock for thread safety (D-005)

**Implementation Status**: COMPLETE

### Cost/Rate Limiter (Feature 4.4)

**Key Decisions**:
1. ✅ Multi-level rate limiting (D-006)
2. ✅ Configurable budget sharing (D-007)
3. ✅ Adaptive rate limiting with cooldown (D-008)
4. ✅ Comprehensive statistics tracking (D-009)
5. ✅ Loose coupling with orchestrator (D-010)

**Implementation Status**: COMPLETE

---

## Decision Making Process

### Criteria

1. **Maintainability**: Can the decision be easily maintained and updated?
2. **Performance**: Does the decision meet performance requirements?
3. **Flexibility**: Can the decision accommodate future changes?
4. **Complexity**: Is the complexity of the decision justified by its benefits?
5. **Dependencies**: Does the decision introduce unacceptable dependencies?
6. **Compatibility**: Is the decision compatible with existing code and requirements?

### Process

1. **Identify the problem**: Clearly define what needs to be decided
2. **Gather requirements**: List all requirements the decision must satisfy
3. **Identify alternatives**: List all reasonable alternatives
4. **Evaluate alternatives**: Score each alternative against criteria
5. **Consider trade-offs**: Identify pros and cons of each alternative
6. **Make decision**: Choose the best alternative
7. **Document**: Record the decision in DECISIONS.md
8. **Review**: Have the decision reviewed if possible
9. **Implement**: Implement the decision
10. **Verify**: Verify the decision meets all requirements

---

## Decision Change Process

### When to Change a Decision

A decision should be reconsidered if:
- New information becomes available
- Requirements change
- The decision is not working as expected
- Better alternatives become available
- The decision is too complex or expensive to maintain

### Change Process

1. **Identify the issue**: Clearly define why the decision needs to change
2. **Document the change**: Record the reason for the change
3. **Evaluate impact**: Assess the impact of the change
4. **Update documentation**: Update DECISIONS.md with the change
5. **Update code**: Make the necessary code changes
6. **Test**: Verify the change doesn't break anything
7. **Communicate**: Notify stakeholders of the change

---

## Decision Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| ✅ Final | Finalized | Decision has been made and implemented |
| 🔄 Pending | In Progress | Decision is being considered |
| ⏳ Draft | Draft | Decision is being documented |
| ❌ Deprecated | Deprecated | Decision has been superseded |
| 🎯 Proposed | Proposed | Decision has been proposed but not finalized |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-10-26 | Developer skill | Initial version with decisions for Features 4.3 and 4.4 |

---

## References

- [PROTOTYPE_DEVELOPMENT_PLAN.md](PROTOTYPE_DEVELOPMENT_PLAN.md) - Project plan
- [MEMORY.md](MEMORY.md) - Current state and memory
- [TODO.md](TODO.md) - Task tracking

---

*Generated by developer skill - Design Decisions Documentation*
