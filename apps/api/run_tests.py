#!/usr/bin/env python
"""Test runner with proper path configuration."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main())
