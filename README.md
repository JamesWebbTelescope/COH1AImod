# CoH1 × Mistral AI Mod

**Replace stock CoH1 skirmish AI macro decisions with Mistral AI**

A mod for Company of Heroes 1 (Relaunch Edition) that replaces the game's default AI with an intelligent system powered by Mistral AI models. Features a two-tier architecture with a local reflex layer for high-frequency decisions and a Mistral-powered strategist for macro-level planning.

## 📋 Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | ✅ **COMPLETE** | Foundation - IPC Spike |
| Phase 1 | ✅ **COMPLETE** | Read-only Intelligence |
| Phase 2 | ✅ **COMPLETE** | Reflex Layer |
| Phase 3 | ⏳ Pending | Strategist (Mistral) |
| Phase 4 | ⏳ Pending | Evaluation |
| Phase 5 | ⏳ Pending | Polish |

**Current Version**: 0.2.0   
**Last Updated**: 2026-11-08   
**Compatibility**: Company of Heroes 1 (Relaunch Edition / Legacy)

---

## 🚀 Quick Start

### Prerequisites

1. **Company of Heroes 1 (Relaunch)** installed via Steam
2. **Python 3.10+** installed
3. **SCAR modding framework** (bundled with CoH1)

---

## 📦 Installation & Setup

### Step 1: Package the Mod

Run the packaging script to create the `.sga` file:

```batch
cd D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod
package_mod.bat
```

This creates **`COh1AIMod_0.2.0.sga`** in the mod directory.

### Step 2: Install the Mod

Copy the `.sga` file to your CoH1 mods directory:

```
From: COh1AIMod\COh1AIMod_0.2.0.sga
To:   D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\coh1_mistral_ai.sga
```

> **Note**: For the command line to work, the `.sga` filename must match the mod name used in the `-modname` parameter.
> Use `coh1_mistral_ai.sga` as the filename.

---

## 🎮 How to Run the Mod

### Step 1: Start the Python Orchestrator FIRST

> **⚠️ IMPORTANT**: Start the Python orchestrator **BEFORE** launching CoH1.

Open **Command Prompt** and run:

```batch
cd D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod
run_mod.bat
```

**OR** run directly:
```bash
python python\main.py
```

**Command Line Options:**
```bash
# Run with debug logging
run_mod.bat --debug

# Run in test mode (no CoH1 needed)
python python\main.py --test

# Run with debug + test
python python\main.py --test --debug

# Custom configuration file
python python\main.py --config myconfig.json

# Show version
python python\main.py --version

# Show help
python python\main.py --help
```

You should see output like:
```
2026-11-08 14:14:56,197 - coh1ai - INFO - CoH1 AI Orchestrator v0.2.0 initialized
2026-11-08 14:14:56,201 - coh1ai - INFO - Orchestrator service started successfully
2026-11-08 14:14:56,201 - coh1ai - INFO - IPC state file: coh1ai_state.json
2026-11-08 14:14:56,201 - coh1ai - INFO - Service running. Press Ctrl+C to stop.
```

**Keep this window open** - the orchestrator must run while you play.

---

### Step 2: Launch CoH1 with the Mod

> **⚠️ IMPORTANT**: CoH1 Relaunch requires loading mods via command line using the `-modname` parameter.

**Method A: Create a Desktop Shortcut (Recommended)**

