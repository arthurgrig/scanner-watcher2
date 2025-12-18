# Implementation Plan

- [x] 1. Set up project structure and development environment
  - Create directory structure for Windows-first architecture
  - Set up Python 3.12+ project with pyproject.toml
  - Configure development dependencies (pytest, hypothesis, black, mypy, ruff)
  - Create basic package structure with __init__.py files
  - _Requirements: All_

- [x] 2. Implement data models and core types
  - Create ProcessingResult, Classification, HealthStatus, ErrorType models
  - Implement pydantic models for configuration (Config, ProcessingConfig, AIConfig, LoggingConfig, ServiceConfig)
  - Add validation logic for configuration fields
  - _Requirements: 8.2, 8.3_

- [x] 2.1 Write property test for configuration validation
  - **Property 31: Configuration validation**
  - **Validates: Requirements 8.2**

- [x] 2.2 Update configuration models for new features
  - Add file_prefix field to ProcessingConfig (default: "SCAN-")
  - Add pages_to_extract field to ProcessingConfig (default: 3, range: 1-10)
  - Update config_template.json with new fields
  - Update configuration wizard to prompt for file prefix
  - Add validation for file_prefix (non-empty, valid filename characters)
  - _Requirements: 1.6, 2.1, 2.4_

- [-] 3. Implement logging system
  - Create Logger class with structured JSON logging
  - Implement log rotation (10MB, 5 backups)
  - Add Windows Event Log integration for critical events
  - Implement correlation ID generation
  - Support multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [-] 3.1 Write property test for structured JSON logging
  - **Property 27: Structured JSON logging**
  - **Validates: Requirements 7.1**

- [x] 3.2 Write property test for log rotation
  - **Property 28: Log rotation**
  - **Validates: Requirements 7.2**

- [x] 3.3 Write property test for success logging completeness
  - **Property 29: Success logging completeness**
  - **Validates: Requirements 7.4, 15.1**

- [x] 4. Implement error handler with retry logic
  - Create ErrorHandler class with error classification
  - Implement exponential backoff with jitter
  - Add circuit breaker pattern for external services
  - Implement execute_with_retry method
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 4.1 Write property test for transient error retry
  - **Property 22: Transient error retry**
  - **Validates: Requirements 6.1, 14.1**

- [x] 4.2 Write property test for permanent error handling
  - **Property 23: Permanent error handling**
  - **Validates: Requirements 6.2**

- [x] 4.3 Write property test for error isolation
  - **Property 24: Error isolation**
  - **Validates: Requirements 6.4**

- [x] 4.4 Write property test for error context logging
  - **Property 25: Error context logging**
  - **Validates: Requirements 6.5**

- [x] 4.5 Write property test for sharing violation classification
  - **Property 26: Sharing violation classification**
  - **Validates: Requirements 14.4**

- [x] 5. Implement configuration management
  - Create ConfigManager class
  - Implement load_config with pydantic validation
  - Add Windows DPAPI encryption/decryption for API keys
  - Support configuration hot-reload
  - Create default configuration template
  - Handle missing configuration gracefully
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 5.1 Write property test for API key encryption
  - **Property 30: API key encryption**
  - **Validates: Requirements 8.1**

- [x] 5.2 Write property test for configuration hot-reload
  - **Property 32: Configuration hot-reload**
  - **Validates: Requirements 8.4**

- [x] 6. Implement PDF processor
  - Create PDFProcessor class
  - Implement extract_first_page using PyMuPDF
  - Add PyPDF2 fallback for extraction failures
  - Implement image optimization for API transmission
  - Add PDF validation
  - Handle corrupted PDFs gracefully
  - Limit memory usage during processing
  - _Requirements: 2.1, 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 6.1 Write property test for first page extraction
  - **Property 6: First three pages extraction**
  - **Validates: Requirements 2.1**

- [x] 6.2 Write property test for extraction fallback
  - **Property 8: Extraction fallback**
  - **Validates: Requirements 9.1, 9.2**

- [x] 6.3 Write property test for image optimization
  - **Property 9: Image optimization**
  - **Validates: Requirements 9.3**

- [x] 6.4 Update PDF processor to extract multiple pages
  - Modify extract_first_page to extract_first_pages returning list[Image]
  - Add num_pages parameter (default: 3) from configuration
  - Handle PDFs with fewer than requested pages gracefully
  - Extract each page independently to prevent single page failures from blocking
  - Update all callers to handle list of images
  - _Requirements: 2.1, 2.4, 9.6_

- [x] 6.5 Write property test for partial page extraction
  - **Property 7: Partial page extraction**
  - **Validates: Requirements 2.4**

- [x] 6.6 Write property test for independent page extraction
  - **Property 10: Independent page extraction**
  - **Validates: Requirements 9.6**

