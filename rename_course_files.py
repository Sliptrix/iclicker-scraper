#!/usr/bin/env python3
"""
Simple script to rename extracted course files with meaningful names.
Renames JSON file and image directories to include course name and class information.
"""

import json
import os
import shutil
import re
from pathlib import Path


def sanitize_name(name):
    """Convert name to filesystem-safe format"""
    # Replace problematic characters with underscores
    name = re.sub(r'[^\w\s-]', '', name)  # Remove special chars except word chars, spaces, hyphens
    name = re.sub(r'[-\s]+', '_', name)   # Replace spaces and hyphens with underscores
    return name.strip('_')


def extract_course_info(json_data):
    """Extract course information from JSON data"""
    course_id = json_data.get('course_id', '')
    
    # Identify course based on course ID or other metadata
    if course_id == "a6f87d72-bca6-49fe-9497-a1728cf38733":
        course_name = "Gross_Anatomy_2025"
    elif course_id == "67d4f5a8-cbd4-41e0-870c-aa09b361da0c":
        course_name = "Gross_Anatomy_Embryo_Imaging_STL_FA25"
    else:
        # Default fallback
        course_name = f"Course_{course_id[:8]}"
    
    return course_name


def rename_files(json_path, dry_run=True):
    """Rename JSON file and image directories with meaningful names"""
    
    print(f"🔄 Course File Renamer")
    print(f"📄 Processing: {json_path}")
    print(f"🔍 Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}")
    print()
    
    # Load JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    course_name = extract_course_info(data)
    timestamp = data.get('extraction_timestamp', 'unknown')
    
    json_dir = Path(json_path).parent
    project_dir = json_dir.parent  # Go up one level from questions/ to project root
    
    # Plan renames
    renames = []
    
    # 1. Rename main JSON file
    old_json_path = Path(json_path)
    new_json_name = f"{course_name}_Complete_Extraction_{timestamp}.json"
    new_json_path = json_dir / new_json_name
    
    if old_json_path.name != new_json_name:
        renames.append(('file', old_json_path, new_json_path))
    
    # 2. Rename main image directory
    old_course_dir = project_dir / "images" / f"course_{data['course_id']}"
    new_course_dir = project_dir / "images" / course_name
    
    if old_course_dir.exists():
        renames.append(('dir', old_course_dir, new_course_dir))
    
    # 3. Rename activity directories
    if old_course_dir.exists():
        activity_renames = []
        for activity in data.get('activities', []):
            activity_name = activity.get('activity_name', '')
            activity_id = activity.get('activity_id', '')
            
            # Parse class number from activity name (e.g., "Class 11 - Poll")
            class_match = re.search(r'Class (\d+)', activity_name)
            if class_match:
                class_num = int(class_match.group(1))
                class_label = f"Class_{class_num:02d}"
            else:
                class_label = "Class_XX"
            
            # Parse activity type
            if 'Poll' in activity_name:
                activity_type = "Poll"
            else:
                activity_type = "Activity"
            
            # Short ID (first 8 chars)
            short_id = activity_id[:8]
            
            # Find current directory
            for item in old_course_dir.iterdir():
                if item.is_dir() and short_id in item.name:
                    new_activity_name = f"{class_label}_{activity_type}_{short_id}"
                    new_activity_path = new_course_dir / new_activity_name
                    activity_renames.append(('activity_dir', item, new_activity_path, activity))
                    break
        
        renames.extend(activity_renames)
    
    # Show planned changes
    print("📋 PLANNED CHANGES:")
    print()
    
    if not renames:
        print("✨ No changes needed - files already have good names!")
        return
    
    for rename_type, old_path, new_path, *extra in renames:
        if rename_type == 'file':
            print(f"📄 JSON File:")
            print(f"   From: {old_path.name}")
            print(f"   To:   {new_path.name}")
            print()
        elif rename_type == 'dir':
            print(f"📁 Course Directory:")
            print(f"   From: {old_path}")
            print(f"   To:   {new_path}")
            print()
        elif rename_type == 'activity_dir':
            activity = extra[0]
            print(f"📂 Activity Directory:")
            print(f"   Activity: {activity['activity_name']} ({activity['questions_found']} questions)")
            print(f"   From: {old_path}")
            print(f"   To:   {new_path}")
            print()
    
    if dry_run:
        print("🔍 DRY RUN COMPLETE - No changes applied")
        print("   To apply changes, run with --apply")
        return
    
    # Apply changes
    print("🚀 APPLYING CHANGES...")
    print()
    
    try:
        # Track old paths for JSON updates
        path_mapping = {}
        
        # Apply renames in order - first move main directory, then handle subdirectories
        main_dir_moved = False
        new_course_dir_actual = None
        
        for rename_type, old_path, new_path, *extra in renames:
            if rename_type == 'file':
                # Will rename JSON file at the end
                continue
            elif rename_type == 'dir':
                print(f"📁 Moving course directory...")
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_path), str(new_path))
                path_mapping[str(old_path)] = str(new_path)
                print(f"   ✅ {old_path} -> {new_path}")
                main_dir_moved = True
                new_course_dir_actual = new_path
        
        # Now handle activity directories within the moved directory
        for rename_type, old_path, new_path, *extra in renames:
            if rename_type == 'activity_dir':
                activity = extra[0]
                # Find the activity directory in the new location
                activity_id = activity['activity_id']
                short_id = activity_id[:8]
                
                # Look for the directory in the new course directory
                current_activity_dir = None
                for item in new_course_dir_actual.iterdir():
                    if item.is_dir() and short_id in item.name:
                        current_activity_dir = item
                        break
                
                if current_activity_dir:
                    print(f"📂 Moving activity directory...")
                    shutil.move(str(current_activity_dir), str(new_path))
                    path_mapping[str(current_activity_dir)] = str(new_path)
                    print(f"   ✅ {current_activity_dir} -> {new_path}")
                else:
                    print(f"   ⚠️ Could not find activity directory for {activity['activity_name']}")
        
        # Update JSON paths
        print(f"📝 Updating JSON file paths...")
        updated_data = update_json_paths(data, path_mapping)
        
        # Write updated JSON to new location
        for rename_type, old_path, new_path, *extra in renames:
            if rename_type == 'file':
                with open(new_path, 'w') as f:
                    json.dump(updated_data, f, indent=2)
                print(f"   ✅ Updated JSON saved to {new_path}")
                
                # Remove old JSON file
                if old_path != new_path and old_path.exists():
                    old_path.unlink()
                    print(f"   🗑️  Removed old JSON file")
                break
        
        print()
        print("🎉 RENAMING COMPLETE!")
        print(f"📋 Course: {course_name}")
        print(f"📊 Activities: {len([r for r in renames if r[0] == 'activity_dir'])}")
        
    except Exception as e:
        print(f"❌ Error applying changes: {e}")
        print("💡 Tip: Check file permissions and ensure no files are open")


