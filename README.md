Simple windows python application to copy files from one directory to another. It will create destination directories based upon the photo's "Date Taken". If there is no date taken it will use the photo's "Modified Date". The destination folder structure will be as follows:
- Photos are sorted into folders by year and month:
  ```
  destination_folder/
  ├── 2024/
  │   ├── 01/
  │   ├── 02/
  │   └── ...
  ```
- Videos are placed in a "Movies" folder
- Other files are placed in an "Other" folder

The application uses color coding to indicate file status:
- 🟩 Green: Successfully copied
- 🟨 Yellow: Renamed due to naming conflict
- 🟧 Salmon: Pending processing or error copying
- 🟦 Light Blue: Duplicate file detected

Naming Conflict
    *The application will append *_1.jpg to the file with the 1 being incremented with each duplicate file name.

Duplicate file
    The application will assign a duplicate file status when the filename and the image hash are the same. It will also rotate the file during duplication check.

1. To run the application, copy the repo to your PC.
2. Install required packages.
3. Run src/main.py
4. When the application launches, select the "Source" drive. and click the "Refresh Files" button.
5. Select the folder that you want to use as the source folder.
6. Select the "Destination" folder.
7. Click the "Start Processing" button.

The application will iterate through all files and subfolders in the source directory.

