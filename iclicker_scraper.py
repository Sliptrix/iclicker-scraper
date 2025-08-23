#!/usr/bin/env python3
"""
iClicker Web Scraper

This module provides a web scraper for extracting questions and answers 
from iClicker student activities using Selenium browser automation.
"""

import json
import os
import time
import logging
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager


# Custom exceptions
class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid"""
    pass


class ScrapingError(Exception):
    """Raised when scraping fails"""
    pass


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IClickerScraper:
    """Web scraper for iClicker student portal"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize the scraper
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for web driver operations
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.headless = headless
        self.timeout = timeout
        self.is_logged_in = False
        self.base_url = "https://student.iclicker.com"
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up and return Chrome driver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # Add user agent to appear more like a real browser
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)
            return driver
        except Exception as e:
            raise ConfigurationError(f"Failed to setup Chrome driver: {e}")
    
    def get_credentials_from_env(self) -> Tuple[str, str]:
        """
        Get credentials from environment variables
        
        Returns:
            Tuple of (username, password)
            
        Raises:
            ConfigurationError: If credentials are not found in environment
        """
        username = os.getenv('ICLICKER_USERNAME')
        password = os.getenv('ICLICKER_PASSWORD')
        
        if not username or not password:
            raise ConfigurationError(
                "ICLICKER_USERNAME and ICLICKER_PASSWORD environment variables must be set"
            )
        
        return username, password
    
    def _perform_login(self, username: str, password: str) -> bool:
        """
        Perform login to iClicker
        
        Args:
            username: iClicker username/email
            password: iClicker password
            
        Returns:
            True if login successful
            
        Raises:
            AuthenticationError: If login fails
        """
        try:
            if not self.driver:
                self.driver = self._setup_driver()
            
            logger.info("Navigating to iClicker login page...")
            self.driver.get(self.base_url)
            
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Look for login form elements - try multiple selectors
            username_selectors = [
                "input[type='email']",
                "input[name='username']",
                "input[name='email']",
                "#username",
                "#email",
                "[data-testid='username']",
                "[data-testid='email']"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found username field with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                # Try to find any input fields and examine the page
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Found {len(inputs)} input elements on page")
                
                # Look for input that might be username/email field
                for inp in inputs:
                    inp_type = inp.get_attribute('type') or ''
                    inp_name = inp.get_attribute('name') or ''
                    inp_id = inp.get_attribute('id') or ''
                    placeholder = inp.get_attribute('placeholder') or ''
                    
                    if any(term in (inp_type + inp_name + inp_id + placeholder).lower() 
                           for term in ['email', 'user', 'login']):
                        username_field = inp
                        logger.info(f"Found potential username field: type={inp_type}, name={inp_name}")
                        break
                
                if not username_field:
                    raise AuthenticationError("Could not find username/email field on login page")
            
            # Find password field
            password_field = None
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "#password",
                "[data-testid='password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                raise AuthenticationError("Could not find password field on login page")
            
            # Enter credentials
            logger.info("Entering credentials...")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Find and click submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Login')",
                "button:contains('Sign In')",
                "[data-testid='login-button']",
                "[data-testid='submit']"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if ":contains(" in selector:
                        # Handle text-based selectors differently
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if any(text in btn.text.lower() for text in ['login', 'sign in', 'submit']):
                                submit_button = btn
                                break
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if submit_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not submit_button:
                # Try pressing Enter on password field as fallback
                logger.info("Submit button not found, trying Enter key...")
                from selenium.webdriver.common.keys import Keys
                password_field.send_keys(Keys.RETURN)
            else:
                logger.info("Clicking submit button...")
                submit_button.click()
            
            # Wait for login to complete - check for redirect or dashboard
            time.sleep(3)
            
            # Check if we're logged in by looking for elements that appear after login
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Signs of successful login
            success_indicators = [
                'dashboard' in current_url.lower(),
                'activities' in current_url.lower(),
                'student' in current_url.lower() and 'login' not in current_url.lower(),
                'logout' in page_source,
                'sign out' in page_source,
                'dashboard' in page_source
            ]
            
            if any(success_indicators):
                logger.info("Login successful!")
                self.is_logged_in = True
                return True
            else:
                # Check for error messages
                error_selectors = [
                    ".error", ".alert", ".warning", 
                    "[data-testid='error']", ".login-error"
                ]
                
                error_message = "Login failed"
                for selector in error_selectors:
                    try:
                        error_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if error_elem.text.strip():
                            error_message = f"Login failed: {error_elem.text.strip()}"
                            break
                    except NoSuchElementException:
                        continue
                
                raise AuthenticationError(error_message)
                
        except TimeoutException:
            raise AuthenticationError("Login page did not load within timeout period")
        except WebDriverException as e:
            raise AuthenticationError(f"Web driver error during login: {e}")
    
    def login(self, username: str, password: str) -> bool:
        """
        Public method to login to iClicker
        
        Args:
            username: iClicker username/email
            password: iClicker password
            
        Returns:
            True if login successful
        """
        return self._perform_login(username, password)
    
    def _scrape_questions_from_page(self, activity_id: str) -> List[Dict]:
        """
        Scrape questions from the activity page
        
        Args:
            activity_id: The activity ID to scrape questions from
            
        Returns:
            List of question dictionaries with answers
            
        Raises:
            ScrapingError: If scraping fails
        """
        if not self.driver or not self.is_logged_in:
            raise AuthenticationError("Must be logged in before scraping questions")
        
        try:
            # Navigate to the questions page
            questions_url = f"{self.base_url}/#/activity/{activity_id}/questions"
            logger.info(f"Navigating to questions page: {questions_url}")
            self.driver.get(questions_url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            time.sleep(5)  # Give dynamic content time to load
            
            questions = []
            
            # Try multiple selectors for finding questions
            question_container_selectors = [
                ".question-container",
                ".question-item",
                ".question",
                "[data-testid='question']",
                ".poll-question",
                ".activity-question"
            ]
            
            question_elements = []
            for selector in question_container_selectors:
                try:
                    question_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if question_elements:
                        logger.info(f"Found {len(question_elements)} questions using selector: {selector}")
                        break
                except NoSuchElementException:
                    continue
            
            if not question_elements:
                # Fallback: look for any elements containing question text
                logger.info("No question containers found, searching for question text...")
                
                # Look for elements with question-like text patterns
                all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '?')]")
                question_elements = [elem for elem in all_elements if len(elem.text.strip()) > 20]
                
                logger.info(f"Found {len(question_elements)} potential question elements")
            
            # Extract questions
            for i, elem in enumerate(question_elements):
                try:
                    question_data = self._extract_question_data(elem, i)
                    if question_data:
                        questions.append(question_data)
                except Exception as e:
                    logger.warning(f"Failed to extract question {i}: {e}")
                    continue
            
            if not questions:
                # Last resort: capture all text content for manual inspection
                logger.warning("No questions found with standard selectors. Capturing page content...")
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Look for question patterns in text
                lines = page_text.split('\n')
                potential_questions = [line.strip() for line in lines if '?' in line and len(line.strip()) > 10]
                
                if potential_questions:
                    logger.info(f"Found {len(potential_questions)} potential questions in page text")
                    for i, q_text in enumerate(potential_questions[:10]):  # Limit to first 10
                        questions.append({
                            "id": f"q{i+1}",
                            "question_text": q_text,
                            "options": [],
                            "correct_answer": "Unknown - manual review needed",
                            "question_type": "text_extracted",
                            "extraction_method": "text_pattern_matching"
                        })
                else:
                    raise ScrapingError("No questions found on the page")
            
            logger.info(f"Successfully extracted {len(questions)} questions")
            return questions
            
        except TimeoutException:
            raise ScrapingError("Questions page did not load within timeout period")
        except WebDriverException as e:
            raise ScrapingError(f"Web driver error while scraping: {e}")
    
    def _extract_question_data(self, question_element, index: int) -> Optional[Dict]:
        """
        Extract question data from a question element
        
        Args:
            question_element: Selenium WebElement containing the question
            index: Question index for ID generation
            
        Returns:
            Dictionary with question data or None if extraction fails
        """
        try:
            question_text = ""
            options = []
            correct_answer = ""
            
            # Try to extract question text
            text_selectors = [
                ".question-text",
                ".question-content", 
                ".poll-question-text",
                "h3", "h4", ".title",
                "[data-testid='question-text']"
            ]
            
            for selector in text_selectors:
                try:
                    text_elem = question_element.find_element(By.CSS_SELECTOR, selector)
                    question_text = text_elem.text.strip()
                    if question_text:
                        break
                except NoSuchElementException:
                    continue
            
            # If no specific question text found, use the element's text
            if not question_text:
                question_text = question_element.text.strip()
                # Clean up the text - take first line that looks like a question
                lines = question_text.split('\n')
                for line in lines:
                    if '?' in line and len(line.strip()) > 10:
                        question_text = line.strip()
                        break
            
            # Try to extract answer options
            option_selectors = [
                ".option", ".choice", ".answer-option",
                ".poll-option", "[data-testid='option']",
                "li", "label"
            ]
            
            for selector in option_selectors:
                try:
                    option_elements = question_element.find_elements(By.CSS_SELECTOR, selector)
                    if option_elements:
                        options = [opt.text.strip() for opt in option_elements if opt.text.strip()]
                        break
                except NoSuchElementException:
                    continue
            
            # Try to find correct answer indicators
            correct_indicators = [
                ".correct", ".right-answer", ".solution",
                "[data-correct='true']", ".answer-correct",
                ".checkmark", ".tick"
            ]
            
            for selector in correct_indicators:
                try:
                    correct_elem = question_element.find_element(By.CSS_SELECTOR, selector)
                    correct_answer = correct_elem.text.strip()
                    if correct_answer:
                        break
                except NoSuchElementException:
                    continue
            
            # If no explicit correct answer found, look for visual indicators
            if not correct_answer and options:
                # Look for options with success/correct styling
                for opt_elem in question_element.find_elements(By.CSS_SELECTOR, ".option, .choice"):
                    classes = opt_elem.get_attribute("class") or ""
                    style = opt_elem.get_attribute("style") or ""
                    
                    if any(indicator in classes.lower() for indicator in ["correct", "right", "success", "green"]) or \
                       any(indicator in style.lower() for indicator in ["green", "correct"]):
                        correct_answer = opt_elem.text.strip()
                        break
            
            if not correct_answer:
                correct_answer = "Answer not available - check manually"
            
            return {
                "id": f"q{index + 1}",
                "question_text": question_text or "Question text not found",
                "options": options,
                "correct_answer": correct_answer,
                "question_type": "multiple_choice" if options else "unknown",
                "extraction_method": "web_scraping"
            }
            
        except Exception as e:
            logger.error(f"Error extracting question data: {e}")
            return None
    
    def get_activity_questions(self, activity_id: str) -> List[Dict]:
        """
        Get all questions for an activity
        
        Args:
            activity_id: The activity ID
            
        Returns:
            List of questions with answers
            
        Raises:
            AuthenticationError: If not logged in
            ScrapingError: If scraping fails
        """
        if not self.is_logged_in:
            raise AuthenticationError("Must be logged in before getting questions")
        
        return self._scrape_questions_from_page(activity_id)
    
    def save_questions_to_file(self, questions: List[Dict], file_path: str) -> None:
        """
        Save questions to a JSON file
        
        Args:
            questions: List of question dictionaries
            file_path: Path to save the file
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(questions)} questions to {file_path}")
        except Exception as e:
            raise Exception(f"Failed to save questions to file: {e}")
    
    def cleanup(self) -> None:
        """Clean up resources (close browser)"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error during driver cleanup: {e}")
            finally:
                self.driver = None
        self.is_logged_in = False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.cleanup()


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape iClicker questions")
    parser.add_argument("activity_id", help="Activity ID to scrape")
    parser.add_argument("-o", "--output", default="questions.json", help="Output file path")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--username", help="iClicker username (or set ICLICKER_USERNAME env var)")
    parser.add_argument("--password", help="iClicker password (or set ICLICKER_PASSWORD env var)")
    
    args = parser.parse_args()
    
    try:
        with IClickerScraper(headless=args.headless) as scraper:
            # Get credentials
            if args.username and args.password:
                username, password = args.username, args.password
            else:
                username, password = scraper.get_credentials_from_env()
            
            # Login and scrape
            scraper.login(username, password)
            questions = scraper.get_activity_questions(args.activity_id)
            scraper.save_questions_to_file(questions, args.output)
            
            print(f"Successfully scraped {len(questions)} questions to {args.output}")
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
