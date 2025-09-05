#!/usr/bin/env python3
"""
Extract Course Activities - Scrape questions from all activities in a course

This script discovers all activities in an iClicker course from the class-history page
and extracts questions from each activity using proven extraction methods.
"""

import time
import os
import json
import re
import requests
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class CourseExtractionResult:
    """Data structure for course extraction results."""
    course_id: str
    course_url: str
    extraction_timestamp: str
    total_activities_processed: int
    total_questions_extracted: int
    total_images_downloaded: int
    activities: List[Dict]
    extraction_method: str = "Course-level activity discovery"


def extract_course_id_from_url(course_url: str) -> str:
    """
    Extract course ID from course URL.
    
    Args:
        course_url: URL like https://student.iclicker.com/#/course/COURSE_ID/class-history
        
    Returns:
        Course ID string
        
    Raises:
        ValueError: If URL format is invalid
    """
    pattern = r'https://student\.iclicker\.com/#/course/([^/]+)/class-history'
    match = re.search(pattern, course_url)
    
    if not match:
        raise ValueError(f"Invalid course URL format: {course_url}")
    
    return match.group(1)


def extract_activity_ids_from_page(driver) -> List[str]:
    """
    Extract all activity IDs from the course class-history page.
    
    Since iClicker uses JavaScript session links, we need to click on each 
    poll link and extract the activity ID from the resulting URL.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of unique activity IDs found on the page
    """
    activity_data = []
    
    try:
        # Instead of caching elements, we'll find them fresh each iteration
        processed_activities = set()
        max_attempts = 20  # Prevent infinite loop
        
        for attempt in range(max_attempts):
            # Find session links fresh each time
            session_links = driver.find_elements(By.CSS_SELECTOR, "a.session-link")
            
            if attempt == 0:
                print(f"   Found {len(session_links)} session links")
            
            # Find an unprocessed poll link
            found_unprocessed = False
            
            for link in session_links:
                try:
                    link_text = link.text.strip()
                    if 'Poll' in link_text and 'Class' in link_text:
                        # Create a unique identifier for this activity
                        activity_identifier = link_text.split('\n')[0].strip()
                        
                        if activity_identifier in processed_activities:
                            continue  # Skip already processed
                        
                        found_unprocessed = True
                        print(f"   Processing: {link_text[:30]}...")
                        
                        # Click the session link
                        driver.execute_script("arguments[0].click();", link)
                        time.sleep(3)  # Wait for navigation
                        
                        # Check if we're now on an activity page
                        current_url = driver.current_url
                        print(f"      Current URL: {current_url}")
                        
                        # Extract activity ID from URL
                        activity_pattern = r'/activity/([^/]+)(?:/|$)'
                        match = re.search(activity_pattern, current_url)
                        
                        if match:
                            activity_id = match.group(1)
                            activity_info = {
                                'activity_id': activity_id,
                                'activity_name': activity_identifier,
                                'activity_url': current_url
                            }
                            activity_data.append(activity_info)
                            processed_activities.add(activity_identifier)
                            print(f"      ✅ Found activity: {activity_id}")
                        else:
                            print(f"      ⚠️ No activity ID found in URL")
                        
                        # Go back to course page for next iteration
                        driver.back()
                        time.sleep(3)  # Wait for page to load
                        break  # Break inner loop to start fresh
                        
                except Exception as e:
                    print(f"      ❌ Error processing session link: {e}")
                    # Try to get back to course page
                    try:
                        driver.back()
                        time.sleep(2)
                    except:
                        pass
                    continue
            
            if not found_unprocessed:
                print(f"   ✅ Processed all available session links")
                break
        
        # Return just the activity IDs for compatibility with existing code
        activity_ids = [item['activity_id'] for item in activity_data]
        
        # Store the full activity data for later use
        driver.activity_data = activity_data
        
        return activity_ids
        
    except Exception as e:
        print(f"   ⚠️ Error extracting activity IDs: {e}")
        return []


