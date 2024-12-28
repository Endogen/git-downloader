# Git Repository Downloader

This Python script allows you to clone a GitHub repository and combine all its files into a single text file. It's specifically designed to create a compact, AI-friendly representation of a codebase, making it easier to share code with AI models like ChatGPT or Claude.

The script strips away non-essential files and folders, combines all relevant code into a single text file, and adds clear file path headers for context. This results in a format that's both efficient for token usage and maintains the necessary context for AI analysis.

## Features

- Clone specific branches from GitHub repositories
- Combine all repository files into a single text file with clear file path headers
- Smart file type filtering
- Configurable file size limits
- Optional processing statistics
- Skip specific folders and files
- Command-line interface with configuration file support

## Requirements

- Python 3.6+
- Git installed and accessible from command line

## Output Format

For each file included in the output, the script adds a header with the file's path and name:

```
============================================================
FILE: src/main.py
============================================================
[content of main.py]

============================================================
FILE: src/utils/helpers.py
============================================================
[content of helpers.py]
```

This format ensures that AI models can understand the context and structure of your codebase while keeping the token count minimal.

## Usage

Basic usage:
```bash
python download.py https://github.com/user/repo.git
```

With options:
```bash
python download.py https://github.com/user/repo.git \
    --config custom_config.json \
    --branch main \
    --output custom_name.txt \
    --exclude docs tests \
    --max-file-size 2.0 \
    --stats
```

### Command Line Options

- `repo_url`: URL of the GitHub repository to clone (required)
- `--config`, `-c`: Path to config file (default: config.json)
- `--branch`, `-b`: Which branch to clone (overrides config's default_branch)
- `--output`, `-o`: Custom name for output file
- `--exclude`, `-e`: Additional folders to exclude (added to skip_folders from config)
- `--max-file-size`: Maximum file size in MB (overrides config value)
- `--stats`: Show processing statistics (file counts, sizes, etc.)
- `--include-binary`: Include binary files (base64 encoded)

## Configuration

The repository includes a default `config.json` file. If no custom config file is provided via the `--config` option, the script will first try to use this default config. If the config file is not found, the script will use built-in default values.

The config file has the following structure:

```json
{
  "default_branch": "main",
  "extensions": [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".c", ".cpp", ".cs", ".rb",
    ".go", ".php", ".html", ".css", ".scss",
    ".json", ".md", ".yml", ".yaml"
  ],
  "skip_folders": [
    ".git",
    ".github",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv"
  ],
  "skip_files": [
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "LICENSE.rst",
    "COPYING",
    "COPYING.txt"
  ],
  "download_folder": "repos",
  "max_file_size_mb": 1.0
}
```

### Configuration Options

- `default_branch`: Default branch to clone if not specified via command line
- `extensions`: List of file extensions to include (empty list includes all files)
- `skip_folders`: Folders to exclude from processing
- `skip_files`: Specific files to exclude
- `download_folder`: Where to save the output text file
- `max_file_size_mb`: Maximum size for individual files in MB

### Notes

- Files without extensions (like LICENSE, README, Makefile) are always included
- The script creates a subfolder (specified by download_folder) in your current directory
- Binary files are skipped by default unless --include-binary is used
- Files using UTF-8 encoding are supported
- Files larger than max_file_size_mb are skipped
- Temporary files are cleaned up after processing
- All paths in the config file should be relative to the repository root

## Example

To download a repository and exclude its documentation and test folders, while also getting processing statistics:

```bash
python download.py https://github.com/user/repo.git --exclude docs tests --stats
```

This will:
1. Clone the repository
2. Remove excluded folders
3. Combine all remaining files into a single text file with path headers
4. Show statistics about processed files
5. Save the result in the configured download folder
6. Clean up temporary files