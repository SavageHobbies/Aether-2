"""
Main entry point for Aether AI Companion API Gateway.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.api.gateway import main

if __name__ == "__main__":
    main()