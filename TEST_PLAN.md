# Phase 0 Testing Plan - Steps 1 & 2
## SCAR Mod Loading & State Collection Tests

All `coh1ai_data/` paths below refer to the folder under the CoH1 installation directory (the same directory as `RelicCOH.exe`), not the mod repository. Run data-file commands from that directory or use its absolute path. IPC snapshots and commands use `.json`; persistent logs use JSON Lines (`.jsonl`).

**Project**: CoH1 × Mistral AI Mod  
**Phase**: 0 - Foundation (IPC Spike)  
**Objective**: Verify SCAR mod loads in CoH1 and game state data is collected correctly  
**Documentation**: Based on PROTOTYPE_DEVELOPMENT_PLAN.md Steps 0.1-0.3 & Features 1.1, 2.1  

---

## 📋 TEST OVERVIEW

This plan covers **Phase 0 Step 1 (SCAR Mod Framework)** and **Step 2 (State Collection)** validation:

| **Test** | **Feature** | **Objective** | **Estimated Time** |
|----------|-------------|---------------|-------------------|
| Test 1 | Feature 1.1: SCAR Mod Framework | Verify mod loads successfully in CoH1 skirmish | 20-40 minutes |
| Test 2 | Feature 2.1: Game State Collector | Verify all game data points are collected accurately | 20-30 minutes |

**Total Estimated Duration**: 40-70 minutes

---

## 🎯 ACCEPTANCE CRITERIA

### Feature 1.1: SCAR Mod Framework
- [ ] Empty mod loads successfully in CoH1 skirmish
- [ ] Mod can be packaged as .sga file
- [ ] Mod executes custom SCAR/Lua code
- [ ] No crashes or errors on load

### Feature 2.1: Game State Collector
- [ ] All specified data points collected accurately
- [ ] Collection completes within tick time budget
- [ ] No performance impact on game
- [ ] Handles edge cases (no units, no enemies visible)

---

## 🛠️ PREREQUISITES

### Required Software
- [ ] **Company of Heroes 1** - Installed and working
- [ ] **SCAR Modding Framework** - Installed and configured
- [ ] **Python 3.10+** - For post-test validation scripts

### Required Files
Ensure all SCAR files are in place:
```
COH1AImod/
├── scar/
│   ├── main.scar          # Entry point (OnScriptLoad, OnGameUpdate)
│   ├── config.scar        # Configuration constants
│   ├── state_collector.scar # Game state collection (ebx: API)
│   └── ipc.scar           # IPC communication (file-based)
└── coh1ai_data/
    └── config.json        # Runtime configuration
```

### Environment Setup
```bash
# 1. Create test results directory
mkdir -p test_results/phase0

# 2. Ensure data directory exists
mkdir -p coh1ai_data

# 3. Create test configuration (optional)
cp coh1ai_data/config.json coh1ai_data/config_test.json
```

---

## 🧪 TEST 1: SCAR Mod Loading (Feature 1.1)

**Objective**: Verify the SCAR mod loads successfully in Company of Heroes 1 skirmish mode without errors.

### Test Setup

#### Step 1.1: Package SCAR Files for CoH1
**Method A: Manual Directory Structure**
```
Company of Heroes\mods\coh1ai_phase0_test\
├── main.scar
├── config.scar
├── state_collector.scar
└── ipc.scar
```

**Method B: Create .sga Archive**
```bash
# Using SCAR compiler (if available)
scar_compiler scar/*.scar -o coh1ai_phase0_test.sga
# Copy .sga to Company of Heroes\mods\ directory
```

#### Step 1.2: Verify File Locations
- Confirm all `.scar` files are in the mod directory
- Ensure files have correct `.scar` extension (not `.lua`)
- Verify file permissions allow reading by CoH1

### Test Execution

#### Step 1.3: Load Mod in CoH1
1. Launch **Company of Heroes 1**
2. Navigate to **Skirmish** mode
3. Click **Mods** tab
4. **Enable** `coh1ai_phase0_test` (or your mod name)
5. Select any map and AI opponent
6. Click **Start Game**

#### Step 1.4: Observe Initialization
**Expected Console Output** (if SCAR console is visible):
```
SCRIPT LOADED: CoH1 Mistral AI Mod v0.2.0
Initializing...
Initializing configuration
Configuration initialized successfully
Initializing state collector
State collector initialized successfully
Initializing IPC system
IPC system initialized successfully
Initialization COMPLETE
Mod is now active
```

