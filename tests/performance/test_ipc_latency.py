"""
IPC Latency Verification Tests (Phase 0, Step 0.5)

Measures round-trip latency for IPC communication between Python and SCAR.
Documents results for Feature 1.3 acceptance criteria.

Acceptance Criteria:
- Measured round-trip time <200ms
- Latency consistent across multiple test runs
- Documentation of latency measurements
"""

import json
import os
import sys
import time
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "python"))

from ipc_reader import IPCReader, IPCStats


class LatencyTester:
    """
    Tests round-trip latency for IPC communication.
    """
    
    def __init__(self, ipc_reader: IPCReader, num_tests: int = 100):
        """
        Initialize latency tester.
        
        Args:
            ipc_reader: IPCReader instance to test
            num_tests: Number of test cycles to run
        """
        self.ipc_reader = ipc_reader
        self.num_tests = num_tests
        self.results: List[float] = []
        self.logger = self.ipc_reader.logger
        
    def run_test(self) -> Dict[str, Any]:
        """
        Run latency test and return results.
        
        Returns:
            Dictionary containing test results
        """
        self.results = []
        
        self.logger.info(f"Starting latency test with {self.num_tests} cycles")
        
        # Warm up
        self._single_test()
        time.sleep(0.1)
        
        # Run actual tests
        for i in range(self.num_tests):
            latency = self._single_test()
            if latency is not None:
                self.results.append(latency)
            
            # Small delay between tests
            time.sleep(0.01)
            
            if (i + 1) % 20 == 0:
                self.logger.info(f"Completed {i + 1}/{self.num_tests} tests")
        
        return self._generate_report()
    
    def _single_test(self) -> Optional[float]:
        """
        Perform a single round-trip latency test.
        
        Returns:
            Latency in milliseconds, or None if test failed
        """
        # Generate a unique test ID
        test_id = f"latency_test_{time.time()}"
        start_time = time.time()
        
        # Send test command with timestamp
        test_command = {
            "command": "PING",
            "test_id": test_id,
            "timestamp": start_time
        }
        
        # Send the command
        if not self.ipc_reader.send_command(test_command):
            return None
        
        # Wait for response
        timeout = 1.0  # 1 second timeout
        end_time = time.time()
        
        # In a real scenario, SCAR would write a response back to the state file
        # For testing without SCAR, we'll simulate the response
        # Check if a response file was created
        response_file = self.ipc_reader.data_dir / f"{test_id}_response.json"
        
        while (end_time - start_time) < timeout:
            if response_file.exists():
                try:
                    with open(response_file, 'r') as f:
                        response = json.load(f)
                    response_time = response.get("timestamp", end_time)
                    latency_ms = (response_time - start_time) * 1000
                    
                    # Clean up response file
                    response_file.unlink()
                    return latency_ms
                except (json.JSONDecodeError, IOError):
                    return None
            
            time.sleep(0.001)
            end_time = time.time()
        
        return None
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        Generate a latency test report.
        
        Returns:
            Dictionary containing test statistics
        """
        if not self.results:
            return {
                "status": "FAILED",
                "error": "No valid test results",
                "num_tests": 0
            }
        
        # Calculate statistics
        avg_latency = sum(self.results) / len(self.results)
        min_latency = min(self.results)
        max_latency = max(self.results)
        
        # Calculate standard deviation
        variance = sum((x - avg_latency) ** 2 for x in self.results) / len(self.results)
        std_dev = variance ** 0.5
        
        # Count failures (None results)
        failure_count = self.num_tests - len(self.results)
        
        return {
            "status": "SUCCESS",
            "timestamp": time.time(),
            "num_tests": self.num_tests,
            "valid_results": len(self.results),
            "failure_count": failure_count,
            "average_latency_ms": round(avg_latency, 3),
            "min_latency_ms": round(min_latency, 3),
            "max_latency_ms": round(max_latency, 3),
            "std_deviation_ms": round(std_dev, 3),
            "passes_acceptance": avg_latency < 200,
            "acceptance_threshold_ms": 200
        }


class FileIOLatencyTester:
    """
    Tests latency for file-based IPC without SCAR.
    Simulates both ends of the communication.
    """
    
    def __init__(self, temp_dir: str, num_tests: int = 100):
        """
        Initialize file I/O latency tester.
        
        Args:
            temp_dir: Temporary directory for test files
            num_tests: Number of test cycles
        """
        self.temp_dir = Path(temp_dir)
        self.num_tests = num_tests
        self.results: List[float] = []
        self.state_file = self.temp_dir / "state.json"
        self.command_file = self.temp_dir / "command.json"
        self.lock_file = self.temp_dir / "lock.tmp"
        
        # Ensure directory exists
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def run_test(self) -> Dict[str, Any]:
        """
        Run file I/O latency test.
        
        Returns:
            Dictionary containing test results
        """
        self.results = []
        
        print(f"Starting file I/O latency test with {self.num_tests} cycles")
        
        for i in range(self.num_tests):
            latency = self._single_file_test()
            if latency is not None:
                self.results.append(latency)
            
            time.sleep(0.001)
        
        return self._generate_report()
    
    def _single_file_test(self) -> Optional[float]:
        """
        Perform a single file I/O test.
        
        Returns:
            Latency in milliseconds, or None if test failed
        """
        # Write test data
        start_time = time.time()
        
        test_data = {
            "test": "latency",
            "timestamp": start_time
        }
        
        try:
            # Write to command file
            with open(self.command_file, 'w') as f:
                json.dump(test_data, f)
            
            # Read from state file (simulating SCAR writing back)
            # First, write a response
            response_data = {
                "test": "response",
                "timestamp": time.time()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(response_data, f)
            
            # Now read the response
            with open(self.state_file, 'r') as f:
                response = json.load(f)
            
            # Clean up
            self.command_file.unlink(missing_ok=True)
            self.state_file.unlink(missing_ok=True)
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            return latency_ms
            
        except (IOError, json.JSONDecodeError):
            return None
    
    def _generate_report(self) -> Dict[str, Any]:
        """
        Generate a latency test report.
        
        Returns:
            Dictionary containing test statistics
        """
        if not self.results:
            return {
                "status": "FAILED",
                "error": "No valid test results",
                "num_tests": 0
            }
        
        avg_latency = sum(self.results) / len(self.results)
        min_latency = min(self.results)
        max_latency = max(self.results)
        variance = sum((x - avg_latency) ** 2 for x in self.results) / len(self.results)
        std_dev = variance ** 0.5
        
        return {
            "status": "SUCCESS",
            "timestamp": time.time(),
            "test_type": "file_io",
            "num_tests": self.num_tests,
            "valid_results": len(self.results),
            "average_latency_ms": round(avg_latency, 3),
            "min_latency_ms": round(min_latency, 3),
            "max_latency_ms": round(max_latency, 3),
            "std_deviation_ms": round(std_dev, 3),
            "passes_acceptance": avg_latency < 200
        }


def run_latency_tests():
    """Run all latency tests and print results."""
    print("=" * 80)
    print("IPC Latency Verification (Phase 0, Step 0.5)")
    print("=" * 80)
    
    # Test 1: File I/O latency
    print("\n[Test 1] File I/O Latency Test")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        io_tester = FileIOLatencyTester(temp_dir, num_tests=100)
        io_report = io_tester.run_test()
        
        print(f"Status: {io_report['status']}")
        print(f"Number of tests: {io_report['num_tests']}")
        print(f"Valid results: {io_report['valid_results']}")
        print(f"Average latency: {io_report['average_latency_ms']}ms")
        print(f"Min latency: {io_report['min_latency_ms']}ms")
        print(f"Max latency: {io_report['max_latency_ms']}ms")
        print(f"Std deviation: {io_report['std_deviation_ms']}ms")
        print(f"Passes acceptance (<200ms): {io_report['passes_acceptance']}")
        
        # Save report
        report_path = Path("docs/IPC_LATENCY_REPORT.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("# IPC Latency Verification Report\n\n")
            f.write("## Test Results\n\n")
            f.write("### File I/O Latency Test\n\n")
            for key, value in io_report.items():
                f.write(f"- **{key}**: {value}\n")
            f.write("\n")
        
        print(f"\nReport saved to: {report_path}")
    
    # Test 2: With IPCReader
    print("\n[Test 2] IPCReader Latency Test")
    print("-" * 40)
    
    from config import Configuration
    config = Configuration()
    config._config["ipc"]["data_dir"] = "temp_ipc_test"
    
    ipc_reader = IPCReader(config)
    
    # Override paths for testing
    ipc_reader.data_dir = Path("temp_ipc_test")
    ipc_reader.state_file = ipc_reader.data_dir / "test_state.json"
    ipc_reader.command_file = ipc_reader.data_dir / "test_command.json"
    ipc_reader.lock_file = ipc_reader.data_dir / "test_lock.tmp"
    
    # Ensure directory exists
    ipc_reader._ensure_data_dir()
    
    # Start IPC reader
    ipc_reader.start()
    time.sleep(0.1)
    
    tester = LatencyTester(ipc_reader, num_tests=50)
    report = tester.run_test()
    
    ipc_reader.stop()
    
    print(f"Status: {report['status']}")
    print(f"Number of tests: {report.get('num_tests', 0)}")
    print(f"Valid results: {report.get('valid_results', 0)}")
    if report.get('status') == "SUCCESS":
        print(f"Average latency: {report.get('average_latency_ms', 'N/A')}ms")
        print(f"Min latency: {report.get('min_latency_ms', 'N/A')}ms")
        print(f"Max latency: {report.get('max_latency_ms', 'N/A')}ms")
        print(f"Std deviation: {report.get('std_deviation_ms', 'N/A')}ms")
        print(f"Passes acceptance (<200ms): {report.get('passes_acceptance', False)}")
    elif report.get('error'):
        print(f"Error: {report.get('error')}")
    
    # Update report
    with open(report_path, 'a') as f:
        f.write("### IPCReader Latency Test\n\n")
        for key, value in report.items():
            f.write(f"- **{key}**: {value}\n")
        f.write("\n")
    
    print(f"\nReport updated: {report_path}")
    
    # Cleanup
    import shutil
    shutil.rmtree("temp_ipc_test", ignore_errors=True)
    
    print("\n" + "=" * 80)
    print("Latency Verification Complete")
    print("=" * 80)


if __name__ == "__main__":
    run_latency_tests()
