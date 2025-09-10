#!/usr/bin/env python3
"""
Metadata Inspector - Extract and display all available metadata from media files
Particularly useful for debugging iPhone video/photo metadata issues
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import os

def get_ffprobe_metadata(file_path):
    """Extract metadata using ffprobe (most comprehensive for videos)"""
    print("🎬 FFPROBE METADATA")
    print("=" * 50)
    
    try:
        # Get all available metadata
        cmd = [
            "ffprobe", 
            "-v", "quiet", 
            "-print_format", "json", 
            "-show_format", 
            "-show_streams", 
            "-show_chapters",
            "-show_programs",
            str(file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ ffprobe failed: {result.stderr}")
            return None
            
        data = json.loads(result.stdout)
        
        # Format information
        if "format" in data:
            print("📁 FORMAT INFO:")
            format_info = data["format"]
            for key, value in format_info.items():
                if key == "tags":
                    print(f"  📋 TAGS:")
                    for tag_key, tag_value in value.items():
                        print(f"    {tag_key}: {tag_value}")
                else:
                    print(f"  {key}: {value}")
            print()
        
        # Stream information
        if "streams" in data:
            print("📺 STREAMS INFO:")
            for i, stream in enumerate(data["streams"]):
                print(f"  🎞️ Stream {i} ({stream.get('codec_type', 'unknown')}):")
                for key, value in stream.items():
                    if key == "tags":
                        print(f"    📋 STREAM TAGS:")
                        for tag_key, tag_value in value.items():
                            print(f"      {tag_key}: {tag_value}")
                    else:
                        print(f"    {key}: {value}")
                print()
        
        return data
        
    except subprocess.TimeoutExpired:
        print("❌ ffprobe timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return None
    except FileNotFoundError:
        print("❌ ffprobe not found. Please install FFmpeg.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def get_exiftool_metadata(file_path):
    """Extract metadata using exiftool (best for photos and detailed metadata)"""
    print("📷 EXIFTOOL METADATA")
    print("=" * 50)
    
    try:
        # Try exiftool with JSON output
        cmd = ["exiftool", "-j", "-G", "-a", "-s", str(file_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ exiftool failed: {result.stderr}")
            return None
            
        data = json.loads(result.stdout)
        if data and len(data) > 0:
            metadata = data[0]
            for key, value in sorted(metadata.items()):
                print(f"  {key}: {value}")
        
        return data[0] if data else None
        
    except FileNotFoundError:
        print("❌ exiftool not found. Install from https://exiftool.org/")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return None
    except subprocess.TimeoutExpired:
        print("❌ exiftool timed out")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def get_filesystem_metadata(file_path):
    """Extract filesystem metadata"""
    print("💾 FILESYSTEM METADATA")
    print("=" * 50)
    
    try:
        stat = file_path.stat()
        
        print(f"  📁 Path: {file_path}")
        print(f"  📄 Filename: {file_path.name}")
        print(f"  📏 Size: {stat.st_size:,} bytes ({stat.st_size / 1024 / 1024:.2f} MB)")
        print(f"  📅 Created: {datetime.fromtimestamp(stat.st_ctime).isoformat()}")
        print(f"  📝 Modified: {datetime.fromtimestamp(stat.st_mtime).isoformat()}")
        print(f"  👁️ Accessed: {datetime.fromtimestamp(stat.st_atime).isoformat()}")
        
        # Windows specific attributes
        if hasattr(stat, 'st_birthtime'):
            print(f"  🎂 Birth time: {datetime.fromtimestamp(stat.st_birthtime).isoformat()}")
            
        return {
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "path": str(file_path),
            "filename": file_path.name
        }
        
    except Exception as e:
        print(f"❌ Error getting filesystem metadata: {e}")
        return None

def analyze_iphone_specifics(ffprobe_data, exiftool_data):
    """Analyze iPhone-specific metadata patterns"""
    print("📱 IPHONE-SPECIFIC ANALYSIS")
    print("=" * 50)
    
    iphone_indicators = []
    
    # Check for iPhone indicators in ffprobe data
    if ffprobe_data:
        # Check format tags
        format_tags = ffprobe_data.get("format", {}).get("tags", {})
        for key, value in format_tags.items():
            if any(indicator in str(value).lower() for indicator in ["iphone", "apple", "ios"]):
                iphone_indicators.append(f"Format tag {key}: {value}")
        
        # Check stream tags
        for i, stream in enumerate(ffprobe_data.get("streams", [])):
            stream_tags = stream.get("tags", {})
            for key, value in stream_tags.items():
                if any(indicator in str(value).lower() for indicator in ["iphone", "apple", "ios"]):
                    iphone_indicators.append(f"Stream {i} tag {key}: {value}")
    
    # Check for iPhone indicators in exiftool data
    if exiftool_data:
        for key, value in exiftool_data.items():
            if any(indicator in str(value).lower() for indicator in ["iphone", "apple", "ios"]) or \
               any(indicator in key.lower() for indicator in ["make", "model", "software"]):
                iphone_indicators.append(f"EXIF {key}: {value}")
    
    if iphone_indicators:
        print("📱 iPhone/Apple indicators found:")
        for indicator in iphone_indicators:
            print(f"  ✅ {indicator}")
    else:
        print("❓ No obvious iPhone/Apple indicators found")
    
    # Analyze creation time patterns
    print("\n🕐 TIMESTAMP ANALYSIS:")
    creation_times = []
    
    if ffprobe_data:
        format_tags = ffprobe_data.get("format", {}).get("tags", {})
        for key in ["creation_time", "date", "DATE"]:
            if key in format_tags:
                creation_times.append(f"ffprobe format.{key}: {format_tags[key]}")
        
        for i, stream in enumerate(ffprobe_data.get("streams", [])):
            stream_tags = stream.get("tags", {})
            for key in ["creation_time", "date", "DATE"]:
                if key in stream_tags:
                    creation_times.append(f"ffprobe stream{i}.{key}: {stream_tags[key]}")
    
    if exiftool_data:
        time_keys = [key for key in exiftool_data.keys() 
                    if any(time_word in key.lower() for time_word in ["time", "date", "created", "modified"])]
        for key in time_keys:
            creation_times.append(f"exiftool {key}: {exiftool_data[key]}")
    
    if creation_times:
        print("📅 Found timestamps:")
        for timestamp in creation_times:
            print(f"  {timestamp}")
    else:
        print("❌ No timestamps found in metadata")

def main():
    parser = argparse.ArgumentParser(description="Extract and display all available metadata from media files")
    parser.add_argument("file_path", type=Path, help="Path to the media file to analyze")
    parser.add_argument("--ffprobe-only", action="store_true", help="Use only ffprobe (skip exiftool)")
    parser.add_argument("--exiftool-only", action="store_true", help="Use only exiftool (skip ffprobe)")
    parser.add_argument("--no-analysis", action="store_true", help="Skip iPhone-specific analysis")
    parser.add_argument("--save-json", type=Path, help="Save raw metadata to JSON file")
    
    args = parser.parse_args()
    
    if not args.file_path.exists():
        print(f"❌ File not found: {args.file_path}")
        sys.exit(1)
    
    print(f"🔍 METADATA INSPECTOR")
    print(f"📁 File: {args.file_path}")
    print(f"📏 Size: {args.file_path.stat().st_size / 1024 / 1024:.2f} MB")
    print("=" * 80)
    print()
    
    # Get filesystem metadata
    fs_data = get_filesystem_metadata(args.file_path)
    print()
    
    # Get ffprobe metadata
    ffprobe_data = None
    if not args.exiftool_only:
        ffprobe_data = get_ffprobe_metadata(args.file_path)
        print()
    
    # Get exiftool metadata
    exiftool_data = None
    if not args.ffprobe_only:
        exiftool_data = get_exiftool_metadata(args.file_path)
        print()
    
    # iPhone-specific analysis
    if not args.no_analysis:
        analyze_iphone_specifics(ffprobe_data, exiftool_data)
        print()
    
    # Save to JSON if requested
    if args.save_json:
        combined_data = {
            "file_path": str(args.file_path),
            "filesystem": fs_data,
            "ffprobe": ffprobe_data,
            "exiftool": exiftool_data,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(args.save_json, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Metadata saved to: {args.save_json}")

if __name__ == "__main__":
    main()