**Expected Behavior**:
- Game starts normally
- No crashes or error popups
- AI functions normally
- No visible impact on game performance

### Test Validation

#### Validation Checklist
- [ ] Mod appears in CoH1 mod list
- [ ] Mod can be enabled without errors
- [ ] Game starts successfully with mod enabled
- [ ] No error messages in SCAR console
- [ ] Initialization messages appear (if console visible)
- [ ] Game runs normally for at least 30 seconds
- [ ] No crashes or freezes

#### Manual Verification
1. **Visual Check**: No error dialogs or console errors
2. **Gameplay Check**: AI behaves normally, units move and fight
3. **Time Check**: Game runs for minimum 1 minute without issues

### Test Data Collection

**Create Test Report**: `test_results/phase0/test1_mod_loading.txt`

```bash
# Run this after test completion
echo "=== TEST 1: SCAR Mod Loading ===" > test_results/phase0/test1_mod_loading.txt
echo "Date: $(date)" >> test_results/phase0/test1_mod_loading.txt
echo "CoH1 Version: [Enter version]" >> test_results/phase0/test1_mod_loading.txt
echo "SCAR Version: [Enter version]" >> test_results/phase0/test1_mod_loading.txt
echo "" >> test_results/phase0/test1_mod_loading.txt
echo "Results:" >> test_results/phase0/test1_mod_loading.txt
echo "- Mod loads in CoH1: [PASS/FAIL]" >> test_results/phase0/test1_mod_loading.txt
echo "- Mod appears in mod list: [PASS/FAIL]" >> test_results/phase0/test1_mod_loading.txt
echo "- Game starts normally: [PASS/FAIL]" >> test_results/phase0/test1_mod_loading.txt
echo "- No errors in console: [PASS/FAIL]" >> test_results/phase0/test1_mod_loading.txt
echo "- No crashes: [PASS/FAIL]" >> test_results/phase0/test1_mod_loading.txt
echo "" >> test_results/phase0/test1_mod_loading.txt
echo "Notes:" >> test_results/phase0/test1_mod_loading.txt
echo "[Add any observations, errors, or unexpected behavior]" >> test_results/phase0/test1_mod_loading.txt
```

### Troubleshooting

| **Issue** | **Diagnosis** | **Solution** |
|-----------|---------------|--------------|
| Mod not in list | Files in wrong directory | Move to `Company of Heroes\mods\[modname]\` |
| Mod not loading | Wrong file extension | Ensure `.scar` extension, not `.lua` |
| SCAR errors | Syntax or API issues | Check SCAR console output |
| Game crashes | SCAR runtime error | Enable debug logging, check error details |
| No initialization messages | Console not visible | Check CoH1 console settings |

---

## 🧪 TEST 2: State Collection (Feature 2.1)

**Objective**: Verify that all game state data points are collected accurately by the SCAR mod.

**Prerequisites**: Test 1 must pass (mod loads successfully)

### Test Setup

#### Step 2.1: Prepare Test Environment
1. Ensure mod is properly installed (from Test 1)
2. Create clean test directory:
   ```bash
   rm -f coh1ai_data/coh1ai_state.json
   rm -f coh1ai_data/coh1ai_commands.json
   rm -f coh1ai_data/coh1ai_lock.tmp
   ```

### Test Execution

#### Step 2.2: Start Game and Collect State
1. Launch CoH1 with mod enabled
2. Start a skirmish game
3. Let the game run for **30-60 seconds** (to generate game state)
4. To inspect the transient `.json` snapshot, pause/stop the Python orchestrator while leaving the match active; otherwise it may consume and delete the snapshot as soon as it is written.

#### Step 2.3: Verify State File Creation
```bash
# Run from the CoH1 installation directory
cd coh1ai_data
ls -la coh1ai_state.json
```

**Expected**: While the orchestrator is stopped and the match is active, `coh1ai_state.json` exists and has content (> 100 bytes). Restart the orchestrator after checking it.

### Test Validation

#### Step 2.4: Validate JSON Structure
```bash
# Validate JSON syntax
python -c "import json; json.load(open('coh1ai_state.json')); print('Valid JSON')"

# Pretty-print for inspection
python -m json.tool coh1ai_state.json > state_pretty.json
```

**Expected**: Command succeeds without errors

#### Step 2.5: Verify Required Fields
Create validation script: `validate_state.py`

```python
#!/usr/bin/env python3
"""
Validate game state file structure and content
"""
import json
import sys