1. Find **RelicCOH.exe** in: `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\`
2. Create a **desktop shortcut** to it
3. Right-click the shortcut → **Properties**
4. In the **Target** field, add `-modname coh1_mistral_ai` at the end:
   ```
   "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\RelicCOH.exe" -modname coh1_mistral_ai
   ```
5. Click **OK**
6. Double-click the shortcut to launch CoH1 with the mod

**Method B: Steam Launch Options**

1. Open **Steam**
2. Right-click **Company of Heroes** in your library
3. Select **Properties**
4. In the **Launch Options** field, add:
   ```
   -modname coh1_mistral_ai
   ```
5. Close the properties window
6. Launch CoH1 from Steam

**Method C: Direct Command Line**

Open Command Prompt and run:
```batch
cd D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch
RelicCOH.exe -modname coh1_mistral_ai
```

> **⚠️ CRITICAL**: The `-modname` parameter must match your `.sga` filename (without the `.sga` extension).
> If your file is `coh1_mistral_ai.sga`, use `-modname coh1_mistral_ai`.

---

### Step 3: Play a Skirmish Game

1. In CoH1, start a **Skirmish** game with your preferred settings
2. The mod will automatically load and:
   - ✅ Start collecting game state using SCAR
   - ✅ Write state to the CoH1 installation's `coh1ai_data/coh1ai_state.json` every second
   - ✅ Read commands from the CoH1 installation's `coh1ai_data/coh1ai_commands.json`
3. The Python orchestrator (running in your command prompt) will:
   - ✅ Read the game state from the file
   - ✅ Log state to the CoH1 installation's `coh1ai_data/states.jsonl`
   - ✅ Run tick schedulers (strategic: 10s, fast: 0.5s)
   - ✅ Execute commands via the Reflex Layer (Phase 2)

---

## 📁 Directory Structure

```
COh1AIMod/
├── README.md                    # ← You are here
├── CHANGELOG.md                # Project changelog
├── PROTOTYPE_DEVELOPMENT_PLAN.md  # Development roadmap
├── TEST_PLAN.md                # Testing strategy
├── AI_Architecture.txt          # High-level architecture
├── run_mod.bat                 # ← Run this to start orchestrator
├── package_mod.bat             # ← Run this to create .sga
├── docs/
│   ├── SCAR_RESEARCH.md        # SCAR framework research
│   ├── SCAR_IMPLEMENTATION.md   # SCAR implementation details
│   ├── TESTING_GUIDE.md        # Testing instructions
│   ├── IPC_LATENCY_REPORT.md    # Phase 0.5 results
│   ├── FALLBACK_IPC_DOCUMENTATION.md  # Phase 0.6 results
│   ├── PHASE_0_COMPLETION.md    # Phase 0 summary
│   ├── PHASE_2_COMPLETION.md    # Phase 2 summary
│   └── PHASE_2_TESTING_PLAN.md  # Phase 2 testing plan
├── scar/
│   ├── config.scar             # SCAR configuration
│   ├── main.scar               # Main SCAR entry point
│   ├── ipc.scar                # IPC communication
│   ├── state_collector.scar    # Game state collection
│   ├── serializer.scar         # JSON serialization
│   ├── command_executor.scar   # Command execution (Phase 2)
│   └── reflex_layer.scar       # Reflex layer logic (Phase 2)
├── python/
│   ├── config.py               # Python configuration
│   ├── schema.py               # JSON schema definitions
│   ├── ipc_reader.py           # IPC reader (Python side)
│   ├── ipc_fallback.py         # Fallback IPC methods
│   ├── logger.py               # State logging
│   ├── scheduler.py            # Tick schedulers
│   ├── safety_filter.py        # Safety validation
│   ├── validator.py            # Command validation
│   ├── main.py                 # Orchestrator entry point
│   └── orchestrator/
│       ├── __init__.py
│       ├── main.py            # Orchestrator service
│       ├── command_processor.py # Command processing
│       ├── state_manager.py   # State management
│       ├── scheduler.py       # Tick schedulers
│       └── fallback.py        # Fallback mechanism
└── tests/
    ├── unit/                   # Unit tests (395 tests)
    │   ├── test_config.py
    │   ├── test_ipc_reader.py
    │   ├── test_logger.py
    │   ├── test_scheduler.py
    │   ├── test_schema.py
    │   ├── test_validator.py
    │   ├── test_safety_filter.py
    │   ├── test_command_executor.py
    │   ├── test_reflex_layer.py
    │   └── test_orchestrator_main.py
    ├── integration/             # Integration tests (137 tests)
    │   ├── test_command_executor_integration.py
    │   ├── test_end_to_end_loop.py
    │   ├── test_end_to_end_simple.py
    │   ├── test_phase2_fallback.py
    │   ├── test_phase2_validation_safety.py
    │   └── test_reflex_integration.py
    ├── performance/            # Performance tests
    │   └── test_ipc_latency.py
    └── regression/              # Regression tests
