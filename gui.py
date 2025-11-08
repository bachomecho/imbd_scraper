import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from extractor.extractor import SetExtractStrategy, IndividualExtractor, FileExtractor, PlaylistExtractor
from extractor.database import DBConnection
import os, json
from dotenv import load_dotenv
load_dotenv('.env')

def box_logging(box, movies):
    box.delete(1.0, tk.END)
    if isinstance(movies, (dict, list)):
        text = json.dumps(movies, indent=2, ensure_ascii=False)
    else:
        text = str(movies)
    box.insert(tk.END, text)

class ExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor GUI")
        self.root.geometry("1000x700")
        self.notebook = ttk.Notebook()
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        extract_tab = ttk.Frame(self.notebook)
        plot_edit_tab = ttk.Frame(self.notebook)  # New tab for plot editing
        self.notebook.add(extract_tab, text='Extract movie data', padding=20)
        self.notebook.add(plot_edit_tab, text='Edit Plots', padding=20)  # Add new tab

        # Extract tab
        options = ["Individual ID", "File with IDs", "Playlist"]
        self.selected_option_strat = tk.StringVar(value=options[0])
        self.dropdown = ttk.OptionMenu(extract_tab, self.selected_option_strat, options[0], *options, command=self.update_input_field)
        self.dropdown.pack(pady=10, fill='x')

        # Placeholder for dynamic input (text or file)
        self.input_frame = tk.Frame(extract_tab)
        self.input_frame.pack(fill='x')
        self.input_entry = ttk.Entry(self.input_frame, width=60)
        self.input_entry.pack(fill='x', padx=5)

        # Extract Button
        controls_frame = tk.Frame(extract_tab)
        controls_frame.pack(pady=10, fill='x')
        self.extract_button = ttk.Button(controls_frame, text="Extract", command=self.run_extraction)
        self.extract_button.pack(side='left', padx=(0,10))
        self.db_button = ttk.Button(controls_frame, text="Insert into DB", command=self.insert_into_db)
        self.db_button.pack(side='left', padx=(0,10))
        self.image_search_button = ttk.Button(controls_frame, text="Copy 'title year' to clipboard", command=self.copy_title_year)
        self.image_search_button.pack(side='left', padx=(0,10))

        # Output Box with scrollbar (editable)
        output_frame = tk.Frame(extract_tab)
        output_frame.pack(pady=10, fill='both', expand=True)
        self.output_box = tk.Text(output_frame, height=20, width=100, wrap='none')
        vsb = ttk.Scrollbar(output_frame, orient='vertical', command=self.output_box.yview)
        hsb = ttk.Scrollbar(output_frame, orient='horizontal', command=self.output_box.xview)
        self.output_box.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.output_box.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')

        # plot edit tab
        self.plot_movies = []
        self.plot_movie_var = tk.StringVar()
        self.plot_dropdown = ttk.Combobox(plot_edit_tab, textvariable=self.plot_movie_var, state="readonly", width=60)
        self.plot_dropdown.pack(pady=10, padx=10)

        self.copy_plot_btn = ttk.Button(plot_edit_tab, text="Copy Original Plot", command=self.copy_original_plot)
        self.copy_plot_btn.pack(pady=5)

        self.plot_edit_box = tk.Text(plot_edit_tab, height=10, width=80, wrap='word')
        self.plot_edit_box.pack(pady=10, padx=10)

        self.overwrite_plot_btn = ttk.Button(plot_edit_tab, text="Overwrite Plot in Extracted Data", command=self.overwrite_plot)
        self.overwrite_plot_btn.pack(pady=5)

        # Initialize input field
        self.update_input_field(options[0])
        self.EXTRACTED_MOVIES = None

    def update_input_field(self, selection):
        for widget in self.input_frame.winfo_children():
            widget.destroy()

        if selection == "Individual ID" or selection == 'Playlist':
            self.input_entry = ttk.Entry(self.input_frame, width=60)
            self.input_entry.pack(fill='x', padx=5)
        elif selection == "File with IDs":
            self.file_path_var = tk.StringVar()
            file_entry = ttk.Entry(self.input_frame, textvariable=self.file_path_var, width=45)
            file_entry.pack(side=tk.LEFT, padx=5)
            browse_button = ttk.Button(self.input_frame, text="Browse", command=self.browse_file)
            browse_button.pack(side=tk.LEFT, padx=5)

    def browse_file(self):
        filepath = filedialog.askopenfilename(initialdir=os.path.curdir)
        if filepath:
            self.file_path_var.set(filepath)

    def parse_json_from_output_box(self):
        content = self.output_box.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("No data", "No extracted data available.")
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON error", f"Could not parse JSON from output box:\n{e}")
            return None

    def insert_into_db(self):
        db_con = DBConnection('movies.db')
        parsed_json_content = self.parse_json_from_output_box()
        if parsed_json_content is None:
            db_con.close_connection()
            return
        if not isinstance(parsed_json_content, list):
            messagebox.showwarning("Invalid format", "Expected a JSON array of movie objects.")
            db_con.close_connection()
            return

        # ensure every item has an imdb_id
        if not all(isinstance(item, dict) and item.get('imdb_id') for item in parsed_json_content):
            messagebox.showwarning("Missing imdb_id", "One or more entries are missing 'imdb_id'. Please fix before inserting.")
            db_con.close_connection()
            return

        # check for duplicates in DB
        existing_rows = db_con.retrieve_all_ids()
        existing_ids = set(row[0] for row in existing_rows)
        parsed_ids = [item['imdb_id'] for item in parsed_json_content]
        duplicates = [mid for mid in parsed_ids if mid in existing_ids]

        if duplicates:
            sample = ", ".join(duplicates[:10])
            more = f"... (+{len(duplicates)-10} more)" if len(duplicates) > 10 else ""
            answer = messagebox.askyesno(
                "Duplicate entries",
                f"Found {len(duplicates)} duplicates in the database (e.g. {sample}{more}).\n\n"
                "Skip duplicates and insert the remaining entries? (Yes = skip duplicates; No = cancel)"
            )
            if not answer:
                db_con.close_connection()
                return
            # filter out duplicates and insert remaining
            filtered = [item for item in parsed_json_content if item['imdb_id'] not in existing_ids]
            if not filtered:
                messagebox.showinfo("Nothing to insert", "All entries were duplicates. No data inserted.")
                db_con.close_connection()
                return
            to_insert = filtered
        else:
            to_insert = parsed_json_content

        self.EXTRACTED_MOVIES = to_insert
        db_con.insert_data(self.EXTRACTED_MOVIES)
        db_con.close_connection()
        messagebox.showinfo("Success", f"Inserted {len(self.EXTRACTED_MOVIES)} record(s) into database.")

    def run_extraction(self):
        selection = self.selected_option_strat.get()
        input_value = None
        strat = SetExtractStrategy(None)
        if selection == "Individual ID":
            input_value = self.input_entry.get()
            assert input_value.startswith('tt'), 'Please give full imdb movie id.'
            strat.set_extract_method(IndividualExtractor(movie_id=input_value)
            )
        elif selection == "File with IDs":
            input_value = self.file_path_var.get()
            strat.set_extract_method(FileExtractor(file=input_value)
            )
        elif selection == "Playlist":
            input_value = self.input_entry.get()
            strat.set_extract_method(PlaylistExtractor(playlist_url=input_value)
            )
            print(strat)
        else:
            input_value = ""

        result: list[dict] = strat.extract()
        """
        create a file containing results in case the db operations fail and you want to load a backup of the extracted data
        """
        with open('last_extraction_backup.json', 'w', encoding='utf-8') as backup:
            json.dump(result, backup, ensure_ascii=False, indent=2)

        # check for duplicate movies in db after extraction of new movie data
        try:
            db_con = DBConnection('movies.db')
            existing_rows = db_con.retrieve_all_ids()
            existing_ids = set(row[0] for row in existing_rows)
            dup_items = [
                (item.get('imdb_id'), item.get('title', '<no title>'))
                for item in result
                if item.get('imdb_id') in existing_ids
            ]

            if dup_items:
                sample = ", ".join(f"{mid} ({title})" for mid, title in dup_items[:10])
                more = f"... (+{len(dup_items)-10} more)" if len(dup_items) > 10 else ""
                keep_or_remove = messagebox.askyesno(
                    "Duplicate entries found",
                    f"Found {len(dup_items)} extracted entries that already exist in the database "
                    f"(e.g. {sample}{more}).\n\n"
                    "Remove these duplicates from the extracted results before showing/inserting? "
                    "(Yes = remove; No = keep)"
                )
                if keep_or_remove:
                    filtered = [item for item in result if item.get('imdb_id') not in existing_ids]
                    removed = len(result) - len(filtered)
                    result = filtered
                    messagebox.showinfo("Duplicates removed", f"Removed {removed} duplicate(s) from extracted results.")
        except Exception as e:
            # non-fatal: just print and continue with results
            print(f"[!] Could not check DB for duplicates: {e}")
        finally:
            try: db_con.close_connection()
            except: pass

        self.EXTRACTED_MOVIES = result

        # Update plot tab dropdown with new movies
        self.update_plot_tab_movies(result)

        box_logging(self.output_box, result)
        return result

    def update_plot_tab_movies(self, movies):
        if not movies:
            self.plot_movies = []
            self.plot_dropdown['values'] = []
            self.plot_movie_var.set('')
            return
        self.plot_movies = movies if isinstance(movies, list) else [movies]
        titles = []
        for m in self.plot_movies:
            title = m.get('title', '')
            year = m.get('release_year', '')
            display = f"{title} ({year})" if year else title
            titles.append(display)
        self.plot_dropdown['values'] = titles
        if titles:
            self.plot_movie_var.set(titles[0])
        else:
            self.plot_movie_var.set('')

    def copy_original_plot(self):
        # Copy the original English plot to clipboard and to the edit box
        idx = self.plot_dropdown.current()
        if idx == -1 or not self.plot_movies:
            messagebox.showwarning("No movie", "No movie selected.")
            return
        movie = self.plot_movies[idx]
        plot = movie.get('plot', '')
        if not plot:
            messagebox.showwarning("No plot", "Selected movie has no plot.")
            return
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(plot)
            self.root.update()
            self.plot_edit_box.delete(1.0, tk.END)
            self.plot_edit_box.insert(tk.END, plot)
            messagebox.showinfo("Copied", "Original plot copied to clipboard and edit box.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy plot:\n{e}")

    def overwrite_plot(self):
        idx = self.plot_dropdown.current()
        if idx == -1 or not self.plot_movies:
            messagebox.showwarning("No movie", "No movie selected.")
            return
        new_plot = self.plot_edit_box.get(1.0, tk.END).strip()
        if not new_plot:
            messagebox.showwarning("No plot", "Edited plot is empty.")
            return
        movie = self.plot_movies[idx]
        imdb_id = movie.get('imdb_id')
        updated = False
        if self.EXTRACTED_MOVIES:
            for m in self.EXTRACTED_MOVIES:
                if m.get('imdb_id') == imdb_id:
                    m['plot'] = new_plot
                    updated = True
                    break
        if updated:
            box_logging(self.output_box, self.EXTRACTED_MOVIES)
            messagebox.showinfo("Success", "Plot updated in extracted data.")
        else:
            messagebox.showwarning("Not found", "Could not find movie to update.")

    def parse_json_from_output_box(self):
        content = self.output_box.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("No data", "No extracted data available.")
            return None
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON error", f"Could not parse JSON from output box:\n{e}")
            return None

    def copy_title_year(self):
        movies = self.parse_json_from_output_box()
        if not movies:
            messagebox.showwarning("No movie", "No extracted movie available. Run an extraction first.")
            return

        # Convert to list if single movie
        movies_list = movies if isinstance(movies, list) else [movies]

        if not movies_list:
            messagebox.showwarning("No movies", "No movies found in the data.")
            return

        # Create popup dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Movie")
        dialog.geometry("400x150")
        dialog.transient(self.root)  # Make dialog modal
        dialog.grab_set()

        label = ttk.Label(dialog, text="Select movie to copy:")
        label.pack(pady=10)

        # Create combobox with movie titles
        movie_var = tk.StringVar()
        combo_values = []
        title_to_movie = {}

        for movie in movies_list:
            title = movie.get('title', '')
            year = movie.get('release_year', '')
            display_text = f"{title} ({year})" if year else title
            if title:
                combo_values.append(display_text)
                title_to_movie[display_text] = movie

        if not combo_values:
            dialog.destroy()
            messagebox.showwarning("Missing titles", "None of the movies have titles.")
            return

        combo = ttk.Combobox(dialog, textvariable=movie_var, values=combo_values, width=50)
        combo.set(combo_values[0])  # first movie default
        combo.pack(pady=10, padx=10)

        def on_copy():
            selected = movie_var.get()
            if selected in title_to_movie:
                movie = title_to_movie[selected]
                title = movie.get('title', '')
                year = movie.get('release_year', '')
                combo_text = f"{title} {year} филм".strip()

                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(combo_text)
                    self.root.update()
                    messagebox.showinfo("Copied", f"Copied to clipboard:\n{combo_text}")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Could not copy to clipboard:\n{e}")
            else:
                messagebox.showwarning("Error", "Please select a movie first.")

        # copy button
        copy_btn = ttk.Button(dialog, text="Copy", command=on_copy)
        copy_btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtractorApp(root)
    root.mainloop()