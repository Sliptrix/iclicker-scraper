#!/usr/bin/env python3
"""
Test suite for course-level activity extraction functionality.

Tests the ability to discover activities from course class-history pages
and extract questions from all discovered activities.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
from selenium.webdriver.common.by import By


class TestCourseActivityDiscovery(unittest.TestCase):
    """Test course activity discovery functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.sample_course_id = "a6f87d72-bca6-49fe-9497-a1728cf38733"
        self.sample_course_url = f"https://student.iclicker.com/#/course/{self.sample_course_id}/class-history"
    
    def test_course_url_parsing(self):
        """Test extraction of course ID from course URL."""
        from extract_course_activities import extract_course_id_from_url
        
        # Test valid course URL
        course_id = extract_course_id_from_url(self.sample_course_url)
        self.assertEqual(course_id, self.sample_course_id)
        
        # Test invalid URL
        with self.assertRaises(ValueError):
            extract_course_id_from_url("https://invalid-url.com")
    
    def test_activity_id_extraction_from_page(self):
        """Test extraction of activity IDs from class-history page."""
        from extract_course_activities import extract_activity_ids_from_page
        
        # Mock page elements with activity links
        mock_links = []
        sample_activity_ids = [
            "028a9cfc-c979-46b7-845c-5f81c85d862e",
            "f7dcba1f-1231-4d91-906c-6e3acd9b660b", 
            "c91973a1-a821-43a4-994d-03fc4a21f2fc"
        ]
        
        for activity_id in sample_activity_ids:
            mock_link = Mock()
            mock_link.get_attribute.return_value = f"https://student.iclicker.com/#/activity/{activity_id}/questions"
            mock_links.append(mock_link)
        
        # Mock both calls to find_elements - first for links, second for data attributes
        self.mock_driver.find_elements.side_effect = [mock_links, []]
        
        # Test activity ID extraction
        extracted_ids = extract_activity_ids_from_page(self.mock_driver)
        
        self.assertEqual(len(extracted_ids), 3)
        for expected_id in sample_activity_ids:
            self.assertIn(expected_id, extracted_ids)
    
    def test_activity_id_extraction_handles_empty_page(self):
        """Test that empty pages are handled gracefully."""
        from extract_course_activities import extract_activity_ids_from_page
        
        self.mock_driver.find_elements.return_value = []
        
        extracted_ids = extract_activity_ids_from_page(self.mock_driver)
        self.assertEqual(extracted_ids, [])
    
    def test_activity_id_extraction_filters_duplicates(self):
        """Test that duplicate activity IDs are filtered out."""
        from extract_course_activities import extract_activity_ids_from_page
        
        # Mock page with duplicate links
        activity_id = "028a9cfc-c979-46b7-845c-5f81c85d862e"
        mock_links = []
        
        for _ in range(3):  # Same activity ID appears 3 times
            mock_link = Mock()
            mock_link.get_attribute.return_value = f"https://student.iclicker.com/#/activity/{activity_id}/questions"
            mock_links.append(mock_link)
        
        # Mock both calls to find_elements - first for links, second for data attributes
        self.mock_driver.find_elements.side_effect = [mock_links, []]
        
        extracted_ids = extract_activity_ids_from_page(self.mock_driver)
        
        self.assertEqual(len(extracted_ids), 1)
        self.assertEqual(extracted_ids[0], activity_id)


