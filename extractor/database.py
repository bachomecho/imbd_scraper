import sqlite3
class DBConnection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DBConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection: sqlite3.Connection = sqlite3.connect(self.db_path)
        self.cur = self.connection.cursor()

    def close_connection(self):
        self.connection.close()

    def insert_data(self, extracted_movies):
        DB_KEYS = [
            "imdb_id",
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

        insert_query = f"""
        INSERT INTO movies (
            {",".join(DB_KEYS)}
        ) VALUES ({"".join([f':{name},' for name in DB_KEYS]).strip(',')})
        ON CONFLICT(imdb_id) DO NOTHING
        """

        self.cur.executemany(insert_query, extracted_movies)
        self.connection.commit()
        print(f"[+] {len(extracted_movies)} movies have been added to movies table in {self.db_path}")


