import os
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ScreenshotManager:
    def __init__(self, base_directory: str = "screenshots"):
        self.base_directory = Path(base_directory)
        self.screenshots: List[str] = []
        self.current_session: Optional[str] = None
        
    def create_session_directory(self, city: str) -> str:
        """Create a session-specific directory for screenshots"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"{city.lower().replace(' ', '_')}_{timestamp}"
        self.current_session = session_name
        
        session_dir = self.base_directory / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created screenshot session directory: {session_dir}")
        return str(session_dir)
        
    def get_session_directory(self) -> str:
        """Get current session directory path"""
        if not self.current_session:
            raise RuntimeError("No active screenshot session")
        return str(self.base_directory / self.current_session)
        
    def add_screenshot(self, file_path: str, step_name: str = "") -> None:
        """Add a screenshot to the current session"""
        self.screenshots.append(file_path)
        logger.info(f"Added screenshot {len(self.screenshots)}: {file_path} ({step_name})")
        
    def get_screenshots(self) -> List[str]:
        """Get list of all screenshots in current session"""
        return self.screenshots.copy()
        
    def clear_session(self) -> None:
        """Clear current session data"""
        self.screenshots.clear()
        self.current_session = None
        logger.info("Screenshot session cleared")
        
    def get_screenshot_metadata(self) -> Dict[str, Any]:
        """Get metadata about current screenshot session"""
        return {
            "session_name": self.current_session,
            "screenshot_count": len(self.screenshots),
            "screenshots": self.screenshots,
            "session_directory": self.get_session_directory() if self.current_session else None
        }
        
    async def cleanup_old_sessions(self, keep_days: int = 7) -> None:
        """Clean up old screenshot sessions older than keep_days"""
        if not self.base_directory.exists():
            return
            
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        cleaned_count = 0
        
        try:
            for session_dir in self.base_directory.iterdir():
                if session_dir.is_dir():
                    if session_dir.stat().st_mtime < cutoff_time:
                        # Remove old session directory
                        import shutil
                        shutil.rmtree(session_dir)
                        cleaned_count += 1
                        
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old screenshot sessions")
                
        except Exception as e:
            logger.error(f"Error during screenshot cleanup: {e}")
            
    def validate_screenshots(self) -> Dict[str, Any]:
        """Validate that all screenshots in session exist and are readable"""
        validation_result = {
            "valid_count": 0,
            "invalid_count": 0,
            "missing_files": [],
            "invalid_files": []
        }
        
        for screenshot_path in self.screenshots:
            if not os.path.exists(screenshot_path):
                validation_result["missing_files"].append(screenshot_path)
                validation_result["invalid_count"] += 1
            else:
                try:
                    # Check if file is readable and has content
                    file_size = os.path.getsize(screenshot_path)
                    if file_size == 0:
                        validation_result["invalid_files"].append(screenshot_path)
                        validation_result["invalid_count"] += 1
                    else:
                        validation_result["valid_count"] += 1
                except Exception as e:
                    logger.error(f"Error validating screenshot {screenshot_path}: {e}")
                    validation_result["invalid_files"].append(screenshot_path)
                    validation_result["invalid_count"] += 1
                    
        logger.info(f"Screenshot validation: {validation_result['valid_count']} valid, {validation_result['invalid_count']} invalid")
        return validation_result