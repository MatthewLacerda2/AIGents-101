import * as fs from 'fs';
import * as path from 'path';
import { execSync } from 'child_process';
import { Type } from '@google/genai';

// --- Tool Implementations ---

export async function fetch_website_text(url: string): Promise<string> {
    try {
        const response = await fetch(url, {
            headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const html = await response.text();
        const noScripts = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        const noStyles = noScripts.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');
        const text = noStyles.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
        return text;
    } catch (e: any) {
        return `Error fetching website: ${e.message}`;
    }
}

export function list_files(directory: string = '.', grep?: string): string {
    try {
        let files = fs.readdirSync(directory);
        if (grep) {
            files = files.filter(f => f.includes(grep));
        }
        if (files.length === 0) {
            if (grep) return `No files matching '${grep}' found in '${directory}'.`;
            return `The directory '${directory}' is empty.`;
        }
        return files.join('\n');
    } catch (e: any) {
        return `Error listing directory '${directory}': ${e.message}`;
    }
}

export function read_image_file(image_paths: string | string[]): string {
    if (typeof image_paths === 'string') {
        image_paths = [image_paths];
    }
    const allowed_extensions = ['.png', '.bmp', '.jpg', '.jpeg'];
    const results: string[] = [];
    
    for (const image_path of image_paths) {
        const ext = path.extname(image_path).toLowerCase();
        if (!allowed_extensions.includes(ext)) {
            results.push(`Error: Extension '${ext}' is not permitted. Only .png, .bmp, .jpg, and .jpeg are allowed.`);
            continue;
        }
        const abs_path = path.resolve(image_path);
        if (!fs.existsSync(abs_path)) {
            const base = path.basename(abs_path);
            const name_only = path.parse(base).name;
            const directory = path.dirname(abs_path) || '.';
            const suggested_files: string[] = [];
            try {
                if (fs.existsSync(directory)) {
                    const files = fs.readdirSync(directory);
                    for (const f of files) {
                        const f_ext = path.extname(f).toLowerCase();
                        if (allowed_extensions.includes(f_ext) && f.includes(name_only)) {
                            suggested_files.push(f);
                        }
                    }
                }
            } catch (e) {}
            let msg = `Image file not found at '${abs_path}'.`;
            if (suggested_files.length > 0) {
                msg += ` Did you mean: ${suggested_files.join(', ')}`;
            }
            results.push(msg);
        } else {
            results.push(`Success: Loaded image from '${abs_path}'.`);
        }
    }
    return results.join('\n');
}

export function create_file(name: string, extension: string, content: string): string {
    const allowed_extensions = ['.py', '.ts', '.md', '.txt'];
    let ext = extension.trim().toLowerCase();
    if (!ext.startsWith('.')) ext = '.' + ext;
    if (!allowed_extensions.includes(ext)) {
        return `Error: Extension '${extension}' is not permitted. Only .py, .ts, .md, and .txt files are allowed.`;
    }
    let filename = name.trim();
    if (!filename.endsWith(ext)) filename += ext;
    
    try {
        fs.writeFileSync(filename, content, 'utf8');
        return `Success: File '${filename}' was successfully created.`;
    } catch (e: any) {
        return `Error creating file '${filename}': ${e.message}`;
    }
}

export function create_text_file(file_path: string, content: string = ""): string {
    const allowed_extensions = ['.py', '.ts', '.tsx', '.md', '.txt'];
    const ext = path.extname(file_path).toLowerCase();
    if (!allowed_extensions.includes(ext)) {
        return `Error: File extension '${ext}' is not allowed. Only .py, .ts, .tsx, .md, and .txt are permitted.`;
    }
    
    const directory = path.dirname(file_path);
    if (directory && directory !== '.') {
        try {
            fs.mkdirSync(directory, { recursive: true });
        } catch (e: any) {
            return `Error creating directory '${directory}': ${e.message}`;
        }
    }
            
    try {
        fs.writeFileSync(file_path, content, 'utf8');
        return `Successfully created ${file_path}`;
    } catch (e: any) {
        return `Error creating file '${file_path}': ${e.message}`;
    }
}

export function get_video_screenshot(video_path: string, timestamp?: string): string {
    if (!fs.existsSync(video_path)) {
        return `Error: Video file not found at '${video_path}'.`;
    }
    const abs_video_path = path.resolve(video_path);
    let duration: number | null = null;
    let height: number | null = null;
    
    try {
        const cmd_duration = `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "${abs_video_path}"`;
        const result_dur = execSync(cmd_duration, { encoding: 'utf8' }).trim();
        if (result_dur) duration = parseFloat(result_dur);
        
        const cmd_res = `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of json "${abs_video_path}"`;
        const result_res = execSync(cmd_res, { encoding: 'utf8' }).trim();
        const res_json = JSON.parse(result_res);
        if (res_json.streams && res_json.streams.length > 0) {
            height = res_json.streams[0].height;
        }
    } catch (e: any) {
        return `Error gathering video metadata with ffprobe: ${e.message}`;
    }
    
    let ts_val: string | number;
    if (timestamp === undefined || String(timestamp).trim() === "") {
        if (duration !== null) {
            ts_val = duration / 2.0;
        } else {
            ts_val = 0.0;
        }
    } else {
        ts_val = String(timestamp).trim();
    }
    
    const video_dir = path.dirname(abs_video_path);
    const video_filename = path.basename(abs_video_path);
    const name_only = path.parse(video_filename).name;
    const safe_ts_filename = String(ts_val).replace(/:/g, '-').replace(/\./g, '_');
    const screenshot_name = `${name_only}_screenshot_${safe_ts_filename}.png`;
    const out_path = path.join(video_dir, screenshot_name);
    
    let vf_args = "";
    if (height !== null && height > 1080) {
        vf_args = "-vf scale=-2:1080";
    }
    
    try {
        execSync(`ffmpeg -y -ss ${ts_val} -i "${abs_video_path}" ${vf_args} -vframes 1 "${out_path}"`, { encoding: 'utf8', stdio: 'ignore' });
        const length_str = duration !== null ? `${duration} seconds` : "unknown";
        return `video_path: ${out_path}.\nLength: ${length_str}.`;
    } catch (e: any) {
        return `Error running ffmpeg: ${e.message}`;
    }
}

export function get_target_info(target_path: string): string {
    const abs_path = path.resolve(target_path);
    if (!fs.existsSync(abs_path)) {
        return `Error: Path '${target_path}' does not exist.`;
    }
    const stat = fs.statSync(abs_path);
    let size_bytes = stat.size;
    let base_type = "File";
    
    if (stat.isDirectory()) {
        base_type = "Folder";
        const getFolderSize = (dir: string): number => {
            let total = 0;
            const files = fs.readdirSync(dir);
            for (const f of files) {
                const p = path.join(dir, f);
                const s = fs.statSync(p);
                if (s.isDirectory()) total += getFolderSize(p);
                else total += s.size;
            }
            return total;
        };
        try {
            size_bytes = getFolderSize(abs_path);
        } catch (e) {}
    }
    
    const format_size = (size: number): string => {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let s = size;
        for (const unit of units) {
            if (s < 1024.0) return `${s.toFixed(2)} ${unit}`;
            s /= 1024.0;
        }
        return `${s.toFixed(2)} TB`;
    };
    
    const size_str = format_size(size_bytes);
    const edited = stat.mtime.toISOString().replace('T', ' ').substring(0, 19);
    const created = stat.birthtime.toISOString().replace('T', ' ').substring(0, 19);
    
    const output = [
        "--- Target Info ---",
        `Path:      ${abs_path}`,
        `Size:      ${size_str}`,
        `Created:   ${created}`,
        `Edited:    ${edited}`
    ];
    
    if (stat.isDirectory()) {
        output.splice(1, 0, `Type:      ${base_type}`);
        output.push("-------------------");
        return output.join('\n');
    }
    
    const ext = path.extname(abs_path).toLowerCase();
    const text_extensions = ['.py', '.txt', '.md', '.ts'];
    
    if (text_extensions.includes(ext)) {
        output.splice(1, 0, `Type:      Written File (${ext})`);
        try {
            const content = fs.readFileSync(abs_path, 'utf8');
            const lines = content.split('\n').length;
            output.push(`Lines:     ${lines}`);
        } catch (e) {
            output.push("Lines:     Error reading file");
        }
    } else {
        output.splice(1, 0, `Type:      File (${ext || 'unknown'})`);
    }
    
    output.push("-------------------");
    return output.join('\n');
}

export function read_text_files(file_paths: string[], read_by_chunks_of_40: boolean = false): string {
    const allowed_extensions = ['.py', '.ts', '.tsx', '.md', '.txt'];
    const results: string[] = [];
    
    for (const p of file_paths) {
        const ext = path.extname(p).toLowerCase();
        if (!allowed_extensions.includes(ext)) {
            results.push(`--- File: ${p} ---\nError: Reading this file extension is not allowed. Only .py, .ts, .tsx, .md, and .txt are permitted.`);
            continue;
        }
        try {
            let content = fs.readFileSync(p, 'utf8');
            if (read_by_chunks_of_40) {
                const lines = content.split('\n');
                const chunks_output = [];
                let j = 0;
                for (let i = 0; i < lines.length; i += 40) {
                    const chunk_lines = lines.slice(i, i + 40);
                    const start_line = i + 1;
                    const end_line = Math.min(i + 40, lines.length);
                    const header = `--- [Chunk ${j} (Lines ${start_line}-${end_line})] ---`;
                    chunks_output.push(header + "\n" + chunk_lines.join('\n'));
                    j++;
                }
                content = chunks_output.join('\n\n');
            }
            results.push(`--- File: ${p} ---\n${content}`);
        } catch (e: any) {
            results.push(`--- File: ${p} ---\nError reading file: ${e.message}`);
        }
    }
    return results.join('\n\n');
}

export function edit_text_files(file_path: string, chunks: any): string {
    if (typeof chunks === 'string') {
        try {
            chunks = JSON.parse(chunks);
        } catch (e: any) {
            return `Error: Could not parse chunks as JSON: ${e.message}`;
        }
    }
    
    if (Array.isArray(chunks)) {
        const new_chunks: any = {};
        chunks.forEach((val, i) => {
            if (val !== null) new_chunks[i.toString()] = val;
        });
        chunks = new_chunks;
    } else if (typeof chunks !== 'object' || chunks === null) {
        return "Error: Chunks must be an array or dictionary of strings.";
    }
    
    if (!fs.existsSync(file_path)) {
        return `Error: File '${file_path}' does not exist. Cannot apply chunk-based edits to a non-existent file.`;
    }
    
    let lines: string[];
    try {
        lines = fs.readFileSync(file_path, 'utf8').split('\n');
    } catch (e: any) {
        return `Error reading file '${file_path}': ${e.message}`;
    }
    
    const sorted_indices = Object.keys(chunks)
        .map(k => parseInt(k, 10))
        .filter(k => !isNaN(k))
        .sort((a, b) => b - a);
        
    for (const j of sorted_indices) {
        const chunk_val = chunks[j.toString()];
        if (chunk_val === null || chunk_val === undefined) continue;
        
        if (typeof chunk_val !== 'string') {
            return `Error: Chunk at index ${j} is not a string or null.`;
        }
        
        const start_idx = j * 40;
        if (start_idx > lines.length) {
            return `Error: Chunk at index ${j} (starting at line ${start_idx + 1}) is out of bounds for file with ${lines.length} lines.`;
        }
        
        const end_idx = Math.min((j + 1) * 40, lines.length);
        const chunk_lines = chunk_val.split('\n');
        
        lines.splice(start_idx, end_idx - start_idx, ...chunk_lines);
    }
    
    try {
        fs.writeFileSync(file_path, lines.join('\n'), 'utf8');
        return `Successfully edited ${file_path}`;
    } catch (e: any) {
        return `Error writing to file '${file_path}': ${e.message}`;
    }
}

// --- Tool Declarations (for @google/genai) ---

export const toolDeclarations = [
    {
        name: 'fetch_website_text',
        description: 'Fetches the text content of a website by URL, removing scripts and styles.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                url: {
                    type: Type.STRING,
                    description: 'The URL of the website to fetch.'
                }
            },
            required: ['url']
        }
    },
    {
        name: 'list_files',
        description: 'Lists files in a directory, optionally filtered by a grep string.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                directory: {
                    type: Type.STRING,
                    description: 'The directory to list files from. Defaults to current directory.'
                },
                grep: {
                    type: Type.STRING,
                    description: 'Optional string to filter files by.'
                }
            }
        }
    },
    {
        name: 'read_image_file',
        description: 'Checks if an image file exists and returns a success message if it does. The image will be attached to the next message if successful.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                image_paths: {
                    type: Type.ARRAY,
                    items: {
                        type: Type.STRING
                    },
                    description: 'The path(s) to the image file(s) to read.'
                }
            },
            required: ['image_paths']
        }
    },
    {
        name: 'create_file',
        description: 'Creates a new file with the specified name, extension, and content. Allowed extensions: .py, .ts, .md, .txt.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                name: {
                    type: Type.STRING,
                    description: 'The name of the file.'
                },
                extension: {
                    type: Type.STRING,
                    description: 'The extension of the file.'
                },
                content: {
                    type: Type.STRING,
                    description: 'The content to write to the file.'
                }
            },
            required: ['name', 'extension', 'content']
        }
    },
    {
        name: 'create_text_file',
        description: 'Creates a new text file with the specified content. Allowed extensions: .py, .ts, .tsx, .md, .txt.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                file_path: {
                    type: Type.STRING,
                    description: 'The path of the file to create.'
                },
                content: {
                    type: Type.STRING,
                    description: 'The content to write to the file.'
                }
            },
            required: ['file_path']
        }
    },
    {
        name: 'get_video_screenshot',
        description: 'Takes a screenshot of a video at a specific timestamp using ffmpeg.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                video_path: {
                    type: Type.STRING,
                    description: 'The path to the video file.'
                },
                timestamp: {
                    type: Type.STRING,
                    description: 'The timestamp to take the screenshot at (in seconds). Defaults to halfway through the video.'
                }
            },
            required: ['video_path']
        }
    },
    {
        name: 'get_target_info',
        description: 'Gets information about a file or folder (size, type, creation/edit time).',
        parameters: {
            type: Type.OBJECT,
            properties: {
                target_path: {
                    type: Type.STRING,
                    description: 'The path to the file or folder.'
                }
            },
            required: ['target_path']
        }
    },
    {
        name: 'read_text_files',
        description: 'Reads the content of text files. Allowed extensions: .py, .ts, .tsx, .md, .txt.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                file_paths: {
                    type: Type.ARRAY,
                    items: {
                        type: Type.STRING
                    },
                    description: 'The path(s) to the text file(s) to read.'
                },
                read_by_chunks_of_40: {
                    type: Type.BOOLEAN,
                    description: 'Whether to read the file in chunks of 40 lines.'
                }
            },
            required: ['file_paths']
        }
    },
    {
        name: 'edit_text_files',
        description: 'Edits specific line chunks of an existing text file.',
        parameters: {
            type: Type.OBJECT,
            properties: {
                file_path: {
                    type: Type.STRING,
                    description: 'The path to the file to edit.'
                },
                chunks: {
                    type: Type.STRING,
                    description: 'A JSON string representing a dictionary mapping chunk indices to new string content.'
                }
            },
            required: ['file_path', 'chunks']
        }
    }
];

export const available_functions: Record<string, Function> = {
    fetch_website_text,
    list_files,
    read_image_file,
    create_file,
    create_text_file,
    get_video_screenshot,
    get_target_info,
    read_text_files,
    edit_text_files
};
