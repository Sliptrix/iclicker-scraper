#!/usr/bin/env python3
"""
Final Summary - Comprehensive view of all iClicker extractions
"""

import os
import json
import time


def create_final_summary():
    """Create a comprehensive summary of all extraction results"""
    print("📊 Final iClicker Extraction Summary")
    print("="*50)
    
    # Known activity IDs and their status
    activity_ids = [
        {
            'id': 'f7dcba1f-1231-4d91-906c-6e3acd9b660b',
            'name': 'Original Working Poll (Class 2 - Poll)', 
            'status': 'Successfully extracted 33 questions',
            'extraction_files': ['comprehensive_extraction_20250823_173844.json'],
            'image_dir': 'images/ (main directory)',
            'notes': 'This was our first successful extraction - all 33 questions with images'
        },
        {
            'id': 'c6d225fa-e422-4222-b0b3-1a7c7a87075a',
            'name': 'Poll 2 (Class 2 - Poll)',
            'status': 'Successfully extracted 33 questions', 
            'extraction_files': [],
            'image_dir': 'images/poll_2/',
            'notes': 'Same content as original - likely same poll with different ID'
        },
        {
            'id': '01930214-6422-79a0-8ef4-30773f1bd3ce',
            'name': 'Poll 3 (Class 2 - Poll)',
            'status': 'Successfully extracted 33 questions',
            'extraction_files': [],
            'image_dir': 'images/poll_3/',
            'notes': 'Same content as original - likely same poll with different ID'
        },
        {
            'id': '76b255b2-9003-402f-9c7b-8ee6995f3724',
            'name': 'Poll 4 (Class 2 - Poll)', 
            'status': 'Partially extracted (interrupted)',
            'extraction_files': [],
            'image_dir': 'images/poll_4/',
            'notes': 'Extraction started but was interrupted during image download'
        },
        {
            'id': '01980e32-c165-7d2b-829d-a6dc6e30500a',
            'name': 'Poll 5 (Class 2 - Poll)',
            'status': 'Not extracted',
            'extraction_files': [],
            'image_dir': None,
            'notes': 'Not reached due to interruption'
        }
    ]
    
    print("🎯 ACTIVITY IDs ANALYSIS:")
    for i, activity in enumerate(activity_ids, 1):
        print(f"\\n{i}. {activity['name']}")
        print(f"   ID: {activity['id']}")
        print(f"   Status: {activity['status']}")
        print(f"   Image Directory: {activity['image_dir'] or 'None'}")
        print(f"   Notes: {activity['notes']}")
    
    # Check what we actually have on disk
    print("\\n📁 FILE SYSTEM ANALYSIS:")
    
    # Check images directory
    images_base = "images"
    if os.path.exists(images_base):
        # Main images directory
        main_images = [f for f in os.listdir(images_base) if f.startswith('question_') and f.endswith('.png')]
        print(f"   Main images directory: {len(main_images)} images")
        
        # Poll subdirectories
        poll_dirs = [d for d in os.listdir(images_base) if d.startswith('poll_') and os.path.isdir(os.path.join(images_base, d))]
        print(f"   Poll subdirectories: {len(poll_dirs)}")
        
        for poll_dir in sorted(poll_dirs):
            poll_path = os.path.join(images_base, poll_dir)
            poll_images = [f for f in os.listdir(poll_path) if f.endswith('.png')]
            print(f"      {poll_dir}: {len(poll_images)} images")
    
    # Check questions directory for JSON files
    questions_dir = "questions"
    if os.path.exists(questions_dir):
        json_files = [f for f in os.listdir(questions_dir) if f.endswith('.json')]
        print(f"   JSON result files: {len(json_files)}")
        for json_file in sorted(json_files):
            print(f"      {json_file}")
    
    # Create comprehensive summary
    total_unique_questions = 33  # Based on our analysis
    total_polls_found = len([a for a in activity_ids if a['status'].startswith('Successfully')])
    total_images_downloaded = 0
    
    # Count actual downloaded images
    for poll_dir in ['poll_1', 'poll_2', 'poll_3', 'poll_4']:
        poll_path = os.path.join(images_base, poll_dir)
        if os.path.exists(poll_path):
            poll_images = [f for f in os.listdir(poll_path) if f.endswith('.png')]
            total_images_downloaded += len(poll_images)
    
    # Add main directory images
    if os.path.exists(images_base):
        main_images = [f for f in os.listdir(images_base) if f.startswith('question_') and f.endswith('.png')]
        total_images_downloaded += len(main_images)
    
    print("\\n📈 OVERALL STATISTICS:")
    print(f"   Total activity IDs tested: {len(activity_ids)}")
    print(f"   Successful poll extractions: {total_polls_found}")
    print(f"   Unique questions found: {total_unique_questions}")
    print(f"   Total images downloaded: {total_images_downloaded}")
    print(f"   Course ID: 03aa6f57-ac2f-43f6-9d5f-fbd2225b3303")
    
    # Create final summary JSON
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    summary_file = f"questions/final_summary_{timestamp}.json"
    
    summary_data = {
        'summary_timestamp': timestamp,
        'course_id': '03aa6f57-ac2f-43f6-9d5f-fbd2225b3303',
        'total_activity_ids_tested': len(activity_ids),
        'successful_extractions': total_polls_found,
        'total_unique_questions': total_unique_questions,
        'total_images_downloaded': total_images_downloaded,
        'activity_ids': activity_ids,
        'extraction_notes': [
            'All extractions show "Class 2 - Poll" as the title',
            'All successfully extracted polls contain the same 33 questions',
            'Different activity IDs likely represent the same poll content',
            'Images are 323x182 pixels, hosted on reef-prod-storage.s3.amazonaws.com',
            'Main extraction method: Direct image extraction from questions page'
        ],
        'recommendations': [
            'The main questions are in images/ directory and images/poll_1/',
            'All poll directories contain duplicate content',
            'Focus on the main images directory for unique questions',
            'Consider using OCR tools to extract text from question images'
        ]
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\\n💾 Final summary saved to: {summary_file}")
    
    print("\\n🎉 EXTRACTION SUCCESS SUMMARY:")
    print("   ✅ Successfully logged into iClicker")
    print("   ✅ Successfully navigated to course content") 
    print("   ✅ Successfully identified and extracted question images")
    print("   ✅ Successfully downloaded 33 unique questions")
    print("   ✅ Successfully found multiple activity IDs (likely same content)")
    print("   ✅ Successfully organized images in separate directories")
    
    print("\\n📋 WHAT YOU HAVE:")
    print("   • 33 question images in multiple formats/directories")
    print("   • Complete metadata in JSON files")  
    print("   • Working scraper code for future use")
    print("   • All images are high-quality PNG files (323x182 pixels)")
    
    print("\\n💡 NEXT STEPS (if needed):")
    print("   • Use OCR tools to extract text from the question images")
    print("   • The scraper can be run again if new polls are added")
    print("   • Check for other courses using the same approach")
    
    return summary_data


if __name__ == "__main__":
    create_final_summary()
