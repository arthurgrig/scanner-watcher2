# Product Overview

Scanner-Watcher2 is a Windows-native legal document processing system that automates document classification and organization.

## Core Functionality

The system monitors designated directories for scanned documents (PDFs with "SCAN-" prefix), uses OpenAI GPT-4 Vision to classify document types, and automatically renames files with meaningful names based on classification results.

## Key Features

- **Automatic Detection**: Monitors directories for new scanned documents using Windows filesystem APIs
- **AI Classification**: Leverages GPT-4 Vision to identify document types (medical reports, court orders, etc.)
- **Intelligent Organization**: Renames files with structured names including date, document type, and identifiers
- **Windows Service**: Runs as native Windows service with automatic startup and lifecycle management
- **Production-Ready**: Comprehensive error handling, retry logic with exponential backoff, and circuit breakers
- **Secure Configuration**: API keys encrypted using Windows DPAPI
- **Enterprise Logging**: Structured JSON logs with Windows Event Log integration

## Target Platform

Windows 10, Windows 11, and Windows Server 2019+ with Python 3.12+ for development. End-user deployment uses bundled Python runtime requiring no prerequisites.

## Design Principles

1. **Windows-First**: Native Windows service, standard Windows paths, single-click installer
2. **Zero-Dependency Installation**: Bundled Python runtime, no prerequisites for end users
3. **Production-Ready**: Proper error handling, logging, and recovery mechanisms
4. **Maintainable**: Clean architecture with clear separation of concerns
