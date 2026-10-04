# CoH1 × Mistral AI Mod - Testing Guide

## Overview

This guide provides instructions for testing the various components of the CoH1 × Mistral AI Mod in the actual Company of Heroes 1 environment.

## Prerequisites

### Required Software
- **Company of Heroes 1** (with latest patches)
- **SCAR Modding Tools** (if available)
- **Python 3.10+**
- **Text Editor** (VS Code, Notepad++, etc.)

### Project Setup
1. Clone or copy this project to your development machine
2. Install Python dependencies: `pip install -r requirements.txt`
3. Locate your CoH1 installation directory

## Step 0.2: SCAR Modding Research Testing

### Test 1: Basic SCAR File Creation

**Objective**: Verify SCAR scripts can be created and loaded in CoH1.

**Steps**:
1. Navigate to `scar/` directory
2. Copy `mod.scar` to your CoH1 mods directory
3. Launch CoH1 and enable the mod in skirmish mode
4. Check game console/logs for initialization messages

**Expected Results**:
- Mod loads without errors
- Console shows "Initializing CoH1 Mistral AI Mod v0.1.0"
- No crashes or performance issues

**Test File**: `scar/mod.scar`

---

### Test 2: File I/O Capabilities

**Objective**: Verify SCAR can write to and read from files.

**Steps**:
1. Create a test SCAR script: `scar/test_file_io.scar`
2. Add the following content:

```scar
// Test File I/O
function TestFileIO() {
    local testFile = "coh1ai_test.tmp"
    local testContent = "SCAR File I/O Test - " + GetGameTime()
    
    Log("Testing file I/O...")
    
    // Test writing
    if (WriteFile(testFile, testContent)) {
        Log("File write: SUCCESS")
        
        // Test reading
        local content = ReadFile(testFile)
        if (content == testContent) {
            Log("File read: SUCCESS")
            Log("Content: " + content)
        } else {
            Log("File read: FAILED - Content mismatch")
        }
        
        // Test deletion
        if (DeleteFile(testFile)) {
            Log("File delete: SUCCESS")
        } else {
            Log("File delete: FAILED")
        }
    } else {
        Log("File write: FAILED")
    }
}

// Run test on game start
function OnGameStart() {
    TestFileIO()
}
```

3. Package and load the mod in CoH1
4. Launch a skirmish match

**Expected Results**:
- Console shows all SUCCESS messages
- Test file is created, read, and deleted
- No permission errors

**Success Criteria**: All file operations complete successfully

---

### Test 3: Game Data Access

**Objective**: Verify SCAR can access game state data.

**Steps**:
1. Create `scar/test_game_data.scar`
2. Add comprehensive data access tests:

```scar
// Test Game Data Access
function TestGameData() {
    Log("Testing game data access...")
    
    // Test player resources
    local resources = GetPlayerResources()
    if (resources && resources.manpower != null) {
        Log("Resources: Manpower=" + resources.manpower + 
            ", Fuel=" + resources.fuel + 
            ", Munitions=" + resources.munitions)
    } else {
        Log("Resources: FAILED - Cannot access")
    }
    
    // Test squad data
    local squads = GetPlayerSquads()
    if (squads && squads.length > 0) {
        Log("Squads: Found " + squads.length + " squads")
        local firstSquad = squads[0]
        Log("First squad: Type=" + firstSquad.type + 
            ", Health=" + firstSquad.health)
    } else {
        Log("Squads: FAILED - No squads found or cannot access")
    }
    
    // Test capture points
    local cps = GetAllCapturePoints()
    if (cps && cps.length > 0) {
        Log("Capture Points: Found " + cps.length + " points")
    } else {
        Log("Capture Points: FAILED - No points found or cannot access")
    }
    
    // Test build queue
    local queue = GetBuildQueue()
    if (queue != null) {
        Log("Build Queue: " + queue.length + " items")
    } else {
        Log("Build Queue: FAILED - Cannot access")
    }
}

function OnGameStart() {
    TestGameData()
}

// Run periodically
function OnUpdate() {
    if (GetGameTime() % 10 == 0) {  // Every 10 seconds
        TestGameData()
    }
}
```