- [x] 7. Implement AI service
  - Create AIService class with OpenAI SDK integration
  - Implement classify_document method
  - Add response parsing and validation
  - Handle API errors and rate limits
  - Implement timeout handling (30 seconds)
  - Use HTTPS with TLS 1.2+
  - Support corporate proxy configuration
  - _Requirements: 2.2, 2.3, 2.6, 12.1, 12.3, 12.4, 12.5_

- [x] 7.1 Write property test for image to API transmission
  - **Property 11: Multiple images to API transmission**
  - **Validates: Requirements 2.2**

- [x] 7.2 Write property test for response parsing
  - **Property 12: Response parsing**
  - **Validates: Requirements 2.3**

- [x] 7.3 Write property test for response validation
  - **Property 13: Response validation**
  - **Validates: Requirements 2.6**

- [x] 7.4 Write property test for rate limit handling
  - **Property 33: Rate limit handling**
  - **Validates: Requirements 12.1**

- [x] 7.5 Write property test for timeout handling
  - **Property 35: Timeout handling**
  - **Validates: Requirements 12.3**

- [x] 7.6 Write property test for TLS security
  - **Property 36: TLS security**
  - **Validates: Requirements 12.4**

- [x] 7.7 Write property test for API latency logging
  - **Property 42: API latency logging**
  - **Validates: Requirements 15.2**

- [x] 7.8 Update AI service to support multiple images
  - Modify classify_document to accept list[Image] instead of single Image
  - Update _encode_image to handle multiple images
  - Update API request to send all images in the message content
  - Test with 1, 2, and 3 images to ensure proper handling
  - _Requirements: 2.2_

- [x] 7.9 Add comprehensive document type support to AI service
  - Define SUPPORTED_DOCUMENT_TYPES constant with all 15 legal document types
  - Implement get_supported_document_types method
  - Update system prompt to include all supported document types
  - Ensure standardized document type names are returned
  - _Requirements: 16.1-16.17_

- [x] 7.10 Write property test for document type support
  - **Property 14: Document type support**
  - **Validates: Requirements 16.1-16.15, 16.17**

- [x] 7.11 Write property test for comprehensive prompt inclusion
  - **Property 15: Comprehensive prompt inclusion**
  - **Validates: Requirements 16.16**

- [x] 8. Implement file manager
  - Create FileManager class
  - Implement rename_file with conflict resolution
  - Add atomic file operations
  - Handle Windows file locking with retry
  - Implement temporary file management
  - Add file verification after operations
  - Implement cleanup with verification
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 13.1, 13.2, 13.3, 13.4, 13.5, 14.1, 14.2, 14.5_

- [x] 8.1 Write property test for filename structure
  - **Property 16: Filename structure**
  - **Validates: Requirements 3.1**

- [x] 8.2 Write property test for conflict resolution
  - **Property 17: Conflict resolution**
  - **Validates: Requirements 3.2**

- [x] 8.3 Write property test for file verification before cleanup
  - **Property 18: File verification before cleanup**
  - **Validates: Requirements 3.5, 14.5**

- [x] 8.4 Write property test for temporary file cleanup
  - **Property 37: Temporary file cleanup**
  - **Validates: Requirements 13.1, 13.2**

- [x] 8.5 Write property test for deletion verification
  - **Property 38: Deletion verification**
  - **Validates: Requirements 13.4**

- [x] 9. Implement file processor workflow coordinator
  - Create FileProcessor class
  - Implement process_file method coordinating full workflow
  - Add file validation
  - Coordinate PDF extraction, AI classification, and file renaming
  - Handle processing errors with proper classification
  - Track processing metrics (time, file size)
  - Ensure sequential processing to avoid parallel API calls
  - _Requirements: 2.1, 2.2, 2.3, 3.1, 6.4, 12.2, 15.1_

- [x] 9.1 Write property test for sequential processing
  - **Property 34: Sequential processing**
  - **Validates: Requirements 12.2**

- [x] 10. Implement directory watcher
  - Create DirectoryWatcher class using watchdog library
  - Implement file detection for "SCAN-" prefix
  - Add file stability checking (2 second unchanged size)
  - Implement debouncing for file events
  - Handle network drive monitoring
  - Detect watch directory unavailability
  - Queue files for processing via callback
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 14.3_

- [x] 10.1 Write property test for file detection timeliness
  - **Property 1: File detection timeliness**
  - **Validates: Requirements 1.1**

- [x] 10.2 Write property test for file stability waiting
  - **Property 2: File stability waiting**
  - **Validates: Requirements 1.2, 14.3**

- [x] 10.3 Write property test for multiple file queueing
  - **Property 3: Multiple file queueing**
  - **Validates: Requirements 1.3**

