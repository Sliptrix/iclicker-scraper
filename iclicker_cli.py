#!/usr/bin/env python3
"""
iClicker CLI Tool

Command-line interface for scraping iClicker questions regularly.
Supports both one-time runs and scheduled execution.
"""

import argparse
import os
import sys
import json
import datetime
from pathlib import Path
from typing import Optional

from iclicker_scraper import IClickerScraper, AuthenticationError, ConfigurationError, ScrapingError


def setup_credentials(args) -> tuple[str, str]:
    """
    Set up credentials from various sources
    
    Args:
        args: Command line arguments
        
    Returns:
        Tuple of (username, password)
        
    Raises:
        ConfigurationError: If credentials cannot be found
    """
    # Priority: command line args > environment variables > .env file > prompt
    username = args.username
    password = args.password
    
    if not username or not password:
        try:
            scraper = IClickerScraper()
            env_username, env_password = scraper.get_credentials_from_env()
            username = username or env_username
            password = password or env_password
        except ConfigurationError:
            pass
    
    # If still missing credentials, prompt user (only in interactive mode)
    if not username and sys.stdin.isatty():
        username = input("iClicker username: ")
    
    if not password and sys.stdin.isatty():
        import getpass
        password = getpass.getpass("iClicker password: ")
    
    if not username or not password:
        raise ConfigurationError(
            "Username and password required. Provide via:\n"
            "  1. Command line: --username and --password\n"
            "  2. Environment variables: ICLICKER_USERNAME and ICLICKER_PASSWORD\n"
            "  3. Interactive input (when running in terminal)"
        )
    
    return username, password


def create_output_filename(activity_id: str, output_dir: str) -> str:
    """
    Create a unique output filename with timestamp
    
    Args:
        activity_id: The activity ID
        output_dir: Output directory
        
    Returns:
        Full path to output file
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"iclicker_questions_{activity_id}_{timestamp}.json"
    return os.path.join(output_dir, filename)


def scrape_questions(args) -> None:
    """
    Main function to scrape questions
    
    Args:
        args: Command line arguments
    """
    try:
        print("Setting up iClicker scraper...")
        
        # Get credentials
        username, password = setup_credentials(args)
        
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine output file path
        if args.output:
            output_file = args.output
        else:
            output_file = create_output_filename(args.activity_id, str(output_dir))
        
        print(f"Output will be saved to: {output_file}")
        
        # Initialize scraper
        with IClickerScraper(headless=not args.show_browser, timeout=args.timeout) as scraper:
            print("Logging in to iClicker...")
            scraper.login(username, password)
            
            print(f"Scraping questions for activity: {args.activity_id}")
            questions = scraper.get_activity_questions(args.activity_id)
            
            if not questions:
                print("⚠️  No questions found for this activity")
                return
            
            print(f"✅ Successfully scraped {len(questions)} questions")
            
            # Save to file
            scraper.save_questions_to_file(questions, output_file)
            
            # Print summary if verbose
            if args.verbose:
                print("\n📋 Questions Summary:")
                for i, q in enumerate(questions, 1):
                    print(f"  {i}. {q.get('question_text', 'N/A')[:80]}...")
                    if q.get('correct_answer'):
                        print(f"     ✓ Answer: {q['correct_answer']}")
                    else:
                        print(f"     ⚠ Answer: {q.get('correct_answer', 'Not found')}")
                    print()
            
            print(f"✅ Questions saved to: {output_file}")
            
            # Create symlink to latest if requested
            if args.create_latest_link:
                latest_link = os.path.join(str(output_dir), "latest_questions.json")
                try:
                    if os.path.exists(latest_link):
                        os.unlink(latest_link)
                    os.symlink(os.path.basename(output_file), latest_link)
                    print(f"📎 Created link: {latest_link}")
                except OSError as e:
                    print(f"⚠️  Could not create symlink: {e}")
    
    except AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)
    
    except ScrapingError as e:
        print(f"❌ Scraping failed: {e}")
        sys.exit(1)
    
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Scraping cancelled by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def list_recent_files(args) -> None:
    """List recent output files"""
    output_dir = Path(args.output_dir)
    
    if not output_dir.exists():
        print(f"Output directory does not exist: {output_dir}")
        return
    
    # Find JSON files matching our pattern
    pattern = "iclicker_questions_*.json"
    json_files = sorted(output_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not json_files:
        print(f"No question files found in {output_dir}")
        return
    
    print(f"Recent question files in {output_dir}:")
    print("=" * 60)
    
    for i, file_path in enumerate(json_files[:args.limit], 1):
        stat = file_path.stat()
        timestamp = datetime.datetime.fromtimestamp(stat.st_mtime)
        size_kb = stat.st_size / 1024
        
        print(f"{i:2d}. {file_path.name}")
        print(f"    📅 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    📦 {size_kb:.1f} KB")
        
        # Try to read question count
        try:
            with open(file_path) as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"    📋 {len(data)} questions")
        except:
            pass
        
        print()


def setup_environment_file(args) -> None:
    """Set up .env file with credentials"""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env_file = output_dir / ".env"
    
    if env_file.exists() and not args.force:
        print(f"❌ Environment file already exists: {env_file}")
        print("Use --force to overwrite")
        return
    
    # Get credentials
    try:
        username, password = setup_credentials(args)
    except ConfigurationError:
        # Prompt for credentials if not available
        username = input("iClicker username: ")
        import getpass
        password = getpass.getpass("iClicker password: ")
    
    # Create .env file
    env_content = f"""# iClicker credentials
