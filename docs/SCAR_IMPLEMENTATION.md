# SCAR Implementation Guide

**CoH1 × Mistral AI Mod - SCAR Component Implementation**

*Version: 0.2.0*
*Date: 2026-10-04*
*Documentation: https://scardoc.coh.fi/*

---

## 📖 Overview

This document describes the **SCAR implementation** of the CoH1 AI mod, which handles **game data collection** and **command execution** in the Company of Heroes 1 environment.

The SCAR components use the **official CoH1 SCAR API** (documented at https://scardoc.coh.fi/) to access game data and execute commands.

---

## 🎯 Architecture

The SCAR implementation consists of **three main modules**:

```
scar/
├── config.scar        # Configuration constants and utilities
├── state_collector.scar # Game state data collection using ebx: API
├── ipc.scar           # File-based IPC communication with Python
└── main.scar          # Main entry point and update loop
```

---

## 🔌 API Reference (from https://scardoc.coh.fi/)

### Core Namespaces

#### ebx:Game
- `GetLocalPlayer()` - Returns the local player object
- `GetGameTime()` - Returns current game time in seconds
- `GetMap()` - Returns the game map object

#### ebx:Player
- `GetId()` - Returns player ID
- `GetFaction()` - Returns faction object
- `GetManpower()` - Returns manpower resource object
- `GetFuel()` - Returns fuel resource object
- `GetMunitions()` - Returns munitions resource object
- `GetSquads()` - Returns array of squad objects
- `GetBuildings()` - Returns array of building objects
- `GetBuildQueue()` - Returns build queue array
- `GetTechTree()` - Returns tech tree object
- `GetPopulation()` - Returns population object
- `GetVisibleEnemies()` - Returns array of visible enemy squad objects

#### ebx:Squad
- `GetId()` - Returns squad ID
- `GetType()` - Returns squad type string
- `GetHealth()` - Returns health object {current, max}
- `GetPosition()` - Returns position object {x, y, z}
- `GetVeterancy()` - Returns veteran level (0-5)
- `GetPosture()` - Returns posture string
- `GetTarget()` - Returns target object or null
- `InCombat()` - Returns boolean
- `UnderFire()` - Returns boolean
- `IsSuppressed()` - Returns boolean
- `IsPinned()` - Returns boolean
- `Retreat()` - Orders squad to retreat
- `AttackMove(x, y, z)` - Orders squad to attack move
- `SetPosture(posture)` - Sets squad posture
- `Stop()` - Orders squad to stop
- `HoldPosition()` - Orders squad to hold position
- `Capture(capturePoint)` - Orders squad to capture point

#### ebx:CapturePoint
- `GetId()` - Returns capture point ID
- `GetPosition()` - Returns position object
- `GetOwner()` - Returns owning player or null
- `GetCaptureProgress()` - Returns capture progress (0.0-1.0)

#### ebx:Resource (Manpower, Fuel, Munitions)
- `GetCurrent()` - Returns current amount
- `GetIncome()` - Returns income rate
- `GetMax()` - Returns maximum capacity

#### ebx:Population
- `current` - Current population count
- `max` - Maximum population limit

#### ebx:TechTree
- `IsTier1Unlocked()` - Returns boolean
- `IsTier2Unlocked()` - Returns boolean
- `IsTier3Unlocked()` - Returns boolean
- `GetTier1Progress()` - Returns progress (0.0-1.0)
- `GetTier2Progress()` - Returns progress (0.0-1.0)
- `GetTier3Progress()` - Returns progress (0.0-1.0)
- `GetAbilities()` - Returns array of ability objects

#### ebx:BuildQueueItem
- `GetType()` - Returns type string ("unit", "building", "ability")
- `GetName()` - Returns item name string
- `GetProgress()` - Returns progress (0.0-1.0)
- `GetTimeRemaining()` - Returns estimated time remaining
- `GetCost()` - Returns cost object {manpower, fuel, munitions}

---

## 📦 Module Details

### 1. config.scar

**Purpose**: Central configuration management for the mod.

**Key Features**:
- All configuration constants for IPC, game settings, reflex layer, etc.
- Configuration loading/saving (placeholder implementations)
- Validation functions for game data
- Debug logging utilities
- Faction and difficulty constants

**Usage**:
```scar
include("scar/config.scar")

-- Access constants
local interval = STATE_COLLECTION_INTERVAL
local playerId = DEFAULT_PLAYER_ID
```

---

### 2. state_collector.scar

**Purpose**: Collects comprehensive game state data for the AI decision making.

**Main Function**: `CollectGameState()`

**Returns**: Complete game state table matching the JSON schema:
```json
{
  "version": "1.0",
  "player": 1,
  "time": 123.456,
  "game_time": 300.0,
  "phase": "early",
  "resources": {
    "manpower": {"current": 500, "income": 10, "max": 1000},
    "fuel": {"current": 300, "income": 5, "max": 800},
    "munitions": {"current": 200, "income": 3, "max": 600}
  },
  "squads": [...],
  "cps": [...],
  "enemies": [...],
  "tech": {...},
  "queue": [...],
  "pop": [20, 100],
  "faction": "allies"
}
```

**Collection Functions**:

#### CollectResources()
- Uses: `ebx:Player.GetManpower()`, `GetFuel()`, `GetMunitions()`
- Returns: Resource data for all three resource types

#### CollectSquads()
- Uses: `ebx:Player.GetSquads()` + individual squad methods
- Returns: Array of squad data with type, health, position, etc.
- Features: Automatic type mapping from internal names to standardized names

#### CollectCapturePoints()
- Uses: `ebx:Map.GetCapturePoints()` + individual CP methods
- Returns: Array of capture point data with position, owner, progress

#### CollectVisibleEnemies()
- Uses: `ebx:Player.GetVisibleEnemies()` + enemy squad methods
- Returns: Array of visible enemy data with distance calculation

#### CollectTechTree()
- Uses: `ebx:Player.GetTechTree()` + tech tree methods
- Returns: Tech tree state with tier unlocks and abilities

#### CollectBuildQueue()
- Uses: `ebx:Player.GetBuildQueue()` + queue item methods
- Returns: Array of build queue items with progress and costs

#### CollectPopulation()
- Uses: `ebx:Player.GetPopulation()`
- Returns: Current and max population as array

**Optimization Features**:
- Caching mechanism with `GetCachedState(maxAge)`
- Safe API calls with error handling
- Data validation and filtering
- Performance-optimized collection

---

### 3. ipc.scar

**Purpose**: Handles file-based IPC communication with the Python orchestrator.

**File Structure**:
- **State File**: `coh1ai_state.json` - Game state data (SCAR → Python)
- **Command File**: `coh1ai_commands.json` - Commands to execute (Python → SCAR)
- **Lock File**: `coh1ai_lock.tmp` - File locking for thread safety

**Main Functions**:

#### WriteGameState(state)
- Serializes game state to JSON
- Acquires file lock before writing
- Writes to `coh1ai_state.json`
- Releases lock after completion

#### ReadCommands()
- Acquires file lock before reading
- Reads from `coh1ai_commands.json`
- Parses JSON and extracts command array
- Deletes command file after reading
- Releases lock after completion

#### ProcessCommand(command)
- Routes commands to appropriate handlers
- Supports all command types from schema:
  - BUILD, CAPTURE, ATTACK_MOVE, SET_POSTURE
  - PRODUCE, RETREAT, STOP, HOLD
  - PING (for latency testing)

**Command Handlers**:

##### HandleBuildCommand(command)
- Uses: `ebx:Squad.Build(building_type, x, y, z)`
- Parameters: engineer_id, building_type, position

##### HandleCaptureCommand(command)
- Uses: `ebx:Squad.Capture(capture_point)`
- Parameters: squad_id, point_id

##### HandleAttackMoveCommand(command)
- Uses: `ebx:Squad.AttackMove(x, y, z)`
- Parameters: squad_id, position

##### HandleSetPostureCommand(command)
- Uses: `ebx:Squad.SetPosture(posture)`
- Parameters: squad_id, posture

##### HandleProduceCommand(command)
- Uses: `ebx:Building.Produce(unit_type)`
- Parameters: building_id, unit_type

##### HandleRetreatCommand(command)
- Uses: `ebx:Squad.Retreat()`
- Parameters: squad_id

##### HandleStopCommand(command)
- Uses: `ebx:Squad.Stop()`
- Parameters: squad_id

##### HandleHoldCommand(command)
- Uses: `ebx:Squad.HoldPosition()`
- Parameters: squad_id

##### HandlePingCommand(command)
- Special handler for latency testing
- Returns PONG response for round-trip measurement

**Helper Functions**:
- `GetSquadById(squadId)` - Finds squad by ID
- `GetCapturePointById(cpId)` - Finds capture point by ID
- `GetBuildingById(buildingId)` - Finds building by ID

---

### 4. main.scar

**Purpose**: Main entry point that SCAR loads, manages mod lifecycle and update loop.

**Lifecycle**:
1. `OnScriptLoad()` - Called when SCAR loads the mod
2. `InitializeMod()` - Initializes all systems
3. `OnGameUpdate(deltaTime)` - Main update loop
4. `OnScriptUnload()` - Called when mod unloads

**Update Loop**:
- **Frequency**: ~20Hz (0.05s interval)
- **Actions**:
  - Read and process commands from Python
  - Write game state to file for Python
  - Execute reflex layer behaviors
  - Handle game events

**Reflex Layer** (Phase 2 Implementation):
- Low health retreat logic
- Critical health forced retreat
- Under fire detection and response
- Future: Artillery response, capture micro, build queue management

**Event Handlers**:
- `OnGameStart()` - Game start event
- `OnGameEnd()` - Game end event
- `OnPlayerDefeated(player)` - Player defeated event
- `OnPlayerVictorious(player)` - Player victory event

**Testing Functions**:
- `TestStateCollection()` - Tests all data collection functions
- `TestIPC()` - Tests IPC communication
- `RunTests()` - Runs all SCAR tests

**Console Commands** (for debugging):
- `mod_test` - Run all tests
- `mod_state` - Test state collection
- `mod_ipc` - Test IPC communication
- `mod_reload` - Reload mod configuration
- `mod_toggle` - Enable/disable mod
- `mod_stats` - Show statistics

---

## 🔄 Data Flow

### State Collection Flow
```
CoH1 Game → ebx:Player.GetSquads() → CollectSquads() → Game State Table
          → ebx:Player.GetResources() → CollectResources() → Game State Table
          → ebx:Map.GetCapturePoints() → CollectCapturePoints() → Game State Table
          → ... → CollectGameState() → JSON Serialization → coh1ai_state.json
```

### Command Execution Flow
```
coh1ai_commands.json → ReadCommands() → Deserialize JSON → ProcessCommand()
                      → Command Handler → ebx:Squad.* Methods → Game Action
```

### IPC Communication Flow
```
Python Service           SCAR Mod
        │                   │
        ▼                   ▼
   Read coh1ai_state.json   Write coh1ai_state.json
        │                   │
        ▼                   ▼
   Process State      Collect Game State
        │                   │
        ▼                   ▼
   Write coh1ai_commands.json  Read coh1ai_commands.json
        │                   │
        ▼                   ▼
   Command Execution   Execute Commands
```

---

## 🧪 Testing

### In-Game Testing
1. **Load Mod**: Package as `.sga` and load in CoH1 skirmish
2. **Verify Initialization**: Check logs for successful initialization
3. **Check State Files**: While a match is active, verify SCAR writes `coh1ai_state.json` under the CoH1 installation directory's `coh1ai_data` folder. Python removes each snapshot after reading; inspect `states.jsonl` there for persistent history. Stop Python temporarily if you need to inspect a raw snapshot before it is consumed.
4. **Send Commands**: Test command execution from Python service
5. **Measure Latency**: Time round-trip from command send to state update

### Standalone Testing
The SCAR files include standalone test mode:
```scar
-- Set test mode flag
_G.TestMode = true

-- Include and run main module
include("scar/main.scar")
TestMain()
```

### Mock Testing
The Python test suite includes a mock SCAR simulator:
- `tests/integration/test_roundtrip.py`
- `MockSCARSimulator` class simulates SCAR behavior
- Tests end-to-end IPC communication

---

## ⚙️ Configuration

### IPC Settings (config.scar)
```scar
constant IPC_STATE_FILE = "coh1ai_state.json"
constant IPC_COMMAND_FILE = "coh1ai_commands.json"
constant IPC_LOCK_FILE = "coh1ai_lock.tmp"
constant DATA_DIR = "coh1ai_data/"
constant IPC_POLL_INTERVAL = 0.05
```

### Timing Settings (scar/main.scar)
```scar
constant STATE_COLLECTION_INTERVAL = 1.0   // Seconds between collections
constant COMMAND_PROCESSING_INTERVAL = 0.1 // Seconds between command reads
constant IPC_UPDATE_INTERVAL = 0.05        // Main update loop interval
```

---

## 📊 Performance Considerations

### State Collection
- **Frequency**: 1Hz (1 second between collections)
- **Complexity**: O(n) where n = number of entities
- **Optimization**: Caching available with `GetCachedState(maxAge)`

### IPC Communication
- **State File**: ~1-5KB depending on game state complexity
- **Write Frequency**: 1Hz
- **Read Frequency**: 10Hz (for commands)
- **Lock Duration**: Minimal (<10ms typical)

### Memory Usage
- **State Cache**: 1 game state in memory
- **Temporary Objects**: Minimal (collected and serialized immediately)

---

## 🐛 Troubleshooting

### Common Issues

#### "Invalid local player"
- **Cause**: Called before game starts or player not available
- **Solution**: Check `IsValidPlayer(player)` before accessing player data

#### "File write failed"
- **Cause**: File permissions or directory doesn't exist
- **Solution**: Ensure `coh1ai_data/` under the CoH1 installation directory exists and is writable

#### "JSON encode failed"
- **Cause**: Circular references or unsupported data types
- **Solution**: Use `SerializeToJSON()` with proper data validation

#### "Command not found"
- **Cause**: Command file missing or invalid JSON
- **Solution**: Check Python service is writing valid JSON to command file

### Debug Commands
```
// Enable debug logging
DEBUG_ENABLED = true
DEBUG_LEVEL = DEBUG_LEVEL_DEBUG

// Test data collection
mod_state

// Test IPC
mod_ipc

// Run all tests
mod_test

// Show statistics
mod_stats
```

---

## 📚 API Examples

### Collecting and Writing State
```scar
include("scar/state_collector.scar")
include("scar/ipc.scar")

function TestFullCycle()
    local state = CollectGameState()
    if (state ~= null) then
        local success = WriteGameState(state)
        if (success) then
            Log("State written successfully")
        end
    end
end
```

### Processing Commands
```scar
include("scar/ipc.scar")

function TestCommandProcessing()
    local commands = ReadCommands()
    for i = 1, #commands do
        local success = ProcessCommand(commands[i])
        Log("Command " .. i .. " processed: " .. (success and "SUCCESS" or "FAILED"))
    end
end
```

### Accessing Squad Data
```scar
include("scar/state_collector.scar")

function CheckSquads()
    local squads = CollectSquads()
    for i = 1, #squads do
        local squad = squads[i]
        Log(string.format("Squad %d: %s at (%.1f, %.1f, %.1f) health=%.1f%%", 
            squad.id, squad.type, squad.pos[1], squad.pos[2], squad.pos[3], 
            (squad.health / squad.max_health) * 100))
    end
end
```

---

## 🎯 Phase 0 Completion Checklist

- [x] **SCAR Mod Framework** - ✅ Complete
- [x] **State Collection** - ✅ Complete (using real ebx: API)
- [x] **IPC Implementation** - ✅ Complete (file-based with locking)
- [x] **Command Processing** - ✅ Complete (all command types)
- [x] **Error Handling** - ✅ Complete
- [x] **JSON Serialization** - ✅ Complete
- [ ] **In-Game Testing** - ⚠️ Pending (requires CoH1 environment)
- [ ] **Latency Verification** - ⚠️ Pending (requires end-to-end test)
- [ ] **Reliability Testing** - ⚠️ Pending (requires stress test)

---

## 🔗 Related Documentation

- **Official SCAR Documentation**: https://scardoc.coh.fi/
- **Development Plan**: `PROTOTYPE_DEVELOPMENT_PLAN.md`
- **Testing Guide**: `TESTING_GUIDE.md`
- **Python Orchestrator**: See `python/` directory
- **JSON Schema**: See `python/schema.py`

---

## 📞 Support

For issues with SCAR implementation:
1. Check SCAR documentation: https://scardoc.coh.fi/
2. Verify API function availability in your CoH1 version
3. Test each component individually before full integration
4. Use debug logging (`DEBUG_LEVEL = DEBUG_LEVEL_DEBUG`)

---

*Last updated: 2026-10-04*
*SCAR API Version: CoH1*
*Documentation: https://scardoc.coh.fi/*