def extract_questions_from_activity(driver, activity_id: str, activity_name: str = None) -> List[Dict]:
    """
    Extract questions from a single activity using proven extraction methods.
    
    Args:
        driver: Selenium WebDriver instance
        activity_id: The activity ID to extract from
        activity_name: Optional display name for the activity
        
    Returns:
        List of question dictionaries
    """
    questions_data = []
    
    try:
        # Navigate to activity questions page
        activity_url = f"https://student.iclicker.com/#/activity/{activity_id}/questions"
        print(f"   📝 Extracting from: {activity_url}")
        driver.get(activity_url)
        time.sleep(8)  # Wait for page to load
        
        # Use proven image extraction method from existing code
        images = driver.find_elements(By.TAG_NAME, "img")
        question_images = []
        seen_urls = set()
        
        for img in images:
            src = img.get_attribute('src') or ''
            alt = img.get_attribute('alt') or ''
            width = img.get_attribute('width') or '0'
            height = img.get_attribute('height') or '0'
            
            is_question_image = False
            question_number = None
            
            # Check alt text for "Question N"
            if alt and 'Question' in alt:
                alt_words = alt.split()
                for i, word in enumerate(alt_words):
                    if word == 'Question' and i + 1 < len(alt_words):
                        try:
                            question_number = int(alt_words[i + 1])
                            is_question_image = True
                            break
                        except ValueError:
                            pass
            
            # Check for reef-prod-storage images with good dimensions
            if not is_question_image and 'reef-prod-storage' in src and 'attachments' in src:
                try:
                    w = int(width) if width.isdigit() else 0
                    h = int(height) if height.isdigit() else 0
                    if w > 200 and h > 100:
                        is_question_image = True
                        if question_number is None:
                            question_number = len([q for q in question_images if q.get('question_number')]) + 1
                except:
                    pass
            
            if is_question_image and src and src not in seen_urls:
                question_images.append({
                    'question_number': question_number or len(question_images) + 1,
                    'src': src,
                    'alt': alt,
                    'width': width,
                    'height': height
                })
                seen_urls.add(src)
        
        # Sort by question number
        question_images.sort(key=lambda x: x['question_number'])
        
        # Convert to standard format
        for img_data in question_images:
            questions_data.append({
                'question_number': img_data['question_number'],
                'question_text': f"Question {img_data['question_number']}",
                'question_image_url': img_data['src'],
                'image_alt': img_data['alt'],
                'image_dimensions': f"{img_data['width']}x{img_data['height']}",
                'activity_id': activity_id,
                'activity_name': activity_name or f"Activity {activity_id[:8]}...",
                'extraction_method': 'Proven course-level extraction'
            })
        
    except Exception as e:
        print(f"      ❌ Error extracting from activity {activity_id}: {e}")
    
    return questions_data


def download_images_for_activity(questions_data: List[Dict], activity_dir: str, activity_name: str) -> int:
    """
    Download images for all questions in an activity.
    
    Args:
        questions_data: List of question dictionaries
        activity_dir: Directory to save images
        activity_name: Display name for activity
        
    Returns:
        Number of images successfully downloaded
    """
    if not questions_data:
        return 0
    
    print(f"   📥 Downloading images for {activity_name}...")
    
    # Create directory for this activity
    os.makedirs(activity_dir, exist_ok=True)
    
    downloaded_count = 0
    
    for question in questions_data:
        if question.get('question_image_url'):
            try:
                img_url = question['question_image_url']
                response = requests.get(img_url, timeout=15)
                
                if response.status_code == 200:
                    filename = f"{activity_dir}/question_{question['question_number']:02d}.png"
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    # Add local path to question data
                    question['local_image_path'] = filename
                    question['image_size_bytes'] = len(response.content)
                    downloaded_count += 1
                    
            except Exception as e:
                print(f"      ❌ Failed to download question {question['question_number']}: {e}")
    
    return downloaded_count


