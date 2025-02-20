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

def create_video_chunk(images, output_path, duration_per_image, fade_duration):
    """Create a video chunk from a subset of images with crossfade transitions."""
    if not images:
        return False
        
    # Special case for single image
    if len(images) == 1:
        cmd = [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel', 'error',
            '-loop', '1',
            '-framerate', '30',
            '-t', str(duration_per_image),
            '-i', images[0],
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            output_path
        ]
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating video chunk: {e}")
            return False

    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        # First, convert each image to a video clip with fade in/out
        video_clips = []
        for i, img in enumerate(images):
            clip_path = os.path.join(temp_dir, f'clip_{i}.mp4')
            # Add fade in/out for each clip except first (no fade in) and last (no fade out)
            fade_filter = ''
            if i == 0:
                fade_filter = f'fade=t=out:st={duration_per_image-fade_duration}:d={fade_duration}'
            elif i == len(images) - 1:
                fade_filter = f'fade=t=in:st=0:d={fade_duration}'
            else:
                fade_filter = f'fade=t=in:st=0:d={fade_duration},fade=t=out:st={duration_per_image-fade_duration}:d={fade_duration}'

            cmd = [
                'ffmpeg',
                '-y',
                '-hide_banner',
                '-loglevel', 'error',
                '-loop', '1',
                '-framerate', '30',
                '-t', str(duration_per_image),
                '-i', img,
                '-vf',
                f'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,{fade_filter}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                clip_path
            ]
            try:
                subprocess.run(cmd, check=True)
                video_clips.append(clip_path)
            except subprocess.CalledProcessError as e:
                print(f"Error creating clip for {img}: {e}")
                return False

        # Create a list file for concatenation
        list_file = os.path.join(temp_dir, 'list.txt')
        with open(list_file, 'w') as f:
            for clip in video_clips:
                f.write(f"file '{clip}'\n")

        # Concatenate all clips
        cmd = [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating final video: {e}")
            return False

def create_video(image_files, output_path='output.mp4', duration_per_image=3):
    """Create a video from the list of image files using ffmpeg."""
    if not image_files:
        print("No image files found!")
        return

    print(f"\nProcessing {len(image_files)} images...")

    # Create a temporary directory for processed images and chunks
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process all images and get their temporary paths
        print("\nStep 1: Processing images and fixing orientations...")
        processed_images = []
        for i, img in enumerate(image_files, 1):
            print(f"Processing image {i}/{len(image_files)}: {os.path.basename(img)}")
            processed_path = process_image_with_exif(img, temp_dir)
            processed_images.append(processed_path)
        print("Image processing complete!")
        
        # Parameters for transitions
        fade_duration = 0.5
        chunk_size = 10  # Process 10 images at a time
        
        # Create video chunks
        total_chunks = (len(processed_images) + chunk_size - 1) // chunk_size
        print(f"\nStep 2: Creating {total_chunks} video chunks...")
        chunk_files = []
        
        # Process chunks in order
        for chunk_start in range(0, len(processed_images), chunk_size):
            chunk_num = (chunk_start // chunk_size) + 1
            chunk_end = min(chunk_start + chunk_size, len(processed_images))
            chunk = processed_images[chunk_start:chunk_end]
            
            print(f"\nProcessing chunk {chunk_num}/{total_chunks} ({len(chunk)} images)")
            print("Images in this chunk:")
            for i, img in enumerate(chunk, 1):
                print(f"  {i}. {os.path.basename(img)}")
            
            chunk_output = os.path.join(temp_dir, f'chunk_{chunk_start:03d}.mp4')
            if create_video_chunk(chunk, chunk_output, duration_per_image, fade_duration):
                chunk_files.append(chunk_output)
                print(f"Successfully created chunk: {os.path.basename(chunk_output)}")
            else:
                print(f"Warning: Failed to process chunk {chunk_num}")

        if not chunk_files:
            print("Failed to create any video chunks!")
            return

        print(f"\nStep 3: Combining {len(chunk_files)} chunks into final video...")
        print("Chunks in order:")
        for i, chunk in enumerate(chunk_files, 1):
            print(f"{i}. {os.path.basename(chunk)}")

        # If we only have one chunk, it's our final video
        if len(chunk_files) == 1:
            print("Only one chunk - using it as final video")
            os.rename(chunk_files[0], output_path)
            print(f"\nVideo created successfully: {output_path}")
            estimated_duration = len(image_files) * duration_per_image
            print(f"Duration: approximately {estimated_duration} seconds")
            return

        # Create a concat file for the chunks
        concat_file = os.path.join(temp_dir, 'chunks.txt')
        print("\nWriting concat file with the following order:")
        with open(concat_file, 'w') as f:
            for chunk in chunk_files:
                print(f"- {os.path.basename(chunk)}")
                f.write(f"file '{chunk}'\n")

        # Concatenate all chunks into final video
        print("\nMerging chunks into final video...")
        cmd = [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel', 'error',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"\nVideo created successfully: {output_path}")
            estimated_duration = len(image_files) * duration_per_image
            print(f"Duration: approximately {estimated_duration} seconds")
        except subprocess.CalledProcessError as e:
            print(f"\nError creating final video: {e}")

def main():
    parser = argparse.ArgumentParser(description='Create video from images in a folder')
    parser.add_argument('folder_path', help='Path to folder containing images')
    parser.add_argument('--output', default='output.mp4', help='Output video path')
    parser.add_argument('--duration', type=int, default=3, help='Duration per image in seconds')
    parser.add_argument('--first-image', help='Specify the filename or path of the image to appear first in the video')
    
    args = parser.parse_args()
    
    # Get list of image files
    image_files = get_image_files(args.folder_path)
    
    if not image_files:
        print(f"No image files found in {args.folder_path}")
        return
    
    print("\nInitial image list:")
    for img in image_files:
        print(f"- {os.path.basename(img)}")
    
    # Handle first image selection
    if args.first_image:
        # Convert the first image to absolute path if it's not already
        first_image_path = args.first_image
        if not os.path.isabs(first_image_path):
            first_image_path = os.path.join(args.folder_path, first_image_path)
        
        print(f"\nLooking for first image: {args.first_image}")
        print(f"Full path: {first_image_path}")
        
        # Try to find the image both by absolute path and by basename
        first_image_found = None
        for img in image_files:
            if img == first_image_path or os.path.basename(img) == os.path.basename(first_image_path):
                first_image_found = img
                break
        
        if first_image_found:
            print(f"Found first image: {os.path.basename(first_image_found)}")
            # Remove the first image from the list and shuffle the rest
            image_files.remove(first_image_found)
            random.shuffle(image_files)
            # Put the first image back at the beginning
            image_files.insert(0, first_image_found)
            print("\nFinal image order:")
            for img in image_files:
                print(f"- {os.path.basename(img)}")
        else:
            print(f"Warning: Specified first image '{args.first_image}' not found in folder. Using random order.")
            random.shuffle(image_files)
    else:
        # Randomize the order if no first image specified
        random.shuffle(image_files)
    
    # Create the video
    create_video(image_files, args.output, args.duration)

if __name__ == "__main__":
    main()
