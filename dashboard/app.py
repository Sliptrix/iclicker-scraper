#!/usr/bin/env python3
"""
iClicker Scraper Dashboard
A web interface for extracting and browsing iClicker questions
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import json
import glob
import re
import threading
import time
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iclicker-scraper-dashboard-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
BASE_DIR = Path(__file__).parent.parent
QUESTIONS_DIR = BASE_DIR / "questions"
IMAGES_DIR = BASE_DIR / "images"

class ExtractionManager:
    def __init__(self):
        self.current_extraction = None
        self.status = "idle"
        
    def start_extraction(self, course_url):
        """Start course extraction in background thread"""
        if self.status == "running":
            return {"error": "Extraction already in progress"}
        
        self.status = "running"
        self.current_extraction = {
            'course_url': course_url,
            'start_time': datetime.now(),
            'progress': 0,
            'status': 'Starting...'
        }
        
        # Start extraction in background thread
        thread = threading.Thread(target=self._run_extraction, args=(course_url,))
        thread.daemon = True
        thread.start()
        
        return {"success": True, "message": "Extraction started"}
    
    def _run_extraction(self, course_url):
        """Run the actual extraction process"""
        try:
            # Import our extraction module
            import sys
            sys.path.append(str(BASE_DIR))
            from extract_course_activities import extract_course_activities
            
            # Update progress
            socketio.emit('extraction_progress', {
                'progress': 10,
                'status': 'Logging in and discovering activities...'
            })
            
            # Run extraction
            result = extract_course_activities(
                course_url=course_url,
                output_dir=str(QUESTIONS_DIR),
                headless=True
            )
            
            if result and 'activities' in result:
                # Update progress during extraction
                total_activities = len(result['activities'])
                for i, activity in enumerate(result['activities']):
                    progress = 20 + (i / total_activities) * 60
                    socketio.emit('extraction_progress', {
                        'progress': progress,
                        'status': f'Processing {activity.get("activity_name", "activity")}...'
                    })
                    time.sleep(0.1)  # Small delay for UI
                
                # Auto-rename files
                socketio.emit('extraction_progress', {
                    'progress': 90,
                    'status': 'Organizing files...'
                })
                
                self._auto_rename_files(result)
                
                # Complete
                socketio.emit('extraction_complete', {
                    'success': True,
                    'message': f'Successfully extracted {result.get("total_questions_extracted", 0)} questions from {total_activities} activities',
                    'result': result
                })
            else:
                raise Exception("No activities found or extraction failed")
                
        except Exception as e:
            socketio.emit('extraction_error', {
                'error': str(e)
            })
        finally:
            self.status = "idle"
            self.current_extraction = None
    
    def _auto_rename_files(self, result):
        """Automatically rename extracted files"""
        try:
            import sys
            sys.path.append(str(BASE_DIR))
            from rename_course_files import rename_files
            
            # Find the JSON file that was just created
            course_id = result.get('course_id', '')
            timestamp = result.get('extraction_timestamp', '')
            
            json_pattern = f"course_{course_id}_extraction_{timestamp}.json"
            json_files = glob.glob(str(QUESTIONS_DIR / json_pattern))
            
            if json_files:
                rename_files(json_files[0], dry_run=False)
        except Exception as e:
            print(f"Auto-rename failed: {e}")

extraction_manager = ExtractionManager()

def load_courses():
    """Load extracted course data"""
    courses = []
    
    # Find all complete extraction JSON files
    json_files = glob.glob(str(QUESTIONS_DIR / "*Complete_Extraction*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract course info
            course_name = Path(json_file).stem.replace('_Complete_Extraction', '').split('_')
            course_name = ' '.join([word.capitalize() for word in course_name[:-1]])  # Remove timestamp
            
            course_info = {
                'name': course_name,
                'file': json_file,
                'id': data.get('course_id', ''),
                'activities': len(data.get('activities', [])),
                'questions': data.get('total_questions_extracted', 0),
                'images': data.get('total_images_downloaded', 0),
                'timestamp': data.get('extraction_timestamp', ''),
                'data': data
            }
            courses.append(course_info)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    # Sort by timestamp (most recent first)
    courses.sort(key=lambda x: x['timestamp'], reverse=True)
    return courses

@app.route('/')
def dashboard():
    """Main dashboard page"""
    courses = load_courses()
    return render_template('dashboard.html', courses=courses)

@app.route('/extract', methods=['POST'])
def start_extraction():
    """Start course extraction"""
    course_url = request.json.get('course_url', '').strip()
    
    # Validate URL
    if not course_url:
        return jsonify({'error': 'Course URL is required'})
    
    if 'student.iclicker.com/#/course/' not in course_url:
        return jsonify({'error': 'Invalid iClicker course URL'})
    
    result = extraction_manager.start_extraction(course_url)
    return jsonify(result)

@app.route('/course/<course_id>')
def course_detail(course_id):
    """Course detail page"""
    courses = load_courses()
    course = next((c for c in courses if c['id'] == course_id), None)
    
    if not course:
        return "Course not found", 404
    
    return render_template('course_detail.html', course=course)

@app.route('/api/courses')
def api_courses():
    """API endpoint for course data"""
    return jsonify(load_courses())

@app.route('/api/extraction/status')
def extraction_status():
    """Get current extraction status"""
    return jsonify({
        'status': extraction_manager.status,
        'current': extraction_manager.current_extraction
    })

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve image files"""
    try:
        image_path = IMAGES_DIR / filename
        if image_path.exists():
            return send_file(str(image_path))
        else:
            return "Image not found", 404
    except Exception as e:
        return f"Error serving image: {e}", 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to iClicker Scraper Dashboard'})

@socketio.on('get_status')
def handle_get_status():
    """Send current extraction status to client"""
    emit('status_update', {
        'status': extraction_manager.status,
        'current': extraction_manager.current_extraction
    })

if __name__ == '__main__':
    print("🚀 Starting iClicker Scraper Dashboard...")
    print(f"📁 Base directory: {BASE_DIR}")
    print(f"📄 Questions directory: {QUESTIONS_DIR}")
    print(f"🖼️  Images directory: {IMAGES_DIR}")
    print("🌐 Dashboard will be available at: http://localhost:5001")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
