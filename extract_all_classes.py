#!/usr/bin/env python3
"""
Extract All Classes - Scrape questions from all three specific class polls
"""

import time
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def extract_all_classes():
    """Extract questions from all three specified class polls"""
    print("🎯 Extract All Classes Scraper")
    print("Extracting questions from Class 1, Class 2, and Class 3 polls")
    
    # Get credentials
    with open("questions/.env", "r") as f:
        env_content = f.read()
    
    username = None
    password = None
    for line in env_content.split('\n'):
        if line.startswith('ICLICKER_USERNAME='):
            username = line.split('=', 1)[1]
        elif line.startswith('ICLICKER_PASSWORD='):
            password = line.split('=', 1)[1]
    
    # Setup headless driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1400,1000")
    
    # Define all three class polls
    class_polls = [
        {
            'class_name': 'Class 1',
            'activity_id': '028a9cfc-c979-46b7-845c-5f81c85d862e',
            'url': 'https://student.iclicker.com/#/activity/028a9cfc-c979-46b7-845c-5f81c85d862e/questions'
        },
        {
            'class_name': 'Class 2', 
            'activity_id': 'f7dcba1f-1231-4d91-906c-6e3acd9b660b',
            'url': 'https://student.iclicker.com/#/activity/f7dcba1f-1231-4d91-906c-6e3acd9b660b/questions'
        },
        {
            'class_name': 'Class 3',
            'activity_id': 'c91973a1-a821-43a4-994d-03fc4a21f2fc', 
            'url': 'https://student.iclicker.com/#/activity/c91973a1-a821-43a4-994d-03fc4a21f2fc/questions'
        }
    ]
    
    all_class_data = []
    
    try:
        print("🚀 Setting up browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(5)
        
        # Login
        print("🔐 Logging in...")
        driver.get("https://student.iclicker.com")
        time.sleep(3)
        
        # Handle overlay
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
        
        # Extract from each class poll
        for i, class_poll in enumerate(class_polls, 1):
            print(f"\n📝 Processing {class_poll['class_name']}: {class_poll['activity_id']}")
            
            try:
                # Navigate to the class questions page
                print(f"   Going to: {class_poll['url']}")
                driver.get(class_poll['url'])
                time.sleep(8)
                
                # Get page info
                title = driver.title
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                print(f"   Title: {title}")
                print(f"   Page content length: {len(page_text)} characters")
                
                # Extract questions using our proven method
                questions_data = extract_questions_from_page(driver, class_poll['activity_id'], class_poll['class_name'])
                
                if questions_data:
                    # Create class-specific directory for images
                    class_dir = f"images/class_{i}_{class_poll['class_name'].lower().replace(' ', '_')}"
                    downloaded_count = download_images_for_class(questions_data, class_dir, class_poll['class_name'])
                    
                    class_data = {
                        'class_name': class_poll['class_name'],
                        'activity_id': class_poll['activity_id'],
                        'activity_url': class_poll['url'],
                        'title': title,
                        'questions_found': len(questions_data),
                        'images_downloaded': downloaded_count,
                        'questions': questions_data,
                        'image_directory': class_dir,
                        'extraction_method': 'Targeted class extraction'
                    }
                    
                    all_class_data.append(class_data)
                    
                    print(f"   ✅ Extracted {len(questions_data)} questions")
                    print(f"   ✅ Downloaded {downloaded_count} images to {class_dir}/")
                    
                else:
                    print(f"   ⚠️ No questions found in {class_poll['class_name']}")
                    
            except Exception as e:
                print(f"   ❌ Error processing {class_poll['class_name']}: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'driver' in locals():
            driver.quit()
    
    # Save comprehensive results
    print("\n💾 Saving comprehensive results...")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"questions/all_classes_extraction_{timestamp}.json"
    
    total_questions = sum(len(class_data['questions']) for class_data in all_class_data)
    total_images = sum(class_data['images_downloaded'] for class_data in all_class_data)
    
    with open(output_file, 'w') as f:
        json.dump({
            'extraction_timestamp': timestamp,
            'total_classes_processed': len(all_class_data),
            'total_questions_extracted': total_questions,
            'total_images_downloaded': total_images,
            'extraction_method': 'Targeted all classes extraction',
            'classes': all_class_data
        }, f, indent=2)
    
    print(f"✅ Results saved to {output_file}")
    
    # Summary
    print(f"\n📊 ALL CLASSES EXTRACTION SUMMARY:")
    print(f"   Total classes processed: {len(all_class_data)}")
    print(f"   Total questions extracted: {total_questions}")
    print(f"   Total images downloaded: {total_images}")
    
    if all_class_data:
        print(f"\n📋 CLASSES EXTRACTED:")
        for class_data in all_class_data:
            print(f"   • {class_data['class_name']}: {class_data['questions_found']} questions, {class_data['images_downloaded']} images")
            print(f"     Directory: {class_data['image_directory']}")
    
    return all_class_data


def extract_questions_from_page(driver, activity_id, class_name):
    """Extract questions using our proven method"""
    questions_data = []
    
    try:
        # Use our successful image extraction method
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
                'class_name': class_name,
                'extraction_method': 'Proven image extraction'
            })
        
        return questions_data
        
    except Exception as e:
        print(f"      ❌ Error extracting questions: {e}")
        return []


def download_images_for_class(questions_data, class_dir, class_name):
    """Download images for a specific class"""
    if not questions_data:
        return 0
    
    print(f"   📥 Downloading images for {class_name}...")
    
    # Create directory for this class
    os.makedirs(class_dir, exist_ok=True)
    
    downloaded_count = 0
    
    for question in questions_data:
        if question.get('question_image_url'):
            try:
                img_url = question['question_image_url']
                response = requests.get(img_url, timeout=15)
                
                if response.status_code == 200:
                    filename = f"{class_dir}/question_{question['question_number']:02d}.png"
                    
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    # Add local path to question data
                    question['local_image_path'] = filename
                    question['image_size_bytes'] = len(response.content)
                    downloaded_count += 1
                    
            except Exception as e:
                print(f"      ❌ Failed to download question {question['question_number']}: {e}")
    
    return downloaded_count


if __name__ == "__main__":
    extract_all_classes()
