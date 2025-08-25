"""
Investment chatbot router.
Provides AI-powered investment guidance and conversation endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from ..services.investment_chatbot import chatbot
from ..utils.token_dep import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/chatbot")


# Request/Response models
class ChatMessage(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    portfolio_data: Optional[dict] = Field(None, description="Optional portfolio context")


class ChatResponse(BaseModel):
    response: str
    intent: str
    entities: dict
    session_id: str
    timestamp: str
    suggestions: List[str]


class ConversationHistory(BaseModel):
    messages: List[dict]
    session_id: str
    total_messages: int


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Send a message to the investment chatbot.
    
    The chatbot provides personalized investment guidance based on:
    - User's questions and context
    - Portfolio data (if provided)
    - Market knowledge and investment principles
    
    Authentication is optional - anonymous users get general advice,
    authenticated users get personalized recommendations.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Use user ID if authenticated, otherwise use session ID
    user_id = str(current_user.id) if current_user else f"anonymous_{session_id}"
    
    # Process the message
    result = chatbot.process_message(
        user_id=user_id,
        session_id=session_id,
        message=request.message,
        portfolio_data=request.portfolio_data
    )
    
    return ChatResponse(**result)


@router.get("/history/{session_id}", response_model=ConversationHistory)
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get conversation history for a session.
    
    Returns the message history for continuity in conversations.
    """
    user_id = str(current_user.id) if current_user else f"anonymous_{session_id}"
    
    messages = chatbot.get_conversation_history(
        user_id=user_id,
        session_id=session_id,
        limit=limit
    )
    
    return ConversationHistory(
        messages=messages,
        session_id=session_id,
        total_messages=len(messages)
    )


@router.delete("/session/{session_id}")
async def clear_session(
    session_id: str,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Clear a conversation session.
    
    Removes all messages and context for a session.
    """
    user_id = str(current_user.id) if current_user else f"anonymous_{session_id}"
    
    chatbot.clear_session(user_id, session_id)
    
    return {
        "status": "cleared",
        "session_id": session_id,
        "message": "Conversation session cleared successfully"
    }


@router.get("/suggestions")
async def get_topic_suggestions():
    """
    Get suggested topics and questions.
    
    Provides users with example questions and topics they can explore.
    """
    return {
        "categories": [
            {
                "name": "Portfolio Management",
                "icon": "📊",
                "suggestions": [
                    "Analyze my portfolio performance",
                    "How can I diversify better?",
                    "What's my risk score?",
                    "Should I rebalance my portfolio?"
                ]
            },
            {
                "name": "Market Analysis",
                "icon": "📈",
                "suggestions": [
                    "What's the market outlook?",
                    "Which sectors are trending?",
                    "Is it a good time to invest?",
                    "What are the major market risks?"
                ]
            },
            {
                "name": "Stock Research",
                "icon": "🔍",
                "suggestions": [
                    "Tell me about AAPL",
                    "Compare MSFT and GOOGL",
                    "What are the best dividend stocks?",
                    "Find undervalued stocks"
                ]
            },
            {
                "name": "Investment Strategy",
                "icon": "🎯",
                "suggestions": [
                    "Best strategy for retirement",
                    "How to invest $10,000?",
                    "Dollar-cost averaging explained",
                    "Growth vs value investing"
                ]
            },
            {
                "name": "Risk Management",
                "icon": "🛡️",
                "suggestions": [
                    "How to protect my portfolio?",
                    "What's a safe investment?",
                    "Explain stop-loss orders",
                    "How to hedge risks?"
                ]
            },
            {
                "name": "Educational",
                "icon": "📚",
                "suggestions": [
                    "What is P/E ratio?",
                    "Explain market cap",
                    "How do dividends work?",
                    "What is dollar-cost averaging?"
                ]
            }
        ]
    }


@router.post("/feedback/{session_id}")
async def submit_feedback(
    session_id: str,
    helpful: bool,
    feedback: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Submit feedback on chatbot responses.
    
    Helps improve the chatbot's responses over time.
    """
    # In production, this would store feedback for analysis
    return {
        "status": "received",
        "session_id": session_id,
        "message": "Thank you for your feedback!"
    }


@router.get("/capabilities")
async def get_chatbot_capabilities():
    """
    Get information about chatbot capabilities.
    
    Explains what the chatbot can and cannot do.
    """
    return {
        "capabilities": [
            {
                "feature": "Portfolio Analysis",
                "description": "Analyze portfolio composition, performance, and provide improvement suggestions",
                "available": True
            },
            {
                "feature": "Market Insights",
                "description": "Provide market outlook, trends, and economic analysis",
                "available": True
            },
            {
                "feature": "Stock Research",
                "description": "Basic stock analysis and comparison",
                "available": True
            },
            {
                "feature": "Investment Education",
                "description": "Explain investment concepts and strategies",
                "available": True
            },
            {
                "feature": "Risk Assessment",
                "description": "Evaluate portfolio risk and suggest risk management strategies",
                "available": True
            },
            {
                "feature": "Personalized Advice",
                "description": "Tailored recommendations based on your profile and goals",
                "available": True
            },
            {
                "feature": "Real-time Data",
                "description": "Live market data and pricing",
                "available": False,
                "note": "Requires API keys configuration"
            },
            {
                "feature": "Trade Execution",
                "description": "Place actual trades",
                "available": False,
                "note": "Use simulation mode for practice"
            }
        ],
        "disclaimers": [
            "This chatbot provides educational information only",
            "Not a substitute for professional financial advice",
            "Always do your own research before investing",
            "Past performance doesn't guarantee future results"
        ],
        "ai_mode": "rule-based",  # Can be "ai-powered" when API keys are configured
        "last_updated": "2025-01-25"
    }


@router.get("/quick-insights")
async def get_quick_insights(
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Get quick market insights and tips.
    
    Provides daily insights without needing to start a conversation.
    """
    import random
    
    # In production, these would be generated based on real market data
    insights = [
        {
            "type": "tip",
            "title": "Diversification Reminder",
            "content": "A well-diversified portfolio typically includes 15-20 different stocks across various sectors.",
            "icon": "💡"
        },
        {
            "type": "market",
            "title": "Market Volatility",
            "content": "Markets experiencing normal volatility. Stay focused on long-term goals.",
            "icon": "📊"
        },
        {
            "type": "strategy",
            "title": "Dollar-Cost Averaging",
            "content": "Consider investing a fixed amount regularly regardless of market conditions.",
            "icon": "📈"
        },
        {
            "type": "risk",
            "title": "Risk Management",
            "content": "Review your stop-loss orders and ensure they align with your risk tolerance.",
            "icon": "🛡️"
        }
    ]
    
    # Select 2-3 random insights
    selected = random.sample(insights, min(3, len(insights)))
    
    return {
        "insights": selected,
        "generated_at": datetime.utcnow().isoformat(),
        "personalized": current_user is not None
    }