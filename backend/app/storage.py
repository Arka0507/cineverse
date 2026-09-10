from __future__ import annotations
from contextlib import contextmanager
from collections.abc import Iterator
from pathlib import Path
import json
import sqlite3
import time
from typing import Any

class Store:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS ratings (
                user_id INTEGER NOT NULL, movie_id INTEGER NOT NULL,
                rating REAL NOT NULL CHECK(rating BETWEEN 1 AND 5), updated_at REAL NOT NULL,
                PRIMARY KEY(user_id,movie_id));
            CREATE TABLE IF NOT EXISTS feedback_events (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, movie_id INTEGER NOT NULL,
                rating REAL NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS metadata (movie_id INTEGER PRIMARY KEY, payload TEXT NOT NULL, expires_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS profiles (user_id INTEGER PRIMARY KEY AUTOINCREMENT);
            INSERT OR IGNORE INTO profiles(user_id) VALUES(100000);
            CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, bucket INTEGER NOT NULL, count INTEGER NOT NULL);
            ''')

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db: yield db
        finally: db.close()

    def create_profile(self) -> int:
        with self.connect() as db:
            cursor = db.execute('INSERT INTO profiles DEFAULT VALUES')
            return int(cursor.lastrowid or 0)

    def feedback(self, user_id: int) -> dict[int, float]:
        with self.connect() as db:
            return {int(m): float(r) for m, r in db.execute('SELECT movie_id,rating FROM ratings WHERE user_id=?', (user_id,))}

    def rate(self, user_id: int, movie_id: int, rating: float) -> None:
        with self.connect() as db:
            now = time.time()
            db.execute('INSERT INTO ratings VALUES(?,?,?,?) ON CONFLICT(user_id,movie_id) DO UPDATE SET rating=excluded.rating,updated_at=excluded.updated_at', (user_id, movie_id, rating, now))
            db.execute('INSERT INTO feedback_events(user_id,movie_id,rating,created_at) VALUES(?,?,?,?)', (user_id, movie_id, rating, now))

    def metadata(self, movie_id: int) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute('SELECT payload FROM metadata WHERE movie_id=? AND expires_at>?', (movie_id, time.time())).fetchone()
            return json.loads(row[0]) if row else None

    def cache(self, movie_id: int, payload: dict[str, Any], ttl: float = 86400 * 7) -> None:
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO metadata VALUES(?,?,?)', (movie_id, json.dumps(payload), time.time() + ttl))

    def allow(self, key: str, limit: int) -> bool:
        bucket = int(time.time() // 60)
        with self.connect() as db:
            db.execute('INSERT INTO rate_limits VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN bucket=excluded.bucket THEN count+1 ELSE 1 END,bucket=excluded.bucket', (key, bucket))
            count = db.execute('SELECT count FROM rate_limits WHERE key=?', (key,)).fetchone()[0]
            db.execute('DELETE FROM rate_limits WHERE bucket<?', (bucket - 2,))
            return bool(count <= limit)
