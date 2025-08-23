import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile


class TestIClickerWebScraper(unittest.TestCase):
    """Test suite for iClicker web scraper"""
    
    def setUp(self):
        """Set up test environment"""
        self.username = "test_user"
        self.password = "test_pass"
        self.activity_id = "f7dcba1f-1231-4d91-906c-6e3acd9b660b"
    
    def test_scraper_initialization(self):
        """Test that scraper initializes correctly"""
        from iclicker_scraper import IClickerScraper
        
        scraper = IClickerScraper()
        self.assertIsNotNone(scraper)
        self.assertIsNone(scraper.driver)
    
    def test_login_success(self):
        """Test successful login to iClicker"""
        from iclicker_scraper import IClickerScraper
        
        scraper = IClickerScraper()
        scraper.driver = MagicMock()
        
        with patch.object(scraper, '_perform_login') as mock_login:
            mock_login.return_value = True
            
            result = scraper.login(self.username, self.password)
            
            self.assertTrue(result)
            mock_login.assert_called_once_with(self.username, self.password)
    
    def test_login_failure(self):
        """Test login failure raises appropriate exception"""
        from iclicker_scraper import IClickerScraper, AuthenticationError
        
        scraper = IClickerScraper()
        scraper.driver = MagicMock()
        
        with patch.object(scraper, '_perform_login') as mock_login:
            mock_login.side_effect = AuthenticationError("Invalid credentials")
            
            with self.assertRaises(AuthenticationError):
                scraper.login("wrong_user", "wrong_pass")
    
    def test_scrape_questions_success(self):
        """Test successful scraping of activity questions"""
        from iclicker_scraper import IClickerScraper
        
        scraper = IClickerScraper()
        scraper.driver = MagicMock()
        scraper.is_logged_in = True
        
        expected_questions = [
            {
                "id": "q1",
                "question_text": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "correct_answer": "4",
                "question_type": "multiple_choice"
            },
            {
                "id": "q2", 
                "question_text": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct_answer": "Paris",
                "question_type": "multiple_choice"
            }
        ]
        
        with patch.object(scraper, '_scrape_questions_from_page') as mock_scrape:
            mock_scrape.return_value = expected_questions
            
            result = scraper.get_activity_questions(self.activity_id)
            
            self.assertEqual(result, expected_questions)
            self.assertEqual(len(result), 2)
            self.assertIn("correct_answer", result[0])
            mock_scrape.assert_called_once_with(self.activity_id)
    
    def test_scrape_questions_without_login(self):
        """Test that scraping questions without login raises error"""
        from iclicker_scraper import IClickerScraper, AuthenticationError
        
        scraper = IClickerScraper()
        scraper.driver = MagicMock()
        scraper.is_logged_in = False
        
        with self.assertRaises(AuthenticationError):
            scraper.get_activity_questions(self.activity_id)
    
    def test_save_questions_to_file(self):
        """Test saving questions to JSON file"""
        from iclicker_scraper import IClickerScraper
        
        scraper = IClickerScraper()
        questions = [
            {
                "id": "q1",
                "question_text": "Test question",
                "correct_answer": "Test answer"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as test_file:
            test_file_path = test_file.name
        
        try:
            scraper.save_questions_to_file(questions, test_file_path)
            
            # Verify file was created and contains correct data
            self.assertTrue(os.path.exists(test_file_path))
            
            with open(test_file_path, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, questions)
            
        finally:
            # Clean up
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_environment_variables_for_credentials(self):
        """Test that credentials can be loaded from environment variables"""
        from iclicker_scraper import IClickerScraper
        
        with patch.dict(os.environ, {
            'ICLICKER_USERNAME': 'env_user',
            'ICLICKER_PASSWORD': 'env_pass'
        }):
            scraper = IClickerScraper()
            username, password = scraper.get_credentials_from_env()
            
            self.assertEqual(username, 'env_user')
            self.assertEqual(password, 'env_pass')
    
    def test_get_credentials_from_env_missing(self):
        """Test handling of missing environment variables"""
        from iclicker_scraper import IClickerScraper, ConfigurationError
        
        # Ensure env vars are not set
        with patch.dict(os.environ, {}, clear=True):
            scraper = IClickerScraper()
            
            with self.assertRaises(ConfigurationError):
                scraper.get_credentials_from_env()
    
    def test_driver_cleanup(self):
        """Test that browser driver is properly cleaned up"""
        from iclicker_scraper import IClickerScraper
        
        scraper = IClickerScraper()
        mock_driver = MagicMock()
        scraper.driver = mock_driver
        
        scraper.cleanup()
        
        mock_driver.quit.assert_called_once()
        self.assertIsNone(scraper.driver)


if __name__ == '__main__':
    unittest.main()
