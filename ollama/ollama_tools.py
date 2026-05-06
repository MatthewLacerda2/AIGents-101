import os
import json
import requests
import mimetypes
import subprocess
from pathlib import Path
from typing import List, Any
from datetime import datetime
from bs4 import BeautifulSoup

def fetch_website_text(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        return f"Error fetching website: {e}"

def list_files(directory: str = '.') -> str:
    try:
        files = os.listdir(directory)
        if not files:
            return f"The directory '{directory}' is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error listing directory '{directory}': {e}"

def read_image_file(image_path: str) -> str:
    allowed_extensions = {'.png', '.bmp', '.jpg', '.jpeg'}
    _, ext = os.path.splitext(image_path)
    if ext.lower() not in allowed_extensions:
        return f"Error: Extension '{ext}' is not permitted. Only .png, .bmp, .jpg, and .jpeg are allowed."
    path = os.path.abspath(image_path)
    if not os.path.exists(path):
        base = os.path.basename(path)
        name_only, _ = os.path.splitext(base)
        directory = os.path.dirname(path) or '.'
        suggested_files = []
        try:
            if os.path.exists(directory):
                for f in os.listdir(directory):
                    f_ext = os.path.splitext(f)[1].lower()
                    if f_ext in allowed_extensions and name_only in f:
                        suggested_files.append(f)
        except Exception:
            pass
        msg = f"Image file not found at '{path}'."
        if suggested_files:
            msg += f" Did you mean: {', '.join(suggested_files)}"
        return msg
    return f"Success: Loaded image from '{path}'."

def create_file(name: str, extension: str, content: str) -> str:
    allowed_extensions = {'.py', '.ts', '.md', '.txt'}
    ext = extension.strip().lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    if ext not in allowed_extensions:
        return f"Error: Extension '{extension}' is not permitted. Only .py, .ts, .md, and .txt files are allowed."
    filename = name.strip()
    if not filename.endswith(ext):
        filename += ext
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: File '{filename}' was successfully created."
    except Exception as e:
        return f"Error creating file '{filename}': {e}"

def create_text_file(file_path: str, content: str = "") -> str:
    """Creates a new text file with the specified content.
    
    Only .py, .ts, .tsx, .md, and .txt files are allowed.
    """
    allowed_extensions = {'.py', '.ts', '.tsx', '.md', '.txt'}
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in allowed_extensions:
        return f"Error: File extension '{ext}' is not allowed. Only .py, .ts, .tsx, .md, and .txt are permitted."
    
    directory = os.path.dirname(file_path)
    if directory:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            return f"Error creating directory '{directory}': {e}"
            
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully created {file_path}"
    except Exception as e:
        return f"Error creating file '{file_path}': {e}"

def get_video_screenshot(video_path: str, timestamp: str = None) -> str:
    if not os.path.exists(video_path):
        return f"Error: Video file not found at '{video_path}'."
    abs_video_path = os.path.abspath(video_path)
    duration = None
    height = None
    try:
        cmd_duration = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', abs_video_path
        ]
        result_dur = subprocess.run(cmd_duration, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        duration_str = result_dur.stdout.strip()
        if duration_str:
            duration = float(duration_str)
        cmd_res = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
            '-of', 'json', abs_video_path
        ]
        result_res = subprocess.run(cmd_res, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        res_json = json.loads(result_res.stdout)
        if 'streams' in res_json and len(res_json['streams']) > 0:
            height = res_json['streams'][0].get('height')
    except Exception as e:
        return f"Error gathering video metadata with ffprobe: {e}"
    if timestamp is None or str(timestamp).strip() == "":
        if duration is not None:
            ts_val = duration / 2.0
            timestamp_str = f"{ts_val:.3f}"
        else:
            ts_val = 0.0
            timestamp_str = "0.0"
    else:
        timestamp_str = str(timestamp).strip()
        ts_val = timestamp_str
    video_dir = os.path.dirname(abs_video_path)
    video_filename = os.path.basename(abs_video_path)
    name_only, _ = os.path.splitext(video_filename)
    safe_ts_filename = timestamp_str.replace(':', '-').replace('.', '_')
    screenshot_name = f"{name_only}_screenshot_{safe_ts_filename}.png"
    out_path = os.path.join(video_dir, screenshot_name)
    vf_args = []
    if height is not None and height > 1080:
        vf_args = ['-vf', 'scale=-2:1080']
    cmd_ffmpeg = [
        'ffmpeg', '-y', '-ss', str(ts_val), '-i', abs_video_path
    ] + vf_args + [
        '-vframes', '1', out_path
    ]
    try:
        sub_res = subprocess.run(cmd_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if sub_res.returncode != 0:
            return f"Error executing ffmpeg command: {sub_res.stderr.strip()}"
        length_str = f"{duration} seconds" if duration is not None else "unknown"
        return f"video_path: {out_path}.\nLength: {length_str}."
    except Exception as e:
        return f"Error running ffmpeg: {e}"

def get_target_info(target_path: str) -> str:
    path = Path(target_path).resolve()
    if not path.exists():
        return f"Error: Path '{target_path}' does not exist."
    abs_path = str(path)
    if path.is_dir():
        size_bytes = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        base_type = "Folder"
    else:
        size_bytes = path.stat().st_size
        base_type = "File"
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
    size_str = format_size(size_bytes)
    stat_info = path.stat()
    edited = datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    try:
        created = datetime.fromtimestamp(stat_info.st_birthtime).strftime('%Y-%m-%d %H:%M:%S')
    except AttributeError:
        created = datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S (Approx/Metadata Change)')
    output = [
        "--- Target Info ---",
        f"Path:      {abs_path}",
        f"Size:      {size_str}",
        f"Created:   {created}",
        f"Edited:    {edited}",
    ]
    if path.is_dir():
        output.insert(1, f"Type:      {base_type}")
        output.append("-------------------")
        return "\n".join(output)
    mime_type, _ = mimetypes.guess_type(abs_path)
    mime_type = mime_type or "unknown/unknown"
    ext = path.suffix.lower()
    text_extensions = {'.py', '.txt', '.md', '.ts'}
    if ext in text_extensions:
        output.insert(1, f"Type:      Written File ({ext})")
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = sum(1 for _ in f)
            output.append(f"Lines:     {lines}")
        except Exception:
            output.append("Lines:     Error reading file")
    elif mime_type.startswith('video/'):
        output.insert(1, f"Type:      Video ({mime_type})")
        try:
            res_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                       "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", abs_path]
            res = subprocess.check_output(res_cmd, text=True, stderr=subprocess.DEVNULL).strip()
            dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                       "-of", "default=noprint_wrappers=1:nokey=1", abs_path]
            dur = subprocess.check_output(dur_cmd, text=True, stderr=subprocess.DEVNULL).strip()
            dur_str = f"{float(dur):.2f} seconds" if dur else "Unknown"
            output.append(f"Resolution: {res if res else 'Unknown'}")
            output.append(f"Length:     {dur_str}")
        except Exception:
            output.append("Resolution: Error (ffprobe required)")
            output.append("Length:     Error (ffprobe required)")
    elif mime_type.startswith('image/'):
        output.insert(1, f"Type:      Image ({mime_type})")
        try:
            res_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                       "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", abs_path]
            res = subprocess.check_output(res_cmd, text=True, stderr=subprocess.DEVNULL).strip()
            output.append(f"Resolution: {res if res else 'Unknown'}")
        except Exception:
            output.append("Resolution: Error (ffprobe required)")
    else:
        output.insert(1, f"Type:      File ({mime_type})")
    output.append("-------------------")
    return "\n".join(output)