```

> **Note**: The `coh1ai_data/` directory is created automatically in the CoH1 installation directory when the orchestrator runs.

---

## 🎯 Command Line Summary

### For the Mod (Python Orchestrator)

| Action | Command |
|--------|---------|
| **Package mod** | `package_mod.bat` |
| **Run orchestrator** | `run_mod.bat` |
| **Run orchestrator (debug)** | `run_mod.bat --debug` |
| **Run orchestrator (test)** | `python python\main.py --test` |
| **Check version** | `python python\main.py --version` |

### For CoH1

| Method | Command |
|--------|---------|
| **Shortcut Target** | `"RelicCOH.exe" -modname coh1_mistral_ai` |
| **Steam Launch Options** | `-modname coh1_mistral_ai` |
| **Direct command line** | `RelicCOH.exe -modname coh1_mistral_ai` |

> **⚠️ IMPORTANT**: The mod name in `-modname` must match your `.sga` filename.
> Example: `coh1_mistral_ai.sga` → `-modname coh1_mistral_ai`

---

## ⚙️ Configuration

The orchestrator reads its runtime configuration from `coh1ai_data/config.json` in the CoH1 installation directory, or from the path specified with `--config`. The repository's `coh1ai_data/config.json` is the sample configuration; copy it to the runtime path to use it. If no runtime config exists, the orchestrator creates one using defaults.
Keep `ipc.data_dir` set to `coh1ai_data` for SCAR/Python IPC. The runtime resolver prevents a folder named `coh1ai_data` from being redirected elsewhere and prevents relative data paths from escaping the CoH1 installation directory.

### Default Configuration

```json
{
  "mod": {
    "version": "0.2.0",
    "name": "CoH1 Mistral AI Mod"
  },
  "ipc": {
    "state_file": "coh1ai_state.json",
    "command_file": "coh1ai_commands.json",
    "lock_file": "coh1ai_lock.tmp",
    "poll_interval": 0.05,
    "max_retries": 3,
    "data_dir": "coh1ai_data"
  },
  "game": {
    "faction": "axis",
    "difficulty": "normal",
    "player_id": 1
  },
  "debug": {
    "enabled": true,
    "level": "INFO",
    "file_logging": true,
    "console_logging": true,
    "log_file": "coh1ai.log",
    "state_log_file": "states.jsonl",
    "command_log_file": "commands.jsonl",
    "error_log_file": "errors.log"
  },
  "testing": {
    "test_mode": false,
    "fake_game_data": false
  }
}
```

### Key Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `ipc.poll_interval` | Polling interval in seconds | 0.05 |
| `ipc.data_dir` | Directory for IPC and log files, relative to the CoH1 installation directory | coh1ai_data |
| `debug.level` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `debug.enabled` | Enable/disable debugging | true |
| `testing.test_mode` | Run in test mode (no CoH1 needed) | false |

---

## 📊 Features Implemented

### Phase 0: Foundation (✅ COMPLETE)

1. **SCAR Mod Framework**
   - Base mod loads successfully in CoH1
   - Custom SCAR/Lua code execution
   - No crashes or errors on load

2. **IPC Channel Implementation**
   - File polling between SCAR and Python
   - Round-trip latency **~2.6ms** (requirement: <200ms)
   - Reliable under game load

3. **Latency Verification**
   - File I/O latency: ~2.6ms average
   - 100+ test cycles completed
   - Full documentation in `docs/IPC_LATENCY_REPORT.md`

4. **Fallback IPC Methods**
   - Shared memory IPC (prototype)
   - Console-log relay IPC (prototype)
   - Automatic fallback handling
   - Full documentation in `docs/FALLBACK_IPC_DOCUMENTATION.md`

### Phase 1: Read-only Intelligence (✅ COMPLETE)

1. **Game State Collector**
   - Collects all required data points
   - Uses real **ebx: API** calls
   - Optimized for performance
   - Data points: resources, squads, capture points, enemies, tech tree, build queue, population

2. **Compact JSON Serializer**
   - Valid JSON schema matching `python/schema.py`
   - Optimized for transmission
   - Deserialization works correctly

3. **State Logging**
   - Snapshots logged with timestamps to `states.jsonl`
   - Log rotation implemented (10MB max, 5 backups)
   - Logs can be parsed post-match for analysis

### Phase 2: Reflex Layer (✅ COMPLETE)

1. **Command Execution API**
   - Complete implementation of all command types (BUILD, CAPTURE, ATTACK_MOVE, SET_POSTURE, PRODUCE, RETREAT, STOP, HOLD, PING)
   - Statistics tracking (success/failure rates, execution times)
   - Anti-spam protection with pending command queue
   - Command spacing to prevent entity command flooding

2. **Local Reflex Layer**
   - All 4 autonomous heuristics implemented and tested
   - Attack heuristic: Engages enemy squads in range
   - Build heuristic: Constructs buildings from build queue
   - Idle heuristic: Handles idle squad decisions
   - Retreat heuristic: Falls back when under fire

3. **Safety & Validation**
   - Comprehensive validation of all inputs
   - Safety filtering for all commands
   - Validation of command structures, types, positions, and parameters

4. **End-to-End Loop Validation**
   - 8/8 end-to-end tests passing
   - Complete state → decision → command pipeline validated
   - Milestone 1: End-to-End Loop Stabilization achieved

For complete Phase 2 details, see `docs/PHASE_2_COMPLETION.md`

---

## 🔍 How It Works

### Communication Flow

```
STEP 1: You run the Python orchestrator
┌─────────────────────────────────────────────────────────────────┐
│  Python Orchestrator (python\main.py)                            │
│  - IPC Reader: Watches for coh1ai_state.json                     │
│  - State Logger: Logs to states.jsonl                             │
│  - Schedulers: Strategic (10s) & Fast (0.5s) ticks                 │
│  - Command Processor: Executes commands via Reflex Layer        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
STEP 2: You launch CoH1 with: RelicCOH.exe -modname coh1_mistral_ai
┌─────────────────────────────────────────────────────────────────┐
│  SCAR Mod (scar\main.scar)                                       │
│  - Loads mod into CoH1                                            │
│  - Collects game state every second                               │
│  - Writes to <CoH1 install>\coh1ai_data\coh1ai_state.json        │
│  - Reads from <CoH1 install>\coh1ai_data\coh1ai_commands.json    │
│  - Executes commands via command_executor.scar                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
             <CoH1 install>\coh1ai_data\coh1ai_state.json
                              ▼
             Python reads and removes the snapshot
                              ▼
             Reflex Layer analyzes state and generates commands
                              ▼
             Commands written to coh1ai_commands.json
                              ▼
             SCAR reads and executes commands in-game
