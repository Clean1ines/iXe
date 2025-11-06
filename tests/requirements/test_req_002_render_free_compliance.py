import pytest
from pathlib import Path

def test_web_api_build_size_optimized():
    """Test that Dockerfile.web is optimized for Render Free tier (size, cache purge)."""
    dockerfile = Path("Dockerfile.web")
    assert dockerfile.exists(), "Dockerfile.web should exist"
    
    content = dockerfile.read_text()
    
    # Check for multi-stage build
    assert "FROM python:3.11-slim as builder" in content, "Dockerfile.web should have a builder stage"
    assert "FROM python:3.11-slim as runtime" in content, "Dockerfile.web should have a runtime stage"
    assert "COPY --from=builder" in content, "Dockerfile.web should copy from builder stage to runtime stage"
    
    # Check for cache purge
    assert "pip cache purge" in content, "Dockerfile.web should include 'pip cache purge' command"
    
    # Check for minimal runtime dependencies installation
    # This is harder to assert without specific commands, but we can check for the absence of heavy build dependencies in the runtime stage
    # Usually build-essential, gcc, etc. should be in builder, not runtime
    # For this test, we'll focus on the presence of the key optimization patterns above.