def load_credentials() -> Tuple[str, str]:
    """
    Load iClicker credentials from environment variables.
    
    Returns:
        Tuple of (username, password)
        
    Raises:
        ValueError: If credentials are not found
    """
    username = os.getenv('ICLICKER_USERNAME')
    password = os.getenv('ICLICKER_PASSWORD')
    
    if not username or not password:
        # Try loading from questions/.env file
        try:
            username, password = load_credentials_from_file('questions/.env')
        except:
            raise ValueError(
                "Credentials not found. Please set ICLICKER_USERNAME and ICLICKER_PASSWORD "
                "environment variables or create questions/.env file"
            )
    
    return username, password


def load_credentials_from_file(env_file_path: str) -> Tuple[str, str]:
    """
    Load credentials from .env file.
    
    Args:
        env_file_path: Path to .env file
        
    Returns:
        Tuple of (username, password)
    """
    username = None
    password = None
    
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('ICLICKER_USERNAME='):
                username = line.split('=', 1)[1]
            elif line.startswith('ICLICKER_PASSWORD='):
                password = line.split('=', 1)[1]
    
    if not username or not password:
        raise ValueError(f"Missing credentials in {env_file_path}")
    
    return username, password


def create_output_filename(course_id: str, timestamp: str, output_dir: str) -> str:
    """
    Create output filename for course extraction results.
    
    Args:
        course_id: The course ID
        timestamp: Extraction timestamp
        output_dir: Output directory
        
    Returns:
        Full path to output file
    """
    filename = f"course_{course_id}_extraction_{timestamp}.json"
    return os.path.join(output_dir, filename)


