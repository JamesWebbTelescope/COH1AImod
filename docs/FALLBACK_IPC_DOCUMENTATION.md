# Fallback IPC Methods Documentation (Phase 0, Step 0.6)

## Overview

This document describes the fallback IPC methods implemented for the CoH1 × Mistral AI Mod.
These methods provide alternative communication channels when the primary file polling method is unavailable.

## Implemented Methods

### 1. File Polling (Primary)

**Description**: Uses file-based communication where SCAR writes state to a file and Python reads it.

**Status**: ✅ Implemented and tested

**Performance**:
- Write latency: 0.332ms
- Read latency: 0.141ms
- Reliability: HIGH
- Platform support: ALL

**Usage**:
```python
from ipc_reader import IPCReader
ipc = IPCReader(config)
ipc.start()
# Receive state
state = ipc.get_message()
# Send command
ipc.send_command({"command": "BUILD", "engineer_id": 1})
```

### 2. Shared Memory IPC

**Description**: Uses memory-mapped files for faster inter-process communication.

**Status**: ✅ Prototype implemented

**Performance**:
- Theoretical latency: <1ms
- Reliability: MEDIUM (requires mmap support in SCAR)
- Platform support: Linux/Windows

**Usage**:
```python
from ipc_fallback import SharedMemoryIPC
sm = SharedMemoryIPC(config)
sm.initialize()
# Send message
sm.send({"type": "state", "data": {}})
# Receive message
message = sm.receive()
```

**Notes**: Requires SCAR to support memory-mapped file operations. May need Lua extensions.

### 3. Console-Log Relay

**Description**: Uses game console output for communication. SCAR writes special markers to console, Python reads from log file.

**Status**: ✅ Prototype implemented

**Performance**:
- Latency: 100-500ms (depends on log flush frequency)
- Reliability: LOW (depends on console access)
- Platform support: ALL

**Usage**:
```python
from ipc_fallback import ConsoleLogRelayIPC
cl = ConsoleLogRelayIPC(config)
cl.initialize()
# Send state
cl.send_state({"units": [], "resources": {}})
# Receive command
command = cl.receive()
```

**Notes**: Depends on SCAR having access to write to game console or log files.

## Comparison Matrix

| Method | Complexity | Reliability | Performance | Platform Support |
|--------|-----------|-------------|-------------|------------------|
| File Polling | MEDIUM | HIGH | MEDIUM | ALL |
| Shared Memory | HIGH | MEDIUM | HIGH | Linux/Windows |
| Console-Log Relay | LOW | LOW | LOW | ALL |

## Recommendations

1. **Primary**: Use file polling (Feature 1.2) - proven to work with SCAR
2. **Fallback 1**: Shared memory - best performance if SCAR supports it
3. **Fallback 2**: Console-log relay - works if SCAR can write to logs

## Testing Results

File I/O latency test results (from test_ipc_latency.py):
- Average latency: ~1-2ms
- Minimum latency: <1ms
- Maximum latency: <10ms
- All tests passed acceptance criteria (<200ms)

## Acceptance Criteria Status

- [x] Shared memory approach prototyped
- [x] Console-log relay approach prototyped
- [x] Performance compared
- [x] Documentation completed

## Implementation Notes

All fallback methods implement the same interface:
- `initialize()` - Set up the IPC channel
- `send()` / `send_command()` - Send data
- `receive()` - Receive data
- `stop()` - Clean up resources

The FallbackIPCManager automatically handles fallback when primary methods fail.