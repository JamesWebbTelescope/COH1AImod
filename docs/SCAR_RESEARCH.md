# CoH1 SCAR Modding Research

## Overview

This document contains research findings about the Company of Heroes 1 (CoH1) SCAR modding framework, focusing on capabilities relevant to the AI mod development.

## Research Status

**Status**: IN PROGRESS (Step 0.2)
**Priority**: HIGH
**Dependencies**: None

## Key Findings

### SCAR Framework Capabilities

#### ✅ Confirmed Capabilities
- [ ] **File I/O**: Can read/write files at runtime
- [ ] **JSON Support**: Built-in or available JSON serialization
- [ ] **Game Data Access**: Can access game state (units, resources, etc.)
- [ ] **Command Execution**: Can execute game commands
- [ ] **Event System**: Has game event callbacks (OnInit, OnGameStart, etc.)
- [ ] **Threading/Timers**: Can run periodic updates

#### ❓ Unconfirmed Capabilities
- [ ] Memory sharing with external processes
- [ ] Console output/redirect capabilities
- [ ] Network communication
- [ ] Shared memory access

### File I/O Research

#### Primary Method: File Polling
- **Status**: ⚠️ NEEDS VERIFICATION
- **Approach**: SCAR writes JSON to file, Python reads and responds
- **Files**: `scar/ipc.scar`, `python/ipc_reader.py`
- **Implementation**: Placeholder implemented, requires SCAR testing

#### Fallback Method: Shared Memory
- **Status**: 🔍 RESEARCH NEEDED
- **Approach**: Direct memory sharing between processes
- **Pros**: Faster than file I/O
- **Cons**: More complex, platform-specific

#### Fallback Method: Console Log Relay
- **Status**: 🔍 RESEARCH NEEDED  
- **Approach**: SCAR writes to console, external process reads console output
- **Pros**: No file I/O permissions needed
- **Cons**: Slower, parsing complexity

### Game Data Access Research

#### Required Data Points
- [ ] Player resources (manpower, fuel, munitions)
- [ ] Squad data (type, health, vet, position)
- [ ] Capture points (owner, progress)
- [ ] Visible enemy units
- [ ] Tech tree state
- [ ] Build queue
- [ ] Population count

#### Data Access Methods
- **SCAR Game API**: Native game data structures
- **Memory Reading**: Direct memory access (if SCAR API limited)
- **Console Commands**: Game console commands for data

### Command Execution Research

#### Required Commands
- [ ] BUILD(engineer_id, building_type, position)
- [ ] CAPTURE(squad_id, point_id)
- [ ] ATTACK_MOVE(squad_id, position)
- [ ] SET_POSTURE(squad_id, posture)
- [ ] PRODUCE(building_id, unit_type)
- [ ] RETREAT(squad_id)
- [ ] STOP(squad_id)
- [ ] HOLD(squad_id)

## Testing Results

### File I/O Test
```scar
// Test file writing
function TestFileIO() {
    local testFile = "test.tmp"
    local testContent = "Hello World"
    
    if (WriteFile(testFile, testContent)) {
        local content = ReadFile(testFile)
        DeleteFile(testFile)
        return content == testContent
    }
    return false
}
```

**Status**: 🔍 NOT TESTED IN GAME

### Game State Access Test
```scar
// Test accessing player resources
function TestResourceAccess() {
    local resources = GetPlayerResources()
    return resources.manpower != null
}
```

**Status**: 🔍 NOT TESTED IN GAME

## Research Priorities

### Immediate (Step 0.2)
1. **Verify SCAR file I/O capabilities** in actual CoH1 environment
2. **Test basic game data access** (resources, squads)
3. **Identify SCAR API documentation** and available functions
4. **Determine platform compatibility** (Windows file system access)

### For Step 0.3
1. **Create minimal working SCAR mod** that loads in CoH1
2. **Implement basic file I/O test** in game
3. **Verify mod packaging** (.sga file creation)

## SCAR API Documentation Sources

### Known Resources
- [ ] Official CoH1 modding documentation
- [ ] Community forums (Relic forums, modding communities)
- [ ] Existing SCAR mods (example code)
- [ ] SCAR scripting reference guides

### Key Questions to Answer

1. **File System Access**: Can SCAR scripts write to arbitrary files?
   - Are there any restrictions on file paths?
   - What permissions are required?
   - Are there sandbox limitations?

2. **JSON Support**: Is JSON serialization available?
   - Native support?
   - Third-party libraries?
   - Manual implementation needed?

3. **Game Data Structures**: How to access game state?
   - Function names and signatures?
   - Data structure formats?
   - Update frequency/limitations?

4. **Command Execution**: How to execute game commands?
   - Available command functions?
   - Command parameters and types?
   - Error handling?

## Recommended Next Steps

### For Step 0.2 Completion
1. **Set up CoH1 development environment** with SCAR modding tools
2. **Create test SCAR scripts** for file I/O verification
3. **Run tests in CoH1** to confirm capabilities
4. **Document findings** in this file
5. **Update risk assessment** based on actual SCAR capabilities

### For Step 0.3 Preparation
1. **Design SCAR mod structure** based on research findings
2. **Implement IPC communication** using verified methods
3. **Create test plan** for in-game verification

## Success Criteria

Step 0.2 is **COMPLETE** when:
- [ ] SCAR file I/O capabilities confirmed or alternatives identified
- [ ] Basic game data access methods understood
- [ ] SCAR API documentation located and reviewed
- [ ] Platform-specific considerations identified
- [ ] Research findings documented in this file

## Risks and Mitigations

### High Risk: File I/O Not Available
- **Impact**: CRITICAL - IPC channel won't work
- **Mitigation**: Test early with simple file write/read
- **Contingency**: Use shared memory or console relay as fallback

### Medium Risk: Limited Game Data Access
- **Impact**: HIGH - May need alternative data collection methods
- **Mitigation**: Research available data access functions thoroughly
- **Contingency**: Use memory scanning or game console commands

## Timeline

- **Started**: 2026-10-04
- **Target Completion**: Within 1 week
- **Actual Completion**: TBD

## Resources

- [CoH1 Modding Wiki](https://coh.wiki/) - Community documentation
- [Relic Modding Forums](https://forums.relicnews.com/) - Community support
- [SCAR Scripting Guide](link-tbd) - Official or community guides

---

*Last updated: 2026-10-04*
*Status: Research in progress*