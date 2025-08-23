# iClicker Question Scraper

A Python tool to automatically scrape questions and answers from iClicker student activities using web automation.

## Features

- 🔐 Secure credential handling via environment variables
- 📋 Extracts questions with correct answers
- 💾 Saves results in JSON format with timestamps  
- 🖥️ Both headless and visible browser modes
- 🔄 Designed for regular/automated usage
- ✅ Comprehensive test suite
- 🛠️ Easy-to-use CLI interface

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

**Option A: Environment Variables (Recommended)**
```bash
export ICLICKER_USERNAME="your_username@email.com"
export ICLICKER_PASSWORD="your_password"
```

**Option B: Use the setup command**
```bash
python iclicker_cli.py setup-env --username your_username@email.com
```

### 3. Scrape Questions

```bash
# Basic usage - scrape questions from an activity
python iclicker_cli.py scrape f7dcba1f-1231-4d91-906c-6e3acd9b660b

# With custom output file
python iclicker_cli.py scrape f7dcba1f-1231-4d91-906c-6e3acd9b660b -o my_questions.json

# Show browser window (for debugging)
python iclicker_cli.py scrape f7dcba1f-1231-4d91-906c-6e3acd9b660b --show-browser

# Verbose output with question details
python iclicker_cli.py scrape f7dcba1f-1231-4d91-906c-6e3acd9b660b --verbose
```

## CLI Commands

### `scrape` - Extract Questions
```bash
python iclicker_cli.py scrape ACTIVITY_ID [options]
```

**Options:**
- `-o, --output` - Custom output file path
- `--username` - iClicker username (overrides env var)
- `--password` - iClicker password (overrides env var)
- `--show-browser` - Show browser window instead of headless mode
- `--timeout` - Timeout in seconds (default: 30)
- `--create-latest-link` - Create symlink to latest file
- `-v, --verbose` - Show detailed output

### `list` - View Recent Files
```bash
python iclicker_cli.py list [--limit N]
```

Shows recent question files with timestamps and question counts.

### `setup-env` - Configure Credentials
```bash
python iclicker_cli.py setup-env [--username USER] [--force]
```

Creates a `.env` file with your credentials securely stored.

## How to Find Activity ID

The activity ID is in the iClicker URL. For example:
```
https://student.iclicker.com/#/activity/f7dcba1f-1231-4d91-906c-6e3acd9b660b/questions
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      This is your activity ID
```

## Output Format

Questions are saved as JSON with this structure:

```json
[
  {
    "id": "q1",
    "question_text": "What is 2+2?",
    "options": ["3", "4", "5", "6"],
    "correct_answer": "4",
    "question_type": "multiple_choice",
    "extraction_method": "web_scraping"
  }
]
```

## Regular Usage

For regular usage, set up a script or cron job:

```bash
#!/bin/bash
# daily_questions.sh

cd /path/to/iclicker-scraper
source venv/bin/activate

# Your activity ID
ACTIVITY_ID="f7dcba1f-1231-4d91-906c-6e3acd9b660b"

python iclicker_cli.py scrape "$ACTIVITY_ID" --create-latest-link --verbose
```

## Development

### Running Tests
```bash
source venv/bin/activate
python -m pytest test_iclicker_client.py -v
```

### Project Structure
```
iclicker-scraper/
├── iclicker_scraper.py      # Main scraper class
├── iclicker_cli.py          # CLI interface
├── test_iclicker_client.py  # Test suite
├── requirements.txt         # Dependencies
├── README.md               # This file
└── questions/              # Output directory (created automatically)
```

## Troubleshooting

### Chrome Driver Issues
If you get Chrome driver errors:
```bash
# Update Chrome driver
pip install --upgrade webdriver-manager
```

### Authentication Issues
- Verify your credentials are correct
- Check if iClicker requires 2FA (not currently supported)
- Try running with `--show-browser` to see what's happening

### No Questions Found
- Ensure the activity ID is correct
- Check if you have access to the activity
- Try running with `--show-browser` and `--verbose` for debugging

## Security Notes

- Credentials are stored securely in environment variables or `.env` files
- The `.env` file is created with restricted permissions (600)
- Never commit credentials to version control
- Use different credentials for different environments

## License

This tool is for educational purposes. Please respect iClicker's terms of service and only use this tool for activities you have legitimate access to.