3. Load mod in CoH1 skirmish
4. Monitor console output

**Expected Results**:
- All data access functions return valid data
- No null/undefined values for basic game data
- Data updates correctly over time

**Success Criteria**: All game data access functions work and return meaningful values

---

### Test 4: Command Execution

**Objective**: Verify SCAR can execute game commands.

**Steps**:
1. Create `scar/test_commands.scar`
2. Add command execution tests:

```scar
// Test Command Execution
function TestCommands() {
    Log("Testing command execution...")
    
    // Test STOP command
    local squad = GetPlayerSquads()[0]
    if (squad) {
        if (ExecuteCommand("STOP", squad.id)) {
            Log("STOP command: SUCCESS")
        } else {
            Log("STOP command: FAILED")
        }
        
        // Test ATTACK_MOVE
        local targetPos = [500, 500, 0]
        if (ExecuteCommand("ATTACK_MOVE", squad.id, targetPos)) {
            Log("ATTACK_MOVE command: SUCCESS")
        } else {
            Log("ATTACK_MOVE command: FAILED")
        }
    } else {
        Log("Commands: FAILED - No squads available")
    }
}

function OnGameStart() {
    // Wait a bit for game to initialize
    Sleep(5)
    TestCommands()
}
```

3. Load mod in CoH1
4. Observe squad behavior and console output

**Expected Results**:
- Commands execute without errors
- Squads respond to commands (move, stop, etc.)
- Console shows SUCCESS for all commands

**Success Criteria**: All basic commands execute successfully

---

## Step 0.3: Empty SCAR Mod Testing

### Test 5: Minimal Mod Loading

**Objective**: Verify the empty SCAR mod loads correctly.

**Steps**:
1. Use the existing `scar/mod.scar` file
2. Ensure it's in the correct CoH1 mods directory
3. Package as `.sga` file if required
4. Launch CoH1 skirmish mode
5. Enable the mod

**Expected Results**:
- Mod loads without errors
- Console shows initialization messages
- Game runs normally

**Success Criteria**: Mod loads successfully in CoH1 skirmish

---

## Step 0.4: IPC Implementation Testing

### Test 6: File Polling IPC

**Objective**: Test the complete file-based IPC communication.

**Steps**:
1. Ensure SCAR mod has IPC functionality (`scar/ipc.scar`)
2. Start the Python orchestrator: `python python/main.py` (to be created)
3. Launch CoH1 with the mod
4. Monitor both console outputs

**Expected Results**:
- SCAR writes state to file
- Python reads state and responds with commands
- SCAR reads commands and executes them
- No communication errors

**Success Criteria**: Complete round-trip communication works

---

### Test 7: Latency Measurement

**Objective**: Measure IPC round-trip latency.

**Steps**:
1. Run the latency test script: `python tests/performance/test_latency.py`
2. Or use the built-in latency tester in `ipc_reader.py`
3. Run 100+ test cycles
4. Record measurements

**Expected Results**:
- Average latency <200ms
- Consistent latency across tests
- No timeouts or errors

**Success Criteria**: Measured round-trip time <200ms with <1% error rate

---

## Test Result Documentation

### Test Report Template

```markdown
## Test Report: [Test Name]

**Test Date**: [YYYY-MM-DD]
**Tester**: [Name]
**CoH1 Version**: [Version]
**Mod Version**: [Version]

### Test Results
| Test | Result | Notes | Screenshot |
|------|--------|-------|-----------|
| Basic Loading | ✅ PASS | Mod loaded successfully | |
| File I/O | ❌ FAIL | Write works, read fails | |
| Game Data | ⚠️ PARTIAL | Resources work, squads don't | |

### Issues Found
1. [Issue description and steps to reproduce]
2. [Workaround if available]

### Next Steps
- [Action items based on test results]
```

