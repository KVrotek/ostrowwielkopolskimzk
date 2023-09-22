import sqlite3


class CreatingDatabase:
    def __init__(self):
        try:
            db_connection = sqlite3.connect('database.db')
            db_cursor = db_connection.cursor()

            db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS bus_lines(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_name TEXT NOT NULL,
                line_link TEXT NOT NULL
            )
            """)
            db_connection.commit()
            db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS bus_stops(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bus_stop_name TEXT NOT NULL,
                bus_stop_index INT NOT NULL,
                direction TEXT NOT NULL,
                map_link TEXT NOT NULL,
                attribute TEXT NOT NULL,
                bus_line_id INTEGER, 
                FOREIGN KEY (bus_line_id) 
                    REFERENCES bus_lines(id)
            )
            """)
            db_connection.commit()
            db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS bus_hours(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour TEXT,
                day TEXT,
                bus_stop_id INTEGER,
                bus_line_id INTEGER,
                FOREIGN KEY (bus_stop_id) 
                    REFERENCES bus_stops(id),
                FOREIGN KEY (bus_line_id) 
                    REFERENCES bus_lines(id)
            )
            """)
            db_connection.commit()
            db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS legends(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                legend TEXT,
                bus_stop_id INTEGER,
                bus_line_id INTEGER,
                FOREIGN KEY (bus_stop_id) 
                    REFERENCES bus_stops(id),
                FOREIGN KEY (bus_line_id) 
                    REFERENCES bus_lines(id)
            )
            """)
            db_connection.commit()
            db_connection.close()
        except sqlite3.Error as e:
            print(e)


class ClearDatabase:
    def __init__(self):
        try:
            table_names = ["bus_lines", "bus_stops", "bus_hours"]
            db_connection = sqlite3.connect('database_2.db')
            db_cursor = db_connection.cursor()

            for i in table_names:
                print(i)
                db_cursor.execute(f'DELETE FROM {i}')
                db_connection.commit()

            db_connection.close()
        except sqlite3.Error as e:
            print(e)

