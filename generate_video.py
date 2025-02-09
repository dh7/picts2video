import os
import random
import subprocess
import argparse
from pathlib import Path

def get_image_files(folder_path):
    """Get all image files from the specified folder."""
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
    image_files = []
    
    for file in os.listdir(folder_path):
        if file.lower().endswith(image_extensions):
            image_files.append(os.path.join(folder_path, file))
    
    return image_files

def create_video(image_files, output_path='output.mp4', duration_per_image=3):
    """Create a video from the list of image files using ffmpeg."""
    if not image_files:
        print("No image files found!")
        return

    # Create a temporary file with the list of images and their durations
    concat_file = 'temp_concat.txt'
    with open(concat_file, 'w') as f:
        for img in image_files:
            f.write(f"file '{img}'\n")
            f.write(f"duration {duration_per_image}\n")
        # Write the last file again (required by ffmpeg)
        f.write(f"file '{image_files[-1]}'\n")

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
