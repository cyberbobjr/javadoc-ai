"""
Example usage of the Javadoc automation system.
This script demonstrates how to use the automation programmatically.
"""

import logging
from javadoc_automation import JavadocAutomation, load_config, setup_logging


def main():
    """Example usage of Javadoc automation."""
    
    # Load configuration
    config = load_config('config.yaml')
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Javadoc automation example")
    
    # Create automation instance
    automation = JavadocAutomation(config)
    
    # Run the automation
    success = automation.run()
    
    if success:
        logger.info("Automation completed successfully!")
        print("\n✓ Javadoc generation completed successfully!")
        print("Check the email report for details.")
    else:
        logger.error("Automation failed!")
        print("\n✗ Javadoc generation failed!")
        print("Check the logs for details.")
    
    return success


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