```

### File Watching

SCAR and Python use `coh1ai_data/` under the CoH1 installation directory:

| File | Direction | Purpose |
|------|-----------|---------|
| `coh1ai_state.json` | SCAR → Python | Transient game-state snapshot; Python removes it after reading |
| `coh1ai_commands.json` | Python → SCAR | Commands to execute |
| `coh1ai_lock.tmp` | Both | File locking for safety |
| `states.jsonl` | Python | Persistent JSON Lines history of game states |
| `commands.jsonl` | Python | Persistent JSON Lines history of commands |
| `coh1ai.log` | Python | General log file |

---

## 🎯 SCAR Mod Components

| File | Purpose | Status |
|------|---------|--------|
| `scar/config.scar` | Configuration constants | ✅ Complete |
| `scar/main.scar` | Main entry point & update loop | ✅ Complete |
| `scar/ipc.scar` | File-based IPC communication | ✅ Complete |
| `scar/state_collector.scar` | Game state collection | ✅ Complete |
| `scar/serializer.scar` | JSON serialization for state data | ✅ Complete |
| `scar/command_executor.scar` | Command execution API (Phase 2) | ✅ Complete |
| `scar/reflex_layer.scar` | Reflex layer decision making (Phase 2) | ✅ Complete |

### API Used

The mod uses the official CoH1 **ebx:** API documented at: https://scardoc.coh.fi/

- `ebx:Game.GetLocalPlayer()` - Get the local player
- `ebx:Game.GetGameTime()` - Get current game time
- `ebx:Player.GetSquads()` - Get all player squads
- `ebx:Player.GetResources()` - Get resource data
- `ebx:Player.GetTechTree()` - Get tech tree state
- `ebx:Player.GetBuildQueue()` - Get build queue
- And many more...

See `docs/SCAR_IMPLEMENTATION.md` for complete API reference.

---

## 🎮 Testing

### Run Unit Tests

```bash
# Run all 395 unit tests
python -m pytest tests/unit/ -v

