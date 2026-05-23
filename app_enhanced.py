"""
ASK YOUR BOOK - Enhanced Document Intelligence Platform
Restructured for better maintainability, performance, and user experience
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import enhanced modules
from ui.layout import setup_page_config, render_sidebar, render_main_content
from ui.state_manager import StateManager
from ui.error_handler import ErrorHandler
from core.document_manager import DocumentManager
from core.chat_manager import ChatManager
from utils.logger import setup_logger

# Initialize components
logger = setup_logger()
state_manager = StateManager()
error_handler = ErrorHandler()
document_manager = DocumentManager()
chat_manager = ChatManager()

def main():
    """Main application entry point"""
    try:
        # Setup page configuration
        setup_page_config()
        
        # Initialize application state
        state_manager.initialize()
        
        # Create main layout
        with st.container():
            # Render sidebar
            sidebar_data = render_sidebar(
                document_manager=document_manager,
                state_manager=state_manager
            )
            
            # Render main content
            render_main_content(
                document_manager=document_manager,
                chat_manager=chat_manager,
                state_manager=state_manager,
                sidebar_data=sidebar_data
            )
            
    except Exception as e:
        error_handler.handle_critical_error(e)
        logger.error(f"Critical application error: {e}")

if __name__ == "__main__":
    main()