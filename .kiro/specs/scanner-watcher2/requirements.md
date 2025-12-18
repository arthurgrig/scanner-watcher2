# Requirements Document

## Introduction

Scanner-Watcher2 is a Windows-first legal document processing system that monitors directories for scanned documents, uses AI to classify them, and organizes files intelligently. The system operates as a native Windows service with zero-dependency installation, providing production-ready document processing with proper error handling, logging, and recovery mechanisms.

## Glossary

- **System**: The Scanner-Watcher2 application
- **Watch Directory**: A filesystem directory monitored by the System for new documents
- **Scan File**: A PDF file with the configured file prefix in the Watch Directory
- **File Prefix**: A configurable string prefix used to identify files for processing (default: "SCAN-")
- **Document Classification**: The process of identifying document type using AI analysis
- **Processing Workflow**: The complete sequence of detecting, extracting, classifying, and renaming a document
- **Windows Service**: A native Windows background process managed by Windows Services Manager
- **Service Orchestrator**: The main application coordinator component
- **PDF Processor**: The component responsible for extracting pages from PDF documents
- **AI Service**: The component that interfaces with OpenAI API for document classification
- **File Manager**: The component handling file operations and renaming
- **Configuration File**: JSON file stored in %APPDATA%\ScannerWatcher2\config.json
- **Transient Error**: A temporary error condition that may succeed on retry
- **Permanent Error**: An error condition that will not succeed on retry
- **Circuit Breaker**: A pattern that prevents repeated calls to a failing service

## Requirements

### Requirement 1

**User Story:** As a legal office administrator, I want the system to automatically detect new scanned documents, so that I don't have to manually trigger processing.

#### Acceptance Criteria

1. WHEN a file with the configured File Prefix is created in the Watch Directory THEN the System SHALL detect the file within 5 seconds
2. WHEN a file is still being written to disk THEN the System SHALL wait until the file is stable before processing
3. WHEN multiple files are detected simultaneously THEN the System SHALL queue all files for processing
4. WHEN the Watch Directory is on a network drive THEN the System SHALL monitor the directory successfully
5. WHILE the System is monitoring THEN the System SHALL consume less than 5% CPU during idle periods
6. WHEN the File Prefix is configured in the Configuration File THEN the System SHALL use that prefix for file detection

### Requirement 2

**User Story:** As a legal office administrator, I want documents to be classified by AI, so that they are automatically organized by document type.

#### Acceptance Criteria

1. WHEN a Scan File is detected THEN the System SHALL extract the first three pages as images
2. WHEN the first three page images are extracted THEN the System SHALL send the images to OpenAI API for classification
3. WHEN OpenAI returns a classification THEN the System SHALL parse the document type from the response
4. WHEN a PDF has fewer than three pages THEN the System SHALL extract all available pages
5. WHEN a PDF is corrupted THEN the System SHALL log the error and skip the file
6. WHEN the AI Service receives a classification response THEN the System SHALL validate the response format before processing

### Requirement 3

**User Story:** As a legal office administrator, I want processed documents to be renamed with meaningful names, so that I can easily identify documents without opening them.

#### Acceptance Criteria

1. WHEN a document is classified THEN the System SHALL rename the file to include the date, document type, and relevant identifiers
2. WHEN a file with the target name already exists THEN the System SHALL append a unique suffix to prevent overwriting
3. WHEN renaming a file THEN the System SHALL perform the operation atomically to prevent partial renames
4. WHEN a file is locked by another process THEN the System SHALL retry the rename operation up to 3 times
5. WHEN the renamed file is created THEN the System SHALL verify the file is accessible before deleting temporary files

### Requirement 4

**User Story:** As a system administrator, I want the application to run as a native Windows service, so that it starts automatically and runs reliably in the background.

#### Acceptance Criteria

1. WHEN the System is installed THEN the System SHALL register as a Windows service
2. WHEN Windows starts THEN the System SHALL start automatically without user intervention
3. WHEN the service is stopped via Windows Services Manager THEN the System SHALL shut down gracefully within 30 seconds
4. WHEN the service starts THEN the System SHALL log a start event to Windows Event Log
5. WHEN the service encounters a critical error THEN the System SHALL log the error to Windows Event Log before stopping

### Requirement 5

**User Story:** As a system administrator, I want a single-click installer, so that deployment is simple and requires no technical expertise.

#### Acceptance Criteria

