"""
Portfolio simulation router for paper trading.
Provides endpoints for simulated trading and portfolio management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.portfolio_simulator import (
    simulator,
    OrderType,
    OrderSide,
    SimulatedPortfolio,
    SimulatedOrder
)
from ..utils.token_dep import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/v1/simulation")


# Request/Response models
class CreatePortfolioRequest(BaseModel):
    name: str = Field(default="Paper Portfolio", description="Portfolio name")
    initial_balance: float = Field(default=100000.0, ge=1000, description="Starting balance")


class PlaceOrderRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    side: str = Field(..., description="buy or sell")
    quantity: float = Field(..., gt=0, description="Number of shares")
    order_type: str = Field(default="market", description="market, limit, stop, stop_limit")
    limit_price: Optional[float] = Field(None, description="Price for limit orders")
    stop_price: Optional[float] = Field(None, description="Price for stop orders")


class PortfolioResponse(BaseModel):
    id: str
    name: str
    total_value: float
    cash_balance: float
    total_pnl: float
    total_pnl_percent: float
    positions_count: int
    created_at: str


class OrderResponse(BaseModel):
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    status: str
    filled_quantity: float
    filled_price: float
    created_at: str
    message: str


@router.post("/portfolios", response_model=PortfolioResponse)
async def create_portfolio(
    request: CreatePortfolioRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new simulated portfolio for paper trading.
    
    Each user can have multiple simulated portfolios to test different strategies.
    """
    portfolio = simulator.create_portfolio(
        user_id=str(current_user.id),
        name=request.name,
        initial_balance=request.initial_balance
    )
    
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        total_value=portfolio.total_value,
        cash_balance=portfolio.cash_balance,
        total_pnl=0.0,
        total_pnl_percent=0.0,
        positions_count=0,
        created_at=portfolio.created_at.isoformat()
    )


@router.get("/portfolios", response_model=List[PortfolioResponse])
async def get_portfolios(
    current_user: User = Depends(get_current_user)
):
    """
    Get all simulated portfolios for the current user.
    """
    portfolios = simulator.get_user_portfolios(str(current_user.id))
    
    return [
        PortfolioResponse(
            id=p.id,
            name=p.name,
            total_value=p.total_value,
            cash_balance=p.cash_balance,
            total_pnl=p.total_pnl,
            total_pnl_percent=p.total_pnl_percent,
            positions_count=len(p.positions),
            created_at=p.created_at.isoformat()
        )
        for p in portfolios
    ]


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio_details(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific portfolio.
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    return simulator.get_portfolio_performance(portfolio)


@router.post("/portfolios/{portfolio_id}/orders", response_model=OrderResponse)
async def place_order(
    portfolio_id: str,
    request: PlaceOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Place a simulated order in a portfolio.
    
    Supports market, limit, and stop orders with realistic execution simulation.
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Convert string enums
    try:
        order_side = OrderSide(request.side.lower())
        order_type = OrderType(request.order_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order side or type"
        )
    
    # Place the order
    order, success, message = simulator.place_order(
        portfolio=portfolio,
        symbol=request.symbol.upper(),
        side=order_side,
        quantity=request.quantity,
        order_type=order_type,
        limit_price=request.limit_price,
        stop_price=request.stop_price
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return OrderResponse(
        id=order.id,
        symbol=order.symbol,
        side=order.side.value,
        order_type=order.order_type.value,
        quantity=order.quantity,
        status=order.status.value,
        filled_quantity=order.filled_quantity,
        filled_price=order.filled_price,
        created_at=order.created_at.isoformat(),
        message=message
    )


@router.get("/portfolios/{portfolio_id}/orders")
async def get_orders(
    portfolio_id: str,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get orders for a portfolio.
    
    Can filter by status: pending, filled, cancelled, rejected
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Get all orders (pending + history)
    all_orders = portfolio.orders + portfolio.transaction_history
    
    # Filter by status if specified
    if status:
        all_orders = [o for o in all_orders if o.status.value == status.lower()]
    
    return [
        {
            "id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "order_type": order.order_type.value,
            "quantity": order.quantity,
            "price": order.price,
            "stop_price": order.stop_price,
            "status": order.status.value,
            "filled_quantity": order.filled_quantity,
            "filled_price": order.filled_price,
            "commission": order.commission,
            "created_at": order.created_at.isoformat(),
            "filled_at": order.filled_at.isoformat() if order.filled_at else None,
        }
        for order in all_orders
    ]


@router.delete("/portfolios/{portfolio_id}/orders/{order_id}")
async def cancel_order(
    portfolio_id: str,
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending order.
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    success, message = simulator.cancel_order(portfolio, order_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"status": "cancelled", "message": message}


@router.get("/portfolios/{portfolio_id}/positions")
async def get_positions(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all positions in a portfolio.
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    # Update market values
    simulator.update_portfolio_metrics(portfolio)
    
    return [
        {
            "symbol": pos.symbol,
            "quantity": pos.quantity,
            "average_cost": pos.average_cost,
            "current_price": pos.current_price,
            "market_value": pos.market_value,
            "cost_basis": pos.quantity * pos.average_cost,
            "unrealized_pnl": pos.unrealized_pnl,
            "unrealized_pnl_percent": pos.unrealized_pnl_percent,
        }
        for pos in portfolio.positions.values()
    ]


@router.post("/portfolios/{portfolio_id}/reset")
async def reset_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Reset a portfolio to its initial state.
    
    This will close all positions and cancel all orders.
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    simulator.reset_portfolio(portfolio)
    
    return {
        "status": "reset",
        "message": "Portfolio has been reset to initial state",
        "cash_balance": portfolio.cash_balance
    }


@router.get("/market/price/{symbol}")
async def get_market_price(symbol: str):
    """
    Get simulated market price for a symbol.
    
    In production, this would return real market data.
    """
    price = simulator.get_market_price(symbol.upper())
    
    return {
        "symbol": symbol.upper(),
        "price": price,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "simulated"
    }


@router.post("/portfolios/{portfolio_id}/process-orders")
async def process_pending_orders(
    portfolio_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Process pending limit and stop orders.
    
    This checks if any pending orders can be filled based on current market prices.
    In production, this would be called periodically by a background task.
    """
    portfolio = simulator.get_portfolio(str(current_user.id), portfolio_id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    filled_orders = simulator.process_limit_orders(portfolio)
    
    return {
        "processed": len(filled_orders),
        "filled_orders": [
            {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": order.filled_quantity,
                "price": order.filled_price,
            }
            for order in filled_orders
        ]
    }


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Get top performing simulated portfolios across all users.
    
    This creates a competitive element for paper trading.
    """
    all_portfolios = []
    
    for user_portfolios in simulator.portfolios.values():
        for portfolio in user_portfolios:
            simulator.update_portfolio_metrics(portfolio)
            all_portfolios.append({
                "portfolio_id": portfolio.id,
                "name": portfolio.name,
                "total_value": portfolio.total_value,
                "total_pnl_percent": portfolio.total_pnl_percent,
                "win_rate": portfolio.win_rate,
                "total_trades": portfolio.total_trades,
            })
    
    # Sort by P&L percentage
    all_portfolios.sort(key=lambda x: x["total_pnl_percent"], reverse=True)
    
    return all_portfolios[:limit]