#!/usr/bin/env python3
"""
CoH1 × Mistral AI Mod - Main Orchestrator Service

This is the main entry point for the Python orchestrator service.
It manages communication between the SCAR mod and Mistral AI.

Usage:
    python main.py [options]

Options:
    --config PATH    Load configuration from specific file
    --test           Run in test mode with mock data
    --debug          Enable debug logging
    --help           Show this help message

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-04
"""

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config, get_config
from ipc_reader import IPCReader, start_ipc, stop_ipc, get_ipc_reader
from logger import StateLogger, LogParser
from scheduler import StrategicTickScheduler, FastTickScheduler, SchedulerManager


class OrchestratorService:
    """Main orchestrator service for CoH1 AI mod."""
    
    def __init__(self, config_path=None, test_mode=False, debug_mode=False):
        """
        Initialize orchestrator service.
        
        Args:
            config_path: Path to configuration file
            test_mode: Run in test mode with mock data
            debug_mode: Enable debug logging
        """
        self.config_path = config_path
        self.test_mode = test_mode
        self.debug_mode = debug_mode
        self.running = False
        
        # Load configuration
        self.config = load_config(config_path)
        
        if debug_mode:
            self.config.set("debug", "level", "DEBUG")
            self.config.set("debug", "console_logging", True)
            self.config.set("debug", "file_logging", True)
        
        if test_mode:
            self.config.set("testing", "test_mode", True)
            self.config.set("testing", "fake_game_data", True)
        
        # Set up logging
        self.logger = self.config.setup_logging()
        
        # Initialize IPC reader
        self.ipc_reader = IPCReader(self.config)
        
        # Initialize state logger
        self.state_logger = StateLogger(self.config)
        
        # Initialize schedulers
        self.scheduler_manager = SchedulerManager()
        self.strategic_scheduler = StrategicTickScheduler(
            interval=10.0,  # 10 seconds between strategic decisions
            callback=self._on_strategic_tick
        )
        self.fast_scheduler = FastTickScheduler(
            interval=0.5,  # 500ms between fast ticks
            callback=self._on_fast_tick
        )
        self.scheduler_manager.add_scheduler("strategic", self.strategic_scheduler)
        self.scheduler_manager.add_scheduler("fast", self.fast_scheduler)
        
        self.logger.info(f"CoH1 AI Orchestrator v{self.config.get('mod', 'version')} initialized")
        if test_mode:
            self.logger.info("Running in TEST mode")
        if debug_mode:
            self.logger.info("Running in DEBUG mode")
    
    def start(self):
        """Start the orchestrator service."""
        if self.running:
            self.logger.warning("Service is already running")
            return False
        
        self.logger.info("Starting orchestrator service...")
        
        # Start IPC reader
        if not self.ipc_reader.start():
            self.logger.error("Failed to start IPC reader")
            return False
        
        self.running = True
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        # Start schedulers
        self.scheduler_manager.start_all()
        
        self.logger.info("Orchestrator service started successfully")
        self.logger.info(f"IPC state file: {self.ipc_reader.state_file}")
        self.logger.info(f"IPC command file: {self.ipc_reader.command_file}")
        self.logger.info(f"Data directory: {self.ipc_reader.data_dir}")
        
        return True
    
    def stop(self):
        """Stop the orchestrator service."""
        if not self.running:
            self.logger.info("Service is already stopped")
            return True
        
        self.logger.info("Stopping orchestrator service...")
        
        # Stop schedulers
        self.scheduler_manager.stop_all()
        
        # Stop IPC reader
        if not self.ipc_reader.stop():
            self.logger.warning("IPC reader did not stop gracefully")
        
        self.running = False
        self.logger.info("Orchestrator service stopped")
        
        return True
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def run(self):
        """Main service loop."""
        if not self.start():
            self.logger.error("Failed to start service")
            return False
        
        self.logger.info("Service running. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                self._process_messages()
                time.sleep(0.1)  # Small sleep to prevent busy waiting
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Service error: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        self.stop()
        return True
    
    def _process_messages(self):
        """Process incoming messages from SCAR mod."""
        try:
            # Get latest state
            message = self.ipc_reader.get_message(timeout=0.01)
            
            if message:
                self._handle_state_message(message)
            
            # In test mode, generate mock data if no real data
            if self.test_mode and self.ipc_reader.get_stats().messages_received == 0:
                self._generate_mock_data()
                
        except Exception as e:
            self.logger.error(f"Error processing messages: {e}")
    
    def _handle_state_message(self, message):
        """Handle a state message from SCAR."""
        self.logger.debug(f"Received state message at {message.timestamp}")
        
        # Log state using state logger
        state = message.data
        self.state_logger.log_state(state)
        
        # Log state summary
        if "player_id" in state:
            self.logger.info(f"State update from player {state['player_id']}")
            
            if "resources" in state:
                resources = state["resources"]
                self.logger.debug(f"Resources - MP: {resources.get('manpower', {}).get('current', 0)}, "
                                f"Fuel: {resources.get('fuel', {}).get('current', 0)}, "
                                f"Muni: {resources.get('munitions', {}).get('current', 0)}")
            
            if "squads" in state:
                self.logger.debug(f"Squads: {len(state['squads'])} active")
            
            if "game_time" in state:
                self.logger.debug(f"Game time: {state['game_time']:.1f}s")
        
        # Send test command if in test mode
        if self.test_mode:
            self._send_test_command()
    
    def _on_strategic_tick(self):
        """Callback for strategic tick scheduler."""
        self.logger.info("Strategic tick - Time to make macro decisions")
        # In Phase 1, we just log this event
        # In Phase 2+, this will trigger strategist decisions
        
    def _on_fast_tick(self):
        """Callback for fast tick scheduler."""
        self.logger.debug("Fast tick - Reflex layer update")
        # In Phase 1, we just log this event
        # In Phase 2+, this will trigger reflex decisions
    
    def _generate_mock_data(self):
        """Generate mock game data for testing."""
        # This would be replaced with actual state file creation in real use
        pass
    
    def _send_test_command(self):
        """Send a test command to SCAR."""
        test_command = {
            "command": "TEST",
            "data": "orchestrator_test",
            "timestamp": time.time()
        }
        
        if self.ipc_reader.send_command(test_command):
            self.logger.debug("Sent test command to SCAR")
        else:
            self.logger.warning("Failed to send test command")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CoH1 × Mistral AI Mod Orchestrator Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                      # Start with default config
  python main.py --config myconfig.json  # Use custom config
  python main.py --test              # Run in test mode
  python main.py --debug             # Enable debug logging
        """
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        default=False,
        help="Run in test mode with mock data"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        default=False,
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        default=False,
        help="Show version and exit"
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.version:
        # Get version from config
        try:
            config = load_config()
            version = config.get("mod", "version") or "unknown"
            name = config.get("mod", "name") or "CoH1 AI Orchestrator"
            print(f"{name} v{version}")
            return 0
        except Exception:
            print("CoH1 AI Orchestrator v0.1.0")
            return 0
    
    # Create and run orchestrator service
    try:
        service = OrchestratorService(
            config_path=args.config,
            test_mode=args.test,
            debug_mode=args.debug
        )
        
        # Run the service
        success = service.run()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nService stopped by user")
        return 0
    except Exception as e:
        print(f"Service error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())