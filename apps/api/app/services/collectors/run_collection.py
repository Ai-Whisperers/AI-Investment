"""
Run Collection Script
Entry point for GitHub Actions scheduled collection
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime

from zero_cost_orchestrator import ZeroCostOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/collection_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main collection entry point."""
    parser = argparse.ArgumentParser(description='Run signal collection')
    parser.add_argument('--hour', type=str, help='Collection hour (e.g., 06:00)')
    parser.add_argument('--focus', type=str, default='auto', 
                      help='Collection focus: auto, momentum, research, insider')
    
    args = parser.parse_args()
    
    logger.info(f"Starting collection - Hour: {args.hour}, Focus: {args.focus}")
    
    # Initialize orchestrator
    orchestrator = ZeroCostOrchestrator()
    
    # Run scheduled collection
    if args.hour:
        # Override current time for testing
        import app.services.collectors.zero_cost_orchestrator as zco
        original_now = datetime.now
        
        def mock_now():
            hour = int(args.hour.split(':')[0])
            return datetime.now().replace(hour=hour, minute=0, second=0)
        
        zco.datetime.now = mock_now
    
    try:
        await orchestrator.run_scheduled_collection()
        
        # Log quota status
        quota_status = orchestrator.get_quota_status()
        logger.info(f"Quota status: {quota_status}")
        
        # Log signals collected
        logger.info(f"Total signals collected: {len(orchestrator.signals_collected)}")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("Collection completed successfully")


if __name__ == "__main__":
    asyncio.run(main())