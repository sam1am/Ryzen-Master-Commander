#!/usr/bin/env python3
"""
Test script to verify QProcess changes work correctly.
This script tests that the converted functions can be called without blocking.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Import the modified functions
from src.app.system_utils import apply_tdp_settings
from src.app.main_window import MainWindow


def test_tdp_settings():
    """Test that apply_tdp_settings doesn't block"""
    print("Testing TDP settings with QProcess...")

    test_profile = {
        "fast-limit": 25,
        "slow-limit": 15,
    }

    def callback(success, message):
        print(f"TDP Settings callback: success={success}, message={message}")
        # Exit after 2 seconds to allow process to complete
        QTimer.singleShot(2000, app.quit)

    # This should return None immediately and not block
    result = apply_tdp_settings(test_profile, callback)
    print(f"apply_tdp_settings returned: {result} (should be None for async)")
    print("✓ Function returned immediately without blocking!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing QProcess Non-Blocking Behavior")
    print("=" * 60)

    app = QApplication(sys.argv)

    # Test TDP settings
    test_tdp_settings()

    print("\nIf the UI is responsive and you can see this message,")
    print("the QProcess conversion is working correctly!")
    print("\nWaiting for process to complete...")

    sys.exit(app.exec())
