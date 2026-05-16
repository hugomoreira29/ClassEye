import os
import sqlite3
from datetime import datetime


def _project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_db_path():
    data_dir = os.path.join(_project_root(), "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "classeye.sqlite3")


def connect():
    conn = sqlite3.connect(get_db_path())
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                session_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                record_date TEXT NOT NULL,
                record_time TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES attendance_sessions(id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE (session_id, student_id)
            )
            """
        )


def get_or_create_student(conn, name):
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT OR IGNORE INTO students (name, active, created_at)
        VALUES (?, 1, ?)
        """,
        (name, now),
    )
    row = conn.execute(
        "SELECT id FROM students WHERE name = ?",
        (name,),
    ).fetchone()
    return row[0]


def get_or_create_class(conn, class_name):
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        INSERT OR IGNORE INTO classes (name, created_at)
        VALUES (?, ?)
        """,
        (class_name, now),
    )
    row = conn.execute(
        "SELECT id FROM classes WHERE name = ?",
        (class_name,),
    ).fetchone()
    return row[0]


def create_attendance_session(conn, class_id, date_str, time_str):
    now = datetime.now().isoformat(timespec="seconds")
    cursor = conn.execute(
        """
        INSERT INTO attendance_sessions
            (class_id, session_date, session_time, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (class_id, date_str, time_str, now),
    )
    return cursor.lastrowid


def save_attendance(present_students, all_students, class_name="Default Class"):
    init_db()

    present_set = set(present_students)
    roster = sorted(set(all_students)) if all_students else sorted(present_set)

    if not roster:
        return None

    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    now = datetime.now().isoformat(timespec="seconds")

    with connect() as conn:
        class_id = get_or_create_class(conn, class_name)
        session_id = create_attendance_session(conn, class_id, date_str, time_str)

        for name in roster:
            student_id = get_or_create_student(conn, name)
            status = "Present" if name in present_set else "Absent"

            conn.execute(
                """
                INSERT OR IGNORE INTO attendance_records
                    (session_id, student_id, status, record_date, record_time, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, student_id, status, date_str, time_str, now),
            )

        return session_id
