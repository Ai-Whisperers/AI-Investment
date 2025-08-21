"""
Index composition and value models.
"""

from sqlalchemy import Column, Date, Float, ForeignKey, Integer

from ..core.database import Base


class IndexValue(Base):
    """Index performance history model."""

    __tablename__ = "index_values"

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    value = Column(Float, nullable=False)  # base = 100

    def __repr__(self):
        return f"<IndexValue(date={self.date}, value={self.value})>"


class Allocation(Base):
    """Index asset allocation model."""

    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), index=True, nullable=False)
    weight = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Allocation(date={self.date}, asset_id={self.asset_id}, weight={self.weight})>"
