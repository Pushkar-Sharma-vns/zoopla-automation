# Zoopla Automation Workflow

An AI-powered browser automation tool that searches Zoopla property listings, captures screenshots, generates videos, and extracts property data using Browserbase and Stagehand.

## Features

- **AI-Powered Automation**: Uses Stagehand for intelligent browser interactions
- **Cloudflare Bypass**: Advanced anti-detection with natural challenge completion
- **Video Generation**: Captures screenshots and creates silent 720p MP4 videos
- **Enhanced Screenshots**: Detailed capture of typing, clicking, and scrolling interactions
- **Data Extraction**: Pulls property details using Stagehand's AI extraction
- **Anti-Detection**: User agent rotation, viewport randomization, human behavior simulation
- **Retry Logic**: Exponential backoff for error handling
- **CLI Interface**: Command-line tool with city name arguments

## 📁 Project Structure

```
zoopla-automation/
├── main.py                          # CLI entry point
├── automation/                      # Core automation modules
│   ├── browserbase_client.py       # Stagehand/Browserbase integration
│   ├── zoopla_navigator.py         # Zoopla-specific navigation
│   ├── screenshot_manager.py       # Screenshot capture logic
│   └── data_extractor.py           # Property data extraction
├── utils/                          # Utility functions
│   ├── csv_handler.py              # CSV input/output operations
│   └── video_generator.py          # MP4 generation with ffmpeg
├── config/                         # Configuration management
│   └── settings.py                 # Environment variables
├── logs/                           # Log files (city-specific)
├── videos/                         # Generated MP4 files
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
└── README.md                       # This file
```

## Setup

### Prerequisites

- Python 3.8+
- FFmpeg (for video generation)
- Browserbase account and API key
- OpenAI API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd zoopla-automation
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg:**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Environment Variables

Create a `.env` file from `.env.example`


## Quick Start

### 1. Single City Automation (Recommended)

Run automation for a specific city:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Search for properties in a single city
python main.py Manchester
python main.py "Greater London"
python main.py Birmingham
python main.py Leeds
```

### 2. CSV Batch Processing (Legacy): **Not Implemented Yet**

For processing multiple cities from CSV:

```csv
city,video_path,property_data
London,,
Manchester,,
Birmingham,,
```

```bash
python main.py cities.csv
```

### 3. Results

- **Videos**: Generated MP4s in `videos/` directory
- **Screenshots**: Timestamped screenshots in session directories
- **Logs**: Automation logs in `logs/` directory  
- **Results JSON**: Detailed results saved as `automation_results_{city}.json`

## Output Format

### Single City Results

The automation provides comprehensive output including:

**Terminal Output:**
```
🚀 ZOOPLA AUTOMATION COMPLETED!
======================================================================
📍 City Searched: Manchester
✅ Success: Yes
📸 Screenshots Captured: 8
📁 Session Directory: zoopla_automation/manchester_20250125_143022
🎬 Generated Video: videos/manchester_20250125_143022.mp4
   📊 Video Size: 2.4 MB
   ⏱️  Duration: 12 seconds
🏠 Property Selected: https://www.zoopla.co.uk/for-sale/details/12345678

📋 Steps Completed (6/6):
   1. ✅ Navigate to Zoopla
   2. ✅ Search for city
   3. ✅ Access property listings
   4. ✅ Scroll through properties
   5. ✅ Select property
   6. ✅ Generate video

🎬 GENERATED VIDEO FILE:
   /home/user/zoopla-automation/videos/manchester_20250125_143022.mp4
======================================================================
```

**JSON Results File:**
```json
{
  "city": "Manchester",
  "success": true,
  "screenshots": [
    "zoopla_automation/manchester_20250125_143022/01_homepage_20250125_143025_001.png",
    "zoopla_automation/manchester_20250125_143022/02a_search_typed_20250125_143028_002.png",
    "zoopla_automation/manchester_20250125_143022/02b_search_clicked_20250125_143030_003.png"
  ],
  "video_path": "videos/manchester_20250125_143022.mp4",
  "property_url": "https://www.zoopla.co.uk/for-sale/details/12345678",
  "total_screenshots": 8,
  "steps_completed": ["Navigate to Zoopla", "Search for city", "Access property listings", "Scroll through properties", "Select property", "Generate video"]
}
```

### CSV Batch Processing (Legacy) **Not Implemented Yet**

For CSV workflow, the tool updates your input CSV with:

- `video_path`: Path to generated MP4 file
- `property_data`: JSON object with property details

Example output:
```csv
city,video_path,property_data
London,videos/london_20241124_143022.mp4,"{""title"":""2 bed flat"",""price"":""£450000"",""address"":""Central London""}"
```

## Configuration

### Video Settings

- **Resolution**: 720p (1280x720) - configurable via `VIDEO_WIDTH`/`VIDEO_HEIGHT`
- **Frame Rate**: 2 FPS - configurable via `VIDEO_FPS`  
- **Format**: H.264 MP4, no audio
- **Screenshots**: Enhanced capture including typing, clicking, and scrolling interactions

### Cloudflare Bypass

- **Natural Challenge Completion**: Waits for Cloudflare challenge to complete naturally
- **Anti-Detection**: User agent rotation, viewport randomization, realistic browser fingerprints
- **Cookie Injection**: Legitimate session cookies to bypass bot detection
- **Human Behavior Simulation**: Mouse movements, realistic delays, browsing patterns

### Retry Logic

- **Max Retries**: 3 attempts with exponential backoff
- **Handles**: Browserbase errors, Cloudflare challenges, HTTP 429 from Zoopla
- **Configurable**: Via `MAX_RETRIES` and `RETRY_DELAY`

### Logging

- **Console**: Real-time progress updates with emoji indicators
- **Files**: Detailed automation logs in `logs/main_automation.log`
- **Levels**: INFO, ERROR, DEBUG

## Troubleshooting

### Common Issues

**1. Missing API Keys**
```
Error: Missing required environment variables: BROWSERBASE_API_KEY
```
→ Check your `.env` file has all required keys

**2. FFmpeg Not Found**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```
→ Install FFmpeg using platform-specific instructions above

**3. Browserbase Connection Issues**
```
Failed to initialize Browserbase client
```
→ Verify API key and project ID are correct

**4. Cloudflare Challenge Timeout**
```
⚠️ Cloudflare challenge did not complete within timeout
```
→ Retry the automation - challenges are handled naturally and may take time

**5. Video Generation Failed**
```
Error generating video for city
```
→ Check FFmpeg installation and screenshot directory permissions

**6. City Name with Spaces**
```bash
# Use quotes for city names with spaces
python main.py "Greater London"
python main.py "West Yorkshire"
```

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python main.py Manchester
```

### Monitoring Browser Sessions

When using Browserbase, you can monitor live browser sessions:
```
Browser session: https://www.browserbase.com/sessions/{session_id}
```

### Testing Individual Components

```bash
# Test Cloudflare bypass
python test_natural_bypass.py

# Test complete workflow
python test_working_workflow.py London
```
