"""
Database Manager for MarketMan.

This module provides a centralized database abstraction layer with:
- Connection management
- CRUD operations
- Transaction handling
- Query builders
"""

import sqlite3
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Centralized database manager for MarketMan.

    Provides a clean abstraction layer for all database operations
    with proper connection management and error handling.
    """

    def __init__(self, db_path: str):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Database manager initialized for: {self.db_path}")

    @contextmanager
    def get_connection(self):
        """
        Get a database connection with proper error handling.

        Yields:
            sqlite3.Connection: Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of dictionaries representing the results
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            cursor = conn.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
        """
        result = self.execute_query(query, (table_name,))
        return len(result) > 0

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about a table's columns.

        Args:
            table_name: Name of the table

        Returns:
            List of column information dictionaries
        """
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)

    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database.

        Args:
            backup_path: Path for the backup file

        Returns:
            True if backup successful, False otherwise
        """
        try:
            import shutil

            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def vacuum_database(self) -> bool:
        """
        Optimize the database by rebuilding it.

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuum completed")
                return True
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False

    def _init_database(self) -> None:
        """Initialize database schema and tables."""
        # This will be overridden by specific database managers
        pass


class MarketMemoryDB(DatabaseManager):
    """
    Database manager for market memory operations.

    Handles all market signal and pattern storage operations.
    """

    def __init__(self, db_path: str = "marketman_memory.db"):
        """Initialize the market memory database."""
        import sqlite3
        if db_path == ':memory:':
            logger.info("Initializing in-memory database schema with persistent connection (before super)")
            self.db_path = ':memory:'
            self._memory_conn = sqlite3.connect(':memory:')
            self._memory_conn.row_factory = sqlite3.Row
            self._init_database()
        else:
            super().__init__(db_path)
            self._memory_conn = None

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper error handling."""
        if getattr(self, '_memory_conn', None) is not None:
            try:
                yield self._memory_conn
            except Exception as e:
                logger.error(f"Database error: {e}")
                self._memory_conn.rollback()
                raise
        else:
            conn = None
            try:
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                yield conn
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                if conn:
                    conn.rollback()
                raise
            finally:
                if conn:
                    conn.close()

    def _init_database(self) -> None:
        """Initialize market memory database schema."""
        logger.info(f"Initializing database schema for path: {self.db_path}")
        
        # For in-memory databases, always create tables
        if self.db_path == ':memory:' or not self.table_exists("signals"):
            logger.info("Creating database tables")
            
            # Create signals table
            signals_schema = """
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL,
                etfs TEXT,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            # Create patterns table
            patterns_schema = """
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT,
                pattern_type TEXT NOT NULL,
                etfs TEXT,
                strength REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            # Create contextual insights table
            insights_schema = """
            CREATE TABLE IF NOT EXISTS contextual_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                content TEXT,
                relevance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """

            try:
                with self.get_connection() as conn:
                    conn.execute("PRAGMA journal_mode=WAL;")
                    conn.execute(signals_schema)
                    conn.execute(patterns_schema)
                    conn.execute(insights_schema)
                    conn.commit()

                logger.info("Market memory database schema initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize market memory schema: {e}")
                raise
        else:
            logger.info("Database tables already exist, skipping initialization")

    def store_signal(self, signal_data: Dict[str, Any]) -> int:
        """
        Store a market signal.

        Args:
            signal_data: Dictionary containing signal information

        Returns:
            ID of the inserted signal
        """
        query = """
        INSERT INTO signals (date, signal_type, confidence, etfs, reasoning)
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            signal_data.get("date"),
            signal_data.get("signal_type"),
            signal_data.get("confidence"),
            ",".join(signal_data.get("etfs", [])),
            signal_data.get("reasoning"),
        )

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_signals(
        self, limit: int = 100, signal_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve market signals.

        Args:
            limit: Maximum number of signals to return
            signal_type: Filter by signal type

        Returns:
            List of signal dictionaries
        """
        query = "SELECT * FROM signals"
        params = []

        if signal_type:
            query += " WHERE signal_type = ?"
            params.append(signal_type)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def store_pattern(self, pattern_data: Dict[str, Any]) -> int:
        """
        Store a market pattern.

        Args:
            pattern_data: Dictionary containing pattern information

        Returns:
            ID of the inserted pattern
        """
        query = """
        INSERT INTO patterns (start_date, end_date, pattern_type, etfs, strength)
        VALUES (?, ?, ?, ?, ?)
        """

        params = (
            pattern_data.get("start_date"),
            pattern_data.get("end_date"),
            pattern_data.get("pattern_type"),
            ",".join(pattern_data.get("etfs", [])),
            pattern_data.get("strength"),
        )

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_patterns(self, pattern_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve market patterns.

        Args:
            pattern_type: Filter by pattern type

        Returns:
            List of pattern dictionaries
        """
        query = "SELECT * FROM patterns"
        params = []

        if pattern_type:
            query += " WHERE pattern_type = ?"
            params.append(pattern_type)

        query += " ORDER BY start_date DESC"

        return self.execute_query(query, tuple(params))

    def store_insight(self, insight_data: Dict[str, Any]) -> int:
        """
        Store a contextual insight.

        Args:
            insight_data: Dictionary containing insight information

        Returns:
            ID of the inserted insight
        """
        query = """
        INSERT INTO contextual_insights (date, insight_type, content, relevance_score)
        VALUES (?, ?, ?, ?)
        """

        params = (
            insight_data.get("date"),
            insight_data.get("insight_type"),
            insight_data.get("content"),
            insight_data.get("relevance_score"),
        )

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_insights(
        self, insight_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieve contextual insights.

        Args:
            insight_type: Filter by insight type
            limit: Maximum number of insights to return

        Returns:
            List of insight dictionaries
        """
        query = "SELECT * FROM contextual_insights"
        params = []

        if insight_type:
            query += " WHERE insight_type = ?"
            params.append(insight_type)

        query += " ORDER BY date DESC LIMIT ?"
        params.append(limit)

        return self.execute_query(query, tuple(params))

    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """
        Remove old data from the database.

        Args:
            days_to_keep: Number of days of data to keep

        Returns:
            Number of deleted records
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

        queries = [
            ("DELETE FROM signals WHERE date < ?", (cutoff_date,)),
            ("DELETE FROM patterns WHERE start_date < ?", (cutoff_date,)),
            ("DELETE FROM contextual_insights WHERE date < ?", (cutoff_date,)),
        ]

        total_deleted = 0
        with self.get_connection() as conn:
            for query, params in queries:
                cursor = conn.execute(query, params)
                total_deleted += cursor.rowcount
            conn.commit()

        logger.info(f"Cleaned up {total_deleted} old records")
        return total_deleted

    def delete_signals(self, cutoff_date: str) -> int:
        """
        Delete signals older than the cutoff date.

        Args:
            cutoff_date: Date cutoff in YYYY-MM-DD format

        Returns:
            Number of deleted signals
        """
        query = "DELETE FROM signals WHERE date < ?"
        return self.execute_update(query, (cutoff_date,))

    def delete_patterns(self, cutoff_date: str) -> int:
        """
        Delete patterns older than the cutoff date.

        Args:
            cutoff_date: Date cutoff in YYYY-MM-DD format

        Returns:
            Number of deleted patterns
        """
        query = "DELETE FROM patterns WHERE start_date < ?"
        return self.execute_update(query, (cutoff_date,))

    def get_signal_count(self) -> int:
        """
        Get total number of signals.

        Returns:
            Total signal count
        """
        query = "SELECT COUNT(*) as count FROM signals"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def get_pattern_count(self) -> int:
        """
        Get total number of patterns.

        Returns:
            Total pattern count
        """
        query = "SELECT COUNT(*) as count FROM patterns"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def get_signal_breakdown(self) -> Dict[str, int]:
        """
        Get breakdown of signals by type.

        Returns:
            Dictionary mapping signal types to counts
        """
        query = "SELECT signal_type, COUNT(*) as count FROM signals GROUP BY signal_type"
        results = self.execute_query(query)
        return {row["signal_type"]: row["count"] for row in results}

    def get_recent_activity(self, days: int = 7) -> int:
        """
        Get number of signals in recent days.

        Args:
            days: Number of days to look back

        Returns:
            Number of recent signals
        """
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        query = "SELECT COUNT(*) as count FROM signals WHERE date >= ?"
        result = self.execute_query(query, (cutoff_date,))
        return result[0]["count"] if result else 0

    def get_date_range(self) -> Tuple[str, str]:
        """
        Get the date range of stored signals.

        Returns:
            Tuple of (min_date, max_date)
        """
        query = "SELECT MIN(date) as min_date, MAX(date) as max_date FROM signals"
        result = self.execute_query(query)
        if result and result[0]["min_date"]:
            return (result[0]["min_date"], result[0]["max_date"])
        return ("", "")

    def clear_all(self) -> int:
        """
        Clear all data from the database.

        Returns:
            Number of deleted records
        """
        queries = [
            ("DELETE FROM signals", ()),
            ("DELETE FROM patterns", ()),
            ("DELETE FROM contextual_insights", ()),
        ]

        total_deleted = 0
        with self.get_connection() as conn:
            for query, params in queries:
                cursor = conn.execute(query, params)
                total_deleted += cursor.rowcount
            conn.commit()

        logger.info(f"Cleared {total_deleted} records from database")
        return total_deleted


class AlertBatchDB(DatabaseManager):
    """
    Database manager for alert batching operations.

    Handles all alert storage and batching operations.
    """

    def __init__(self, db_path: str = "alert_batch.db"):
        """Initialize the alert batch database."""
        super().__init__(db_path)

    def _init_database(self) -> None:
        """Initialize alert batch database schema."""
        if self.table_exists("alerts"):
            return

        # Create alerts table
        alerts_schema = """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            content TEXT,
            processed BOOLEAN DEFAULT FALSE,
            batch_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        # Create batches table
        batches_schema = """
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            strategy TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        )
        """

        try:
            with self.get_connection() as conn:
                conn.execute(alerts_schema)
                conn.execute(batches_schema)
                conn.commit()

            logger.info("Alert batch database schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize alert batch schema: {e}")
            raise

    def store_alert(self, alert_data: Dict[str, Any]) -> int:
        """
        Store an alert.

        Args:
            alert_data: Dictionary containing alert information

        Returns:
            ID of the inserted alert
        """
        query = """
        INSERT INTO alerts (timestamp, alert_type, content, batch_id)
        VALUES (?, ?, ?, ?)
        """

        params = (
            alert_data.get("timestamp"),
            alert_data.get("alert_type"),
            alert_data.get("content"),
            alert_data.get("batch_id"),
        )

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def get_pending_alerts(self, alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get pending alerts.

        Args:
            alert_type: Filter by alert type

        Returns:
            List of pending alert dictionaries
        """
        query = "SELECT * FROM alerts WHERE processed = FALSE"
        params = []

        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)

        query += " ORDER BY timestamp ASC"

        return self.execute_query(query, tuple(params))

    def mark_alert_processed(self, alert_id: int) -> bool:
        """
        Mark an alert as processed.

        Args:
            alert_id: ID of the alert to mark

        Returns:
            True if successful
        """
        query = "UPDATE alerts SET processed = TRUE WHERE id = ?"
        affected = self.execute_update(query, (alert_id,))
        return affected > 0

    def create_batch(self, batch_id: str, strategy: str) -> int:
        """
        Create a new batch.

        Args:
            batch_id: Unique batch identifier
            strategy: Batching strategy used

        Returns:
            ID of the created batch
        """
        query = "INSERT INTO batches (batch_id, strategy) VALUES (?, ?)"

        with self.get_connection() as conn:
            cursor = conn.execute(query, (batch_id, strategy))
            conn.commit()
            return cursor.lastrowid

    def update_batch_status(self, batch_id: str, status: str) -> bool:
        """
        Update batch status.

        Args:
            batch_id: Batch identifier
            status: New status

        Returns:
            True if successful
        """
        query = "UPDATE batches SET status = ?, processed_at = CURRENT_TIMESTAMP WHERE batch_id = ?"
        affected = self.execute_update(query, (status, batch_id))
        return affected > 0


# Global database instances
market_memory_db = MarketMemoryDB()
alert_batch_db = AlertBatchDB()
