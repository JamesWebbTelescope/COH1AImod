# CoH1 × Mistral AI Mod Execution Sheet

This document is the working execution checklist for the current prototype. It is intended to be used as a stop/go board for each implementation phase.

All references to `coh1ai_data` in this sheet mean the single runtime data folder at `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data` (the same installation directory as `RelicCOH.exe`). Do not create or inspect a runtime data folder under the mod directory.

## Phase 0 — Baseline and runtime smoke checks

Goal: make sure the project boots and the Python orchestrator starts cleanly before deeper gameplay work.

### Commands

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"

python -m pytest tests/unit/test_config.py -q
python -m pytest tests/unit/test_ipc_reader.py -q
python -m pytest tests/unit/test_logger.py -q
python -m pytest tests/unit/test_schema.py -q
python python\main.py --test --debug
```

### Expected pass markers

- [ ] `test_config.py` passes cleanly
- [ ] No import-time or runtime traceback
- [ ] Orchestrator logs startup lines like:
  - `CoH1 AI Orchestrator v0.1.0 initialized`
  - `Orchestrator service started successfully`
  - `Service running. Press Ctrl+C to stop.`
- [ ] The session stays alive in test mode

### Expected fail markers

- [ ] `ModuleNotFoundError` or import problems
- [ ] Python process exits immediately
- [ ] No `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data` folder or no log output
- [ ] Orchestrator loops / hangs before startup completes

### Gate

- [ ] GO: baseline startup is clean
- [ ] STOP: startup fails and blocks state/IPC work

---

## Phase 1 — State collection and IPC validation

Goal: verify the SCAR-to-Python data path works and the JSON is valid.

### Commands

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"

mkdir "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data" 2>nul
python -m pytest tests/unit/test_schema.py -q
python -m pytest tests/integration/test_roundtrip.py -q
python python\main.py --test --debug
```

While the orchestrator is running (or after it stops), check the persistent state history:

```bat
python -c "import json, pathlib; p=pathlib.Path(r'D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data\states.jsonl'); print('exists=', p.exists()); lines=p.read_text().splitlines(); data=json.loads(lines[-1]); print('keys=', sorted(data.keys())[:10])"
```

SCAR and Python share `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data`. IPC snapshots use `.json` and are consumed and removed by Python after reading. Persistent state history uses JSON Lines (`.jsonl`) and is written to `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data\states.jsonl`.

### Expected pass markers

- [ ] `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data\states.jsonl` exists and contains at least one state
- [ ] Each non-empty line parses as JSON
- [ ] Output includes relevant keys such as `player_id`, `resources`, `squads`, `cps`, `tech`
- [ ] A new JSONL line is appended for each received state

### Expected fail markers

- [ ] Persistent state history is missing
- [ ] Empty or malformed JSON
- [ ] File never updates after game/test start
- [ ] State schema mismatches expected fields

### Gate

- [ ] GO: valid state pipeline exists
- [ ] STOP: no valid state file or state cannot be parsed

---

## Phase 2 — Reflex layer validation

Goal: confirm the local tactical logic works without waiting on the cloud strategist.

### Commands

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"

python -m pytest tests/unit/test_reflex_layer.py -q
python -m pytest tests/integration/test_reflex_integration.py -q
python -m pytest tests/unit/test_safety_filter.py -q
```

Runtime confidence check:

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
run_mod.bat --debug
```

### Expected pass markers

- [ ] Reflex tests pass
- [ ] Local safety checks do not reject valid commands
- [ ] Under-fire / low-health / capture-micro logic behaves predictably
- [ ] No scheduler deadlock or crash during fast ticks

### Expected fail markers

- [ ] Reflex logic never triggers
- [ ] Unsafe commands pass through validation
- [ ] Orchestrator logs show repeated errors or thread stalls
- [ ] Fast scheduler drifts or hangs

### Gate

- [ ] GO: reflex layer is safe and reliable
- [ ] STOP: emergency behaviors are unreliable or unsafe

---

## Phase 3 — Strategist / Mistral integration validation

Goal: ensure the model strategy loop emits valid decisions and stays safe when the API is offline or slow.

### Commands

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"

python -m pytest tests/unit -q
python -m pytest tests/integration -q
python python\main.py --debug
```

### Expected pass markers

- [ ] Strategist returns valid structured JSON
- [ ] Commands pass queue validation and safety checks
- [ ] API failure triggers fallback behavior gracefully
- [ ] No crash if Mistral is unavailable or times out

### Expected fail markers

- [ ] Invalid JSON output
- [ ] Strategist decisions never reach the command queue
- [ ] API timeout without fallback
- [ ] Commands rejected silently without diagnostics

### Gate

- [ ] GO: strategy layer is valid, safe, and recoverable
- [ ] STOP: model output cannot be consumed safely

---

## Phase 4 — Performance and evaluation

Goal: verify the system is performant, stable, and within intended cost/latency budgets.

### Commands

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"

python -m pytest tests/performance/test_ipc_latency.py -q
python -m pytest -q
```