def extract_course_activities(course_url: str, username: str = None, password: str = None, 
                            output_dir: str = "questions", headless: bool = True) -> Dict:
    """
    Extract all activities and questions from an iClicker course.
    
    Args:
        course_url: Course class-history URL
        username: iClicker username (optional if in environment)
        password: iClicker password (optional if in environment)
        output_dir: Directory to save results
        headless: Whether to run browser in headless mode
        
    Returns:
        Dictionary containing extraction results
    """
    print("🎯 Course Activity Extractor")
    print(f"📚 Course URL: {course_url}")
    
    # Extract course ID
    course_id = extract_course_id_from_url(course_url)
    print(f"📋 Course ID: {course_id}")
    
    # Get credentials
    if not username or not password:
        username, password = load_credentials()
    
    # Setup driver
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1400,1000")
    
    all_activities = []
    
    try:
        print("🚀 Setting up browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(5)
        
        # Login
        print("🔐 Logging in...")
        driver.get("https://student.iclicker.com")
        time.sleep(3)
        
        # Handle cookie overlay
        try:
            overlay_btn = driver.find_element(By.CSS_SELECTOR, "#onetrust-accept-btn-handler")
            overlay_btn.click()
            time.sleep(1)
        except:
            pass
        
        # Login
        username_field = driver.find_element(By.CSS_SELECTOR, "#input-email")
        password_field = driver.find_element(By.CSS_SELECTOR, "#input-password")
        
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        
        # Submit
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if 'sign in' in btn.text.lower() and btn.get_attribute('type') == 'submit':
                driver.execute_script("arguments[0].click();", btn)
                break
        
        time.sleep(5)
        print("✅ Login successful")
        
        # Navigate to course class-history page
        print(f"📖 Loading course class-history page...")
        driver.get(course_url)
        time.sleep(8)
        
        # Discover all activities
        print("🔍 Discovering activities...")
        
        # Debug: Print page title and some content
        page_title = driver.title
        print(f"   Page title: {page_title}")
        
        # Debug: Look for any links on the page
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"   Total links found on page: {len(all_links)}")
        
        activity_ids = extract_activity_ids_from_page(driver)
        
        print(f"📋 Found {len(activity_ids)} activities to process")
        if activity_ids:
            print(f"   Activity IDs: {activity_ids}")
        
        if not activity_ids:
            print("⚠️  No activities found in course")
            return {
                'course_id': course_id,
                'course_url': course_url,
                'error': 'No activities found',
                'activities': []
            }
        
        # Extract questions from each activity
        activity_info_list = getattr(driver, 'activity_data', [])
        
        for i, activity_id in enumerate(activity_ids, 1):
            # Find the matching activity info
            activity_info = next((info for info in activity_info_list if info['activity_id'] == activity_id), None)
            activity_name = activity_info['activity_name'] if activity_info else f"Activity {i}"
            
            print(f"\\n📝 Processing {activity_name}: {activity_id}")
            
            try:
                # Extract questions
                questions_data = extract_questions_from_activity(driver, activity_id, activity_name)
                
                if questions_data:
                    # Create activity-specific directory for images
                    activity_dir = f"images/course_{course_id}/activity_{i}_{activity_id[:8]}"
                    downloaded_count = download_images_for_activity(questions_data, activity_dir, activity_name)
                    
                    activity_data = {
                        'activity_id': activity_id,
                        'activity_name': activity_name,
                        'activity_url': f"https://student.iclicker.com/#/activity/{activity_id}/questions",
                        'questions_found': len(questions_data),
                        'images_downloaded': downloaded_count,
                        'questions': questions_data,
                        'image_directory': activity_dir,
                        'extraction_method': 'Course-level discovery and extraction'
                    }
                    
                    all_activities.append(activity_data)
                    
                    print(f"   ✅ Extracted {len(questions_data)} questions")
                    print(f"   ✅ Downloaded {downloaded_count} images to {activity_dir}/")
                    
                else:
                    print(f"   ⚠️ No questions found in {activity_name}")
                    
            except Exception as e:
                print(f"   ❌ Error processing {activity_name}: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'driver' in locals():
            driver.quit()
    
    # Save comprehensive results
    print("\\n💾 Saving comprehensive results...")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = create_output_filename(course_id, timestamp, output_dir)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    total_questions = sum(len(activity['questions']) for activity in all_activities)
    total_images = sum(activity['images_downloaded'] for activity in all_activities)
    
    result_data = {
        'course_id': course_id,
        'course_url': course_url,
        'extraction_timestamp': timestamp,
        'total_activities_processed': len(all_activities),
        'total_questions_extracted': total_questions,
        'total_images_downloaded': total_images,
        'extraction_method': 'Course-level activity discovery',
        'activities': all_activities
    }
    
    with open(output_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    print(f"✅ Results saved to {output_file}")
    
    # Summary
    print(f"\\n📊 COURSE EXTRACTION SUMMARY:")
    print(f"   Course ID: {course_id}")
    print(f"   Total activities processed: {len(all_activities)}")
    print(f"   Total questions extracted: {total_questions}")
    print(f"   Total images downloaded: {total_images}")
    
    if all_activities:
        print(f"\\n📋 ACTIVITIES EXTRACTED:")
        for activity in all_activities:
            print(f"   • {activity['activity_name']} ({activity['activity_id'][:8]}...): {activity['questions_found']} questions, {activity['images_downloaded']} images")
    
    return result_data


if __name__ == "__main__":
    import sys
    
    # Allow course URL as command line argument
    if len(sys.argv) > 1:
        course_url = sys.argv[1]
    else:
        # Default to the new course URL
        course_url = "https://student.iclicker.com/#/course/67d4f5a8-cbd4-41e0-870c-aa09b361da0c/class-history"
    
    print(f"🎯 Extracting from course: {course_url}")
    
    result = extract_course_activities(
        course_url=course_url,
        output_dir="questions",
        headless=False  # Show browser for debugging
    )
    
    print("\\n🎉 Course extraction complete!")