---

## Known Issues and Workarounds

### Issue 1: File I/O Permissions
- **Symptoms**: SCAR cannot write to certain directories
- **Workaround**: Use CoH1's data directory or user documents folder
- **Solution**: Configure IPC to use writable directories

### Issue 2: Missing Game Data Functions
- **Symptoms**: Certain game data cannot be accessed
- **Workaround**: Use alternative data access methods
- **Solution**: Research SCAR API for available functions

### Issue 3: Command Execution Failures
- **Symptoms**: Commands fail silently or with errors
- **Workaround**: Add comprehensive error logging
- **Solution**: Validate command parameters before execution

---

## Performance Testing

### Latency Requirements
- **Target**: <200ms round-trip latency
- **Minimum**: <500ms for acceptable gameplay
- **Maximum**: <1000ms before gameplay impact

### Throughput Requirements
- **Target**: 10+ state updates per second
- **Minimum**: 5+ updates per second
- **Maximum**: 1+ update per second minimum for basic functionality

### Stress Testing
- Test with 50+ squads
- Test with 10+ capture points
- Test with active combat
- Test with build queue full

---

## Test Environment Setup

### Directory Structure
```
C:/Games/Company of Heroes/
├── Data/
│   └── Mods/
│       └── COH1AImod/
│           ├── mod.scar
│           ├── ipc.scar
│           └── ...
├── coh1ai_data/
│   ├── coh1ai_state.json
│   ├── coh1ai_commands.json
│   └── coh1ai.log
└── python/
    ├── orchestrator/
    └── config.py
```

### Configuration Files
- `coh1ai_data/config.json` - Main configuration
- `scar/config.scar` - SCAR-side configuration

---

## Automated Testing

### Running Unit Tests
```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test module
python -m pytest tests/unit/test_config.py -v

# Run with coverage
python -m pytest tests/unit/ --cov=python --cov-report=html
```

### Running Integration Tests
```bash
# Run all integration tests
python -m pytest tests/integration/ -v

# Run specific integration test
python -m pytest tests/integration/test_roundtrip.py::TestRoundtripIntegration::test_basic_roundtrip -v
```

### Running Performance Tests
```bash
# Measure IPC latency
python tests/performance/test_latency.py

# Stress test with mock data
python tests/stress/test_throughput.py
```

---

## Success Criteria Checklist

### Phase 0 Completion
- [ ] Empty mod loads in CoH1 skirmish
- [ ] IPC round-trip proven with <200ms latency
- [ ] At least one working IPC method
- [ ] File I/O capabilities confirmed
- [ ] Game data access methods verified

### Phase 1 Readiness
- [ ] Full state collection working
- [ ] Snapshots serialized to JSON
- [ ] Orchestrator reads and logs state
- [ ] Post-match analysis possible

---

## Support and Troubleshooting

### Common Issues

**Mod doesn't load**:
- Check file paths and permissions
- Verify SCAR script syntax
- Check CoH1 console for error messages

**IPC communication fails**:
- Verify file paths are correct
- Check that both SCAR and Python are using same paths
- Ensure no antivirus/firewall blocking file access

**Data not updating**:
- Check polling intervals
- Verify game state collection timing
- Ensure no race conditions in file access

### Debugging Tips

1. **Enable debug logging** in `config.py`
2. **Check console output** in CoH1
3. **Monitor file timestamps** to verify writes/reads
4. **Add logging** to SCAR scripts temporarily
5. **Test with smaller data** to isolate issues

---

## Version Compatibility

### CoH1 Versions Tested
- [ ] 1.0 (Original)
- [ ] 1.1 (Patch)
- [ ] 1.2 (Latest patch)
- [ ] Steam version
- [ ] GOG version

### Python Versions Tested
- [ ] 3.10
- [ ] 3.11
- [ ] 3.12
- [ ] 3.13
- [ ] 3.14

---

*Last updated: 2026-10-04*
*Document version: 1.0*