def validate_state_file(filepath):
    """Validate that state file contains all required fields and valid data."""
    
    try:
        with open(filepath, 'r') as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ FAIL: Cannot load JSON: {e}")
        return False
    
    # Check top-level required fields
    required_fields = [
        'version', 'player', 'time', 'game_time', 'phase',
        'resources', 'squads', 'cps', 'enemies', 'tech', 'queue', 'pop', 'faction'
    ]
    
    missing_fields = [field for field in required_fields if field not in state]
    if missing_fields:
        print(f"❌ FAIL: Missing required fields: {missing_fields}")
        return False
    
    print("✅ Top-level fields: All present")
    
    # Validate resources
    resources = state.get('resources', {})
    if not resources:
        print("❌ FAIL: Resources missing")
        return False
    
    required_resources = ['manpower', 'fuel', 'munitions']
    for res in required_resources:
        if res not in resources:
            print(f"❌ FAIL: Missing resource: {res}")
            return False
        
        res_data = resources[res]
        required_res_fields = ['current', 'income', 'max']
        missing_res_fields = [f for f in required_res_fields if f not in res_data]
        if missing_res_fields:
            print(f"❌ FAIL: Resource {res} missing fields: {missing_res_fields}")
            return False
        
        # Validate resource values
        if res_data['current'] < 0 or res_data['max'] <= 0:
            print(f"❌ FAIL: Invalid {res} values: current={res_data['current']}, max={res_data['max']}")
            return False
    
    print("✅ Resources: All valid")
    
    # Validate squads
    squads = state.get('squads', [])
    if not isinstance(squads, list):
        print(f"❌ FAIL: Squads is not a list: {type(squads)}")
        return False
    
    if len(squads) == 0:
        print("⚠️  WARNING: No squads found (might be expected early game)")
    else:
        print(f"✅ Squads: {len(squads)} units found")
        
        # Check squad structure
        for i, squad in enumerate(squads):
            required_squad_fields = ['id', 'type', 'health', 'max_health', 'vet_level', 'pos']
            missing_squad_fields = [f for f in required_squad_fields if f not in squad]
            if missing_squad_fields:
                print(f"❌ FAIL: Squad {i} missing fields: {missing_squad_fields}")
                return False
            
            # Validate position
            pos = squad.get('pos')
            if not isinstance(pos, list) or len(pos) < 3:
                print(f"❌ FAIL: Squad {i} has invalid position: {pos}")
                return False
    
    # Validate capture points
    cps = state.get('cps', [])
    if not isinstance(cps, list):
        print(f"❌ FAIL: Capture points is not a list: {type(cps)}")
        return False
    
    print(f"✅ Capture Points: {len(cps)} found")
    
    # Validate enemies (may be empty)
    enemies = state.get('enemies', [])
    if not isinstance(enemies, list):
        print(f"❌ FAIL: Enemies is not a list: {type(enemies)}")
        return False
    
    print(f"✅ Enemies: {len(enemies)} visible")
    
    # Validate tech tree
    tech = state.get('tech', {})
    if not isinstance(tech, dict):
        print(f"❌ FAIL: Tech tree is not a dict: {type(tech)}")
        return False
    
    required_tech_fields = ['tier_1', 'tier_2', 'tier_3']
    missing_tech_fields = [f for f in required_tech_fields if f not in tech]
    if missing_tech_fields:
        print(f"❌ FAIL: Tech tree missing fields: {missing_tech_fields}")
        return False
    
    print("✅ Tech Tree: All fields present")
    
    # Validate build queue
    queue = state.get('queue', [])
    if not isinstance(queue, list):
        print(f"❌ FAIL: Build queue is not a list: {type(queue)}")
        return False
    
    print(f"✅ Build Queue: {len(queue)} items")
    
    # Validate population
    pop = state.get('pop', [])
    if not isinstance(pop, list) or len(pop) != 2:
        print(f"❌ FAIL: Population is not [current, max]: {pop}")
        return False
    
    if pop[0] < 0 or pop[1] <= 0:
        print(f"❌ FAIL: Invalid population values: current={pop[0]}, max={pop[1]}")
        return False
    
    print(f"✅ Population: {pop[0]}/{pop[1]}")
    
    # Validate game time
    game_time = state.get('game_time')
    if game_time is None or game_time < 0:
        print(f"❌ FAIL: Invalid game_time: {game_time}")
        return False
    
    print(f"✅ Game Time: {game_time:.1f}s")
    
    # Validate phase
    phase = state.get('phase')
    valid_phases = ['early', 'mid', 'late']
    if phase not in valid_phases:
        print(f"❌ FAIL: Invalid phase: {phase}")
        return False
    
    print(f"✅ Game Phase: {phase}")
    
    # Validate faction
    faction = state.get('faction')
    valid_factions = ['allies', 'axis']
    if faction not in valid_factions:
        print(f"❌ FAIL: Invalid faction: {faction}")
        return False
    
    print(f"✅ Faction: {faction}")
    
    # Summary
    print("\n" + "="*50)
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("="*50)
    return True

