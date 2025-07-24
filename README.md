# Zoopla Automation Workflow

An AI-powered browser automation tool that searches Zoopla property listings, captures screenshots, generates videos, and extracts property data using Browserbase and Stagehand.

## Features

- **AI-Powered Automation**: Uses Stagehand for intelligent browser interactions
- **Video Generation**: Captures screenshots and creates silent 720p MP4 videos
- **Data Extraction**: Pulls property details (title, price, address) from listings
- **Idempotent Runs**: Skips already processed cities
- **Retry Logic**: Exponential backoff for error handling
- **CSV Workflow**: Reads cities from input CSV, outputs results

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

### 1. Prepare Input CSV

Create a CSV file with cities to search:

```csv
city,video_path,property_data
London,,
Manchester,,
Birmingham,,
```

### 2. Run the Automation

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

python main.py cities.csv
```

### 3. Results

- **Videos**: Generated MP4s in `videos/` directory
- **Logs**: City-specific logs in `logs/` directory  
- **Updated CSV**: Property data and video paths added to input file

## Output Format

The tool updates your input CSV with:

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
- **Screenshots**: Captured at key workflow steps

### Retry Logic

- **Max Retries**: 3 attempts with exponential backoff
- **Handles**: Browserbase errors, HTTP 429 from Zoopla
- **Configurable**: Via `MAX_RETRIES` and `RETRY_DELAY`

### Logging

- **Console**: Real-time progress updates
- **Files**: City-specific logs in `logs/{city}.log`
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

**4. Video Generation Failed**
```
Error generating video for city
```
→ Check FFmpeg installation and screenshot directory permissions

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python main.py cities.csv
```
