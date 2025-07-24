#!/usr/bin/env python3
"""
Video generation pipeline for Zoopla automation screenshots
Creates MP4 videos from screenshot sequences
"""

import os
import logging
import subprocess
from typing import List, Optional, Dict, Any
from pathlib import Path
import glob
from config.settings import settings

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self, output_dir: str = "videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Video settings
        self.fps = settings.VIDEO_FPS
        self.width = settings.VIDEO_WIDTH
        self.height = settings.VIDEO_HEIGHT
        
        logger.info(f"VideoGenerator initialized: {self.width}x{self.height} @ {self.fps}fps")
        
    def generate_video_from_screenshots(self, 
                                      screenshot_dir: str,
                                      city_name: str,
                                      output_filename: Optional[str] = None) -> str:
        """
        Generate MP4 video from screenshots in a directory
        
        Args:
            screenshot_dir: Directory containing screenshots
            city_name: Name of the city for filename
            output_filename: Custom output filename (optional)
            
        Returns:
            Path to generated video file
        """
        try:
            screenshot_path = Path(screenshot_dir)
            if not screenshot_path.exists():
                raise ValueError(f"Screenshot directory does not exist: {screenshot_dir}")
            
            # Find all PNG screenshots and sort them
            screenshot_files = sorted(glob.glob(str(screenshot_path / "*.png")))
            
            if not screenshot_files:
                raise ValueError(f"No PNG screenshots found in {screenshot_dir}")
                
            logger.info(f"Found {len(screenshot_files)} screenshots for video generation")
            
            # Generate output filename
            if not output_filename:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{city_name.lower()}_{timestamp}.mp4"
            
            output_path = self.output_dir / output_filename
            
            # Create video using simple ffmpeg approach
            success = self._create_video_simple(screenshot_files, output_path)
            
            if success and output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"✅ Video generated successfully: {output_path}")
                logger.info(f"   - File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                logger.info(f"   - Screenshots used: {len(screenshot_files)}")
                return str(output_path)
            else:
                raise Exception("Video generation failed - output file not created")
                
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            raise
    
    def _create_video_simple(self, screenshot_files: List[str], output_path: Path) -> bool:
        """Create video using simple ffmpeg concatenation"""
        try:
            # Create temporary file list for ffmpeg
            temp_list_file = output_path.parent / f"temp_filelist_{os.getpid()}.txt"
            
            with open(temp_list_file, 'w') as f:
                for screenshot in screenshot_files:
                    # Each image shown for duration based on fps (e.g., 0.5 seconds at 2fps)
                    duration = 1.0 / self.fps
                    f.write(f"file '{os.path.abspath(screenshot)}'\n")
                    f.write(f"duration {duration}\n")
                # Repeat last frame to ensure proper ending
                if screenshot_files:
                    f.write(f"file '{os.path.abspath(screenshot_files[-1])}'\n")
            
            # Simple ffmpeg command for basic video creation
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-f', 'concat',
                '-safe', '0',
                '-i', str(temp_list_file),
                '-vf', f'scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', str(self.fps),
                str(output_path)
            ]
            
            logger.info(f"Running ffmpeg command...")
            logger.debug(f"Command: {' '.join(cmd)}")
            
            # Run ffmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Clean up temp file
            if temp_list_file.exists():
                temp_list_file.unlink()
            
            if result.returncode == 0:
                logger.info("✅ FFmpeg completed successfully")
                return True
            else:
                logger.error(f"FFmpeg failed with return code {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg process timed out")
            return False
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install ffmpeg: sudo apt install ffmpeg")
            return False
        except Exception as e:
            logger.error(f"Error running ffmpeg: {e}")
            return False
    
    def generate_video_from_session(self, session_metadata: Dict[str, Any]) -> Optional[str]:
        """
        Generate video from screenshot session metadata
        
        Args:
            session_metadata: Metadata from ScreenshotManager
            
        Returns:
            Path to generated video or None if failed
        """
        try:
            session_dir = session_metadata.get('session_directory')
            if not session_dir:
                logger.error("No session directory in metadata")
                return None
                
            screenshots = session_metadata.get('screenshots', [])
            if not screenshots:
                logger.error("No screenshots in session metadata")
                return None
            
            # Extract city name from session directory
            city_name = "unknown"
            if '_' in os.path.basename(session_dir):
                city_name = os.path.basename(session_dir).split('_')[0]
            
            logger.info(f"Generating video for {len(screenshots)} screenshots from {city_name}")
            
            return self.generate_video_from_screenshots(
                session_dir, 
                city_name
            )
            
        except Exception as e:
            logger.error(f"Failed to generate video from session: {e}")
            return None
    
    def check_ffmpeg_availability(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("✅ FFmpeg is available")
                return True
            else:
                logger.warning("FFmpeg check failed")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("FFmpeg not found or not responding")
            return False
    
    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Get information about generated video"""
        try:
            video_file = Path(video_path)
            if not video_file.exists():
                return None
                
            # Get basic file info
            stat = video_file.stat()
            
            info = {
                'path': str(video_file),
                'filename': video_file.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / 1024 / 1024, 1),
                'created': stat.st_ctime,
                'settings': {
                    'width': self.width,
                    'height': self.height,
                    'fps': self.fps
                }
            }
            
            # Try to get video duration using ffprobe if available
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-print_format', 'json', 
                    '-show_format', str(video_file)
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    import json
                    probe_data = json.loads(result.stdout)
                    duration = float(probe_data.get('format', {}).get('duration', 0))
                    info['duration_seconds'] = round(duration, 1)
                    
            except Exception:
                logger.debug("Could not get video duration")
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None

# Convenience function for direct use
def create_video_from_screenshots(screenshot_dir: str, city_name: str, output_dir: str = "videos") -> Optional[str]:
    """
    Simple function to create video from screenshots
    
    Args:
        screenshot_dir: Directory containing screenshots
        city_name: City name for output filename
        output_dir: Output directory for video
        
    Returns:
        Path to generated video file or None if failed
    """
    try:
        generator = VideoGenerator(output_dir)
        return generator.generate_video_from_screenshots(screenshot_dir, city_name)
    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        return None