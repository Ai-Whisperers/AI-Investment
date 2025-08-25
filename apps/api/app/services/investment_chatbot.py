"""
Investment guidance chatbot service.
Provides intelligent investment advice and portfolio recommendations.
Can work standalone or integrate with OpenAI/Claude APIs.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import re
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageRole(Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(Enum):
    """Types of user intents."""
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    STOCK_RESEARCH = "stock_research"
    MARKET_OUTLOOK = "market_outlook"
    RISK_ASSESSMENT = "risk_assessment"
    INVESTMENT_STRATEGY = "investment_strategy"
    EDUCATIONAL = "educational"
    GENERAL_QUERY = "general_query"
    GREETING = "greeting"
    UNKNOWN = "unknown"


@dataclass
class Message:
    """Chat message."""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ConversationContext:
    """Conversation context and state."""
    user_id: str
    session_id: str
    messages: List[Message] = field(default_factory=list)
    user_portfolio: Optional[dict] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, role: MessageRole, content: str, metadata: dict = None) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role, content, metadata=metadata or {}))
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages from conversation."""
        return self.messages[-limit:] if self.messages else []


class InvestmentChatbot:
    """
    AI-powered investment guidance chatbot.
    Provides personalized investment advice based on user context.
    """
    
    def __init__(self, use_ai_api: bool = False):
        """
        Initialize the chatbot.
        
        Args:
            use_ai_api: Whether to use external AI API (OpenAI/Claude)
        """
        self.use_ai_api = use_ai_api
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Knowledge base for rule-based responses
        self.knowledge_base = self._build_knowledge_base()
        
        # Intent patterns for classification
        self.intent_patterns = self._build_intent_patterns()
        
    def _build_knowledge_base(self) -> dict:
        """Build the knowledge base for rule-based responses."""
        return {
            "portfolio_tips": [
                "Diversification is key to reducing risk. Aim for a mix of stocks, bonds, and other assets.",
                "Rebalance your portfolio periodically to maintain your target allocation.",
                "Consider your time horizon when making investment decisions.",
                "Don't put all your eggs in one basket - spread investments across sectors.",
                "Review your portfolio quarterly but avoid overtrading.",
            ],
            "risk_management": [
                "Never invest more than you can afford to lose.",
                "Use stop-loss orders to limit potential losses.",
                "Consider your risk tolerance before making investment decisions.",
                "Emergency funds should be kept separate from investment portfolios.",
                "Diversification helps manage systematic risk.",
            ],
            "market_insights": [
                "Market volatility is normal - stay focused on long-term goals.",
                "Dollar-cost averaging can help reduce the impact of market timing.",
                "Economic indicators like GDP, inflation, and employment affect markets.",
                "Interest rate changes significantly impact bond and stock prices.",
                "Global events can create both risks and opportunities.",
            ],
            "investment_strategies": {
                "conservative": "Focus on bonds, dividend stocks, and stable value funds. Target 20-40% stocks, 60-80% bonds.",
                "moderate": "Balanced approach with 50-60% stocks, 30-40% bonds, 10% alternatives.",
                "aggressive": "Growth-focused with 80-90% stocks, emphasis on technology and emerging markets.",
                "income": "Prioritize dividend-paying stocks, REITs, and corporate bonds for regular income.",
            },
            "educational": {
                "P/E Ratio": "Price-to-Earnings ratio measures a stock's valuation. Lower P/E may indicate undervaluation.",
                "Market Cap": "Total value of a company's shares. Large-cap stocks are generally more stable.",
                "Dividend Yield": "Annual dividends per share divided by stock price. Higher yield means more income.",
                "Beta": "Measures volatility relative to market. Beta > 1 means more volatile than market.",
                "Sharpe Ratio": "Risk-adjusted return metric. Higher is better, indicating better returns per unit of risk.",
            }
        }
    
    def _build_intent_patterns(self) -> dict:
        """Build intent recognition patterns."""
        return {
            IntentType.PORTFOLIO_ANALYSIS: [
                r"analyze.*portfolio",
                r"review.*investments",
                r"portfolio.*performance",
                r"how.*doing",
                r"check.*holdings",
            ],
            IntentType.STOCK_RESEARCH: [
                r"what.*think.*\b[A-Z]{2,5}\b",
                r"research.*stock",
                r"tell.*about.*\b[A-Z]{2,5}\b",
                r"should.*buy",
                r"stock.*recommendation",
            ],
            IntentType.MARKET_OUTLOOK: [
                r"market.*outlook",
                r"market.*trend",
                r"economy",
                r"forecast",
                r"prediction",
            ],
            IntentType.RISK_ASSESSMENT: [
                r"risk",
                r"volatility",
                r"safe",
                r"conservative",
                r"protect",
            ],
            IntentType.INVESTMENT_STRATEGY: [
                r"strategy",
                r"approach",
                r"plan",
                r"allocat",
                r"diversif",
            ],
            IntentType.EDUCATIONAL: [
                r"what.*is",
                r"explain",
                r"how.*work",
                r"teach",
                r"learn",
            ],
            IntentType.GREETING: [
                r"^hi\b",
                r"^hello",
                r"^hey",
                r"good morning",
                r"good afternoon",
            ],
        }
    
    def classify_intent(self, message: str) -> IntentType:
        """
        Classify the intent of a user message.
        
        Args:
            message: User message
            
        Returns:
            Classified intent type
        """
        message_lower = message.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent_type
        
        return IntentType.UNKNOWN
    
    def extract_entities(self, message: str) -> dict:
        """
        Extract entities from user message.
        
        Args:
            message: User message
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract stock symbols (2-5 uppercase letters)
        symbols = re.findall(r'\b[A-Z]{2,5}\b', message)
        if symbols:
            entities['symbols'] = symbols
        
        # Extract percentages
        percentages = re.findall(r'\b\d+(?:\.\d+)?%', message)
        if percentages:
            entities['percentages'] = percentages
        
        # Extract dollar amounts
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', message)
        if amounts:
            entities['amounts'] = amounts
        
        # Extract time periods
        time_patterns = {
            'days': r'\b\d+\s*days?\b',
            'weeks': r'\b\d+\s*weeks?\b',
            'months': r'\b\d+\s*months?\b',
            'years': r'\b\d+\s*years?\b',
        }
        
        for period, pattern in time_patterns.items():
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                entities[period] = matches
        
        return entities
    
    def generate_response(
        self,
        context: ConversationContext,
        user_message: str
    ) -> str:
        """
        Generate a response to user message.
        
        Args:
            context: Conversation context
            user_message: User's message
            
        Returns:
            Generated response
        """
        # Classify intent
        intent = self.classify_intent(user_message)
        
        # Extract entities
        entities = self.extract_entities(user_message)
        
        # Log for debugging
        logger.info(f"Intent: {intent}, Entities: {entities}")
        
        # Generate response based on intent
        if self.use_ai_api:
            # Use external AI API (would need API key)
            return self._generate_ai_response(context, user_message, intent, entities)
        else:
            # Use rule-based response
            return self._generate_rule_based_response(context, intent, entities, user_message)
    
    def _generate_rule_based_response(
        self,
        context: ConversationContext,
        intent: IntentType,
        entities: dict,
        user_message: str
    ) -> str:
        """Generate rule-based response without AI API."""
        
        if intent == IntentType.GREETING:
            return self._handle_greeting()
        
        elif intent == IntentType.PORTFOLIO_ANALYSIS:
            return self._handle_portfolio_analysis(context, entities)
        
        elif intent == IntentType.STOCK_RESEARCH:
            return self._handle_stock_research(entities)
        
        elif intent == IntentType.MARKET_OUTLOOK:
            return self._handle_market_outlook()
        
        elif intent == IntentType.RISK_ASSESSMENT:
            return self._handle_risk_assessment(context)
        
        elif intent == IntentType.INVESTMENT_STRATEGY:
            return self._handle_investment_strategy(context)
        
        elif intent == IntentType.EDUCATIONAL:
            return self._handle_educational_query(user_message)
        
        else:
            return self._handle_unknown()
    
    def _handle_greeting(self) -> str:
        """Handle greeting messages."""
        import random
        greetings = [
            "Hello! I'm your AI investment assistant. How can I help you with your investment journey today?",
            "Hi there! Ready to explore investment opportunities? I can help with portfolio analysis, market insights, or answer your investment questions.",
            "Welcome! I'm here to provide investment guidance. Would you like to review your portfolio, explore strategies, or learn about the markets?",
        ]
        return random.choice(greetings)
    
    def _handle_portfolio_analysis(self, context: ConversationContext, entities: dict) -> str:
        """Handle portfolio analysis requests."""
        if not context.user_portfolio:
            return (
                "I'd be happy to analyze your portfolio! However, I don't have access to your current holdings yet. "
                "Could you tell me about your investments, or would you like general portfolio guidance?"
            )
        
        # Analyze portfolio (simplified)
        total_value = context.user_portfolio.get('total_value', 0)
        positions = context.user_portfolio.get('positions', [])
        
        response = f"Based on your portfolio worth ${total_value:,.2f}:\n\n"
        
        if len(positions) < 5:
            response += "• Your portfolio could benefit from more diversification. Consider adding positions across different sectors.\n"
        
        response += "• " + random.choice(self.knowledge_base['portfolio_tips']) + "\n"
        
        return response
    
    def _handle_stock_research(self, entities: dict) -> str:
        """Handle stock research queries."""
        symbols = entities.get('symbols', [])
        
        if symbols:
            symbol = symbols[0]
            return (
                f"For {symbol}, here's what you should consider:\n\n"
                f"• Check the P/E ratio compared to industry average\n"
                f"• Review recent earnings reports and guidance\n"
                f"• Analyze the company's competitive position\n"
                f"• Consider the sector's overall health\n"
                f"• Look at analyst ratings and price targets\n\n"
                f"Remember to do your own research and consider your risk tolerance before investing."
            )
        else:
            return (
                "When researching stocks, consider these factors:\n"
                "• Financial health (revenue growth, profit margins, debt levels)\n"
                "• Competitive advantages (moat, market share, brand strength)\n"
                "• Management quality and insider ownership\n"
                "• Industry trends and growth prospects\n"
                "• Valuation metrics relative to peers"
            )
    
    def _handle_market_outlook(self) -> str:
        """Handle market outlook queries."""
        import random
        insights = random.sample(self.knowledge_base['market_insights'], 2)
        
        return (
            "Here's my current market perspective:\n\n"
            f"• {insights[0]}\n"
            f"• {insights[1]}\n\n"
            "Remember that market predictions are inherently uncertain. "
            "Focus on your long-term investment goals rather than short-term market movements."
        )
    
    def _handle_risk_assessment(self, context: ConversationContext) -> str:
        """Handle risk assessment queries."""
        import random
        tips = random.sample(self.knowledge_base['risk_management'], 2)
        
        response = "Risk management is crucial for successful investing:\n\n"
        for tip in tips:
            response += f"• {tip}\n"
        
        response += "\nWould you like me to help assess your current portfolio's risk level?"
        
        return response
    
    def _handle_investment_strategy(self, context: ConversationContext) -> str:
        """Handle investment strategy queries."""
        risk_profile = context.preferences.get('risk_profile', 'moderate')
        strategy = self.knowledge_base['investment_strategies'].get(
            risk_profile,
            self.knowledge_base['investment_strategies']['moderate']
        )
        
        return (
            f"Based on a {risk_profile} risk profile, here's a suggested strategy:\n\n"
            f"{strategy}\n\n"
            f"Additional considerations:\n"
            f"• Regularly review and rebalance your portfolio\n"
            f"• Consider tax implications of your investments\n"
            f"• Keep some cash reserves for opportunities\n"
            f"• Don't try to time the market - stay consistent"
        )
    
    def _handle_educational_query(self, message: str) -> str:
        """Handle educational queries."""
        # Check if asking about specific terms
        for term, explanation in self.knowledge_base['educational'].items():
            if term.lower() in message.lower():
                return f"{term}:\n{explanation}"
        
        return (
            "I can explain various investment concepts. Here are some key terms:\n\n"
            "• P/E Ratio - Stock valuation metric\n"
            "• Market Cap - Company size classification\n"
            "• Dividend Yield - Income from stocks\n"
            "• Beta - Volatility measure\n"
            "• Sharpe Ratio - Risk-adjusted returns\n\n"
            "Which would you like to learn more about?"
        )
    
    def _handle_unknown(self) -> str:
        """Handle unknown queries."""
        return (
            "I'm not sure I understand your question completely. I can help with:\n"
            "• Portfolio analysis and recommendations\n"
            "• Stock research and market insights\n"
            "• Investment strategies and risk assessment\n"
            "• Educational content about investing\n\n"
            "Could you please rephrase your question or choose one of these topics?"
        )
    
    def _generate_ai_response(
        self,
        context: ConversationContext,
        user_message: str,
        intent: IntentType,
        entities: dict
    ) -> str:
        """
        Generate response using external AI API.
        This would integrate with OpenAI or Claude API.
        """
        # Placeholder for AI API integration
        # In production, this would call OpenAI/Claude API
        
        system_prompt = """You are an expert investment advisor AI assistant. 
        Provide helpful, accurate, and personalized investment guidance. 
        Always remind users to do their own research and consider their risk tolerance.
        Never provide guaranteed predictions or promise specific returns."""
        
        # Would send to AI API with context
        # response = ai_client.generate(
        #     system=system_prompt,
        #     messages=context.get_recent_messages(),
        #     user_message=user_message
        # )
        
        # For now, fall back to rule-based
        return self._generate_rule_based_response(context, intent, entities, user_message)
    
    def process_message(
        self,
        user_id: str,
        session_id: str,
        message: str,
        portfolio_data: Optional[dict] = None
    ) -> dict:
        """
        Process a user message and generate response.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            message: User's message
            portfolio_data: Optional portfolio data for context
            
        Returns:
            Response dictionary with message and metadata
        """
        # Get or create conversation context
        context_key = f"{user_id}_{session_id}"
        if context_key not in self.conversations:
            self.conversations[context_key] = ConversationContext(
                user_id=user_id,
                session_id=session_id,
                user_portfolio=portfolio_data
            )
        
        context = self.conversations[context_key]
        
        # Update portfolio data if provided
        if portfolio_data:
            context.user_portfolio = portfolio_data
        
        # Add user message to context
        context.add_message(MessageRole.USER, message)
        
        # Generate response
        response = self.generate_response(context, message)
        
        # Add assistant response to context
        context.add_message(MessageRole.ASSISTANT, response)
        
        # Extract any actionable items
        intent = self.classify_intent(message)
        entities = self.extract_entities(message)
        
        return {
            "response": response,
            "intent": intent.value,
            "entities": entities,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": self._get_suggestions(intent)
        }
    
    def _get_suggestions(self, intent: IntentType) -> List[str]:
        """Get follow-up suggestions based on intent."""
        suggestions_map = {
            IntentType.PORTFOLIO_ANALYSIS: [
                "Show me diversification analysis",
                "What's my risk score?",
                "How can I improve my returns?"
            ],
            IntentType.STOCK_RESEARCH: [
                "Compare with competitors",
                "What are the risks?",
                "Show me analyst ratings"
            ],
            IntentType.MARKET_OUTLOOK: [
                "What sectors look promising?",
                "How should I position my portfolio?",
                "What are the major risks?"
            ],
            IntentType.INVESTMENT_STRATEGY: [
                "Help me build a portfolio",
                "What's the best strategy for retirement?",
                "How much should I invest monthly?"
            ]
        }
        
        return suggestions_map.get(intent, [
            "Tell me about my portfolio",
            "What's the market outlook?",
            "Explain investment strategies"
        ])
    
    def get_conversation_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        Get conversation history for a session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum messages to return
            
        Returns:
            List of messages
        """
        context_key = f"{user_id}_{session_id}"
        if context_key not in self.conversations:
            return []
        
        context = self.conversations[context_key]
        messages = context.get_recent_messages(limit)
        
        return [msg.to_dict() for msg in messages]
    
    def clear_session(self, user_id: str, session_id: str) -> None:
        """Clear a conversation session."""
        context_key = f"{user_id}_{session_id}"
        if context_key in self.conversations:
            del self.conversations[context_key]


# Global chatbot instance
chatbot = InvestmentChatbot(use_ai_api=False)

# Can be upgraded to use AI API when keys are available:
# chatbot = InvestmentChatbot(use_ai_api=True)


import random