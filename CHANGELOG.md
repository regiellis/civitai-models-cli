# Changelog

All notable changes to this project will be documented in this file.
## [0.7.5] - 2024-08-30
- **Hotfix**: Fixed details for versions not pulling from site.

## [0.7.9] - 2024-08-30
- **Feature**:  "Abilty to create a .env file if one doesnt exist on first run"

## [0.7.8] - 2024-08-30
- **Feature**:  "Added Dockerfile; Lowered reqs for python "

## [0.7.7] - 2024-08-29
- **Feature**:  "More Detail options and New Search Logic"

## [0.7.6] - 2024-08-28
- **Feaeture**: Added a new local search feature to search for models in the local model directory.

## [0.7.5] - 2024-08-21
- **Hotfix**: Removed unused imports and cleaned up the code for better maintainability and readability.

## [0.7.4] - 2024-08-21
- **Windows Fixes**: Odds and Ends to get everything working on windows.

## [0.7.3] - 2024-08-21
- **PyPI Naming Fix**: Fixed naming of internal package so that tool can be uploaded to PyPI.

## [0.7.2] - 2024-08-21
- **Version Bump**: v0.7.1 to v0.7.2

## [0.7.1] - 2024-08-21
- **Hotfix**: Remove all instances of request and replaced with httpx to avoid conflicts with other libraries.

## [0.7.0] - 2024-08-20
- **Documentation**: Created `CHANGELOG.md` to summarize updates from version 0.1 to 0.7.0, providing a clear history of changes for users.
- **Testing**: 
  - Added detailed tests for CLI commands using Typer, ensuring that all commands function as expected.
  - Fixed an undefined name error in the `test_app` function, improving test reliability and coverage.
- **Features**: Introduced an upgrade option in the download module, allowing users to update existing models if a newer version is available.
- **Enhancements**:
  - Refactored the search module to include options for pagination, enabling users to navigate through search results more easily.
  - Added functionality to download models directly from search results, streamlining the user experience.
  - Removed unused imports and cleaned up the code for better maintainability and readability.

## [0.6.5] - 2024-08-17
- **Documentation**: Updated `README.md` to reflect recent changes and improvements in the project, ensuring users have access to the latest information.
- **Dependencies**: 
  - Updated `requirements.txt` to include any new dependencies needed for the project.
  - Updated `pyproject.toml` to ensure consistency in package management and project configuration.

## [0.6.4] - 2024-08-16
- **Hotfix**: Addressed issues from the v0.6.2 release that caused functionality problems, ensuring that the application runs smoothly.

## [0.6.3] - 2024-08-15
- **Hotfix**: Temporarily removed a prompt feature that was causing issues, allowing users to continue using the application without interruptions.

## [0.6.1] - 2024-08-14
- **Feature**: Updated the Civitai Model Manager CLI to version 6.0.1, incorporating new features and improvements from the latest release.

## [0.6.0] - 2024-08-13
- **Features**: 
  - Enhanced the "stats" command to provide more detailed breakdowns by model and directory, including total size and number of files.
  - Moved the stats command to its own file for better organization.
  - Created helper functions to simplify the codebase and improve readability.
  - Adjusted table colors in the output to enhance readability for users.

## [0.5.2] - 2024-08-11
- **Fixes**: Resolved issues with downloading variant models and added support for additional file types, ensuring a smoother user experience.

## [0.5.1] - 2024-08-10
- **Fixes**: 
  - Addressed installation issues in `pyproject.toml` that were preventing proper installation of the package.
  - Fixed broken f-strings in the code, improving string formatting and output accuracy.

## [0.5.0] - 2024-08-09
- **Refactor**: 
  - Major refactor of the project structure to modernize the codebase, making it easier to maintain and extend.
  - Moved source code to a `src` directory for better organization.
  - Updated `README.md` to reflect the new project structure and provide clearer instructions for users.

## [0.3.1] - 2024-08-07
- **Fixes**: Improved the loading of the `.env` file, including support for macOS, ensuring that environment variables are read correctly across platforms.

## [3.0] - 2024-08-06
- **Feature**: Added search capabilities that allow users to search for models using any model ID, enhancing the flexibility and usability of the application.

## [0.2] - 2024-08-05
- **Feature**: 
  - Implemented the initial functionality for the Civitai Model Manager CLI, enabling users to list available models and their details.
  - Added model download and removal features, enhancing user control over model management.
  - Introduced model summarization using Ollama and OpenAI services, improving the information provided to users.
  - Enhanced error handling and user prompts for a better user experience.
  - Added sanity checks for environment variables to ensure proper configuration.

## [0.1] - 2024-08-04
- **Initial Release**: Established the initial codebase for the project, laying the foundation for future development and enhancements.
