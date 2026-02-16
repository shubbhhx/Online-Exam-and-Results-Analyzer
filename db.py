import logging
import queue
import threading
import time
from urllib.parse import urlparse, parse_qs

import pymysql


class Database:
    def __init__(self, config):
        self._config = config
        self._pool = queue.Queue(maxsize=config["DB_POOL_SIZE"])
        self._lock = threading.Lock()
        self._db_settings = self._build_settings()
        self._log = logging.getLogger("db")
        self._log_startup_connection()

    def _build_settings(self):
        url = self._config.get("DATABASE_URL")
        if url:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            ssl_param = (
                query.get("ssl", [None])[0]
                or query.get("sslmode", [None])[0]
                or query.get("ssl-mode", [None])[0]
            )
            ssl_requested = None
            if ssl_param is not None:
                ssl_requested = str(ssl_param).lower() != "false"

            return {
                "host": parsed.hostname,
                "user": parsed.username or "",
                "password": parsed.password or "",
                "database": (parsed.path or "").lstrip("/"),
                "port": int(parsed.port or 3306),
                "ssl_requested": ssl_requested,
            }

        return {
            "host": self._config.get("DB_HOST"),
            "user": self._config.get("DB_USER"),
            "password": self._config.get("DB_PASSWORD"),
            "database": self._config.get("DB_NAME"),
            "port": int(self._config.get("DB_PORT")),
            "ssl_requested": self._config.get("DB_SSL"),
        }

    def _create_connection(self):
        try:
            use_ssl = self._db_settings.get("ssl_requested")
            ssl_config = None
            if use_ssl:
                ssl_config = {"check_hostname": False}
            return pymysql.connect(
                host=self._db_settings["host"],
                user=self._db_settings["user"],
                password=self._db_settings["password"],
                database=self._db_settings["database"],
                port=self._db_settings["port"],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                ssl=ssl_config,
            )
        except Exception as exc:
            self._log.error("Database connection failed: %s", exc)
            return None

    def _get_connection(self):
        try:
            conn = self._pool.get_nowait()
        except queue.Empty:
            conn = None

        if conn is None:
            for attempt in range(1, 4):
                conn = self._create_connection()
                if conn is not None:
                    break
                delay = min(2 ** attempt, 8)
                self._log.warning("Retrying database connection in %ss", delay)
                time.sleep(delay)

        if conn is None:
            return None

        try:
            conn.ping(reconnect=True)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            conn = self._create_connection()

        return conn

    def _release_connection(self, conn):
        if conn is None:
            return
        try:
            if self._pool.full():
                conn.close()
            else:
                self._pool.put(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def fetch_all(self, query, params=None):
        conn = self._get_connection()
        if conn is None:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or [])
                rows = cursor.fetchall()
            return rows
        except Exception as exc:
            self._log.error("Query failed: %s", exc)
            return []
        finally:
            self._release_connection(conn)

    def fetch_one(self, query, params=None):
        rows = self.fetch_all(query, params)
        return rows[0] if rows else None

    def execute(self, query, params=None):
        conn = self._get_connection()
        if conn is None:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or [])
                return cursor.lastrowid
        except Exception as exc:
            self._log.error("Execute failed: %s", exc)
            return None
        finally:
            self._release_connection(conn)

    def transaction(self):
        conn = self._get_connection()
        if conn is None:
            return None
        return conn

    def close(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Exception:
                pass

    def _log_startup_connection(self):
        conn = self._get_connection()
        if conn is None:
            return
        env = (self._config.get("FLASK_ENV") or "").lower()
        if env == "production":
            self._log.info("Database connected (Render production)")
        else:
            self._log.info("Database connected")
        self._release_connection(conn)
