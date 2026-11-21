#!/usr/bin/env python3
"""
Phase 3 Test Runner

Runs all Phase 3 tests in pytest format.

Usage:
    python tests/run_phase3_tests.py              # Run all Phase 3 tests
    python tests/run_phase3_tests.py -v          # Verbose output
    python tests/run_phase3_tests.py --coverage  # With coverage
    python tests/run_phase3_tests.py unit         # Run unit tests only
    python tests/run_phase3_tests.py integration  # Run integration tests only

Author: Generated for Phase 3
Version: 1.0.0
Date: 2026-11-21
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# Phase 3 test files
PHASE3_UNIT_TESTS = [
    "tests/unit/test_mistral_client.py",
    "tests/unit/test_prompts.py",
    "tests/unit/test_strategist.py",
    "tests/unit/test_json_mode.py",
    "tests/unit/test_history.py",
    "tests/unit/test_rate_limiter.py",
]

PHASE3_INTEGRATION_TESTS = [
    "tests/integration/test_mistral_integration.py",
]

PHASE3_ALL_TESTS = PHASE3_UNIT_TESTS + PHASE3_INTEGRATION_TESTS


class TestRunner:
    """Runs Phase 3 tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
    
    def run_tests(self, test_files, verbose=False, coverage=False, 
                  exit_on_failure=False, filter_keyword=None):
        """Run specified test files."""
        if not test_files:
            print("No test files specified.")
            return 0
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend(["--cov=python", "--cov=scar", "--cov-report=term"])
        
        if filter_keyword:
            cmd.extend(["-k", filter_keyword])
        
        # Add test files
        for test_file in test_files:
            full_path = self.project_root / test_file
            if full_path.exists():
                cmd.append(str(full_path))
            else:
                print(f"Warning: Test file not found: {test_file}")
        
        if not cmd[-1].endswith(".py"):
            print("No valid test files found.")
            return 1
        
        # Run tests
        print(f"\n{'='*80}")
        print(f"Running Phase 3 Tests")
        print(f"{'='*80}\n")
        
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=not verbose,
            text=True
        )
        
        # Print output
        if verbose or result.returncode != 0:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        
        # Print summary
        print(f"\n{'='*80}")
        if result.returncode == 0:
            print("✅ ALL PHASE 3 TESTS PASSED")
        else:
            print("❌ SOME PHASE 3 TESTS FAILED")
        print(f"{'='*80}\n")
        
        if exit_on_failure and result.returncode != 0:
            sys.exit(result.returncode)
        
        return result.returncode
    
    def run_all_phase3_tests(self, verbose=False, coverage=False, 
                             exit_on_failure=False):
        """Run all Phase 3 tests."""
        return self.run_tests(
            PHASE3_ALL_TESTS,
            verbose=verbose,
            coverage=coverage,
            exit_on_failure=exit_on_failure
        )
    
    def run_unit_tests(self, verbose=False, coverage=False, 
                       exit_on_failure=False):
        """Run Phase 3 unit tests."""
        return self.run_tests(
            PHASE3_UNIT_TESTS,
            verbose=verbose,
            coverage=coverage,
            exit_on_failure=exit_on_failure
        )
    
    def run_integration_tests(self, verbose=False, coverage=False, 
                              exit_on_failure=False):
        """Run Phase 3 integration tests."""
        return self.run_tests(
            PHASE3_INTEGRATION_TESTS,
            verbose=verbose,
            coverage=coverage,
            exit_on_failure=exit_on_failure
        )
    
    def list_tests(self):
        """List all Phase 3 tests."""
        print("\n" + "="*80)
        print("PHASE 3 TEST FILES")
        print("="*80 + "\n")
        
        print("Unit Tests:")
        for test_file in PHASE3_UNIT_TESTS:
            full_path = self.project_root / test_file
            if full_path.exists():
                print(f"  ✅ {test_file}")
            else:
                print(f"  ❌ {test_file} (not found)")
        
        print("\nIntegration Tests:")
        for test_file in PHASE3_INTEGRATION_TESTS:
            full_path = self.project_root / test_file
            if full_path.exists():
                print(f"  ✅ {test_file}")
            else:
                print(f"  ❌ {test_file} (not found)")
        
        print("\n" + "="*80 + "\n")
    
    def check_test_files(self):
        """Check which test files exist."""
        existing = []
        missing = []
        
        for test_file in PHASE3_ALL_TESTS:
            full_path = self.project_root / test_file
            if full_path.exists():
                existing.append(test_file)
            else:
                missing.append(test_file)
        
        return existing, missing


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Phase 3 tests for CoH1 AI Mod",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_phase3_tests.py              # Run all Phase 3 tests
  python tests/run_phase3_tests.py -v          # Verbose output
  python tests/run_phase3_tests.py --coverage  # With coverage report
  python tests/run_phase3_tests.py unit        # Run unit tests only
  python tests/run_phase3_tests.py integration  # Run integration tests only
  python tests/run_phase3_tests.py --list      # List all test files
        """
    )
    
    parser.add_argument(
        "type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "list"],
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Show verbose output"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=False,
        help="Run with coverage report"
    )
    
    parser.add_argument(
        "--exit-on-failure",
        action="store_true",
        default=False,
        help="Exit immediately on first failure"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        default=False,
        help="List all test files and exit"
    )
    
    parser.add_argument(
        "-k", "--keyword",
        type=str,
        default=None,
        help="Filter tests by keyword"
    )
    
    args = parser.parse_args()
    
    # Create runner
    runner = TestRunner()
    
    # List tests if requested
    if args.list or args.type == "list":
        runner.list_tests()
        return 0
    
    # Check test files
    existing, missing = runner.check_test_files()
    
    if missing:
        print(f"\n⚠️  Warning: {len(missing)} test files not found:")
        for test_file in missing:
            print(f"  - {test_file}")
    
    print(f"\n✅ Found {len(existing)} Phase 3 test files")
    
    # Run tests based on type
    if args.type == "unit":
        return runner.run_unit_tests(
            verbose=args.verbose,
            coverage=args.coverage,
            exit_on_failure=args.exit_on_failure
        )
    elif args.type == "integration":
        return runner.run_integration_tests(
            verbose=args.verbose,
            coverage=args.coverage,
            exit_on_failure=args.exit_on_failure
        )
    else:  # all
        return runner.run_all_phase3_tests(
            verbose=args.verbose,
            coverage=args.coverage,
            exit_on_failure=args.exit_on_failure
        )


if __name__ == "__main__":
    sys.exit(main())
