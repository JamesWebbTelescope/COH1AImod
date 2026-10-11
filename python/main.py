#!/usr/bin/env python3
"""
CoH1 × Mistral AI Mod - Main Orchestrator Service

This is the main entry point for the Python orchestrator service.
It manages communication between the SCAR mod and Mistral AI.

This file delegates to the orchestrator package.

Usage:
    python main.py [options]

Options:
    --config PATH    Load configuration from specific file
    --test           Run in test mode with mock data
    --debug          Enable debug logging
    --help           Show this help message

Author: Generated via planner skill
Version: 0.1.0
Date: 2026-10-11
"""

import sys
import os

# Add the parent directory to the path so we can import from orchestrator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run from orchestrator.main
from orchestrator.main import main as orchestrator_main

if __name__ == "__main__":
    sys.exit(orchestrator_main())
