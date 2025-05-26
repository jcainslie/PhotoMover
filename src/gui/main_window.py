import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog
from src.utils.drive_manager import DriveManager
from src.utils.photo_operations import PhotoHandler
import os
import shutil
import threading


class PhotoMoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PhotoMover")
        self.root.geometry("1200x800")

        # Configure weight for better resize performance
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.resizable(False, False)

        # Initialize managers and variables
        self.drive_manager = DriveManager()
        self.photo_handler = PhotoHandler()
        self.processing = False
        self.current_file = tk.StringVar()
        self.progress_var = tk.DoubleVar()

        # Create and setup UI
        self._setup_tree_colors()
        self._create_widgets()
        self._setup_layout()

        # Bind events
        self.source_tree.bind('<<TreeviewOpen>>', self._on_tree_expand)
        self.dest_tree.bind('<<TreeviewOpen>>', self._on_tree_expand)

        # Schedule drive population
        self.root.after(100, self._delayed_init)
        self.root.resizable(True, True)

    def _setup_tree_colors(self):
        """Configure tree colors"""
        self.tree_colors = {
            'copied': '#90EE90',  # light green
            'renamed': '#FFFF99',  # light yellow
            'pending': '#FFA07A',  # salmon
            'duplicate': '#ADD8E6',  # light blue
            'default': ''  # default background
        }

    def _create_widgets(self):
        # Configure style
        style = ttk.Style()
        style.configure('Treeview', rowheight=25)

        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="10")

        # Create processing controls frame
        self.processing_frame = ttk.Frame(self.main_frame)
        self.move_btn = ttk.Button(self.processing_frame, text="Start Processing",
                                  command=self.move_selected)
        self.stop_btn = ttk.Button(self.processing_frame, text="Stop Processing",
                                  command=self.stop_processing, state='disabled')
        self.current_file_label = ttk.Label(self.processing_frame, textvariable=self.current_file)
        self.progress_bar = ttk.Progressbar(self.processing_frame, variable=self.progress_var,
                                       maximum=100, mode='determinate')

        # Create source frame
        self.source_frame = ttk.LabelFrame(self.main_frame, text="Source", padding="5")

        # Create destination frame
        self.dest_frame = ttk.LabelFrame(self.main_frame, text="Destination Folder", padding="5")

        # Create drive selection widgets
        self.drive_frame = ttk.Frame(self.source_frame)
        self.drive_label = ttk.Label(self.drive_frame, text="Select Drive:")
        self.drive_var = tk.StringVar()
        self.drive_combo = ttk.Combobox(self.drive_frame, textvariable=self.drive_var, state="readonly")
        self.refresh_btn = ttk.Button(self.drive_frame, text="Refresh Drive",
                                  command=self.refresh_drive_list)

        # Create source tree
        self.source_tree = ttk.Treeview(self.source_frame, show="tree")
        self.source_scrollbar = ttk.Scrollbar(self.source_frame,
                                          orient=tk.VERTICAL,
                                          command=self.source_tree.yview)
        self.source_tree.configure(yscrollcommand=self.source_scrollbar.set)

        # Create destination tree
        self.dest_tree = ttk.Treeview(self.dest_frame, show="tree", columns=('FullPath',))
        self.dest_tree.column('FullPath', width=0, stretch=tk.NO)
        self.dest_scrollbar = ttk.Scrollbar(self.dest_frame,
                                        orient=tk.VERTICAL,
                                        command=self.dest_tree.yview)
        self.dest_tree.configure(yscrollcommand=self.dest_scrollbar.set)

        # Create destination buttons
        self.refresh_dest_btn = ttk.Button(self.dest_frame, text="Refresh Folders",
                                       command=self.refresh_dest_folders)
        self.new_folder_btn = ttk.Button(self.dest_frame, text="New Folder",
                                     command=self.create_new_folder)

    def _setup_layout(self):
        # Main frame
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Processing controls at the top
        self.processing_frame.pack(fill=tk.X, pady=(0, 10))
        self.move_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.current_file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        # Source frame layout
        self.source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Drive selection layout
        self.drive_frame.pack(fill=tk.X, pady=(0, 5))
        self.drive_label.pack(side=tk.LEFT, padx=(0, 5))
        self.drive_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Source tree layout
        self.source_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.source_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Destination frame layout
        self.dest_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.refresh_dest_btn.pack(fill=tk.X, pady=(0, 5))
        self.new_folder_btn.pack(fill=tk.X, pady=(0, 5))
        self.dest_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.dest_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


    def refresh_drive_list(self):
        """Update the list of available drives"""
        current_selection = self.drive_var.get()

        available_drives = self.drive_manager.get_available_drives()
        drive_values = [f"{drive['path']} ({drive['label']})" for drive in available_drives]

        self.drive_combo['values'] = drive_values

        if drive_values:
            if current_selection and current_selection in drive_values:
                self.drive_var.set(current_selection)
                drive_path = current_selection.split(' ')[0]
            else:
                self.drive_var.set(drive_values[0])
                drive_path = available_drives[0]['path']

            self.refresh_drive_contents(drive_path)

    def refresh_drive_contents(self, drive_path=None):
        """Refresh the contents of the selected drive"""
        self.source_tree.delete(*self.source_tree.get_children())

        if drive_path is None:
            selected = self.drive_var.get()
            if not selected:
                return
            drive_path = selected.split(' ')[0]

        try:
            self._populate_tree(self.source_tree, drive_path)
        except Exception as e:
            messagebox.showerror("Error", f"Error accessing drive {drive_path}: {str(e)}")

    def _populate_tree(self, tree, path, parent=''):
        """Recursively populate tree with folder structure"""
        try:
            for entry in os.scandir(path):
                try:
                    if entry.name.startswith('$') or entry.name.startswith('.'):
                        continue

                    if entry.is_dir():
                        item_id = tree.insert(parent, 'end', text=entry.name, values=(entry.path,))

                        has_contents = False
                        try:
                            next(os.scandir(entry.path))
                            has_contents = True
                        except StopIteration:
                            pass
                        except PermissionError:
                            pass

                        if has_contents:
                            tree.insert(item_id, 'end')
                    elif entry.is_file():
                        tree.insert(parent, 'end', text=entry.name, values=(entry.path,))

                except PermissionError:
                    continue

        except PermissionError:
            pass
        except Exception as e:
            print(f"Error accessing {path}: {str(e)}")

    def _store_item_tags(self, tree, item):
        """Store the tags of an item and its children"""
        tags = {}
        tags[item] = tree.item(item)['tags']
        for child in tree.get_children(item):
            tags.update(self._store_item_tags(tree, child))
        return tags

    def _restore_item_tags(self, tree, tags):
        """Restore the tags of items"""
        for item, item_tags in tags.items():
            if item_tags:
                tree.item(item, tags=item_tags)

    def _on_tree_expand(self, event):
        """Handle tree node expansion"""
        tree = event.widget
        item = tree.focus()

        # Store existing tags before clearing children
        stored_tags = self._store_item_tags(tree, item)

        # Clear and repopulate children
        children = tree.get_children(item)
        if children:
            tree.delete(*children)

        path = tree.item(item)['values'][0]
        if path:
            self._populate_tree(tree, path, item)

        # Restore tags after repopulating
        self._restore_item_tags(tree, stored_tags)

    def refresh_dest_folders(self):
        """Refresh the destination folders tree"""
        self.dest_tree.delete(*self.dest_tree.get_children())

        available_drives = self.drive_manager.get_available_drives()
        special_folders = self.drive_manager.get_special_folders()

        try:
            for drive in available_drives:
                item_id = self.dest_tree.insert('', 'end',
                                                text=f"{drive['path']} ({drive['label']})",
                                                values=(drive['path'],))
                self.dest_tree.insert(item_id, 'end')

            for folder in special_folders:
                item_id = self.dest_tree.insert('', 'end',
                                                text=folder['label'],
                                                values=(folder['path'],))
                self.dest_tree.insert(item_id, 'end')

        except Exception as e:
            messagebox.showerror("Error", f"Error accessing folders: {str(e)}")

    def create_new_folder(self):
        """Create a new folder in the selected destination"""
        selected = self.dest_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a parent folder")
            return

        parent_path = self.dest_tree.item(selected[0])['values'][0]

        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if not folder_name:
            return

        try:
            new_path = os.path.join(parent_path, folder_name)
            os.makedirs(new_path, exist_ok=True)
            self.refresh_dest_folders()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create folder: {str(e)}")

    def update_item_color(self, tree, item, status):
        """Update the background color of a tree item"""
        tree.tag_configure(status, background=self.tree_colors[status])
        tree.item(item, tags=(status,))

    def update_folder_status(self, folder_item):
        """Update folder color based on contained files"""
        children = self.source_tree.get_children(folder_item)
        if not children:
            return

        has_pending = False
        has_renamed = False
        all_copied = True

        for child in children:
            child_tags = self.source_tree.item(child)['tags']
            if child_tags:
                if 'pending' in child_tags:
                    has_pending = True
                    all_copied = False
                elif 'renamed' in child_tags:
                    has_renamed = True
                elif 'copied' not in child_tags:
                    all_copied = False

            if self.source_tree.get_children(child):
                self.update_folder_status(child)

        if all_copied:
            self.update_item_color(self.source_tree, folder_item, 'copied')
        elif has_pending:
            self.update_item_color(self.source_tree, folder_item, 'pending')
        elif has_renamed:
            self.update_item_color(self.source_tree, folder_item, 'renamed')

    def update_progress(self, current_file, processed_count, total_files):
        """Update progress bar and current file label"""
        self.current_file.set(f"Processing: {os.path.basename(current_file)}")
        self.progress_var.set((processed_count / total_files) * 100)
        self.root.update()

    def stop_processing(self):
        """Stop the processing of files"""
        self.processing = False
        self.stop_btn.configure(state='disabled')
        self.move_btn.configure(state='normal')

    def get_unique_filename(self, filepath):
        """Generate unique filename if file exists"""
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)

        counter = 0
        while os.path.exists(filepath):
            counter += 1
            new_filename = f"{name}_{counter}{ext}"
            filepath = os.path.join(directory, new_filename)

        return filepath

    def move_selected(self):
        """Start processing files"""
        threading.Thread(target=self.process_files, daemon=True).start()

    def _delayed_init(self):
        """Initialize after main window is created"""
        self.refresh_drive_list()
        self.refresh_dest_folders()

    def process_files(self):
        """Process files in a separate thread"""
        selected_items = self.source_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a source folder")
            return

        selected_item = selected_items[0]
        source_path = self.source_tree.item(selected_item)['values'][0]

        if not os.path.isdir(source_path):
            messagebox.showwarning("Invalid Selection", "Please select a folder")
            return

        photos = []
        movies = []
        other_files = []

        def collect_files(folder_path, current_tree_item):
            try:
                for entry in os.scandir(folder_path):
                    if entry.name.startswith('$') or entry.name.startswith('.'):
                        continue

                    # Create tree item if it doesn't exist
                    entry_item = None
                    for child in self.source_tree.get_children(current_tree_item):
                        child_name = self.source_tree.item(child, 'text')
                        if child_name == entry.name:
                            entry_item = child
                            break

                    if not entry_item:
                        # Create new tree item
                        entry_item = self.source_tree.insert(current_tree_item, 'end',
                                                             text=entry.name,
                                                             values=(entry.path,))

                    if entry.is_file():
                        if self.photo_handler.is_image_file(entry.name):
                            photos.append((entry.path, entry_item))
                        elif self.photo_handler.is_movie_file(entry.name):
                            movies.append((entry.path, entry_item))
                        else:
                            other_files.append((entry.path, entry_item))
                    elif entry.is_dir():
                        # Recursively process subdirectories
                        collect_files(entry.path, entry_item)

            except PermissionError:
                messagebox.showerror("Error", f"Access denied to {folder_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error accessing {folder_path}: {str(e)}")

        collect_files(source_path, selected_item)

        if not (photos or movies or other_files):
            messagebox.showwarning("No Files", "No files found to process")
            return

        dest_selection = self.dest_tree.selection()
        if not dest_selection:
            messagebox.showwarning("No Destination", "Please select a destination folder")
            return

        base_dest_path = self.dest_tree.item(dest_selection[0])['values'][0]

        self.progress_var.set(0)
        total_files = len(photos) + len(movies) + len(other_files)

        self.processing = True
        self.move_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')

        processed_count = 0

        # Process photos
        for src_path, tree_item in photos:
            if not self.processing:
                break

            try:
                photo_date = self.photo_handler.get_photo_date(src_path)
                year_folder = str(photo_date.year)
                month_folder = f"{photo_date.month:02d}"

                year_path = os.path.join(base_dest_path, year_folder)
                month_path = os.path.join(year_path, month_folder)

                os.makedirs(year_path, exist_ok=True)
                os.makedirs(month_path, exist_ok=True)

                src_filename = os.path.basename(src_path)
                dest_file = os.path.join(month_path, src_filename)

                if os.path.exists(dest_file):
                    if src_filename == os.path.basename(dest_file) and self.photo_handler.are_images_same(src_path,
                                                                                                          dest_file):
                        self.update_item_color(self.source_tree, tree_item, 'duplicate')
                        continue
                    elif self.photo_handler.are_images_same(src_path, dest_file):
                        self.update_item_color(self.source_tree, tree_item, 'copied')
                        continue
                    else:
                        dest_file = self.get_unique_filename(dest_file)
                        self.update_item_color(self.source_tree, tree_item, 'renamed')

                shutil.copy2(src_path, dest_file)
                self.update_item_color(self.source_tree, tree_item, 'copied')

            except Exception as e:
                messagebox.showerror("Error", f"Error processing {src_path}: {str(e)}")
                self.update_item_color(self.source_tree, tree_item, 'pending')
                continue

            processed_count += 1
            self.update_progress(src_path, processed_count, total_files)

        # Process movies
        movies_folder = os.path.join(base_dest_path, "Movies")
        os.makedirs(movies_folder, exist_ok=True)

        for src_path, tree_item in movies:
            if not self.processing:
                break

            try:
                dest_file = os.path.join(movies_folder, os.path.basename(src_path))
                if os.path.exists(dest_file):
                    dest_file = self.get_unique_filename(dest_file)
                    self.update_item_color(self.source_tree, tree_item, 'renamed')
                else:
                    self.update_item_color(self.source_tree, tree_item, 'copied')

                shutil.copy2(src_path, dest_file)

            except Exception as e:
                messagebox.showerror("Error", f"Error processing {src_path}: {str(e)}")
                self.update_item_color(self.source_tree, tree_item, 'pending')
                continue

            processed_count += 1
            self.update_progress(src_path, processed_count, total_files)

        # Process other files
        other_folder = os.path.join(base_dest_path, "Other")
        os.makedirs(other_folder, exist_ok=True)

        for src_path, tree_item in other_files:
            if not self.processing:
                break

            try:
                dest_file = os.path.join(other_folder, os.path.basename(src_path))
                if os.path.exists(dest_file):
                    dest_file = self.get_unique_filename(dest_file)
                    self.update_item_color(self.source_tree, tree_item, 'renamed')
                else:
                    self.update_item_color(self.source_tree, tree_item, 'copied')

                shutil.copy2(src_path, dest_file)

            except Exception as e:
                messagebox.showerror("Error", f"Error processing {src_path}: {str(e)}")
                self.update_item_color(self.source_tree, tree_item, 'pending')
                continue

            processed_count += 1
            self.update_progress(src_path, processed_count, total_files)

        self.update_folder_status(selected_item)

        self.current_file.set("Processing complete" if self.processing else "Processing stopped")
        self.stop_btn.configure(state='disabled')
        self.move_btn.configure(state='normal')