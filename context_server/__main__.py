"""
Entry point for running MCP Context Server as a module.

Usage:
    python -m context_server [options]

This module entry point delegates to the CLI interface for proper
argument parsing and command handling.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
