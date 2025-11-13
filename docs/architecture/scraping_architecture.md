# Scraping Architecture

## Overview
The scraping functionality follows Clean Architecture principles with clear separation of concerns:

```
+---------------------+
|  Presentation Layer |
|  (CLI Handler)      |
+---------------------+
         |
         v
+---------------------+
|  Application Layer  |
|  (Use Cases,        |
|   Services)         |
+---------------------+
         |
         v
+---------------------+
|   Domain Layer      |
|  (Interfaces, VO)   |
+---------------------+
         |
         v
+---------------------+
| Infrastructure Layer|
|  (Adapters)         |
+---------------------+
```

## Key Components

### 1. Value Objects
- `SubjectInfo`: Encapsulates subject identification logic
- `ScrapingConfig`: Contains all scraping configuration parameters
- `ScrapingResult`: Provides consistent scraping results reporting

### 2. Use Cases
- `ScrapeSubjectUseCase`: Handles single subject scraping workflow
- Future use cases: `ParallelScrapeSubjectsUseCase`, `ResumeScrapingUseCase`

### 3. Application Services
- `ScrapingService`: Coordinates scraping workflow
- `PageScrapingService`: Handles individual page scraping
- `ProblemFactory`: Creates domain problems from scraped data

### 4. External Service Interfaces
- `IBrowserService`: Manages browser resources
- `IDatabaseService`: Handles database operations
- `ISpecificationService`: Provides task specifications

### 5. Infrastructure Adapters
- `BrowserServiceAdapter`: Implements browser management with Playwright
- `DatabaseServiceAdapter`: Implements database operations with SQLAlchemy
- `SpecificationAdapter`: Implements specification loading from JSON files

### 6. CLI Handler
- `ScrapingCLIHandler`: Handles all user interactions
- Delegates to use cases for business logic
- Manages file system operations
- Provides user feedback

## Dependency Flow
1. CLI Handler calls Use Cases
2. Use Cases coordinate Application Services
3. Application Services use Domain Interfaces
4. Infrastructure Adapters implement Domain Interfaces

## Benefits
- **Testability**: Each component can be tested in isolation
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Easy to replace infrastructure components
- **Scalability**: Parallel scraping can be added without affecting core logic
- **Readability**: Business logic is clearly expressed in use cases

## Usage
```bash
python scripts/main_scraping.py
```

## Configuration
All configuration is managed through the `config.py` file and can be overridden via environment variables.

## Removal of Legacy Code
The `scraper/fipi_scraper.py` file has been removed as its functionality has been:
- Refactored into proper use cases and services
- Integrated into the Clean Architecture structure
- Replaced with more maintainable and testable components

The new architecture provides better separation of concerns, improved testability, and greater flexibility for future enhancements.
