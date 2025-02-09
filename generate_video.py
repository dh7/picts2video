import os
import random
import subprocess
import argparse
from pathlib import Path
from PIL import Image
import tempfile

def get_image_files(folder_path):
    """Get all image files from the specified folder."""
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
    image_files = []
    
    for file in os.listdir(folder_path):
        if file.lower().endswith(image_extensions):
            image_files.append(os.path.join(folder_path, file))
    
    return image_files

def process_image_with_exif(image_path, temp_dir):
    """Process image to handle EXIF rotation and return the path to the processed image."""
    try:
        with Image.open(image_path) as img:
            # Auto-rotate image according to EXIF data
            img = Image.open(image_path)
            rotated = img._getexif()
            if rotated is not None:
                orientation = rotated.get(274)  # 274 is the orientation tag in EXIF
                if orientation:
                    # Rotate according to EXIF orientation
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
            
            # Save to temporary file
            temp_path = os.path.join(temp_dir, os.path.basename(image_path))
            img.save(temp_path, quality=95)
            return temp_path
    except Exception as e:
        print(f"Warning: Could not process {image_path}: {e}")
        return image_path

def create_video(image_files, output_path='output.mp4', duration_per_image=3):
    """Create a video from the list of image files using ffmpeg."""
    if not image_files:
        print("No image files found!")
        return

    # Create a temporary directory for processed images
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process all images and get their temporary paths
        processed_images = [process_image_with_exif(img, temp_dir) for img in image_files]

        # Create a temporary file with the list of images and their durations
        concat_file = 'temp_concat.txt'
        with open(concat_file, 'w') as f:
            for img in processed_images:
                f.write(f"file '{img}'\n")
                f.write(f"duration {duration_per_image}\n")
            # Write the last file again (required by ffmpeg)
            f.write(f"file '{processed_images[-1]}'\n")

        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Video created successfully: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating video: {e}")
        finally:
            # Clean up temporary file
            os.remove(concat_file)

def main():
    parser = argparse.ArgumentParser(description='Create video from images in a folder')
    parser.add_argument('folder_path', help='Path to folder containing images')
    parser.add_argument('--output', default='output.mp4', help='Output video path')
    parser.add_argument('--duration', type=int, default=3, help='Duration per image in seconds')
    
    args = parser.parse_args()
    
    # Get list of image files
    image_files = get_image_files(args.folder_path)
    
    if not image_files:
        print(f"No image files found in {args.folder_path}")
        return
    
    # Randomize the order
    random.shuffle(image_files)
    
    # Create the video
    create_video(image_files, args.output, args.duration)

if __name__ == "__main__":
    main()
