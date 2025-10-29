# Footage Organization and Tagging System for DaVinci Resolve

## 🎯 What is this project?

A complete automated workflow to organize video footage from multiple sources (phones, cameras, drones) by date and automatically apply color grading tags in DaVinci Resolve. Perfect for travel videos, event coverage, or any project with mixed footage sources.

## 🚀 Quick Start

1. **Install Prerequisites:** Python 3.8+ and [Gyroflow](https://gyroflow.xyz/) (optional, for stabilization)
2. **Set up your project structure:**
   ```
   my_vacation_project/
   └── Footage_raw/
       ├── phone_footage/
       ├── drone/
       └── camera/
   ```
3. **Run the automation:** `SORT_MEDIA_FOLDER.BAT "path\to\my_vacation_project"`
4. **Import in DaVinci Resolve:** Import the generated `Footage/` folder
5. **Apply tags:** Run the included script to auto-color and group your clips

## 🎬 Key Features

- **📅 Smart Date Organization:** Automatically sorts footage chronologically, even from different time zones
- **⏰ Time Adjustment per Group:** Correct camera clock errors automatically (NEW!)
- **🎨 Automatic Color Tagging:** Intelligently groups clips by camera type and color profile for efficient grading
- **🚁 Gyroflow Integration:** Optional stabilization for drone and action camera footage
- **📱 Multi-Source Support:** Handles phones, cameras, drones with different metadata formats
- **🔒 Safe Processing:** Never modifies original files - works with placeholders first
- **⚡ One-Click Automation:** Complete workflow from raw footage to organized, tagged clips

## ❓ Why Use This?

**The Problem:** Organizing footage from multiple sources (friends' phones, your camera, drone footage) is tedious. Each source needs different color grading approaches, and maintaining chronological order while managing mixed footage becomes overwhelming.

**The Solution:** This system automates everything - from organizing files by date to applying appropriate color tags in DaVinci Resolve, making multi-source edits effortless.

## 🛠️ How It Works

### The Complete Pipeline

1. **🎬 Stabilization (Optional):** Uses Gyroflow to stabilize drone/action camera footage
2. **📁 Organization:** Scans footage and creates date-organized structure with metadata placeholders
3. **📂 Transfer:** Copies/moves actual files to final organized structure
4. **📊 Metadata Analysis:** Analyzes video properties and creates groups by camera/color profile
5. **🎨 DaVinci Resolve Integration:** Automatically applies colors and groups to clips

### File Processing Intelligence

- **Smart Timestamp Detection:** Handles UTC drone metadata, iPhone timestamps, and file modification times
- **Stabilized File Priority:** Automatically prefers `_stabilized` versions when available
- **Multi-Format Support:** Videos (MP4, MOV, AVI, MKV...) and Photos (JPG, RAW, HEIC...)
- **Color Profile Detection:** Automatically detects LOG, HDR, and standard profiles for proper grouping

## 📋 Prerequisites

### Required
- **Python 3.8+** with standard libraries
- **Windows, macOS, or Linux** (batch script is Windows-focused, but core scripts are cross-platform)

### Optional (for Enhanced Features)
- **[Gyroflow](https://gyroflow.xyz/)** - For automatic video stabilization (must be in system PATH)
- **ExifTool** - For enhanced iPhone/Apple device metadata extraction
- **DaVinci Resolve** - For the automated tagging features

## 📁 Project Structure Setup

Create your project with this structure:
```
my_project/
└── Footage_raw/                    # ← This exact name is required
    ├── phone_john/                 # Source folders (any names)
    │   ├── VIDEO001.mp4
    │   ├── IMG_1234.jpg
    │   └── ...
    ├── drone/                      # Drone footage folder
    │   ├── DJI_0001.mp4
    │   └── DJI_0002.mp4
    └── camera/                     # Camera footage folder
        ├── MVI_1234.MOV
        └── IMG_5678.CR2
```

**⚠️ Important Notes:**
- The `Footage_raw` folder name is **required** - the scripts look for this specific name
- Source subfolders can have any names (phone_john, drone, camera, etc.)
- Simply "dump" your files in these source folders - the script handles the rest
- **iPhone Users:** Transfer files via iCloud/AirDrop to preserve metadata (not iTunes sync)

## 🚀 Usage Guide

### Method 1: Automated Processing (Windows - Recommended)

The simplest way to run the complete workflow:

```batch
SORT_MEDIA_FOLDER.BAT "C:\path\to\my_project"
```

This will automatically run through all 4 steps:

**[Step 0/4] Optional Stabilization:**
- Detects if Gyroflow is installed
- Prompts you to select folders to stabilize (e.g., `drone,gopro`)
- Processes multiple video formats: MP4, MOV, AVI, MKV, etc.
- Creates `_stabilized` versions alongside originals

**[Step 1/4] organize_footage_links.py:**
- Scans `Footage_raw/` for videos and photos
- Creates date-organized structure (YYYY-MM-DD folders)
- Generates `.txt` placeholder files with metadata
- Handles timezone conversion for drone footage
- Photos go in separate `photos/` subfolders

**[Step 2/4] transfer_organized_footage.py:**
- Copies actual files based on placeholder organization  
- Preserves folder structure and verifies integrity
- Automatically uses stabilized versions when available

**[Step 3/4] create_metadata.py:**
- Analyzes video metadata (codec, color profile, resolution)
- Creates intelligent groups by camera/source type
- Assigns colorblind-compatible colors
- Generates `metadata.csv` for DaVinci Resolve

### Method 2: Manual Execution

Run the scripts individually for more control:

```bash
# Step 1: Organize files by date
python SORTING/organize_footage_links.py "my_project" --include-photos

# Step 2: Transfer real files
python SORTING/transfer_organized_footage.py "my_project" --copy

# Step 3: Generate metadata for DaVinci Resolve
python SORTING/create_metadata.py "my_project"
```

### Result Structure

After processing, you'll have:
```
my_project/
├── Footage_raw/                    # Original files (unchanged)
├── Footage_metadata_sorted/        # Intermediate placeholders
│   ├── photo/                      # All photos organized by date
│   │   ├── 2024-03-15/
│   │   │   └── 16h45m30s_phone_IMG_1234.txt
│   │   └── 2024-03-16/
│   └── video/                      # All videos organized by date
│       ├── 2024-03-15/
│       │   ├── 14h23m45s_drone_DJI_0001.txt
│       │   └── 15h30m12s_phone_VIDEO001.txt
│       └── 2024-03-16/
└── Footage/                        # Final organized files
    ├── photo/                      # All photos with actual files
    │   ├── 2024-03-15/
    │   │   └── 16h45m30s_phone_IMG_1234.jpg
    │   └── 2024-03-16/
    ├── video/                      # All videos with actual files
    │   ├── 2024-03-15/
    │   │   ├── 14h23m45s_drone_DJI_0001.mp4
    │   │   └── 15h30m12s_phone_VIDEO001.mp4
    │   └── 2024-03-16/
    └── metadata.csv                # For DaVinci Resolve tagging
```

**🆕 NEW: Separate photo and video folders**  
Photos and videos are now organized in separate root folders (`photo/` and `video/`) to make navigation and management easier. Within each folder, the same date-based organization (YYYY-MM-DD) is maintained.
## 🎨 DaVinci Resolve Integration

### Installing the Tagging Script

1. Copy `TagFootageByCSV.py` to your DaVinci Resolve scripts folder:
   - **Windows:** `%APPDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility\`
   - **macOS:** `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/`
   - **Linux:** `~/.local/share/DaVinciResolve/Fusion/Scripts/Utility/`

### Using the Automated Tagging

1. **Import Footage:**
   - In DaVinci Resolve, right-click Media Pool → Import
   - Select your `Footage/` folder
   - ✅ Check "Create bins for subfolders" during import

2. **Apply Automatic Tags:**
   - Go to **Workspace > Scripts > Utility > TagFootageByCSV**
   - Open **Workspace > Console** to see progress
   - Your clips will be automatically colored and grouped by camera/source

3. **Color Grading Workflow:**
   - Switch to Color tab
   - Re-run the tagging script for timeline-specific groups
   - Grade by group to apply corrections to all similar clips at once

### How Grouping Works

The system automatically creates intelligent groups:

- **By Source:** `Phone_John`, `Drone`, `Camera_Canon`
- **By Color Profile:** `Drone_LOG`, `Camera_Rec709`, `Phone_Standard`  
- **Smart Colors:** Colorblind-compatible palette with logical color families
- **Timeline Groups:** Groups only apply to clips in your active timeline

**Example Groups:**
```
📱 Phone_John     → Yellow (standard footage)
🚁 Drone_LOG     → Blue (LOG color profile)  
📷 Camera_Rec709 → Green (standard color profile)
📷 Camera_LOG    → Cyan (same source, different profile)
```

## 🚁 Optional: Gyroflow Stabilization

### What is Gyroflow?

[Gyroflow](https://gyroflow.xyz/) is a video stabilization tool that uses gyroscope data from your camera to provide smooth, high-quality stabilization. Perfect for drone and action camera footage.

### Setup Requirements

- **Install Gyroflow:** Download from https://gyroflow.xyz/
- **Add to PATH:** Ensure `gyroflow` command works in terminal
- **Compatible Footage:** Requires embedded gyro data (drones, GoPros, some phones)
- **Supported Formats:** MP4, MOV, AVI, MKV, MTS, and more

### How to Use Stabilization

When running the batch script, you'll be prompted:
```
[0/4] Checking for Gyroflow...
Gyroflow found! Stabilization option available.
Examples: 'drone' or 'drone,gopro' or 'avata gopro osmo'
Enter folder name(s) to stabilize or press Enter to skip: 
```

**Input Examples:**
- Single folder: `drone`
- Multiple folders: `drone,gopro,osmo` or `drone gopro osmo`
- Common names: `avata`, `mini4`, `gopro`, `osmo`, `insta360`

### Stabilization Features

✅ **Safe Processing:** Never overwrites original files  
✅ **Smart Detection:** Automatically skips files without gyro data  
✅ **Multi-Format:** Handles all common video formats  
✅ **Progress Tracking:** Shows detailed progress for each file  
✅ **Duplicate Prevention:** Won't re-stabilize `_stabilized` files  
✅ **Batch Processing:** Handle multiple folders in one go  

### File Naming

- **Original:** `DJI_0001.mp4`  
- **Stabilized:** `DJI_0001_stabilized.mp4`  
- **Organization:** System automatically prefers stabilized versions  

## 🔧 Advanced Usage

### Individual Script Parameters

<details>
<summary>Click to expand detailed script options</summary>

#### `organize_footage_links.py`
```bash
python organize_footage_links.py PROJECT_ROOT [OPTIONS]

Options:
  --ext               Video extensions (default: .mp4,.mov,.avi,etc.)
  --photo-ext         Photo extensions (default: .jpg,.png,.raw,etc.)
  --include-photos    Process both videos and photos
  --photos-only       Process only photos
  --videos-only       Process only videos (default)
  --tz                Timezone for drone conversion (default: America/Montreal)
  --list-tz           List available timezones
  --simulate          Dry-run mode
```

#### `transfer_organized_footage.py`
```bash
python transfer_organized_footage.py PROJECT_ROOT [OPTIONS]

Options:
  --copy              Keep original files (copy instead of move)
  --verify-only       Only verify files without transferring
```

#### `create_metadata.py`
```bash
python create_metadata.py PROJECT_ROOT [OPTIONS]

Options:
  --dry-run           Preview without writing CSV file
```

</details>

### Timezone Configuration

For drone footage, you can specify your local timezone:

```bash
# List available timezones
python organize_footage_links.py --list-tz

# Use specific timezone
python organize_footage_links.py "my_project" --tz "Europe/Paris"
```

Common timezones: `America/Montreal`, `Europe/Paris`, `Asia/Tokyo`, `America/Los_Angeles`

### ⏰ Time Adjustment per Group (NEW!)

Sometimes cameras have incorrect time settings. You can automatically adjust timestamps for specific groups:

**Create `specific_group_time_adjust.json` in your project root:**
```json
{
    "canon": "+00000001_000000",
    "gopro": "-00000000_020000"
}
```

**Format:** `[+/-]YYYYMMDD_HHMMSS`
- `+00000001_000000` = Add 1 day
- `-00000000_020000` = Subtract 2 hours
- `+00000007_000000` = Add 7 days (1 week)

**Features:**
✅ **Smart Rollover:** 23:00 + 2 hours = next day at 01:00  
✅ **Per-Group:** Different adjustment for each camera/source  
✅ **Non-Destructive:** Original files never modified  
✅ **Case-Insensitive:** "Canon", "canon", "CANON" all work  
✅ **Drone Photos:** Applies to both videos AND photos (uses mtime for photos)

**See:** [`documentation/GUIDE_AJUSTEMENT_TEMPS.md`](documentation/GUIDE_AJUSTEMENT_TEMPS.md) for complete guide and examples.

## ❓ Troubleshooting

### Common Issues

**Gyroflow/Stabilization:**
- **"Gyroflow not found":** Install Gyroflow and add to system PATH
- **"No gyro data found":** Normal for some footage - only drones/action cams have gyro data
- **Long processing time:** Normal for high-resolution videos (1-3 minutes per file)
- **Double-stabilized files:** System automatically prevents `_stabilized_stabilized` files

**File Organization:**
- **"Footage_metadata_sorted already exists":** System automatically cleans up previous runs
- **"Invalid date" folder:** Files with corrupted metadata - check original timestamps
- **iPhone files in wrong dates:** Transfer via iCloud/AirDrop, not iTunes sync
- **Permission errors:** Run as administrator or check file locks in DaVinci Resolve

**DaVinci Resolve:**
- **No colors applied:** Re-run the tagging script after importing footage
- **Groups not working:** Groups only apply to clips in active timeline
- **Script not found:** Check script installation path and restart DaVinci Resolve

### Getting Help

1. **Check the logs:** Look for detailed error messages in console output
2. **Try simulation mode:** Use `--simulate` flag to test without making changes
3. **Verify project structure:** Ensure `Footage_raw/` folder exists with correct name
4. **Test with small batch:** Try with a few files first to identify issues
5. **🆕 Analyze file metadata:** Use `SHOW_FILE_METADATA.BAT` or `python debug/show_file_metadata.py` to see all metadata for a specific file

### 🔍 Debugging Tool: Show File Metadata

**NEW!** Use the metadata viewer to debug any file organization issues:

```bash
# View all metadata for a file
python debug\show_file_metadata.py "path\to\video.mp4"

# Or drag-and-drop a file onto SHOW_FILE_METADATA.BAT

# Save metadata to file
python debug\show_file_metadata.py "video.mp4" --save

# JSON output for automation
python debug\show_file_metadata.py "video.mp4" --json
```

This tool shows:
- ✅ File information (size, dates)
- ✅ All timestamps (FFprobe, ExifTool, filename extraction)
- ✅ Video metadata (codec, resolution, colorspace, HDR/LOG detection)
- ✅ Source detection and categorization
- ✅ Raw FFprobe and ExifTool data

Perfect for understanding why a file isn't being organized correctly!

## ✨ Key Benefits

- **🔒 Safe Processing:** Original files never modified - works with placeholders first
- **⚡ Full Automation:** One command processes everything from raw footage to tagged clips
- **📅 Smart Organization:** Handles mixed timezones, metadata formats, and file types
- **🎨 Intelligent Grouping:** Automatically detects camera types and color profiles
- **🚁 Stabilization Ready:** Optional Gyroflow integration for professional results
- **🎬 Professional Workflow:** Optimized for real-world editing scenarios
- **🌍 Cross-Platform:** Works on Windows, macOS, and Linux
- **📱 Multi-Source Support:** Handles phones, cameras, drones seamlessly

## 📝 Technical Details

### Supported File Formats

**Videos:** MP4, MOV, M4V, AVI, MKV, MTS, M2TS, WMV, 3GP, MPG, MPEG, INSV, 360, MOD, TOD  
**Photos:** JPG, JPEG, PNG, TIFF, TIF, RAW, CR2, CR3, NEF, ARW, DNG, HEIC, HEIF

### Metadata Analysis

The system performs comprehensive analysis:
- **Timestamp Extraction:** Filename → QuickTime → File modification time
- **Color Profile Detection:** LOG, HDR, Rec709, sRGB detection
- **Source Classification:** Drone, phone, camera identification
- **Timezone Intelligence:** UTC conversion for drone metadata

### Security Features

- **Placeholder System:** No files moved until verification complete
- **Integrity Checking:** File size and checksum verification
- **Rollback Capability:** Safe transfer with complete logging
- **Duplicate Detection:** Prevents overwriting and conflicts

---

## 📚 Script Reference

### Core Scripts

| Script | Purpose | Key Features |
|--------|---------|--------------|
| `organize_footage_links.py` | Date organization with placeholders | Timezone handling, metadata extraction |
| `transfer_organized_footage.py` | Safe file transfer | Integrity verification, rollback support |
| `create_metadata.py` | DaVinci Resolve metadata | Color detection, intelligent grouping |
| `TagFootageByCSV.py` | DaVinci Resolve integration | Automatic tagging and coloring |
| `SORT_MEDIA_FOLDER.BAT` | Complete automation | Gyroflow integration, progress tracking |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `debug/metadata_inspector.py` | Debug metadata extraction issues |
| `debug/show_file_metadata.py` | **NEW!** Display complete metadata for any file |
| `SHOW_FILE_METADATA.BAT` | **NEW!** Windows wrapper for easy drag-and-drop metadata viewing |

---

## 📚 Documentation

Complete documentation is available in the [`documentation/`](documentation/) folder:

- **[INDEX.md](documentation/INDEX.md)** - Documentation index and navigation guide
- **[GUIDE_AJUSTEMENT_TEMPS.md](documentation/GUIDE_AJUSTEMENT_TEMPS.md)** - Time adjustment feature guide
- **[GUIDE_METADATA_VIEWER.md](documentation/GUIDE_METADATA_VIEWER.md)** - Metadata viewer tool guide
- **[CHANGELOG_STRUCTURE.md](documentation/CHANGELOG_STRUCTURE.md)** - Project structure changes
- **[CHANGEMENT_FORMAT_JSON.md](documentation/CHANGEMENT_FORMAT_JSON.md)** - JSON format migration
- **[AMELIORATION_LOGGING.md](documentation/AMELIORATION_LOGGING.md)** - Colored logging system

See the [documentation index](documentation/INDEX.md) for a complete list of available documentation.

---

## 🤝 Contributing

This project was developed to solve real-world video editing challenges. If you find it useful or have suggestions:

1. **Report Issues:** Use GitHub issues for bugs or feature requests
2. **Share Use Cases:** Let us know how you're using the system
3. **Contribute:** Pull requests welcome for improvements

## 📄 License & Credits

**Development Note:** This documentation and tool system were created primarily by Claude Sonnet 4 and ChatGPT-5, orchestrated and tested by Guillaume Blain.

The system is designed for practical video editing workflows and has been tested with real-world footage from multiple sources and camera types.