if __name__ == "__main__":
    import os
    
    state_file = "coh1ai_state.json"
    if len(sys.argv) > 1:
        state_file = sys.argv[1]
    
    if not os.path.exists(state_file):
        print(f"❌ FAIL: State file not found: {state_file}")
        sys.exit(1)
    
    success = validate_state_file(state_file)
    sys.exit(0 if success else 1)
```

Run validation:
```bash
python validate_state.py coh1ai_state.json > test_results/phase0/test2_validation.txt 2>&1
```

#### Step 2.6: Additional Validation Checks

**Check File Size**:
```bash
echo "State file size:" >> test_results/phase0/test2_validation.txt
stat -c%s coh1ai_state.json >> test_results/phase0/test2_validation.txt
```

**Check Update Frequency**:
1. Start game and play for 30 seconds
2. Note timestamps in state file (`time` field)
3. Check that multiple updates occurred

```bash
# Extract timestamps from state file
python -c "
import json
with open('coh1ai_state.json') as f:
    state = json.load(f)
    print(f'State timestamp: {state.get(\"time\", \"N/A\")}')
    print(f'Game time: {state.get(\"game_time\", \"N/A\")}s')
" >> test_results/phase0/test2_validation.txt
```

### Acceptance Criteria

| **Criteria** | **Verification** | **Status** |
|--------------|-----------------|------------|
| All data points collected accurately | Validation script passes | [ ] |
| Collection completes within tick time budget | State file updates every ~1 second | [ ] |
| No performance impact on game | Game runs smoothly during collection | [ ] |
| Handles edge cases (no units, no enemies) | Validation handles empty arrays | [ ] |

### Test Data Collection

**Summary Report**:
```bash
cat > test_results/phase0/test2_state_collection.txt << 'EOF'
=== TEST 2: State Collection ===
Date: [DATE]
Game Duration: [X] seconds

Results:
- State file created: [PASS/FAIL]
- Valid JSON: [PASS/FAIL]
- All required fields present: [PASS/FAIL]
- Resources data valid: [PASS/FAIL]
- Squads data valid: [PASS/FAIL] ({count} squads)
- Capture points data valid: [PASS/FAIL] ({count} CPs)
- Enemies data valid: [PASS/FAIL] ({count} enemies)
- Tech tree data valid: [PASS/FAIL]
- Build queue data valid: [PASS/FAIL]
- Population data valid: [PASS/FAIL]
- Game time valid: [PASS/FAIL]
- Phase valid: [PASS/FAIL]
- Faction valid: [PASS/FAIL]

File Size: [X] bytes
Update Frequency: [Every X seconds]

Notes:
[Any observations]

=== VALIDATION OUTPUT ===
EOF

python validate_state.py coh1ai_state.json >> test_results/phase0/test2_state_collection.txt 2>&1
```

### Troubleshooting

| **Issue** | **Diagnosis** | **Solution** |
|-----------|---------------|--------------|
| No state file created | File I/O permissions | Check `coh1ai_data/` directory permissions |
| Empty state file | Collection failed | Check SCAR console for errors |
| Invalid JSON | Serialization error | Verify `SerializeToJSON()` in ipc.scar |
| Missing fields | Incomplete collection | Check each collection function in state_collector.scar |
| Negative values | API returning invalid data | Add validation in collection functions |
| No squads found | Called too early | Wait 30+ seconds before checking |

---

## 🎯 PHASE 0 STEPS 1 & 2 COMPLETION CHECKLIST

### Feature 1.1: SCAR Mod Framework
- [ ] Mod loads in CoH1 skirmish without errors
- [ ] Mod can be enabled in mod selection screen
- [ ] Custom SCAR code executes (initialization messages)
- [ ] Game starts and runs normally

### Feature 2.1: Game State Collector
- [ ] State file (`coh1ai_state.json`) is created
- [ ] State file contains valid JSON
- [ ] All required fields present in state
- [ ] Resources data is accurate (current > 0, max > 0)
- [ ] Squads data is collected (if units exist)
- [ ] Capture points data is collected
- [ ] Enemies data is collected (if visible)
- [ ] Tech tree data is collected
- [ ] Build queue data is collected
- [ ] Population data is collected and valid
- [ ] Game time is tracked
- [ ] Game phase is determined correctly
- [ ] Faction is identified correctly

---

## 📊 TEST SUMMARY REPORT

Create `test_results/phase0/SUMMARY.md`:

```markdown
# Phase 0 Steps 1 & 2 Test Summary

