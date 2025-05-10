import tkinter as tk
from tkinter import ttk, filedialog
from extractor.extractor import SetExtractStrategy, IndividualExtractor, FileExtractor, IDListExtractor, PlaylistExtractor
from selenium_scraping.imdb_custom_parser_selenium import SeleniumScraper
from imdb import Cinemagoer
from extractor.translator import DeeplTranslator
from extractor.database import DBConnection
import os

class ExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor GUI")
        self.notebook = ttk.Notebook()
        self.notebook.pack(padx=5, pady=5)

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
        self.dropdown.pack(pady=10)

        # Placeholder for dynamic input (text or file)
        self.input_frame = tk.Frame(extract_tab)
        self.input_frame.pack()
        self.input_entry = ttk.Entry(self.input_frame, width=40)
        self.input_entry.pack()

        # Extract Button
        self.extract_button = ttk.Button(extract_tab, text="Extract", command=self.run_extraction)
        self.extract_button.pack(pady=10)
        self.db_button = ttk.Button(extract_tab, text="Insert into DB", command=self.insert_into_db)
        self.db_button.pack(pady=10, padx=10)

        # Output Box
        self.output_box = tk.Text(extract_tab, height=5, width=50, state='disabled')
        self.output_box.pack(pady=10)

        """
        Edit tab
        """
        # Dropdown edit db tab
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
            self.input_entry = ttk.Entry(self.input_frame, width=40)
            self.input_entry.pack()
        elif selection == "File with IDs":
            self.file_path_var = tk.StringVar()
            file_entry = ttk.Entry(self.input_frame, textvariable=self.file_path_var, width=30)
            file_entry.pack(side=tk.LEFT)
            browse_button = ttk.Button(self.input_frame, text="Browse", command=self.browse_file)
            browse_button.pack(side=tk.LEFT)

    def browse_file(self):
        filepath = filedialog.askopenfilename(initialdir=os.path.curdir)
        if filepath:
            self.file_path_var.set(filepath)

    def insert_into_db(self, ext_movs):
        db_con = DBConnection('movies.db')
        if not ext_movs:
            return
        db_con.insert_data(ext_movs)
        db_con.close_connection()

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
        imdb = Cinemagoer()
        selenium_scraper = SeleniumScraper()
        translator = DeeplTranslator()
        input_value = None
        strat = SetExtractStrategy(None)
        if selection == "Individual ID":
            input_value = self.input_entry.get()
            assert input_value.startswith('tt'), 'Please give full imdb movie id.'
            strat.set_extract_method(IndividualExtractor(
                selenium_scraper=selenium_scraper,
                translator=translator,
                imdb=imdb,
                movie_id=input_value
                )
            )
        elif selection == "File with IDs":
            input_value = self.file_path_var.get()
            strat.set_extract_method(FileExtractor(
                selenium_scraper=selenium_scraper,
                translator=translator,
                imdb=imdb,
                file=input_value)
            )
        elif selection == "Playlist":
            input_value = self.input_entry.get()
            strat.set_extract_method(PlaylistExtractor(
                selenium_scraper=selenium_scraper,
                translator=translator,
                imdb=imdb,
                playlist_url=input_value)
            )
            print(strat)
        else:
            input_value = ""

        result: list[dict] = strat.extract()
        self.EXTRACTED_MOVIES = result

        # Show result in output box
        self.output_box.config(state='normal')
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(tk.END, f"{result}")
        self.output_box.config(state='disabled')

        return result

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtractorApp(root)
    root.mainloop()