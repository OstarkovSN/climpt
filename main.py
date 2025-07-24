#!/usr/bin/env python3
"""
Climpt - Clipboard Prompt Manager
Entry point for the application
"""

import sys
from app import ClimptApp

def main():
    """Main entry point"""
    app = ClimptApp()
    app.MainLoop()
    sys.exit(0)

if __name__ == "__main__":
    main()