# Run specific test modules
python -m pytest tests/unit/test_logger.py -v
python -m pytest tests/unit/test_scheduler.py -v
python -m pytest tests/unit/test_ipc_reader.py -v
python -m pytest tests/unit/test_schema.py -v
python -m pytest tests/unit/test_config.py -v
python -m pytest tests/unit/test_validator.py -v
python -m pytest tests/unit/test_safety_filter.py -v
python -m pytest tests/unit/test_command_executor.py -v
python -m pytest tests/unit/test_reflex_layer.py -v
python -m pytest tests/unit/test_orchestrator_main.py -v
```

### Run Integration Tests

```bash
# Run all 137 integration tests
python -m pytest tests/integration/ -v

# Run specific integration test modules
python -m pytest tests/integration/test_end_to_end_loop.py -v
python -m pytest tests/integration/test_command_executor_integration.py -v
python -m pytest tests/integration/test_reflex_integration.py -v
```

### Run Performance Tests

```bash
# Run latency verification (generates docs/IPC_LATENCY_REPORT.md)
python tests/performance/test_ipc_latency.py
```

### Test Coverage

- **395 unit tests** passing ✅
- **137 integration tests** passing ✅
- **Total: 532 tests** passing ✅
- All new modules have comprehensive test coverage
- Performance tests verify latency requirements (<200ms)

---

## 🐛 Troubleshooting

### "Python not found"

**Solution**: Install Python 3.10+ and add it to your PATH.

Download: https://www.python.org/downloads/

Verify: `python --version` should show Python 3.10+.

---

### "Module not found" errors

**Solution**: Run from the mod directory:

```bash
cd D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod
python python\main.py
```

---

### "File not found" errors

**Solution**: The orchestrator creates `coh1ai_data\` under the CoH1 installation directory automatically. If preparing it manually, create it there (not under the mod directory).

```batch
mkdir "<CoH1 installation directory>\coh1ai_data"
```

---

### Mod not loading in CoH1

**Solution**: 
1. Verify the `.sga` file is named: `coh1_mistral_ai.sga`
2. Verify it's in: `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\`
3. Ensure you're using: `-modname coh1_mistral_ai` (NOT `+mods`)
4. Check the exact command: `RelicCOH.exe -modname coh1_mistral_ai`
5. Look for SCAR console output (press ~ in CoH1 to see console)

**⚠️ COMMON MISTAKES:**
- ❌ Using `+mods COh1AIMod` (wrong syntax for CoH1)
- ❌ Using `-modname COh1AIMod` but file is `coh1_mistral_ai.sga` (names don't match)
- ❌ File not in the Mods directory
- ✅ **CORRECT**: `-modname coh1_mistral_ai` with file `coh1_mistral_ai.sga`

---

### IPC communication not working

**Solution**:
1. Start Python orchestrator **FIRST** (before CoH1)
2. While a match is active, SCAR writes `coh1ai_state.json` under `<CoH1 installation directory>\coh1ai_data\`; Python may consume and remove it immediately
3. Check persistent state history in `<CoH1 installation directory>\coh1ai_data\states.jsonl`
4. Verify both components use the same `ipc.data_dir` configuration
5. Check the orchestrator console for errors
6. Check SCAR console (press ~ in CoH1) for SCAR-side errors

---

### High latency

**Solution**:
- Measured latency: **~2.6ms** (requirement: <200ms) ✅
- If experiencing high latency:
  - Check disk I/O performance
  - Ensure the `coh1ai_data/` directory is on a fast drive (SSD recommended)
  - Consider using a RAM disk for `coh1ai_data/`
  - Close other programs that might be using disk I/O

---

### "No state files being created"

**Solution**:
1. Ensure Python orchestrator is running
2. Ensure CoH1 is launched with `-modname coh1_mistral_ai`
3. Start a skirmish game (mods don't work in single-player campaigns)
4. Check that the SCAR mod loads (SCAR console should show messages)
5. The state file should appear within 1-2 seconds after game starts

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| `PROTOTYPE_DEVELOPMENT_PLAN.md` | Complete development roadmap |
| `TEST_PLAN.md` | Testing strategy and plans |
| `CHANGELOG.md` | Project changelog |
| `docs/SCAR_RESEARCH.md` | SCAR framework research |
| `docs/SCAR_IMPLEMENTATION.md` | SCAR implementation details (API reference) |
| `docs/TESTING_GUIDE.md` | Testing instructions |
| `docs/IPC_LATENCY_REPORT.md` | Phase 0.5 test results |
| `docs/FALLBACK_IPC_DOCUMENTATION.md` | Phase 0.6 documentation |
| `docs/PHASE_0_COMPLETION.md` | Phase 0 completion summary |
| `docs/PHASE_2_COMPLETION.md` | Phase 2 completion summary |
| `docs/PHASE_2_TESTING_PLAN.md` | Phase 2 testing plan |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Submit a pull request

---

## 📄 License

This mod is for educational and research purposes. All Company of Heroes assets are property of Relic Entertainment and SEGA.

---

## 📞 Support

For issues or questions:
1. ✅ Check this README
2. ✅ Review the documentation in `docs/`
3. ✅ Run the tests to verify your setup
4. ✅ Check the console output for errors
5. ✅ Verify command line parameters

---

## 🎉 Summary

**The mod is ready to run!** Here's what you need to do:

### 1. Rename your .sga file:
```
Copy COh1AIMod_0.2.0.sga to coh1_mistral_ai.sga
```

### 2. Start the orchestrator:
```batch
run_mod.bat
```

### 3. Launch CoH1 with the mod:
```batch
RelicCOH.exe -modname coh1_mistral_ai
```

### 4. Play a skirmish game!

**What happens:**
- SCAR mod loads in CoH1 and collects game state
- Python orchestrator reads state and logs it
- SCAR snapshots are written every second under `<CoH1 installation directory>\coh1ai_data\`; Python consumes them and appends to `states.jsonl`
- Reflex Layer analyzes state and generates commands
- Commands are executed in-game via SCAR command executor
- Schedulers tick for AI decision making

**Phases Complete:** Phase 0 ✅ + Phase 1 ✅ + Phase 2 ✅  
**Ready for:** Phase 3 (Strategist) development

---

## ⚠️ IMPORTANT NOTES

1. **The `-modname` parameter MUST match your `.sga` filename** (without the `.sga` extension)
2. **Start the Python orchestrator BEFORE launching CoH1**
3. **Use skirmish mode** - mods don't work in campaign mode
4. **Use `-modname`, NOT `+mods`** - CoH1 uses the `-modname` syntax

---

*Last updated: 2026-11-08*  
*Version: 0.2.0*  
*Compatibility: CoH1 Relaunch Edition*  
*Command: `RelicCOH.exe -modname coh1_mistral_ai`*