ICLICKER_USERNAME={username}
ICLICKER_PASSWORD={password}
"""
    
    env_file.write_text(env_content)
    os.chmod(env_file, 0o600)  # Secure permissions
    
    print(f"✅ Environment file created: {env_file}")
    print("💡 You can now run the scraper without providing credentials each time")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="iClicker Question Scraper - Extract questions and answers from iClicker activities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape questions and save with timestamp
  %(prog)s scrape f7dcba1f-1231-4d91-906c-6e3acd9b660b
  
  # Scrape with specific credentials and output file
  %(prog)s scrape f7dcba1f-1231-4d91-906c-6e3acd9b660b \\
    --username user@example.com --password mypass \\
    --output my_questions.json
  
  # Set up environment file for credentials
  %(prog)s setup-env --username user@example.com
  
  # List recent files
  %(prog)s list --limit 5
  
Environment Variables:
  ICLICKER_USERNAME    Your iClicker username/email
  ICLICKER_PASSWORD    Your iClicker password
        """
    )
    
    # Global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output-dir", default="./questions", 
                       help="Directory to save questions (default: ./questions)")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape questions from iClicker activity")
    scrape_parser.add_argument("activity_id", help="iClicker activity ID (from URL)")
    scrape_parser.add_argument("-o", "--output", help="Output file path (default: auto-generated)")
    scrape_parser.add_argument("--username", help="iClicker username/email")
    scrape_parser.add_argument("--password", help="iClicker password") 
    scrape_parser.add_argument("--show-browser", action="store_true", 
                              help="Show browser window (default: headless)")
    scrape_parser.add_argument("--timeout", type=int, default=30, 
                              help="Timeout in seconds (default: 30)")
    scrape_parser.add_argument("--create-latest-link", action="store_true",
                              help="Create 'latest_questions.json' symlink")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent question files")
    list_parser.add_argument("--limit", type=int, default=10, 
                            help="Number of files to show (default: 10)")
    
    # Setup environment command
    setup_parser = subparsers.add_parser("setup-env", help="Set up environment file with credentials")
    setup_parser.add_argument("--username", help="iClicker username/email")
    setup_parser.add_argument("--password", help="iClicker password")
    setup_parser.add_argument("--force", action="store_true", help="Overwrite existing .env file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "scrape":
        scrape_questions(args)
    elif args.command == "list":
        list_recent_files(args)
    elif args.command == "setup-env":
        setup_environment_file(args)


if __name__ == "__main__":
    main()