class TestCourseExtraction(unittest.TestCase):
    """Test the main course extraction workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.sample_course_url = "https://student.iclicker.com/#/course/a6f87d72-bca6-49fe-9497-a1728cf38733/class-history"
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('extract_course_activities.webdriver')
    @patch('extract_course_activities.extract_activity_ids_from_page')
    @patch('extract_course_activities.extract_questions_from_activity')
    @patch('extract_course_activities.download_images_for_activity')
    def test_extract_course_activities_workflow(self, mock_download_images, mock_extract_questions, mock_extract_ids, mock_webdriver):
        """Test the complete course extraction workflow."""
        from extract_course_activities import extract_course_activities
        
        # Mock setup
        mock_driver = Mock()
        mock_webdriver.Chrome.return_value = mock_driver
        
        # Mock driver methods
        mock_driver.find_element.return_value = Mock()
        
        # Mock login button
        mock_button = Mock()
        mock_button.text = "Sign In"
        mock_button.get_attribute.return_value = "submit"
        mock_driver.find_elements.return_value = [mock_button]
        
        # Mock activity discovery
        sample_activity_ids = ["activity1", "activity2", "activity3"]
        mock_extract_ids.return_value = sample_activity_ids
        
        # Mock question extraction for each activity
        sample_questions = [
            {
                'question_number': 1,
                'question_text': 'Sample question 1',
                'activity_id': 'activity1',
                'extraction_method': 'test'
            }
        ]
        mock_extract_questions.return_value = sample_questions
        
        # Mock image downloading
        mock_download_images.return_value = 1
        
        # Test extraction
        result = extract_course_activities(
            course_url=self.sample_course_url,
            username="test@example.com",
            password="testpass",
            output_dir=self.temp_dir
        )
        
        # Verify workflow
        self.assertIsNotNone(result)
        self.assertEqual(len(result['activities']), 3)
        self.assertEqual(result['total_activities_processed'], 3)
        self.assertEqual(result['total_questions_extracted'], 3)  # 1 question per activity
    
    def test_result_data_format(self):
        """Test that extraction results follow the expected data format."""
        from extract_course_activities import CourseExtractionResult
        
        # Create sample result data
        result_data = CourseExtractionResult(
            course_id="test-course",
            course_url="https://test.com",
            extraction_timestamp="20250905_120000",
            total_activities_processed=2,
            total_questions_extracted=5,
            total_images_downloaded=5,
            activities=[
                {
                    'activity_id': 'activity1',
                    'activity_name': 'Class 1',
                    'questions_found': 3,
                    'images_downloaded': 3,
                    'questions': []
                },
                {
                    'activity_id': 'activity2', 
                    'activity_name': 'Class 2',
                    'questions_found': 2,
                    'images_downloaded': 2,
                    'questions': []
                }
            ]
        )
        
        # Verify data structure
        self.assertEqual(result_data.course_id, "test-course")
        self.assertEqual(result_data.total_activities_processed, 2)
        self.assertEqual(result_data.total_questions_extracted, 5)
        self.assertEqual(len(result_data.activities), 2)
    
    def test_output_file_creation(self):
        """Test that output files are created with proper naming."""
        from extract_course_activities import create_output_filename
        
        course_id = "a6f87d72-bca6-49fe-9497-a1728cf38733"
        timestamp = "20250905_120000"
        
        filename = create_output_filename(course_id, timestamp, self.temp_dir)
        
        expected_pattern = f"course_{course_id}_extraction_{timestamp}.json"
        self.assertIn(expected_pattern, filename)
        self.assertTrue(filename.startswith(self.temp_dir))


class TestIntegration(unittest.TestCase):
    """Integration tests for course extraction."""
    
    def test_credentials_loading(self):
        """Test that credentials can be loaded from environment."""
        with patch.dict(os.environ, {
            'ICLICKER_USERNAME': 'test@example.com',
            'ICLICKER_PASSWORD': 'testpass123'
        }):
            from extract_course_activities import load_credentials
            
            username, password = load_credentials()
            self.assertEqual(username, 'test@example.com')
            self.assertEqual(password, 'testpass123')
    
    def test_credentials_from_env_file(self):
        """Test loading credentials from .env file."""
        from extract_course_activities import load_credentials_from_file
        
        # Create temporary .env file
        env_content = "ICLICKER_USERNAME=file@example.com\nICLICKER_PASSWORD=filepass123\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            env_file_path = f.name
        
        try:
            username, password = load_credentials_from_file(env_file_path)
            self.assertEqual(username, 'file@example.com')
            self.assertEqual(password, 'filepass123')
        finally:
            os.unlink(env_file_path)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
