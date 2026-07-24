"""
File operations related functions.
"""
# Standard library imports
import mimetypes
import os
import zipfile
import json
from pathlib import Path
from logger_config import get_logger

logger = get_logger(__name__)

# Harmful file extensions to skip during operations
HARMFUL_EXTENSIONS = {'.exe', '.bash', '.sh', '.bat', '.cmd', '.ps1', '.msi', '.dll', '.so'}

def read_file(file_path):
    """
    Reads the content of a file and returns it as a string.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        str: The content of the file or an error message.
    """
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            content = file.read()
        return content
    except Exception as e:
        logger.error('An error occurred in read_file: %s', e)
        raise

def read_file_bytes(file_path):
    """
    Reads the content of a file and returns it as bytes.

    Args:
        file_path (str): The path to the file to be read.

    Returns:
        bytes: The binary content of the file.
    """
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
        logger.debug('File read as bytes: %s', file_path)
        return content
    except Exception as e:
        logger.error('An error occurred in read_file_bytes: %s', e)
        raise

def write_file(file_path, content):
    """
    Writes the given content to a file.

    Args:
        file_path (str): The path to the file where content will be written.
        content (str): The content to write to the file.
    Returns:
        None
    """
    try:
        with open(file_path, 'w', encoding="utf-8") as file:
            file.write(content)
        logger.info('File written successfully to %s', file_path)
    except Exception as e:
        logger.error('An error occurred in write_file: %s', e)
        raise

def list_zip_files(zip_path):
    """Lists all files in a ZIP archive.

    Args:
        zip_path (str): The path to the ZIP file.

    Returns:
        list: A list of file names contained in the ZIP archive.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        file_list = zip_file.namelist()
        return file_list

def read_file_from_zip(zip_path, file_name):
    """
    Reads a text file from within a ZIP archive and returns its content as a string.
    Args:
        zip_path (str): The path to the ZIP file.
        file_name (str): The name of the file within the ZIP archive to read.
    Returns:
        str: The content of the specified file as a string.
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        binary_content = zip_file.read(file_name)
        # Decode binary to string
        text_content = binary_content.decode('utf-8')
        return text_content

def create_folder(folder_paths):
    """
    Creates a folder if it does not already exist.

    Args:
        folder_path (str): The path of the folder to create.
        """
    try:
        for folder_path in folder_paths:
            os.makedirs(folder_path, exist_ok=True)
        logger.debug('Folders ensured at %s', folder_paths)
    except Exception as e:
        logger.error('An error occurred in create_folder: %s', e)
        raise

def get_mime_type(file_path):
    """
    Determine the MIME type of a file based on its extension.
    
    Args:
        file_path (str): The path to the file.
    
    Returns:
        str: The MIME type of the file. Returns 'application/octet-stream' if unknown.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    logger.debug('MIME type for %s: %s', file_path, mime_type)
    return mime_type


def is_harmful_file(file_path):
    """
    Check if a file should be skipped based on harmful extension or .git files.
    
    This function identifies files that could be harmful or should not be uploaded,
    including executables, scripts, compiled binaries, and version control files.
    
    Args:
        file_path (str or Path): Path object or string path for the file.
    
    Returns:
        bool: True if file should be skipped, False otherwise.
    """
    # Convert to Path object if string
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    # Skip .git files and directories
    if file_path.name.startswith('.git'):
        logger.debug('Skipping .git file: %s', file_path.name)
        return True
    
    # Skip harmful extensions
    if file_path.suffix.lower() in HARMFUL_EXTENSIONS:
        logger.debug('Skipping harmful extension file: %s', file_path.name)
        return True
    
    return False


def read_json_file(file_path):
    """
    Read and parse a JSON file.
    
    Args:
        file_path (str or Path): Path to the JSON file.
    
    Returns:
        dict or list: Parsed JSON content.
    
    Raises:
        json.JSONDecodeError: If JSON is invalid.
        FileNotFoundError: If file doesn't exist.
        Exception: For other file read errors.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug('Successfully read JSON file: %s', file_path)
        return data
    except json.JSONDecodeError as e:
        logger.error('Invalid JSON in file %s: %s', file_path, e)
        raise
    except FileNotFoundError as e:
        logger.error('JSON file not found: %s', file_path)
        raise
    except Exception as e:
        logger.error('An error occurred reading JSON file %s: %s', file_path, e)
        raise


def find_files_by_pattern(directory, pattern, current_dir_name=None):
    """
    Find all files matching a glob pattern in a specified directory.
    
    Optionally validates that the current working directory matches an expected name
    before searching in a relative directory.
    
    Args:
        directory (str or Path): Directory to search in. Can be relative (e.g., '../01/') 
                                 or absolute path.
        pattern (str): Glob pattern to match files (e.g., '*_meta_data.json').
        current_dir_name (str, optional): Expected name of current directory. If provided,
                                          validates that Path.cwd().name matches this value.
    
    Returns:
        list: List of Path objects for matching files.
    
    Raises:
        ValueError: If current_dir_name is provided and doesn't match actual current directory.
        FileNotFoundError: If target directory doesn't exist or no files match pattern.
    """
    logger.info(f"Finding files matching pattern '{pattern}' in directory: {directory}")
    
    # Validate current directory name if specified
    if current_dir_name:
        current_dir = Path.cwd()
        if current_dir.name != current_dir_name:
            error_msg = f"Current directory must be named '{current_dir_name}', but found: {current_dir.name}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info(f"Current directory validated: '{current_dir_name}'")
    
    # Convert to Path object and resolve relative paths
    target_dir = Path(directory)
    
    # If relative path, resolve it relative to current working directory
    if not target_dir.is_absolute():
        target_dir = (Path.cwd() / directory).resolve()
    
    # Validate directory exists
    if not target_dir.exists() or not target_dir.is_dir():
        error_msg = f"Directory not found: {target_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Target directory resolved to: {target_dir}")
    
    # Find all matching files
    matched_files = list(target_dir.glob(pattern))
    
    if not matched_files:
        error_msg = f"No files found matching pattern '{pattern}' in {target_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Found {len(matched_files)} file(s): {[f.name for f in matched_files]}")
    
    return matched_files
