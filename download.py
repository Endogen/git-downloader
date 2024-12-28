#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

def load_config(config_file: str) -> dict:
    """
    Load and validate the configuration file.
    Returns default values if no config file is found.
    """
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
        "download_folder": "repos"
    }

    if not os.path.exists(config_file):
        print(f"[WARN] Config file '{config_file}' not found. Using default configuration.")
        return default_config

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"[ERROR] Failed to load config file: {str(e)}")
        print("[INFO] Using default configuration.")
        return default_config

def parse_repo_name(repo_url: str) -> str:
    """
    Attempts to derive a repo name from the given URL.
    e.g. "https://github.com/user/repo_name.git" -> "repo_name"
    """
    base_path = urlparse(repo_url).path
    base_name = os.path.basename(base_path)
    if base_name.endswith(".git"):
        base_name = base_name[:-4]
    return base_name or "repository"

def clone_repo(repo_url: str, dest_path: str, branch: str) -> None:
    """
    Clones only the specified branch from the GitHub repository into dest_path.
    Uses --single-branch to avoid fetching all branches.
    """
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

def remove_unwanted_folders(root_path: str, folders_to_remove=None) -> None:
    """
    Removes unwanted folders as specified in the config.
    """
    if not folders_to_remove:
        return

    for folder_name in folders_to_remove:
        folder_path = os.path.join(root_path, folder_name)
        if os.path.exists(folder_path):
            print(f"[INFO] Removing folder: {folder_path}")
            shutil.rmtree(folder_path, ignore_errors=True)

def is_code_file(filepath: Path, extensions=None) -> bool:
    """
    Determines if the file has an extension listed in the config.
    If no extensions specified, includes all files.
    """
    if not extensions:
        return True
        
    # Files without extension should be included
    if not filepath.suffix:
        return True
        
    return filepath.suffix.lower() in extensions

def gather_files_into_single_text(
    root_path: str,
    output_file: str,
    extensions=None,
    skip_folders=None,
    skip_files=None
):
    """
    Gathers all matching files from root_path into a single output file.
    Uses configuration for extensions, skip_folders, and skip_files.
    """
    if skip_folders is None:
        skip_folders = []
    if skip_files is None:
        skip_files = []

    root = Path(root_path)

    with open(output_file, "w", encoding="utf-8") as out_f:
        for file_path in root.rglob("*"):
            if file_path.is_dir():
                continue

            path_str = str(file_path.relative_to(root)).replace("\\", "/")

            if any(path_str.startswith(folder.strip("/") + "/") for folder in skip_folders):
                continue

            if file_path.name in skip_files:
                continue

            if not is_code_file(file_path, extensions):
                continue

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except:
                continue

            relative_path = file_path.relative_to(root)
            out_f.write(f"\n{'='*60}\n")
            out_f.write(f"FILE: {relative_path}\n")
            out_f.write(f"{'='*60}\n")
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

    # Combine config skip_folders with command line excludes
    all_skip_folders = config["skip_folders"] + args.exclude

    # Remove unwanted folders
    remove_unwanted_folders(temp_folder, all_skip_folders)

    # Gather files into single text
    gather_files_into_single_text(
        root_path=temp_folder,
        output_file=output_file,
        extensions=config["extensions"],
        skip_folders=all_skip_folders,
        skip_files=config["skip_files"]
    )

    print(f"[INFO] Finished writing repo content to '{output_file}'.")
    
    # Cleanup
    shutil.rmtree(temp_folder, ignore_errors=True)

if __name__ == "__main__":
    main()
