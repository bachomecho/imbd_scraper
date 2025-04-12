import tkinter as tk
from tkinter import ttk, filedialog
from extractor.extractor import SetExtractStrategy, IndividualExtractor, FileExtractor
from selenium_scraping.imdb_custom_parser_selenium import SeleniumScraper
from imdb import Cinemagoer
from extractor.translator import DeeplTranslator
from extractor.database import DBConnection
import os

class ExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor GUI")

        # Dropdown
        self.options = ["Individual ID", "File with IDs"]
        self.selected_option = tk.StringVar(value=self.options[0])
        self.dropdown = ttk.OptionMenu(root, self.selected_option, self.options[0], *self.options, command=self.update_input_field)
        self.dropdown.pack(pady=10)

        # Placeholder for dynamic input (text or file)
        self.input_frame = tk.Frame(root)
        self.input_frame.pack()

        # Extract Button
        self.extract_button = ttk.Button(root, text="Extract", command=self.run_extraction)
        self.extract_button.pack(pady=10)
        self.db_button = ttk.Button(root, text="Insert into DB", command=self.insert_into_db)
        self.db_button.pack(pady=10, padx=10)

        # Output Box
        self.output_box = tk.Text(root, height=5, width=50, state='disabled')
        self.output_box.pack(pady=10)

        # Initialize input field
        self.update_input_field(self.options[0])
        self.EXTRACTED_MOVIES = None

    def update_input_field(self, selection):
        for widget in self.input_frame.winfo_children():
            widget.destroy()

        if selection == "Individual ID":
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

    def insert_into_db(self):
        db_con = DBConnection('movies.db')
        if not self.EXTRACTED_MOVIES:
            return 1
        db_con.insert_data(self.EXTRACTED_MOVIES)
        db_con.close_connection()

    def run_extraction(self):
        selection = self.selected_option.get()
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
        else:
            input_value = ""

        result = strat.extract()
        self.EXTRACTED_MOVIES = result

        # Show result in output box
        self.output_box.config(state='normal')
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(tk.END, f"{result}")
        self.output_box.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtractorApp(root)
    root.mainloop()