### Expected pass markers

- [ ] IPC latency remains within the target threshold
- [ ] Tick scheduler stays stable
- [ ] No runaway memory growth or log explosion
- [ ] Cost/rate budget remains under control

### Expected fail markers

- [ ] Significant latency or jitter
- [ ] Scheduler drift / missed ticks
- [ ] API call budget exceeded repeatedly
- [ ] Log or memory growth becomes unbounded

### Gate

- [ ] GO: performance is acceptable and stable
- [ ] STOP: latency or cost issues compromise gameplay

---

## Phase 5 — Packaging and final validation

Goal: confirm the project is installable and launchable as a real mod.

### Commands

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"

python -m pytest -q
package_mod.bat
dir /b "*.sga"
```

### Expected pass markers

- [ ] Full relevant test suite passes or reaches agreed threshold
- [ ] `.sga` package is generated successfully
- [ ] Mod can be launched with `-modname coh1_mistral_ai`
- [ ] No fatal startup issues in CoH1

### Expected fail markers

- [ ] Packaging fails
- [ ] Archive is missing or empty
- [ ] Mod does not appear or crashes on start
- [ ] Critical tests remain red

### Gate

- [ ] GO: mod is packageable and launchable
- [ ] STOP: packaging or runtime launch is not stable

---

## CoH1 runtime launch procedure

### Start the orchestrator

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
run_mod.bat --debug
```

### Package the mod

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
package_mod.bat
```

### Launch CoH1 with the mod

```bat
"D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\RelicCOH.exe" -modname coh1_mistral_ai
```

### Expected runtime markers

- [ ] Orchestrator stays alive without crashing
- [ ] CoH1 starts with the mod enabled
- [ ] `D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\coh1ai_data\coh1ai_state.json` appears while SCAR writes (Python may consume it immediately)
- [ ] No instant crash during the first 30–60 seconds of gameplay
- [ ] Logs show state writes and command processing

### Runtime fail markers

- [ ] Crash on game startup
- [ ] State file never appears
- [ ] Python orchestrator exits immediately
- [ ] Game freezes or becomes unstable shortly after match start

---

## What to do next this week

### Week 1 — Stabilize the baseline

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
python -m pytest tests/unit/test_config.py -q
python -m pytest tests/unit/test_ipc_reader.py -q
python -m pytest tests/unit/test_schema.py -q
python python\main.py --test --debug
```

Checklist:

- [ ] Fix any failing baseline tests
- [ ] Confirm orchestrator startup is stable in test mode
- [ ] Verify the state file path is reliable
- [ ] Ensure log output is usable for debugging

### Week 2 — Finish the reflex layer

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
python -m pytest tests/unit/test_reflex_layer.py -q
python -m pytest tests/integration/test_reflex_integration.py -q
python -m pytest tests/unit/test_safety_filter.py -q
```

Checklist:

- [ ] Add low-health retreat behavior
- [ ] Add under-fire / artillery response hooks
- [ ] Add capture-point micro behavior
- [ ] Ensure build queues remain active

### Week 3 — Implement the strategist contract

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
python -m pytest tests/unit -q
python -m pytest tests/integration -q
python python\main.py --debug
```

Checklist:

- [ ] Implement the Mistral client
- [ ] Validate JSON decision output schema
- [ ] Add API failure fallback behavior
- [ ] Ensure safety checks block unsafe commands before execution

### Week 4 — Evaluate performance and stability

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
python -m pytest tests/performance/test_ipc_latency.py -q
python -m pytest -q
```

Checklist:

- [ ] Measure tick and IPC latency
- [ ] Validate scheduler stability under load
- [ ] Tune the call budget and fallback timings
- [ ] Confirm gameplay remains smooth under decision loops

### Week 5 — Packaging and launch readiness

```bat
cd /d "D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\COh1AIMod"
package_mod.bat
dir /b "*.sga"
```

Checklist:

- [ ] Package builds successfully
- [ ] `.sga` filename matches the expected mod name
- [ ] Launch path is valid in CoH1
- [ ] Runtime smoke test passes in a skirmish match

---

## Recommended implementation order

1. Baseline stability
2. IPC/state pipeline
3. Reflex layer
4. Safety validation
5. Mistral strategist
6. Evaluation / rate limiting
7. Packaging / polish

This order keeps the system playable before adding the expensive strategic layer and reduces wasted time on unstable foundations.
