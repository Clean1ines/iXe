"""
CLI handler for scraping operations.

This class handles all CLI interactions and delegates business logic
to appropriate use cases. It maintains clean separation between
presentation concerns and application logic.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from domain.value_objects.scraping.subject_info import SubjectInfo
from domain.value_objects.scraping.scraping_config import ScrapingConfig, ScrapingMode
from application.use_cases.scraping.scrape_subject_use_case import ScrapeSubjectUseCase
from domain.value_objects.scraping.scraping_result import ScrapingSubjectResult

logger = logging.getLogger(__name__)

class ScrapingCLIHandler:
    """
    CLI handler for scraping operations.
    
    Business Rules:
    - Handles all user interactions
    - Validates user input
    - Delegates to use cases
    - Manages file system operations
    - Provides user feedback
    - Handles keyboard interrupts gracefully
    """
    
    def __init__(self, scrape_subject_use_case: ScrapeSubjectUseCase):
        """
        Initialize CLI handler with required use cases.
        
        Args:
            scrape_subject_use_case: Use case to scrape subjects
        """
        self.scrape_subject_use_case = scrape_subject_use_case
    
    async def run(self) -> None:
        """Run the CLI interface."""
        print("🚀 Welcome to the FIPI Parser!")
        print("=" * 50)
        
        available_subjects = self._get_available_subjects()
        
        while True:
            choice = self._show_main_menu()
            
            if choice == '1':
                await self._handle_single_subject_scraping(available_subjects)
            elif choice == '2':
                await self._handle_parallel_scraping(available_subjects)
            elif choice == '3':
                print("\n👋 Goodbye!")
                print("=" * 50)
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def _show_main_menu(self) -> str:
        """Display main menu and get user choice."""
        print("\n" + "="*40)
        print("📋 MAIN MENU")
        print("="*40)
        print("1. Scrape a single subject")
        print("2. Parallel scrape multiple subjects")
        print("3. Exit")
        print("-"*40)
        return input("👉 Enter your choice (1/2/3): ").strip()
    
    def _get_available_subjects(self) -> List[str]:
        """Get list of available subjects."""
        from utils.subject_mapping import SUBJECT_TO_OFFICIAL_NAME_MAP
        
        # Get subjects that have proj_id mappings
        available_subjects = []
        for alias, official_name in SUBJECT_TO_OFFICIAL_NAME_MAP.items():
            try:
                from utils.subject_mapping import get_proj_id_for_subject, get_subject_key_from_alias
                subject_key = get_subject_key_from_alias(alias)
                get_proj_id_for_subject(subject_key)
                available_subjects.append(official_name)
            except (KeyError, ValueError):
                continue
        
        return available_subjects
    
    async def _handle_single_subject_scraping(self, available_subjects: List[str]) -> None:
        """Handle single subject scraping workflow."""
        if not available_subjects:
            print("❌ No available subjects found.")
            return
        
        subject_name = self._select_subject(available_subjects)
        if not subject_name:
            return
        
        force_restart = self._ask_force_restart()
        
        try:
            subject_info = SubjectInfo.from_official_name(subject_name)
            config = ScrapingConfig.for_sequential_scraping(
                force_restart=force_restart,
                timeout_seconds=30
            )
            
            print(f"\n🚀 Starting scraping for {subject_name}...")
            print(f"📁 Output directory: {subject_info.output_directory}")
            print("-" * 40)
            
            result = await self.scrape_subject_use_case.execute(subject_info, config)
            self._display_scraping_results(result)
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            print(f"\n❌ Scraping failed: {e}")
    
    def _select_subject(self, subjects: List[str]) -> Optional[str]:
        """Display subjects and get user selection."""
        print("\n📋 Available subjects:")
        for i, subject in enumerate(subjects, 1):
            print(f"{i}. {subject}")
        print(f"{len(subjects) + 1}. Back to Main Menu")
        
        while True:
            choice = input(f"\n🔢 Enter subject number (1-{len(subjects)+1}): ").strip()
            if choice == str(len(subjects) + 1):
                return None
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(subjects):
                    return subjects[idx]
                print("❌ Invalid number. Please try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
    
    def _ask_force_restart(self) -> bool:
        """Ask user if they want to force restart scraping."""
        choice = input("🔄 Do you want to force restart scraping (delete existing data)? (y/n): ").strip().lower()
        return choice == 'y'
    
    def _display_scraping_results(self, result: ScrapingSubjectResult) -> None:
        """Display scraping results to user."""
        print("\n" + "="*50)
        if result.success:
            print(f"✅ Scraping completed successfully for {result.subject_name}!")
            print(f"📊 Total pages scraped: {result.total_pages}")
            print(f"📚 Total problems found: {result.total_problems_found}")
            print(f"💾 Total problems saved: {result.total_problems_saved}")
            print(f"⏱️  Duration: {result.duration_seconds:.2f} seconds")
            print(f"📈 Success rate: {result.success_rate:.1f}%")
        else:
            print(f"❌ Scraping failed for {result.subject_name}")
            print(f"📊 Total pages processed: {result.total_pages}")
            print(f"📚 Total problems found: {result.total_problems_found}")
            print(f"💾 Total problems saved: {result.total_problems_saved}")
            print(f"⏱️  Duration: {result.duration_seconds:.2f} seconds")
            
            if result.errors:
                print("\n💥 Errors encountered:")
                for i, error in enumerate(result.errors, 1):
                    print(f"  {i}. {error}")
        
        print("-"*50)
        print(f"📁 Data saved to: {result.metadata['subject_info']['output_directory']}")
        print("="*50)
    
    async def _handle_parallel_scraping(self, available_subjects: List[str]) -> None:
        """Handle parallel scraping workflow."""
        print("\n⚡ Parallel scraping mode is coming soon!")
        print("For now, please use single subject scraping.")
        # Implementation would coordinate multiple scraping tasks concurrently
