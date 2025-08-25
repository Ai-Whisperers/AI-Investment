"""
Portfolio simulation service for paper trading and education.
Implements the latest portfolio simulation patterns.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import random
import uuid
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types for trading."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side (buy/sell)."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order execution status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class SimulatedOrder:
    """Simulated trading order."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    portfolio_id: str = ""
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: float = 0.0
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    commission: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['side'] = self.side.value
        data['order_type'] = self.order_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['filled_at'] = self.filled_at.isoformat() if self.filled_at else None
        return data


@dataclass
class Position:
    """Portfolio position."""
    symbol: str
    quantity: float
    average_cost: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    
    def update_market_value(self, current_price: float) -> None:
        """Update position with current market price."""
        self.current_price = current_price
        self.market_value = self.quantity * current_price
        cost_basis = self.quantity * self.average_cost
        self.unrealized_pnl = self.market_value - cost_basis
        self.unrealized_pnl_percent = (
            (self.unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
        )


@dataclass
class SimulatedPortfolio:
    """Simulated portfolio for paper trading."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    name: str = "Paper Portfolio"
    initial_balance: float = 100000.0
    cash_balance: float = 100000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    orders: List[SimulatedOrder] = field(default_factory=list)
    transaction_history: List[SimulatedOrder] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Performance metrics
    total_value: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    def calculate_total_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        self.total_value = self.cash_balance + positions_value
        self.total_pnl = self.total_value - self.initial_balance
        self.total_pnl_percent = (
            (self.total_pnl / self.initial_balance * 100) 
            if self.initial_balance > 0 else 0
        )
        return self.total_value
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate from closed positions."""
        if self.total_trades == 0:
            return 0.0
        self.win_rate = (self.winning_trades / self.total_trades * 100)
        return self.win_rate


class PortfolioSimulator:
    """
    Portfolio simulation service for paper trading.
    Provides realistic trading simulation with market mechanics.
    """
    
    def __init__(self):
        # Store simulated portfolios by user
        self.portfolios: Dict[str, List[SimulatedPortfolio]] = {}
        
        # Simulated market data (in production, would fetch real prices)
        self.market_prices: Dict[str, float] = {}
        
        # Commission structure
        self.commission_per_trade = 0.0  # Can be set to simulate broker fees
        self.commission_percent = 0.0  # Percentage-based commission
        
        # Market simulation parameters
        self.slippage_percent = 0.01  # 0.01% slippage for market orders
        self.market_hours_only = False  # Whether to restrict to market hours
        
    def create_portfolio(
        self, 
        user_id: str, 
        name: str = "Paper Portfolio",
        initial_balance: float = 100000.0
    ) -> SimulatedPortfolio:
        """
        Create a new simulated portfolio for a user.
        
        Args:
            user_id: User identifier
            name: Portfolio name
            initial_balance: Starting cash balance
            
        Returns:
            Created portfolio
        """
        portfolio = SimulatedPortfolio(
            user_id=user_id,
            name=name,
            initial_balance=initial_balance,
            cash_balance=initial_balance
        )
        
        if user_id not in self.portfolios:
            self.portfolios[user_id] = []
        
        self.portfolios[user_id].append(portfolio)
        
        logger.info(f"Created portfolio {portfolio.id} for user {user_id}")
        return portfolio
    
    def get_portfolio(self, user_id: str, portfolio_id: str) -> Optional[SimulatedPortfolio]:
        """Get a specific portfolio."""
        if user_id in self.portfolios:
            for portfolio in self.portfolios[user_id]:
                if portfolio.id == portfolio_id:
                    return portfolio
        return None
    
    def get_user_portfolios(self, user_id: str) -> List[SimulatedPortfolio]:
        """Get all portfolios for a user."""
        return self.portfolios.get(user_id, [])
    
    def place_order(
        self,
        portfolio: SimulatedPortfolio,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Tuple[SimulatedOrder, bool, str]:
        """
        Place a simulated order.
        
        Args:
            portfolio: The portfolio to trade in
            symbol: Stock symbol
            side: Buy or sell
            quantity: Number of shares
            order_type: Type of order
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            
        Returns:
            Tuple of (order, success, message)
        """
        # Create order
        order = SimulatedOrder(
            user_id=portfolio.user_id,
            portfolio_id=portfolio.id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=limit_price,
            stop_price=stop_price
        )
        
        # Validate order
        validation_result = self._validate_order(portfolio, order)
        if not validation_result[0]:
            order.status = OrderStatus.REJECTED
            return order, False, validation_result[1]
        
        # Add to pending orders
        portfolio.orders.append(order)
        
        # Execute immediately if market order
        if order_type == OrderType.MARKET:
            return self._execute_order(portfolio, order)
        
        logger.info(f"Placed {order_type.value} order {order.id} for {symbol}")
        return order, True, f"{order_type.value.title()} order placed successfully"
    
    def _validate_order(
        self, 
        portfolio: SimulatedPortfolio, 
        order: SimulatedOrder
    ) -> Tuple[bool, str]:
        """
        Validate an order before execution.
        
        Args:
            portfolio: Portfolio to validate against
            order: Order to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check quantity
        if order.quantity <= 0:
            return False, "Quantity must be positive"
        
        # For buy orders, check cash balance
        if order.side == OrderSide.BUY:
            estimated_cost = self._estimate_order_cost(order)
            if estimated_cost > portfolio.cash_balance:
                return False, f"Insufficient funds. Need ${estimated_cost:.2f}, have ${portfolio.cash_balance:.2f}"
        
        # For sell orders, check position
        if order.side == OrderSide.SELL:
            position = portfolio.positions.get(order.symbol)
            if not position or position.quantity < order.quantity:
                available = position.quantity if position else 0
                return False, f"Insufficient shares. Want to sell {order.quantity}, have {available}"
        
        return True, "Order valid"
    
    def _estimate_order_cost(self, order: SimulatedOrder) -> float:
        """Estimate the cost of an order including commission."""
        # Get current market price (in production, fetch real price)
        market_price = self.get_market_price(order.symbol)
        
        # Use limit price if available, otherwise market price
        execution_price = order.price if order.price else market_price
        
        # Apply slippage for market orders
        if order.order_type == OrderType.MARKET:
            execution_price *= (1 + self.slippage_percent / 100)
        
        # Calculate base cost
        base_cost = execution_price * order.quantity
        
        # Add commission
        commission = self._calculate_commission(base_cost)
        
        return base_cost + commission
    
    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate trading commission."""
        fixed_commission = self.commission_per_trade
        percent_commission = trade_value * (self.commission_percent / 100)
        return fixed_commission + percent_commission
    
    def _execute_order(
        self, 
        portfolio: SimulatedPortfolio, 
        order: SimulatedOrder
    ) -> Tuple[SimulatedOrder, bool, str]:
        """
        Execute a market order immediately.
        
        Args:
            portfolio: Portfolio to execute in
            order: Order to execute
            
        Returns:
            Tuple of (order, success, message)
        """
        # Get execution price
        market_price = self.get_market_price(order.symbol)
        
        # Apply slippage
        if order.side == OrderSide.BUY:
            execution_price = market_price * (1 + self.slippage_percent / 100)
        else:
            execution_price = market_price * (1 - self.slippage_percent / 100)
        
        # Calculate commission
        trade_value = execution_price * order.quantity
        commission = self._calculate_commission(trade_value)
        
        # Update order
        order.filled_quantity = order.quantity
        order.filled_price = execution_price
        order.commission = commission
        order.status = OrderStatus.FILLED
        order.filled_at = datetime.utcnow()
        
        # Update portfolio
        if order.side == OrderSide.BUY:
            # Deduct cash
            total_cost = trade_value + commission
            portfolio.cash_balance -= total_cost
            
            # Update or create position
            if order.symbol in portfolio.positions:
                position = portfolio.positions[order.symbol]
                # Calculate new average cost
                total_quantity = position.quantity + order.quantity
                total_cost_basis = (position.quantity * position.average_cost) + trade_value
                position.quantity = total_quantity
                position.average_cost = total_cost_basis / total_quantity
            else:
                portfolio.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    average_cost=execution_price
                )
            
        else:  # SELL
            # Add cash
            total_proceeds = trade_value - commission
            portfolio.cash_balance += total_proceeds
            
            # Update position
            position = portfolio.positions[order.symbol]
            position.quantity -= order.quantity
            
            # Remove position if fully sold
            if position.quantity <= 0:
                del portfolio.positions[order.symbol]
                
            # Track win/loss
            pnl = (execution_price - position.average_cost) * order.quantity
            portfolio.total_trades += 1
            if pnl > 0:
                portfolio.winning_trades += 1
            else:
                portfolio.losing_trades += 1
        
        # Add to transaction history
        portfolio.transaction_history.append(order)
        
        # Remove from pending orders
        portfolio.orders = [o for o in portfolio.orders if o.id != order.id]
        
        # Update portfolio metrics
        self.update_portfolio_metrics(portfolio)
        
        logger.info(
            f"Executed {order.side.value} order for {order.quantity} {order.symbol} "
            f"at ${execution_price:.2f}"
        )
        
        return order, True, f"Order filled at ${execution_price:.2f}"
    
    def cancel_order(
        self, 
        portfolio: SimulatedPortfolio, 
        order_id: str
    ) -> Tuple[bool, str]:
        """
        Cancel a pending order.
        
        Args:
            portfolio: Portfolio containing the order
            order_id: Order to cancel
            
        Returns:
            Tuple of (success, message)
        """
        for order in portfolio.orders:
            if order.id == order_id:
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CANCELLED
                    portfolio.orders.remove(order)
                    portfolio.transaction_history.append(order)
                    return True, "Order cancelled successfully"
                else:
                    return False, f"Cannot cancel order with status {order.status.value}"
        
        return False, "Order not found"
    
    def get_market_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.
        In production, this would fetch real market data.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price
        """
        # Return cached price if available
        if symbol in self.market_prices:
            # Add some random walk for simulation
            current_price = self.market_prices[symbol]
            change = random.uniform(-0.02, 0.02)  # ±2% random change
            new_price = current_price * (1 + change)
            self.market_prices[symbol] = new_price
            return new_price
        
        # Generate initial price for simulation
        base_prices = {
            "AAPL": 180.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "TSLA": 250.0,
            "AMZN": 170.0,
            "META": 480.0,
            "NVDA": 680.0,
            "SPY": 450.0,
        }
        
        if symbol in base_prices:
            price = base_prices[symbol]
        else:
            # Random price between $10 and $500
            price = random.uniform(10, 500)
        
        self.market_prices[symbol] = price
        return price
    
    def update_portfolio_metrics(self, portfolio: SimulatedPortfolio) -> None:
        """
        Update portfolio performance metrics.
        
        Args:
            portfolio: Portfolio to update
        """
        # Update position values
        for position in portfolio.positions.values():
            current_price = self.get_market_price(position.symbol)
            position.update_market_value(current_price)
        
        # Calculate total value and P&L
        portfolio.calculate_total_value()
        portfolio.calculate_win_rate()
    
    def process_limit_orders(self, portfolio: SimulatedPortfolio) -> List[SimulatedOrder]:
        """
        Process pending limit and stop orders.
        This would be called periodically to check if orders can be filled.
        
        Args:
            portfolio: Portfolio to process orders for
            
        Returns:
            List of filled orders
        """
        filled_orders = []
        
        for order in portfolio.orders[:]:  # Copy list to allow modification
            if order.status != OrderStatus.PENDING:
                continue
            
            market_price = self.get_market_price(order.symbol)
            
            # Check limit orders
            if order.order_type == OrderType.LIMIT:
                if order.side == OrderSide.BUY and market_price <= order.price:
                    # Buy limit order fills when market price drops to limit
                    self._execute_order(portfolio, order)
                    filled_orders.append(order)
                elif order.side == OrderSide.SELL and market_price >= order.price:
                    # Sell limit order fills when market price rises to limit
                    self._execute_order(portfolio, order)
                    filled_orders.append(order)
            
            # Check stop orders
            elif order.order_type == OrderType.STOP:
                if order.side == OrderSide.BUY and market_price >= order.stop_price:
                    # Buy stop order triggers when price rises to stop
                    self._execute_order(portfolio, order)
                    filled_orders.append(order)
                elif order.side == OrderSide.SELL and market_price <= order.stop_price:
                    # Sell stop order triggers when price drops to stop
                    self._execute_order(portfolio, order)
                    filled_orders.append(order)
        
        return filled_orders
    
    def get_portfolio_performance(
        self, 
        portfolio: SimulatedPortfolio
    ) -> dict:
        """
        Get detailed portfolio performance metrics.
        
        Args:
            portfolio: Portfolio to analyze
            
        Returns:
            Performance metrics dictionary
        """
        self.update_portfolio_metrics(portfolio)
        
        # Calculate additional metrics
        positions_count = len(portfolio.positions)
        total_invested = sum(
            pos.quantity * pos.average_cost 
            for pos in portfolio.positions.values()
        )
        
        return {
            "portfolio_id": portfolio.id,
            "total_value": portfolio.total_value,
            "cash_balance": portfolio.cash_balance,
            "positions_value": portfolio.total_value - portfolio.cash_balance,
            "total_pnl": portfolio.total_pnl,
            "total_pnl_percent": portfolio.total_pnl_percent,
            "positions_count": positions_count,
            "total_invested": total_invested,
            "win_rate": portfolio.win_rate,
            "total_trades": portfolio.total_trades,
            "winning_trades": portfolio.winning_trades,
            "losing_trades": portfolio.losing_trades,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "average_cost": pos.average_cost,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_percent": pos.unrealized_pnl_percent,
                }
                for pos in portfolio.positions.values()
            ],
            "pending_orders": len(portfolio.orders),
            "created_at": portfolio.created_at.isoformat(),
        }
    
    def reset_portfolio(self, portfolio: SimulatedPortfolio) -> None:
        """
        Reset a portfolio to initial state.
        
        Args:
            portfolio: Portfolio to reset
        """
        portfolio.cash_balance = portfolio.initial_balance
        portfolio.positions.clear()
        portfolio.orders.clear()
        portfolio.transaction_history.clear()
        portfolio.total_value = portfolio.initial_balance
        portfolio.total_pnl = 0.0
        portfolio.total_pnl_percent = 0.0
        portfolio.win_rate = 0.0
        portfolio.total_trades = 0
        portfolio.winning_trades = 0
        portfolio.losing_trades = 0
        
        logger.info(f"Reset portfolio {portfolio.id}")


# Global simulator instance
simulator = PortfolioSimulator()