# Requirements Document

## Introduction

This feature enhances Scanner-Watcher2's file detection capabilities by allowing multiple file prefixes and multiple watch directories. Currently, the system monitors a single directory for files with a single prefix (e.g., "SCAN-"). This enhancement enables monitoring multiple directories simultaneously and detecting files with any of several configured prefixes, providing greater flexibility for diverse scanning workflows.

## Glossary

- **Watch_Directory**: A filesystem directory monitored for new files to process
- **File_Prefix**: A string at the beginning of a filename that identifies it as a candidate for processing (e.g., "SCAN-", "DOC-", "IMG-")
- **Directory_Watcher**: The component responsible for monitoring filesystem changes
- **Service_Orchestrator**: The component that coordinates all application components
- **Config**: The Pydantic model representing application configuration
- **Processing_Config**: The Pydantic model representing document processing configuration

## Requirements

### Requirement 1: Multiple File Prefix Support

**User Story:** As a user, I want to configure multiple file prefixes to monitor, so that I can process files from different scanners or sources that use different naming conventions.

#### Acceptance Criteria

1. WHEN the configuration is loaded, THE Processing_Config SHALL accept a list of file prefixes instead of a single string
2. WHEN a file is created in a watch directory, THE Directory_Watcher SHALL detect it if its name starts with ANY of the configured prefixes
3. WHEN validating file prefixes, THE Processing_Config SHALL ensure each prefix is non-empty and contains only valid filename characters
4. WHEN no file prefixes are configured, THE Processing_Config SHALL reject the configuration with a validation error
5. WHEN duplicate prefixes are provided, THE Processing_Config SHALL accept them without error (duplicates are harmless)

### Requirement 2: Multiple Watch Directory Support

**User Story:** As a user, I want to configure multiple directories to monitor, so that I can process scanned documents from different locations without running multiple instances of the application.

#### Acceptance Criteria

1. WHEN the configuration is loaded, THE Config SHALL accept a list of watch directories instead of a single path
2. WHEN the Service_Orchestrator starts, THE System SHALL create a separate Directory_Watcher instance for each configured watch directory
3. WHEN validating watch directories, THE Config SHALL ensure each path is absolute
4. WHEN no watch directories are configured, THE Config SHALL reject the configuration with a validation error
5. WHEN a watch directory does not exist at startup, THE System SHALL log a warning but continue monitoring other directories
6. WHEN a file is detected in any watch directory, THE System SHALL process it using the same processing pipeline

### Requirement 3: Configuration File Format

**User Story:** As a user, I want the configuration file to clearly represent multiple directories and prefixes, so that I can easily understand and modify my configuration.

#### Acceptance Criteria

1. WHEN the configuration template is provided, THE System SHALL show watch_directories as a JSON array of strings
2. WHEN the configuration template is provided, THE System SHALL show file_prefixes as a JSON array of strings within the processing section
3. WHEN loading configuration, THE Config SHALL accept both legacy single-value format and new array format for backward compatibility
4. WHEN saving configuration, THE Config SHALL always use the array format for both watch_directories and file_prefixes

### Requirement 4: Backward Compatibility

**User Story:** As an existing user, I want my current configuration to continue working, so that I don't need to manually update my config.json file after upgrading.

#### Acceptance Criteria

1. WHEN a configuration file contains watch_directory as a single string, THE Config SHALL convert it to a single-element array
2. WHEN a configuration file contains file_prefix as a single string, THE Processing_Config SHALL convert it to a single-element array
3. WHEN a configuration file uses the new array format, THE Config SHALL load it without conversion
4. WHEN the configuration wizard runs, THE System SHALL prompt for multiple directories and prefixes using the new format

### Requirement 5: Health Check Updates

**User Story:** As a system administrator, I want health checks to validate all watch directories, so that I can identify configuration or filesystem issues across all monitored locations.

#### Acceptance Criteria

1. WHEN a health check is performed, THE Service_Orchestrator SHALL verify accessibility of ALL configured watch directories
2. WHEN any watch directory is inaccessible, THE Health_Status SHALL report the system as unhealthy
3. WHEN health check details are logged, THE System SHALL include the status of each individual watch directory
4. WHEN all watch directories are accessible, THE Health_Status SHALL report the system as healthy

### Requirement 6: Orchestrator Lifecycle Management

**User Story:** As a developer, I want the orchestrator to properly manage multiple directory watchers, so that all resources are correctly initialized and cleaned up.

#### Acceptance Criteria

1. WHEN the Service_Orchestrator starts, THE System SHALL initialize one Directory_Watcher for each configured watch directory
2. WHEN the Service_Orchestrator stops, THE System SHALL stop all Directory_Watcher instances
3. WHEN a Directory_Watcher callback is triggered, THE System SHALL process the file regardless of which directory it came from
4. WHEN multiple files are detected simultaneously across different directories, THE System SHALL process them concurrently without conflicts

### Requirement 7: Logging and Observability

**User Story:** As a system administrator, I want clear logging about which directories are being monitored and which prefixes are active, so that I can troubleshoot configuration issues.

#### Acceptance Criteria

1. WHEN the Service_Orchestrator starts, THE System SHALL log all configured watch directories
2. WHEN the Service_Orchestrator starts, THE System SHALL log all configured file prefixes
3. WHEN a file is detected, THE System SHALL log which watch directory it was found in
4. WHEN a file is detected, THE System SHALL log which prefix matched the filename
