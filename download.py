#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Set


class Stats:
    def __init__(self):
        self.total_files = 0
        self.included_files = 0
        self.total_size = 0
        self.skipped_by_extension = 0
        self.skipped_by_folder = 0
        self.skipped_by_name = 0
        self.skipped_by_size = 0
        self.skipped_binary = 0

    def print_summary(self):
        print("\n=== Processing Summary ===")
        print(f"Total files found: {self.total_files}")
        print(f"Files included: {self.included_files}")
        print(f"Total size: {self.total_size / 1024:.1f} KB")
        print(f"Skipped files:")
        print(f"  - By extension: {self.skipped_by_extension}")
        print(f"  - By folder: {self.skipped_by_folder}")
        print(f"  - By name: {self.skipped_by_name}")
        print(f"  - By size: {self.skipped_by_size}")
        print(f"  - Binary files: {self.skipped_binary}")


def validate_repo_url(url: str) -> bool:
    """Validate if the URL looks like a git repository."""
    parsed = urlparse(url)
    return (
            parsed.scheme in ('http', 'https', 'git') and
            parsed.netloc and
            parsed.path and
            (parsed.path.endswith('.git') or 'github.com' in parsed.netloc)
    )


def validate_config(config: dict) -> None:
    """Validate configuration values."""
    required_keys = {
        'default_branch', 'extensions', 'skip_folders',
        'skip_files', 'download_folder', 'max_file_size_mb'
    }
    missing = required_keys - set(config.keys())
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")

    if not isinstance(config['extensions'], list):
        raise ValueError("'extensions' must be a list")
    if not isinstance(config['skip_folders'], list):
        raise ValueError("'skip_folders' must be a list")
    if not isinstance(config['skip_files'], list):
        raise ValueError("'skip_files' must be a list")
    if not isinstance(config['max_file_size_mb'], (int, float)):
        raise ValueError("'max_file_size_mb' must be a number")