## Test Results

### Test 1: SCAR Mod Loading (Feature 1.1)
**Status**: [PASS/FAIL]

**Details**:
- Mod loads in CoH1: [✅/❌]
- Mod appears in list: [✅/❌]
- Game starts normally: [✅/❌]
- No errors: [✅/❌]
- No crashes: [✅/❌]

**Notes**: [Any observations]

---

### Test 2: State Collection (Feature 2.1)
**Status**: [PASS/FAIL]

**Details**:
- State file created: [✅/❌]
- Valid JSON: [✅/❌]
- All fields present: [✅/❌]
- Resources valid: [✅/❌]
- Squads collected: [✅/❌] ({count})
- Capture points collected: [✅/❌] ({count})
- Enemies collected: [✅/❌] ({count})
- Tech tree valid: [✅/❌]
- Build queue valid: [✅/❌]
- Population valid: [✅/❌]
- Game time valid: [✅/❌]
- Phase valid: [✅/❌]
- Faction valid: [✅/❌]

**File Size**: [X] bytes
**Update Frequency**: Every [X] seconds

**Notes**: [Any observations]

---

## Acceptance Criteria Status

### Feature 1.1: SCAR Mod Framework
- [ ] Empty mod loads successfully in CoH1 skirmish
- [ ] Mod can be packaged as .sga file
- [ ] Mod executes custom SCAR/Lua code
- [ ] No crashes or errors on load

### Feature 2.1: Game State Collector
- [ ] All specified data points collected accurately
- [ ] Collection completes within tick time budget
- [ ] No performance impact on game
- [ ] Handles edge cases (no units, no enemies visible)

---

## Issues Found

1. **[Issue Title]**
   - **Severity**: [High/Medium/Low]
   - **Description**: [Detailed description]
   - **Reproduction**: [Steps to reproduce]
   - **Workaround**: [If any]
   - **Status**: [Open/Resolved]

---

## Recommendations

[List any recommendations for improvements or next steps]

---

## Next Steps

- [ ] If all tests pass: Proceed to Test 3 (IPC Communication)
- [ ] If any tests fail: Resolve issues and retest
- [ ] Document solutions to any issues found

---

*Test Date*: [YYYY-MM-DD]  
*Tester*: [Name]  
*CoH1 Version*: [Version]  
*SCAR Version*: [Version]
```

---

## 📚 REFERENCES

- **Development Plan**: `PROTOTYPE_DEVELOPMENT_PLAN.md`
- **SCAR Documentation**: https://scardoc.coh.fi/
- **SCAR Implementation**: `docs/SCAR_IMPLEMENTATION.md`
- **Python Orchestrator**: `python/main.py`
- **IPC Reader**: `python/ipc_reader.py`

---

## 🎮 TESTING CHECKLIST (Printable)

```
□ Test 1: SCAR Mod Loading
  □ Mod files packaged correctly
  □ Mod appears in CoH1 mod list
  □ Mod loads without errors
  □ Game starts normally
  □ Initialization messages appear
  □ No crashes or freezes

□ Test 2: State Collection
  □ State file created (coh1ai_state.json)
  □ File contains valid JSON
  □ All required fields present
  □ Resources data valid
  □ Squads data collected
  □ Capture points data collected
  □ Enemies data collected
  □ Tech tree data collected
  □ Build queue data collected
  □ Population data valid
  □ Game time tracked
  □ Game phase determined
  □ Faction identified

□ Documentation
  □ Test results saved
  □ Issues documented
  □ Summary report created
```

---

*Document Version*: 1.0  
*Last Updated*: 2026-10-10  
*Author*: Generated via developer skill
