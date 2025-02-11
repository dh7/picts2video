# Picts2Video

A Python tool that creates beautiful videos from your image collections, with smooth crossfade transitions and automatic EXIF rotation handling.

## Features

- Creates videos from multiple image formats (JPG, JPEG, PNG, BMP, GIF, TIFF)
- Automatically handles image rotation based on EXIF data
- Adds smooth crossfade transitions between images
- Standardizes output to 1920x1080 resolution while preserving aspect ratio
- Supports customizable duration per image
- Processes images in batches for efficient memory usage

## Requirements

- Python 3.x
- FFmpeg
- Python packages:
  - Pillow (PIL)

## Installation

1. Ensure you have Python 3.x installed on your system
2. Install FFmpeg:
   - macOS (using Homebrew): `brew install ffmpeg`
3. Install required Python packages:
   ```bash
   pip install Pillow
   ```

## Usage

Basic usage:
```bash
python generate_video.py --input_folder /path/to/images --output output.mp4 --duration 3
```

Arguments:
- `--input_folder`: Directory containing your images
- `--output`: Output video file path (default: output.mp4)
- `--duration`: Duration each image should appear in seconds (default: 3)

## Output

The script generates an MP4 video with the following specifications:
- Resolution: 1920x1080
- Frame rate: 30 fps
- Video codec: H.264
- Pixel format: YUV420P
- Crossfade transition duration: 0.5 seconds

## Notes

- Images are automatically centered and padded if they don't match the target aspect ratio
- The script maintains the original aspect ratio of your images
- EXIF rotation is automatically corrected
- Progress is displayed during video creation

## Error Handling

The script includes robust error handling for:
- Invalid image files
- EXIF processing issues
- FFmpeg conversion errors

## License

This project is open source and available under the MIT License.