def read_text_files(file_paths: List[str], read_by_chunks_of_40: bool = False) -> str:
    """Reads allowed text files (.py, .ts, .tsx, .md, .txt).
    
    If read_by_chunks_of_40 is True, the file content is split into chunks of 40 lines,
    and returned with visual chunk headers (e.g., [Chunk 0 (Lines 1-40)]).
    """
    allowed_extensions = {'.py', '.ts', '.tsx', '.md', '.txt'}
    results = []
    for path in file_paths:
        _, ext = os.path.splitext(path)
        if ext.lower() not in allowed_extensions:
            results.append(f"--- File: {path} ---\nError: Reading this file extension is not allowed. Only .py, .ts, .tsx, .md, and .txt are permitted.")
            continue
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if read_by_chunks_of_40:
                lines = content.splitlines()
                chunks_output = []
                for j, i in enumerate(range(0, len(lines), 40)):
                    chunk_lines = lines[i:i+40]
                    start_line = i + 1
                    end_line = min(i + 40, len(lines))
                    header = f"--- [Chunk {j} (Lines {start_line}-{end_line})] ---"
                    chunks_output.append(header + "\n" + "\n".join(chunk_lines))
                content = "\n\n".join(chunks_output)
            results.append(f"--- File: {path} ---\n{content}")
        except Exception as e:
            results.append(f"--- File: {path} ---\nError reading file: {e}")
    return "\n\n".join(results)

def edit_text_files(file_path: str, chunks: Any) -> str:
    """Edits specific line chunks of an existing text file.
    
    chunks can be a dictionary mapping chunk index (int or str) to the new string content.
    - If a chunk index is not in the dict, it is skipped.
    - If a chunk's value is an empty string "", that chunk is deleted.
    - Otherwise, the chunk is replaced by the new string.
    
    For backward compatibility, an array is also accepted.
    """
    if isinstance(chunks, str):
        try:
            chunks = json.loads(chunks)
        except Exception as e:
            return f"Error: Could not parse chunks as JSON: {e}"
            
    # Convert list to dict for easier processing
    if isinstance(chunks, list):
        chunks = {str(i): val for i, val in enumerate(chunks) if val is not None}
    elif not isinstance(chunks, dict):
        return "Error: Chunks must be an array or dictionary of strings."
        
    # Read original file
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' does not exist. Cannot apply chunk-based edits to a non-existent file."
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.read().splitlines()
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"
        
    # Apply changes in reverse order of indices to keep preceding indices correct
    try:
        sorted_indices = sorted([int(k) for k in chunks.keys()], reverse=True)
    except ValueError:
        return "Error: Chunk keys must be integers."
        
    for j in sorted_indices:
        chunk_val = chunks[str(j)]
        if chunk_val is None:
            continue
            
        if not isinstance(chunk_val, str):
            return f"Error: Chunk at index {j} is not a string or null."
            
        start_idx = j * 40
        if start_idx > len(lines):
            return f"Error: Chunk at index {j} (starting at line {start_idx + 1}) is out of bounds for file with {len(lines)} lines."
            
        end_idx = min((j + 1) * 40, len(lines))
        
        # Replace the range with splitlines from the chunk_val
        chunk_lines = chunk_val.splitlines()
        lines[start_idx : end_idx] = chunk_lines
        
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Error writing to file '{file_path}': {e}"