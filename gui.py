import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from extractor.extractor import SetExtractStrategy, IndividualExtractor, FileExtractor, IDListExtractor, PlaylistExtractor
from selenium_scraping.imdb_custom_parser_selenium import SeleniumScraper
from imdb import Cinemagoer
from extractor.translator import DeeplTranslator
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
        edit_db_tab = ttk.Frame(self.notebook)
        self.notebook.add(extract_tab, text='Extract movie data', padding=20)
        self.notebook.add(edit_db_tab, text='Edit database', padding=20)
        """
        Extract tab
        """
        # Dropdown extract tab
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
        self.load_backup = ttk.Button(controls_frame, text="Load last backup", command=self.load_backup)
        self.load_backup.pack(side='left', padx=(0,10))
        self.db_button = ttk.Button(controls_frame, text="Insert into DB", command=self.insert_into_db)
        self.db_button.pack(side='left', padx=(0,10))

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

        db_keys = [
            "title",
            "thumbnail_name",
            "video_id",
            "site",
            "video_id_1",
            "site_1",
            "gledambg_video_id",
            "multi_part",
            "duration",
            "release_year",
            "genre",
            "rating",
            "director",
            "plot",
        ]
        self.selected_option_db_key = tk.StringVar(value=db_keys[0])
        self.dropdown_edit_db= ttk.OptionMenu(edit_db_tab, self.selected_option_db_key, db_keys[0], *db_keys, command=self.update_input_field)
        self.dropdown_edit_db.pack(pady=10)
        self.edit_db_button = ttk.Button(edit_db_tab, text="Extract and update database", command=self.run_update)
        self.edit_db_button.pack(pady=20)

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

    def load_backup(self):
        movies = None
        try:
            with open('last_extraction_backup.json', 'r', encoding='utf-8') as backup:
                movies = json.load(backup)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load backup: {e}")
            return
        if movies:
            self.EXTRACTED_MOVIES = movies
            box_logging(self.output_box, movies)
            print('[+] Backup has been loaded')
        else:
            print('[-] Backup is either empty or did not load properly')

    def run_update(self):
        db_con = DBConnection('movies.db')
        all_ids = [id[0] for id in db_con.retrieve_all_ids()]
        assert isinstance(all_ids, list), 'all_ids is not a list'
        selection = self.selected_option_db_key.get()
        imdb = Cinemagoer()
        selenium_scraper = SeleniumScraper() if selection == 'plot' else None
        translator = DeeplTranslator()
        strat = SetExtractStrategy(IDListExtractor(
                selenium_scraper=selenium_scraper,
                translator=translator,
                imdb=imdb,
                extract_sole_field=selection,
                id_list=all_ids,
            )
        )
        result = strat.extract()
        update_data = [{'imdb_id': d['imdb_id'], selection:d[selection]} for d in result]
        db_con.update_field_for_all_movies(selection, update_data)
        db_con.close_connection()

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

        box_logging(self.output_box, result)
        return result

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtractorApp(root)
    root.mainloop()