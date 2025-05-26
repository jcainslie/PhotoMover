from PIL import Image
import os
from datetime import datetime
import imagehash

class PhotoHandler:
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        
    def is_image_file(self, filename):
        """Check if file is an image based on extension."""
        return os.path.splitext(filename)[1].lower() in self.supported_formats
        
    def get_image_info(self, filepath):
        """Get image information including metadata."""
        try:
            with Image.open(filepath) as img:
                info = {
                    'size': os.path.getsize(filepath),
                    'dimensions': img.size,
                    'format': img.format,
                    'modified': datetime.fromtimestamp(
                        os.path.getmtime(filepath)
                    ).strftime('%Y-%m-%d %H:%M:%S')
                }
                return info
        except Exception as e:
            return None
            
    def move_photo(self, source, destination):
        """Move photo to destination folder."""
        try:
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            os.rename(source, destination)
            return True
        except Exception as e:
            return False

    def get_image_hash(self, filepath):
        """Calculate perceptual hash of image for comparison"""
        try:
            with Image.open(filepath) as img:
                return str(imagehash.average_hash(img))
        except Exception:
            return None

    def are_images_same(self, path1, path2):
        """
        Compare two images considering possible rotations
        Returns True if images are the same or rotated versions of each other
        """
        # First check if both files are images
        if not (self.is_image_file(path1) and self.is_image_file(path2)):
            return False
        
        try:
            # Open both images
            img1 = Image.open(path1)
            img2 = Image.open(path2)
            
            # Convert images to same mode if different
            if img1.mode != img2.mode:
                img1 = img1.convert(img2.mode)
            
            # Calculate hash of first image
            hash1 = imagehash.average_hash(img1)
            
            # Check original and rotated versions of second image
            for angle in [0, 90, 180, 270]:
                rotated_img2 = img2.rotate(angle, expand=True)
                hash2 = imagehash.average_hash(rotated_img2)
            
                # Compare hashes - if difference is small enough, consider images same
                if hash1 - hash2 < 5:  # Threshold can be adjusted
                    return True
            
            return False
        
        except Exception as e:
            print(f"Error comparing images: {str(e)}")
            return False

    def get_photo_date(self, filepath):
        """Get the date the photo was taken from EXIF data, or file modification date as fallback"""
        try:
            with Image.open(filepath) as img:
                # Check for EXIF data
                if hasattr(img, '_getexif') and img._getexif() is not None:
                    exif = img._getexif()
                    # Check for DateTimeOriginal (tag 36867) or DateTime (tag 306)
                    if 36867 in exif:  # DateTimeOriginal
                        date_str = exif[36867]
                        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    elif 306 in exif:   # DateTime
                        date_str = exif[306]
                        return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            return datetime.fromtimestamp(os.path.getmtime(filepath))
        except Exception as e:
            # If any error occurs, fall back to file modification time
            print(f"Error getting photo date: {str(e)}")
            return datetime.fromtimestamp(os.path.getmtime(filepath))
            
    def is_movie_file(self, filename):
        """Check if a file is a movie based on its extension"""
        movie_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v'}
        return os.path.splitext(filename.lower())[1] in movie_extensions