def load_config(config_file: str) -> dict:
    """Load and validate the configuration file."""
    default_config = {
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

    if not os.path.exists(config_file):
        print(f"[WARN] Config file '{config_file}' not found. Using default configuration.")
        return default_config

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Add any missing keys from default config
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        validate_config(config)
        return config
    except Exception as e:
        print(f"[ERROR] Failed to load config file: {str(e)}")
        print("[INFO] Using default configuration.")
        return default_config


def parse_repo_name(repo_url: str) -> str:
    """Derive a repo name from the given URL."""
    base_path = urlparse(repo_url).path
    base_name = os.path.basename(base_path)
    if base_name.endswith(".git"):
        base_name = base_name[:-4]
    return base_name or "repository"


def clone_repo(repo_url: str, dest_path: str, branch: str) -> None:
    """Clone specific branch from the GitHub repository."""
    if not validate_repo_url(repo_url):
        print(f"[ERROR] Invalid repository URL: {repo_url}")
        sys.exit(1)

    print(f"[INFO] Cloning branch '{branch}' from {repo_url} into {dest_path}...")
    try:
        subprocess.check_call([
            "git",
            "clone",
            "--single-branch",
            "--branch", branch,
            repo_url,
            dest_path
        ])
    except subprocess.CalledProcessError:
        print(f"[ERROR] Failed to clone branch '{branch}' from repository '{repo_url}'.")
        print("       The branch might not exist, or there was a problem accessing the repo.")
        sys.exit(1)


def remove_unwanted_folders(root_path: str, folders_to_remove: Set[str]) -> None:
    """Remove unwanted folders efficiently using sets."""
    if not folders_to_remove:
        return

    for folder_name in folders_to_remove:
        folder_path = os.path.join(root_path, folder_name)
        if os.path.exists(folder_path):
            print(f"[INFO] Removing folder: {folder_path}")
            shutil.rmtree(folder_path, ignore_errors=True)


def is_code_file(filepath: Path, extensions: Optional[Set[str]] = None) -> bool:
    """Check if file should be included based on extension."""
    if not extensions:
        return True

    if not filepath.suffix:
        return True

    return filepath.suffix.lower() in extensions


def is_file_too_large(file_path: Path, max_size_mb: float) -> bool:
    """Check if file exceeds size limit."""
    return file_path.stat().st_size > (max_size_mb * 1024 * 1024)


def read_file_content(file_path: Path) -> Optional[str]:
    """Simple file reading with UTF-8 only."""
    try:
        return file_path.read_text(encoding='utf-8')
    except:
        return None


def gather_files_into_single_text(
        root_path: str,
        output_file: str,
        extensions: Optional[Set[str]] = None,
        skip_folders: Optional[Set[str]] = None,
        skip_files: Optional[Set[str]] = None,
        max_file_size_mb: float = 1.0,
        stats: Optional[Stats] = None
) -> None:
    """Gather files into single text with statistics tracking."""
    if skip_folders is None:
        skip_folders = set()
    if skip_files is None:
        skip_files = set()
    if stats is None:
        stats = Stats()

    root = Path(root_path)

    with open(output_file, "w", encoding="utf-8") as out_f:
        for file_path in root.rglob("*"):
            if file_path.is_dir():
                continue

            stats.total_files += 1
            path_str = str(file_path.relative_to(root)).replace("\\", "/")

            # Check size first to avoid unnecessary processing
            if is_file_too_large(file_path, max_file_size_mb):
                stats.skipped_by_size += 1
                continue

            if any(part in skip_folders for part in path_str.split("/")):
                stats.skipped_by_folder += 1
                continue

            if file_path.name in skip_files:
                stats.skipped_by_name += 1
                continue

            if not is_code_file(file_path, extensions):
                stats.skipped_by_extension += 1
                continue

            content = read_file_content(file_path)
            if content is None:
                stats.skipped_binary += 1
                continue

            stats.included_files += 1
            stats.total_size += len(content.encode('utf-8'))

            relative_path = file_path.relative_to(root)
            out_f.write(f"\n{'=' * 60}\n")
            out_f.write(f"FILE: {relative_path}\n")
            out_f.write(f"{'=' * 60}\n")
            out_f.write(content)
            out_f.write("\n")


def main():
    parser = argparse.ArgumentParser(
        description="Clone a GitHub repo and merge all files into one text file based on configuration."
    )
    parser.add_argument("repo_url", help="URL of the GitHub repository to clone.")
    parser.add_argument(
        "--config",
        "-c",
        default="config.json",
        help="Path to the configuration file. Defaults to 'config.json'."
    )
    parser.add_argument(
        "--branch",
        "-b",
        default=None,
        help="Which branch to clone. Overrides config if specified."
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Name of the output file. If not provided, derived from the repo name."
    )
    parser.add_argument(
        "--exclude",
        "-e",
        nargs="*",
        default=[],
        help="Additional folders to exclude (added to skip_folders from config)"
    )
    parser.add_argument(
        "--max-file-size",
        type=float,
        help="Maximum file size in MB (overrides config)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show processing statistics"
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Include binary files (base64 encoded)"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Set branch (command line overrides config)
    branch = args.branch if args.branch else config["default_branch"]

    # Create download directory from config
    current_dir = os.getcwd()
    download_dir = os.path.join(current_dir, config["download_folder"])
    os.makedirs(download_dir, exist_ok=True)

    # Set output filename
    if args.output is not None:
        output_file = os.path.join(download_dir, os.path.basename(args.output))
    else:
        repo_name = parse_repo_name(args.repo_url)
        output_file = os.path.join(download_dir, f"{repo_name}.txt")

    # Create temp folder for cloning
    temp_folder = os.path.join(download_dir, "repo_temp")
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder, ignore_errors=True)
    os.makedirs(temp_folder, exist_ok=True)

    # Clone repository
    clone_repo(args.repo_url, temp_folder, branch)

    # Convert lists to sets for better performance
    extensions = set(ext.lower() for ext in config["extensions"]) if config["extensions"] else None
    skip_folders = set(config["skip_folders"] + args.exclude)
    skip_files = set(config["skip_files"])

    # Get max file size (command line overrides config)
    max_file_size = args.max_file_size if args.max_file_size is not None else config["max_file_size_mb"]

    # Initialize stats if requested
    stats = Stats() if args.stats else None

    # Gather files into single text
    gather_files_into_single_text(
        root_path=temp_folder,
        output_file=output_file,
        extensions=extensions,
        skip_folders=skip_folders,
        skip_files=skip_files,
        max_file_size_mb=max_file_size,
        stats=stats
    )

    if stats:
        stats.print_summary()

    print(f"[INFO] Finished writing repo content to '{output_file}'.")

    # Cleanup
    shutil.rmtree(temp_folder, ignore_errors=True)


if __name__ == "__main__":
    main()