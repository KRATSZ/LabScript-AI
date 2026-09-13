"""
PyLabRobot Protocol Template
===========================

This is the golden template for all PyLabRobot protocols.
It provides the necessary scaffolding and structure that every PyLabRobot protocol must have.

The Agent will replace the [AGENT_CODE_STUB] placeholder with generated protocol logic.
"""

import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import (
    LiquidHandlerChatterboxBackend,  # For simulation
)

# Import common PyLabRobot resources.
# Note: Specific resources like plates and tip racks are usually defined in the
# hardware configuration and loaded dynamically, not imported directly.
from pylabrobot.resources import Deck, Plate, TipRack, Well


async def protocol(lh: LiquidHandler):
    """
    Main protocol function for PyLabRobot.

    This function contains all the liquid handling operations.
    The AI Agent will replace the placeholder below with generated protocol logic.

    Args:
        lh (LiquidHandler): The liquid handler instance for performing operations
    """
    
    # [AGENT_CODE_STUB]
    # The AI Agent will replace this comment with the actual protocol logic
    pass

async def main():
    """
    Main execution function that sets up the liquid handler and runs the protocol.
    """
    deck = Deck(name="sim_deck", size_x=600, size_y=400, size_z=120)
    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=deck)
    
    try:
        # Setup the liquid handler
        await lh.setup()
        
        # Run the protocol
        await protocol(lh)
        
        print("✅ Protocol execution completed successfully!")
        
    except Exception as e:
        print(f"❌ Protocol execution failed: {e}")
        raise
    finally:
        # Always stop the liquid handler to clean up resources
        try:
            await lh.stop()
        except Exception as cleanup_error:
            print(f"⚠️ Warning: Failed to clean up liquid handler: {cleanup_error}")

if __name__ == "__main__":
    """
    Entry point for running the protocol.
    """
    print("🚀 Starting PyLabRobot Protocol Execution...")
    asyncio.run(main())