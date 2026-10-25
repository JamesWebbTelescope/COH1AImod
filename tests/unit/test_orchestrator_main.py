import json
import sys
import time
from pathlib import Path
from unittest.mock import Mock

# Add the Python package directory to the import path.
sys.path.insert(0, str((Path(__file__).parent.parent.parent / "python").resolve()))

from config import COH1AI_DATA_DIR, Configuration
from ipc_reader import IPCReader
from logger import StateLogger
from orchestrator.main import OrchestratorService
from orchestrator.state_manager import StateManager
from ipc_fallback import ConsoleLogRelayIPC
from logger import LogParser


def test_generate_mock_data_writes_valid_state_file(tmp_path: Path):
    state_file = tmp_path / "coh1ai_state.json"
    service = OrchestratorService.__new__(OrchestratorService)
    service.ipc_reader = Mock(state_file=state_file)
    service.logger = Mock()

    service._generate_mock_data()

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["version"] == "1.0"
    assert state["player_id"] == 1
    assert state["resources"]["manpower"]["current"] == 500
    assert "squads" in state


def test_test_mode_persists_generated_state_history(tmp_path: Path):
    config = Configuration()
    config._config["ipc"].update(
        {
            "data_dir": str(tmp_path),
            "state_file": "coh1ai_state.json",
            "command_file": "coh1ai_commands.json",
            "lock_file": "coh1ai_lock.tmp",
            "poll_interval": 0.01,
        }
    )
    ipc_reader = IPCReader(config)
    state_logger = StateLogger(config)
    state_manager = StateManager(config, ipc_reader)
    service = OrchestratorService.__new__(OrchestratorService)
    service.ipc_reader = ipc_reader
    service.state_logger = state_logger
    service.state_manager = state_manager
    service.logger = Mock()
    service.test_mode = True

    assert ipc_reader.start()
    assert state_manager.start()
    try:
        deadline = time.monotonic() + 1.0
        while state_manager.get_current_state() is None and time.monotonic() < deadline:
            service._process_messages()
            time.sleep(0.01)

        assert state_manager.get_current_state() is not None
        assert state_logger.state_log_file.exists()
        logged_state = json.loads(state_logger.state_log_file.read_text(encoding="utf-8").splitlines()[0])
        assert logged_state["player_id"] == 1
    finally:
        state_manager.stop()
        ipc_reader.stop()


def test_ipc_and_state_history_use_same_data_directory(tmp_path: Path):
    config = Configuration()
    config._config["ipc"]["data_dir"] = str(tmp_path)
    config._config["debug"]["state_log_file"] = "states.jsonl"

    ipc_reader = IPCReader(config)
    state_logger = StateLogger(config)

    assert ipc_reader.data_dir == tmp_path
    assert ipc_reader.data_dirs == [tmp_path]
    assert ipc_reader.state_file.name == "coh1ai_state.json"
    assert ipc_reader.command_file.name == "coh1ai_commands.json"
    assert state_logger.log_dir == ipc_reader.data_dir
    assert state_logger.state_log_file.name == "states.jsonl"


def test_default_data_access_uses_coh1_install_data_folder():
    config = Configuration()

    ipc_reader = IPCReader(config)
    state_logger = StateLogger(config)
    log_parser = LogParser(config.get("ipc", "data_dir"))
    console_relay = ConsoleLogRelayIPC(config)

    assert ipc_reader.data_dir == COH1AI_DATA_DIR
    assert state_logger.log_dir == COH1AI_DATA_DIR
    assert log_parser.log_dir == COH1AI_DATA_DIR
    assert console_relay.log_file.parent == COH1AI_DATA_DIR
