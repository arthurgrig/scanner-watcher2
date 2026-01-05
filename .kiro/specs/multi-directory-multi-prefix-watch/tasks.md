# Implementation Plan: Multi-Directory Multi-Prefix Watch

## Overview

This implementation plan breaks down the multi-directory and multi-prefix watch feature into discrete coding tasks. The approach prioritizes backward compatibility, ensuring existing configurations continue to work while enabling the new functionality. Tasks are ordered to build incrementally, with testing integrated throughout.

## Tasks

- [x] 1. Update ProcessingConfig to support multiple file prefixes
  - Rename `file_prefix` field to `file_prefixes` with list type
  - Update field validator to validate all prefixes in the list
  - Add model validator to convert legacy `file_prefix` to `file_prefixes` array
  - Update default value to be a list containing "SCAN-"
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 4.2_

- [ ]* 1.1 Write property test for prefix list validation
  - **Property 1: Configuration accepts list of file prefixes**
  - **Validates: Requirements 1.1**

- [ ]* 1.2 Write property test for invalid character rejection
  - **Property 3: Invalid prefix characters are rejected**
  - **Validates: Requirements 1.3**

- [ ]* 1.3 Write property test for duplicate prefix acceptance
  - **Property 4: Duplicate prefixes are accepted**
  - **Validates: Requirements 1.5**

- [ ]* 1.4 Write property test for legacy prefix conversion
  - **Property 10: Legacy single-value format is converted**
  - **Validates: Requirements 4.2**

- [ ]* 1.5 Write unit test for empty prefix list rejection
  - Test that empty list raises ValidationError
  - _Requirements: 1.4_

- [x] 2. Update Config to support multiple watch directories
  - Rename `watch_directory` field to `watch_directories` with list type
  - Update field validator to validate all paths in the list
  - Add model validator to convert legacy `watch_directory` to `watch_directories` array
  - Ensure minimum length of 1 for the list
  - _Requirements: 2.1, 2.3, 2.4, 4.1_

- [ ]* 2.1 Write property test for directory list validation
  - **Property 5: Configuration accepts list of watch directories**
  - **Validates: Requirements 2.1**

- [ ]* 2.2 Write property test for absolute path requirement
  - **Property 7: Only absolute paths are accepted**
  - **Validates: Requirements 2.3**

- [ ]* 2.3 Write property test for legacy directory conversion
  - **Property 10: Legacy single-value format is converted**
  - **Validates: Requirements 4.1**

- [ ]* 2.4 Write unit test for empty directory list rejection
  - Test that empty list raises ValidationError
  - _Requirements: 2.4_

- [x] 3. Update DirectoryWatcher to accept multiple prefixes
  - Change `file_prefix` parameter to `file_prefixes` (list type)
  - Update `_ScanFileEventHandler` to check if filename starts with ANY prefix
  - Modify `on_created` and `on_modified` methods to use `any()` with prefix list
  - Store matched prefix for logging purposes
  - _Requirements: 1.2_

- [ ]* 3.1 Write property test for multi-prefix file detection
  - **Property 2: File detection matches any configured prefix**
  - **Validates: Requirements 1.2**

- [ ]* 3.2 Write unit tests for prefix matching logic
  - Test single prefix matching
  - Test multiple prefix matching
  - Test no prefix matching
  - _Requirements: 1.2_

- [x] 4. Update ServiceOrchestrator to manage multiple watchers
  - Change `directory_watcher` to `directory_watchers` (list type)
  - Update `start()` to create one watcher per configured directory
  - Update `stop()` to stop all watchers in the list
  - Add logging for each watcher startup with directory and prefixes
  - _Requirements: 2.2, 6.1, 6.2, 7.1, 7.2_

- [ ]* 4.1 Write property test for watcher count
  - **Property 6: Watcher count equals directory count**
  - **Validates: Requirements 2.2, 6.1**

- [ ]* 4.2 Write property test for watcher shutdown
  - **Property 16: All watchers are stopped on shutdown**
  - **Validates: Requirements 6.2**

- [ ]* 4.3 Write property test for shared callback
  - **Property 9: All watchers use same processing pipeline**
  - **Validates: Requirements 2.6, 6.3**

