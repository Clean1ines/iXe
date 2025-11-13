"""
Main entry point for scraping operations.

This script initializes the application container and starts the CLI interface.
It follows clean architecture principles by keeping the entry point thin
and delegating all business logic to use cases.
"""
import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.container.application_container import ApplicationContainer
from presentation.cli.scraping_cli_handler import ScrapingCLIHandler
from utils.logging_config import configure_logging
import config

async def main():
    """Main application entry point."""
    # Configure logging
    configure_logging(level=config.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 FIPI Parser starting...")
    print("🚀 FIPI Parser starting...")
    
    # Initialize application container
    container = ApplicationContainer(config.__dict__)
    
    try:
        # Get CLI handler
        cli_handler = ScrapingCLIHandler(
            scrape_subject_use_case=container.get_scrape_subject_use_case()
        )
        
        # Run CLI interface
        await cli_handler.run()
        
        logger.info("✅ FIPI Parser completed successfully")
        print("✅ FIPI Parser completed successfully")
        
    except KeyboardInterrupt:
        logger.info("👋 Application interrupted by user")
        print("\n👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"💥 Application failed: {e}", exc_info=True)
        print(f"\n💥 Application failed: {e}")
        sys.exit(1)
    finally:
        # Clean up resources
        await container.shutdown()

def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logging.info(f"Received shutdown signal {signum}, cleaning up...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Run main application
    asyncio.run(main())
