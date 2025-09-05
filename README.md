# iClicker Course Extractor

A comprehensive Python tool to automatically extract questions and images from entire iClicker courses using web automation, featuring a professional web dashboard for easy management.

## Features

- 🎯 **Complete Course Extraction**: Extract all activities and questions from an entire iClicker course
- 🌐 **Web Dashboard**: Professional Flask-based web interface for easy course management
- 📋 **Question & Image Extraction**: Download questions with associated images automatically
- 🔄 **Real-time Progress**: Live progress tracking during extractions via WebSocket
- 📁 **Smart Organization**: Automatic file organization with consistent naming schemes
- 💾 **JSON Export**: Structured data storage with complete extraction metadata
- 🔐 **Secure Credentials**: Environment variable-based credential management
- 📱 **Responsive Interface**: Mobile-friendly Bootstrap-based dashboard

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/iclicker-course-extractor.git
cd iclicker-course-extractor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Create a `.env` file in the `questions/` directory:
```bash
ICLICKER_USERNAME=your_username@email.com
ICLICKER_PASSWORD=your_password
```

### 3. Start the Dashboard

```bash
# Navigate to dashboard directory
cd dashboard

# Start the web dashboard
python app.py
```

Open your browser and go to `http://localhost:5001` to access the dashboard.

### 4. Extract Courses

**Option A: Use the Web Dashboard (Recommended)**
1. Open the dashboard at `http://localhost:5001`
2. Paste your course URL in the extraction form
3. Monitor real-time progress
4. Browse extracted courses and questions

**Option B: Command Line**
```bash
# Extract entire course
python extract_course_activities.py https://student.iclicker.com/#/course/COURSE_ID/class-history

# Organize extracted files
python rename_course_files.py
```

## Dashboard Features

### 🏠 **Course Management**
- View all extracted courses in a clean card-based interface
- See extraction metadata (dates, question counts, activity counts)
- Quick access to course details and questions

### ⚡ **Real-time Extraction**
- Paste any iClicker course URL to start extraction
- Live progress updates via WebSocket
- Automatic course addition to dashboard upon completion

### 📊 **Course Details**
- Browse all activities/classes within a course
- View question thumbnails in an organized grid
- Full-size image modal viewer
- Download and export capabilities

## How to Find Course URL

The course URL is in your iClicker dashboard. Look for:
```
https://student.iclicker.com/#/course/646a06a0-645e-4632-af88-6483178c08c5/class-history
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      This is your course ID
```

The full URL including `/class-history` is what you need for extraction.

## Output Format

Course extractions are saved with this structure:

```json
{
  "course_id": "646a06a0-645e-4632-af88-6483178c08c5",
  "course_url": "https://student.iclicker.com/#/course/.../class-history",
  "extraction_timestamp": "20250905_151628",
  "total_activities_processed": 9,
  "total_questions_extracted": 122,
  "total_images_downloaded": 122,
  "extraction_method": "Course-level activity discovery",
  "activities": [
    {
      "activity_id": "82d2883e-dd1f-4779-8199-d3ef1693c449",
      "activity_name": "Class 5 - Poll",
      "questions_found": 34,
      "images_downloaded": 34,
      "questions": [
        {
          "question_number": 1,
          "question_text": "Question 1",
          "local_image_path": "images/Course_Name/Class_05_Poll_82d2883e/question_01.png",
          "image_size_bytes": 140114
        }
      ]
    }
  ]
}
```

## Project Structure

```
iclicker-course-extractor/
├── dashboard/                    # Web dashboard
│   ├── app.py                   # Flask application
│   └── templates/               # HTML templates
├── extract_course_activities.py # Main extraction script
├── rename_course_files.py       # File organization utility
├── requirements.txt             # Python dependencies
├── questions/                   # Extracted course data (JSON)
├── images/                      # Downloaded question images
└── README.md                   # This file
```

## Troubleshooting

### Dashboard Won't Start
- Ensure you're in the `dashboard/` directory: `cd dashboard`
- Check that Flask and Flask-SocketIO are installed: `pip install -r ../requirements.txt`
- Try a different port if 5001 is in use: modify `app.py` to use a different port

### Chrome Driver Issues
```bash
# Update Chrome driver
pip install --upgrade webdriver-manager
```

### Authentication Issues
- Verify credentials in `questions/.env` file
- Ensure you have access to the course
- Check if iClicker requires 2FA (not currently supported)
- Try running extraction with `--show-browser` flag for debugging

### Extraction Fails
- Verify the course URL format includes `/class-history`
- Check that you're enrolled in the course
- Ensure stable internet connection
- Try extracting during off-peak hours

## Security Notes

- 🔒 Credentials stored securely in `.env` files with restricted permissions
- ⚠️ Never commit credential files to version control
- 🌍 Only use this tool for courses you have legitimate access to
- 📊 Consider the impact on iClicker's servers - avoid excessive concurrent extractions

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with detailed description

## License

This tool is for educational purposes. Please respect iClicker's terms of service and only use this tool for courses you have legitimate access to.
