# Git Repository Downloader

This Python script allows you to clone a GitHub repository and combine all its files into a single text file. It provides configuration options to control which files and folders should be included or excluded from the final output.

## Features

- Clone specific branches from GitHub repositories
- Combine all repository files into a single text file
- Configure which file types to include via extensions
- Skip specific folders and files
- Command-line interface with configuration file support

## Requirements

- Python 3.6+
- Git installed and accessible from command line

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
    --exclude docs tests
```

### Command Line Options

- `repo_url`: URL of the GitHub repository to clone (required)
- `--config`, `-c`: Path to config file (default: config.json)
- `--branch`, `-b`: Which branch to clone (overrides config's default_branch)
- `--output`, `-o`: Custom name for output file
- `--exclude`, `-e`: Additional folders to exclude (added to skip_folders from config)

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
  "download_folder": "repos"
}
```

### Configuration Options

- `default_branch`: Default branch to clone if not specified via command line
- `extensions`: List of file extensions to include (empty list includes all files)
- `skip_folders`: Folders to exclude from processing
- `skip_files`: Specific files to exclude
- `download_folder`: Where to save the output text file

### Notes

- Files without extensions (like LICENSE, README, Makefile) are always included
- The script creates a subfolder (specified by download_folder) in your current directory
- Temporary files are cleaned up after processing
- All paths in the config file should be relative to the repository root

## Example

To download a repository and exclude its documentation and test folders:

```bash
python download.py https://github.com/user/repo.git --exclude docs tests
```

This will:
1. Clone the repository
2. Remove excluded folders
3. Combine all remaining files into a single text file
4. Save the result in the configured download folder
5. Clean up temporary files