- [ ]* 4.4 Write unit tests for orchestrator lifecycle
  - Test starting with multiple directories
  - Test stopping all watchers
  - Test callback invocation from different watchers
  - _Requirements: 2.2, 6.1, 6.2, 2.6, 6.3_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Update health check to validate all directories
  - Modify `health_check()` to iterate over all watch directories
  - Create directory status dictionary with accessibility for each directory
  - Set `all_accessible` flag based on all directories being accessible
  - Update health status to use `all_accessible` flag
  - Include individual directory status in details
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ]* 6.1 Write property test for health check validation
  - **Property 12: Health check validates all directories**
  - **Validates: Requirements 5.1**

- [ ]* 6.2 Write property test for unhealthy status with inaccessible directory
  - **Property 13: Inaccessible directory causes unhealthy status**
  - **Validates: Requirements 5.2**

- [ ]* 6.3 Write property test for health check details
  - **Property 14: Health check details include all directories**
  - **Validates: Requirements 5.3**

- [ ]* 6.4 Write property test for healthy status with all accessible
  - **Property 15: All accessible directories yield healthy status**
  - **Validates: Requirements 5.4**

- [ ]* 6.5 Write unit tests for health check scenarios
  - Test all directories accessible
  - Test some directories inaccessible
  - Test all directories inaccessible
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Add enhanced logging for file detection
  - Update `_process_file_callback` to log source directory
  - Update `DirectoryWatcher` to track and log matched prefix
  - Ensure logs include both directory path and matched prefix
  - _Requirements: 7.3, 7.4_

- [ ]* 7.1 Write property test for directory logging
  - **Property 20: Detection logs include source directory**
  - **Validates: Requirements 7.3**

- [ ]* 7.2 Write property test for prefix logging
  - **Property 21: Detection logs include matched prefix**
  - **Validates: Requirements 7.4**

- [ ]* 7.3 Write unit tests for logging content
  - Test log entries contain directory path
  - Test log entries contain matched prefix
  - _Requirements: 7.3, 7.4_

- [x] 8. Update configuration template
  - Change `watch_directory` to `watch_directories` array in config_template.json
  - Change `file_prefix` to `file_prefixes` array in config_template.json
  - Add comments explaining the array format
  - Include multiple example entries
  - _Requirements: 3.1, 3.2_

- [x] 9. Handle non-existent directories gracefully
  - Update orchestrator to check directory existence before creating watcher
  - Log warning for non-existent directories but continue with others
  - Ensure at least one valid directory exists before proceeding
  - _Requirements: 2.5_

- [ ]* 9.1 Write property test for non-existent directory handling
  - **Property 8: Non-existent directories don't prevent startup**
  - **Validates: Requirements 2.5**

- [ ]* 9.2 Write unit tests for directory existence handling
  - Test startup with all directories existing
  - Test startup with some directories missing
  - Test startup with all directories missing (should fail)
  - _Requirements: 2.5_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 11. Write integration test for multi-directory watch
  - Test multiple watchers detecting files simultaneously
  - Test files with different prefixes in different directories
  - Test concurrent file processing from multiple directories
  - **Property 17: Concurrent file detection is thread-safe**
  - **Validates: Requirements 6.4**

- [ ]* 12. Write property tests for logging
  - **Property 18: Startup logs all directories**
  - **Property 19: Startup logs all prefixes**
  - **Validates: Requirements 7.1, 7.2**

- [ ]* 13. Write property test for array format preservation
  - **Property 11: New array format is preserved**
  - **Validates: Requirements 4.3**

- [x] 14. Update existing tests to use new field names
  - Search for references to `watch_directory` in tests and update to `watch_directories`
  - Search for references to `file_prefix` in tests and update to `file_prefixes`
  - Ensure all existing tests pass with new configuration structure
  - _Requirements: All_

- [x] 15. Final checkpoint - Full test suite
  - Run complete test suite (unit, property, integration)
  - Verify all tests pass
  - Check code coverage meets project standards
  - Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end functionality
- Backward compatibility is maintained throughout via model validators
