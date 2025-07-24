import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Browserbase Configuration
    BROWSERBASE_API_KEY: str = os.getenv("BROWSERBASE_API_KEY", "")
    BROWSERBASE_PROJECT_ID: str = os.getenv("BROWSERBASE_PROJECT_ID", "")
    
    # Model Configuration
    MODEL_API_KEY: str = os.getenv("MODEL_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    
    # Stagehand Configuration
    STAGEHAND_API_URL: str = os.getenv("STAGEHAND_API_URL", "")
    
    # Video Configuration
    VIDEO_WIDTH: int = int(os.getenv("VIDEO_WIDTH", "1280"))
    VIDEO_HEIGHT: int = int(os.getenv("VIDEO_HEIGHT", "720"))
    VIDEO_FPS: int = int(os.getenv("VIDEO_FPS", "2"))
    
    # Retry Configuration
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("RETRY_DELAY", "1.0"))
    
    # Paths
    LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")
    VIDEOS_DIR: str = os.getenv("VIDEOS_DIR", "videos")
    
    # Zoopla Configuration
    ZOOPLA_BASE_URL: str = "https://www.zoopla.co.uk"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required environment variables"""
        required_vars = [
            ("BROWSERBASE_API_KEY", cls.BROWSERBASE_API_KEY),
            ("BROWSERBASE_PROJECT_ID", cls.BROWSERBASE_PROJECT_ID),
            ("MODEL_API_KEY", cls.MODEL_API_KEY),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

settings = Settings()