- [x] 10.4 Write property test for idle CPU usage
  - **Property 4: Idle CPU usage**
  - **Validates: Requirements 1.5**

- [x] 10.5 Update directory watcher to use configurable file prefix
  - Modify DirectoryWatcher to accept file_prefix parameter from configuration
  - Update file detection logic to use configurable prefix instead of hardcoded "SCAN-"
  - Ensure prefix is validated (non-empty, valid filename characters)
  - Update all tests to use configurable prefix
  - _Requirements: 1.1, 1.6_

- [x] 10.6 Write property test for configurable prefix detection
  - **Property 5: Configurable prefix detection**
  - **Validates: Requirements 1.6**

- [x] 11. Implement service orchestrator
  - Create ServiceOrchestrator class
  - Implement component initialization in correct order
  - Add start/stop methods with graceful shutdown
  - Implement health check scheduling (60 second interval)
  - Add health check logic (watch directory, config validation)
  - Handle component lifecycle coordination
  - Implement graceful shutdown with 30 second timeout
  - _Requirements: 4.3, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 11.1 Write property test for graceful shutdown timing
  - **Property 19: Graceful shutdown timing**
  - **Validates: Requirements 4.3**

- [x] 11.2 Write property test for health check interval
  - **Property 39: Health check interval**
  - **Validates: Requirements 10.1**

- [x] 11.3 Write property test for health check completeness
  - **Property 40: Health check completeness**
  - **Validates: Requirements 10.2, 10.3**

- [x] 11.4 Write property test for health check failure logging
  - **Property 41: Health check failure logging**
  - **Validates: Requirements 10.4**

- [x] 11.5 Write property test for memory usage logging
  - **Property 43: Memory usage logging**
  - **Validates: Requirements 15.3**

- [x] 11.6 Write property test for average processing time calculation
  - **Property 44: Average processing time calculation**
  - **Validates: Requirements 15.4**

- [x] 11.7 Write property test for error rate calculation
  - **Property 45: Error rate calculation**
  - **Validates: Requirements 15.5**

- [x] 12. Implement Windows service layer
  - Create ScannerWatcher2Service class using pywin32
  - Implement SvcStop and SvcDoRun methods
  - Add Windows Event Log integration for service events
  - Handle service lifecycle (start, stop, restart)
  - Implement service status reporting
  - Add command-line service management (--install-service, --start-service, --stop-service, --remove-service)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 12.1 Write property test for service start logging
  - **Property 20: Service start logging**
  - **Validates: Requirements 4.4, 7.5**

- [x] 12.2 Write property test for critical error logging
  - **Property 21: Critical error logging**
  - **Validates: Requirements 4.5, 7.3**

- [x] 13. Create main application entry point
  - Create main.py with application initialization
  - Wire all components together
  - Add command-line argument parsing
  - Support both service mode and console mode for development
  - Handle configuration loading and validation
  - Initialize logging before other components
  - _Requirements: All_

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Create PyInstaller specification
  - Create scanner_watcher2.spec file
  - Configure single-file executable bundling
  - Include config_template.json and README.txt
  - Add hidden imports for pywin32 modules
  - Configure Windows-specific settings (no console, icon)
  - Test executable build on clean Windows machine
  - _Requirements: 5.1_

- [x] 16. Create Inno Setup installer script
  - Create scanner_watcher2.iss file
  - Configure installation to C:\Program Files\ScannerWatcher2\
  - Add post-install script to create %APPDATA% directories
  - Configure service installation during setup
  - Add uninstall script to remove service
  - Create Start Menu shortcuts
  - Test installer on Windows 10 and Windows 11
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 17. Create configuration wizard
  - Implement interactive configuration setup
  - Prompt for watch directory path
  - Prompt for OpenAI API key
  - Prompt for log level
  - Validate inputs before saving
  - Save configuration to %APPDATA%\ScannerWatcher2\config.json
  - _Requirements: 8.2, 8.3_

- [x] 18. Create documentation
  - Write README.md with installation instructions
  - Document configuration options
  - Add troubleshooting guide
  - Create developer setup guide
  - Document Windows-specific requirements
  - _Requirements: All_

- [x] 19. Checkpoint - Ensure new feature tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [-] 20. Update documentation for new features
  - Document new document type categories in README.md
  - Document configurable file prefix in configuration guide
  - Document pages_to_extract configuration option
  - Add examples of supported document types
  - Update troubleshooting guide with multi-page extraction considerations
  - _Requirements: 1.6, 2.1, 2.4, 16.1-16.17_

- [x] 21. Final checkpoint - Complete system test
  - Ensure all tests pass, ask the user if questions arise.
