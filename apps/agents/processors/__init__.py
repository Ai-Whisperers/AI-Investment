"""
Content processors for AI-powered signal extraction.

Implements MCP (Model Context Protocol) processors using Claude and GPT
to transform raw social media content into actionable trading signals.
"""

from .claude_mcp_processor import ClaudeMCPProcessor
from .signal_extractor import SignalExtractor
from .context_manager import ContextManager
from .pattern_detector import PatternDetector
from .credibility_scorer import CredibilityScorer

__all__ = [
    "ClaudeMCPProcessor",
    "SignalExtractor", 
    "ContextManager",
    "PatternDetector",
    "CredibilityScorer",
]