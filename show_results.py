#!/usr/bin/env python3
"""
Show Results - Display the final extraction results
"""

import json
import os


def show_results():
    """Display comprehensive extraction results"""
    print("🎉 iClicker Scraper - Final Results")
    print("="*50)
    
    # Find the latest comprehensive extraction file
    extraction_files = [f for f in os.listdir('questions') if f.startswith('comprehensive_extraction_') and f.endswith('.json')]
    
    if not extraction_files:
        print("❌ No extraction results found!")
        return
    
    latest_file = sorted(extraction_files)[-1]
    file_path = f"questions/{latest_file}"
    
    print(f"📂 Reading results from: {latest_file}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    questions = data['questions']
    
    print(f"\n📊 OVERALL SUMMARY:")
    print(f"   Extraction timestamp: {data['extraction_timestamp']}")
    print(f"   Total questions found: {data['total_questions_found']}")
    print(f"   Total images downloaded: {data['total_images_downloaded']}")
    print(f"   Success rate: {data['total_images_downloaded']/data['total_questions_found']*100:.1f}%")
    
    print(f"\n📋 QUESTION DETAILS:")
    
    for q in questions:
        print(f"\n   📝 Question {q['question_number']:2d}:")
        print(f"      Image: {'✅' if q.get('local_image_path') else '❌'} {q.get('image_size_bytes', 0):,} bytes")
        print(f"      File: {q.get('local_image_path', 'Not downloaded')}")
        print(f"      Dimensions: {q.get('image_dimensions', 'Unknown')}")
        print(f"      Status: {q['status']}")
    
    # Check image files exist
    print(f"\n🖼️ IMAGE FILE VERIFICATION:")
    
    images_dir = "images"
    if os.path.exists(images_dir):
        image_files = [f for f in os.listdir(images_dir) if f.startswith('question_') and f.endswith('.png')]
        print(f"   Found {len(image_files)} image files in {images_dir}/")
        
        # Show file sizes to confirm uniqueness
        print(f"   File size distribution:")
        sizes = []
        for img_file in sorted(image_files):
            full_path = os.path.join(images_dir, img_file)
            size = os.path.getsize(full_path)
            sizes.append(size)
            question_num = img_file.replace('question_', '').replace('.png', '')
            print(f"      {img_file}: {size:,} bytes")
        
        unique_sizes = len(set(sizes))
        print(f"\n   Unique file sizes: {unique_sizes} out of {len(sizes)} files")
        if unique_sizes == len(sizes):
            print("   ✅ All images are unique!")
        else:
            print("   ⚠️ Some images may be duplicates")
    else:
        print(f"   ❌ Images directory not found")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. All {data['total_images_downloaded']} question images have been successfully downloaded")
    print(f"   2. Images are stored in the 'images/' directory")
    print(f"   3. Each image file is named 'question_XX.png' (XX = question number)")
    print(f"   4. You can now view the images to see the actual questions")
    print(f"   5. If you need answer choices, you may need to extract them manually from the images")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   - Open a few sample images to verify quality and content")
    print(f"   - Use OCR tools if you need to extract text from the images")
    print(f"   - The JSON file contains all metadata including original URLs")
    
    return data


if __name__ == "__main__":
    show_results()
