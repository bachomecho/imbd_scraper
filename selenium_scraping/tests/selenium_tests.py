import unittest
import sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile
from selenium_scraping.imdb_custom_parser_selenium import get_imdb_ids

class TestGetImdbIds(unittest.TestCase):
    def setUp(self):
        """Set up a temporary SQLite database for testing."""
        self.db_file = NamedTemporaryFile(delete=False)
        self.db_path = Path(self.db_file.name)

        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.cursor.execute('CREATE TABLE movies (imdb_id TEXT)')
        self.connection.commit()

    def tearDown(self):
        """Close the connection and remove the temporary database."""
        self.connection.close()
        self.db_file.close()
        self.db_path.unlink()

    def test_get_imdb_ids(self):
        """Test the get_imdb_ids function with mock data."""
        sample_data = [('tt1234567',), ('tt2345678',), ('tt3456789',)]
        self.cursor.executemany('INSERT INTO movies (imdb_id) VALUES (?)', sample_data)
        self.connection.commit()

        expected_ids = sample_data
        actual_ids = get_imdb_ids(self.db_path)
        self.assertEqual(actual_ids, expected_ids)

if __name__ == '__main__':
    unittest.main()