def update_json_paths(data, path_mapping):
    """Update local image paths in JSON data based on directory renames"""
    updated_data = data.copy()
    
    if 'activities' in updated_data:
        for activity in updated_data['activities']:
            if 'questions' in activity:
                for question in activity['questions']:
                    if 'local_image_path' in question:
                        old_path = question['local_image_path']
                        
                        # Update path based on mappings
                        new_path = old_path
                        for old_dir, new_dir in path_mapping.items():
                            if old_path.startswith(old_dir):
                                new_path = old_path.replace(old_dir, new_dir)
                                break
                        
                        question['local_image_path'] = new_path
            
            # Update image_directory field
            if 'image_directory' in activity:
                old_dir = activity['image_directory']
                new_dir = old_dir
                for old_path, new_path in path_mapping.items():
                    if old_dir.startswith(old_path):
                        new_dir = old_dir.replace(old_path, new_path)
                        break
                activity['image_directory'] = new_dir
    
    return updated_data


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rename course files with meaningful names")
    parser.add_argument('json_file', help='Path to the course extraction JSON file')
    parser.add_argument('--apply', action='store_true', help='Apply changes (default is dry-run)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"❌ JSON file not found: {args.json_file}")
        return 1
    
    rename_files(args.json_file, dry_run=not args.apply)
    return 0


if __name__ == '__main__':
    exit(main())