1. WHEN the installer runs THEN the System SHALL install all files to C:\Program Files\ScannerWatcher2\ without requiring Python installation
2. WHEN the installer completes THEN the System SHALL create %APPDATA%\ScannerWatcher2\ directory structure
3. WHEN the installer completes THEN the System SHALL copy the default configuration template to the user data directory
4. WHEN the installer completes THEN the System SHALL register the Windows service automatically
5. WHEN the uninstaller runs THEN the System SHALL remove all installed files and registry entries

### Requirement 6

**User Story:** As a system administrator, I want comprehensive error handling, so that temporary issues don't cause the system to fail permanently.

#### Acceptance Criteria

1. WHEN a Transient Error occurs THEN the System SHALL retry the operation with exponential backoff up to 3 attempts
2. WHEN a Permanent Error occurs THEN the System SHALL skip the file and log the error without retrying
3. WHEN the OpenAI API fails 5 times within 60 seconds THEN the System SHALL open the Circuit Breaker and wait 5 minutes before retrying
4. WHEN a file processing error occurs THEN the System SHALL continue processing other files in the queue
5. WHEN an error is logged THEN the System SHALL include context information such as file path, error type, and correlation ID

### Requirement 7

**User Story:** As a system administrator, I want detailed logging, so that I can troubleshoot issues and monitor system health.

#### Acceptance Criteria

1. WHEN the System performs any operation THEN the System SHALL write structured JSON logs to %APPDATA%\ScannerWatcher2\logs\
2. WHEN a log file reaches 10MB THEN the System SHALL rotate the log file and keep 5 backup files
3. WHEN a critical error occurs THEN the System SHALL write an entry to Windows Event Log
4. WHEN a file is processed successfully THEN the System SHALL log the processing time, file size, and document type
5. WHEN the System starts or stops THEN the System SHALL log service lifecycle events to Windows Event Log

### Requirement 8

**User Story:** As a system administrator, I want secure configuration management, so that sensitive information like API keys is protected.

#### Acceptance Criteria

1. WHEN the Configuration File is created THEN the System SHALL store the OpenAI API key encrypted using Windows DPAPI
2. WHEN the Configuration File is loaded THEN the System SHALL validate all required fields are present
3. WHEN the Watch Directory path is invalid THEN the System SHALL log an error and refuse to start
4. WHEN the configuration is updated THEN the System SHALL reload the configuration without requiring a service restart
5. WHERE the Configuration File is missing THEN the System SHALL create a default configuration with placeholder values

### Requirement 9

**User Story:** As a legal office administrator, I want the system to handle various PDF formats, so that all scanned documents can be processed regardless of how they were created.

#### Acceptance Criteria

1. WHEN a PDF is processed THEN the System SHALL attempt extraction using PyMuPDF as the primary method
2. IF PyMuPDF fails THEN the System SHALL attempt extraction using PyPDF2 as a fallback
3. WHEN extracting page images THEN the System SHALL optimize each image size to reduce API transmission time
4. WHEN a PDF has no pages THEN the System SHALL log an error and skip the file
5. WHEN processing a PDF THEN the System SHALL limit memory usage to prevent system resource exhaustion
6. WHEN extracting multiple pages THEN the System SHALL handle each page extraction independently to prevent single page failures from blocking the entire process

### Requirement 10

**User Story:** As a system administrator, I want the system to perform health checks, so that I can monitor system status and detect issues early.

#### Acceptance Criteria

1. WHILE the System is running THEN the System SHALL perform health checks every 60 seconds
2. WHEN a health check runs THEN the System SHALL verify the Watch Directory is accessible
3. WHEN a health check runs THEN the System SHALL verify the Configuration File is valid
4. WHEN a health check fails THEN the System SHALL log a warning with details about the failure
5. WHEN consecutive health checks fail 3 times THEN the System SHALL log a critical error to Windows Event Log

### Requirement 11

**User Story:** As a developer, I want comprehensive test coverage, so that the system is reliable and regressions are caught early.

#### Acceptance Criteria

1. WHEN unit tests are executed THEN the System SHALL achieve greater than 90% code coverage
2. WHEN integration tests are executed THEN the System SHALL test all critical processing paths
3. WHEN Windows-specific tests are executed THEN the System SHALL verify service installation, path handling, and event log integration
4. WHEN end-to-end tests are executed THEN the System SHALL process a sample document through the complete workflow
5. WHEN tests use external dependencies THEN the System SHALL mock only external APIs while using real filesystem operations

### Requirement 12

**User Story:** As a system administrator, I want the system to respect API rate limits, so that the OpenAI account is not suspended or throttled.

#### Acceptance Criteria

1. WHEN the OpenAI API returns a rate limit error THEN the System SHALL wait the specified retry-after duration before retrying
2. WHEN multiple files are queued THEN the System SHALL process them sequentially to avoid parallel API calls
3. WHEN an API call times out after 30 seconds THEN the System SHALL log the timeout and retry according to the retry policy
4. WHEN API calls are made THEN the System SHALL use HTTPS with TLS 1.2 or higher
5. WHERE a corporate proxy is configured THEN the System SHALL route API calls through the proxy

### Requirement 13

**User Story:** As a legal office administrator, I want temporary files to be cleaned up automatically, so that disk space is not wasted.

#### Acceptance Criteria

1. WHEN a document is processed successfully THEN the System SHALL delete all temporary files created during processing
2. WHEN a document processing fails THEN the System SHALL delete temporary files after logging the error
3. WHEN the System starts THEN the System SHALL clean up any temporary files from previous sessions
4. WHEN temporary files are deleted THEN the System SHALL verify deletion was successful
5. WHERE a temporary directory is not configured THEN the System SHALL use %APPDATA%\ScannerWatcher2\temp\ as the default

### Requirement 14

**User Story:** As a system administrator, I want the system to handle Windows file locking gracefully, so that processing continues even when files are temporarily locked.

#### Acceptance Criteria

1. WHEN a file is locked by another process THEN the System SHALL retry the operation after a delay
2. WHEN a file remains locked after 3 retry attempts THEN the System SHALL skip the file and log an error
3. WHEN checking if a file is stable THEN the System SHALL verify the file size has not changed for 2 seconds
4. WHEN a file operation fails with a sharing violation THEN the System SHALL treat it as a Transient Error
5. WHEN a file is successfully accessed THEN the System SHALL release the file handle immediately after use

### Requirement 15

**User Story:** As a system administrator, I want performance metrics logged, so that I can identify bottlenecks and optimize system performance.

#### Acceptance Criteria

1. WHEN a file is processed THEN the System SHALL log the total processing time in milliseconds
2. WHEN an API call is made THEN the System SHALL log the API response latency
3. WHEN the System is running THEN the System SHALL log memory usage during health checks
4. WHEN files are processed THEN the System SHALL calculate and log the average processing time per hour
5. WHEN errors occur THEN the System SHALL calculate and log the error rate as a percentage of total files processed

### Requirement 16

**User Story:** As a legal office administrator, I want the system to recognize a comprehensive set of legal document types, so that all common documents in my workflow are properly classified and organized.

#### Acceptance Criteria

1. WHEN the AI Service classifies a document THEN the System SHALL support identification of Panel List documents
2. WHEN the AI Service classifies a document THEN the System SHALL support identification of QME Appointment Notification Form documents
3. WHEN the AI Service classifies a document THEN the System SHALL support identification of Agreed Medical Evaluator Report documents
4. WHEN the AI Service classifies a document THEN the System SHALL support identification of Qualified Medical Evaluator Report documents
5. WHEN the AI Service classifies a document THEN the System SHALL support identification of PTP Initial Report documents
6. WHEN the AI Service classifies a document THEN the System SHALL support identification of PTP P&S Report documents
7. WHEN the AI Service classifies a document THEN the System SHALL support identification of RFA (Request for Authorization) documents
8. WHEN the AI Service classifies a document THEN the System SHALL support identification of UR Approval documents
9. WHEN the AI Service classifies a document THEN the System SHALL support identification of UR Denial documents
10. WHEN the AI Service classifies a document THEN the System SHALL support identification of Modified UR documents
11. WHEN the AI Service classifies a document THEN the System SHALL support identification of Finding and Award documents
12. WHEN the AI Service classifies a document THEN the System SHALL support identification of Finding & Order documents
13. WHEN the AI Service classifies a document THEN the System SHALL support identification of Advocacy/Cover Letter documents
14. WHEN the AI Service classifies a document THEN the System SHALL support identification of Declaration of Readiness to Proceed documents
15. WHEN the AI Service classifies a document THEN the System SHALL support identification of Objection to Declaration of Readiness to Proceed documents
16. WHEN the AI Service provides classification instructions to the AI model THEN the System SHALL include all supported document types in the prompt
17. WHEN a document matches one of the supported types THEN the System SHALL return the standardized document type name in the classification result
