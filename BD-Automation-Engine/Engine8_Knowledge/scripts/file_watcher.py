"""
BD File Watcher - Monitor directories for new files and auto-process them.
Watches Bullhorn exports, outputs, and other key directories.
"""

import sys
import time
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Engine8_Knowledge.scripts.document_processor import BDDocumentProcessor, ProcessedDocument
from Engine8_Knowledge.scripts.vector_store import BDKnowledgeStore
from Engine8_Knowledge.scripts.indexer import BDIndexer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('BDFileWatcher')

# Check for watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning("watchdog not installed. Install with: pip install watchdog")

# =========================================
# CONFIGURATION
# =========================================

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default directories to watch
WATCH_DIRECTORIES = {
    'bullhorn_exports': {
        'path': PROJECT_ROOT / "docs" / "Bullhorn Exports",
        'extensions': ['.xls', '.xlsx', '.csv', '.txt'],
        'collection': 'documents'
    },
    'outputs': {
        'path': PROJECT_ROOT / "outputs",
        'extensions': ['.md', '.txt', '.json'],
        'collection': 'documents'
    },
    'prime_contacts': {
        'path': PROJECT_ROOT / "Engine3_OrgChart" / "data" / "Prime_Contacts",
        'extensions': ['.csv', '.json'],
        'collection': 'contacts'
    },
    'dashboard_data': {
        'path': PROJECT_ROOT / "dashboard" / "public" / "data",
        'extensions': ['.json'],
        'collection': 'all'  # Trigger full re-index
    }
}

# Debounce delay (seconds) to avoid processing same file multiple times
DEBOUNCE_DELAY = 2.0


@dataclass
class WatchEvent:
    """Represents a file system event."""
    event_type: str  # 'created', 'modified', 'deleted'
    file_path: Path
    timestamp: datetime
    processed: bool = False
    result: Optional[str] = None


@dataclass
class WatcherStats:
    """Statistics for the file watcher."""
    start_time: datetime
    events_received: int = 0
    files_processed: int = 0
    files_indexed: int = 0
    errors: int = 0
    last_event_time: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
            'events_received': self.events_received,
            'files_processed': self.files_processed,
            'files_indexed': self.files_indexed,
            'errors': self.errors,
            'last_event_time': self.last_event_time.isoformat() if self.last_event_time else None
        }


# =========================================
# FILE WATCHER CLASS
# =========================================

class BDFileWatcher:
    """
    Watch directories for new files and auto-process them.

    Integrates with document processor and knowledge store for
    automatic indexing of new content.
    """

    def __init__(
        self,
        auto_index: bool = True,
        debounce_delay: float = DEBOUNCE_DELAY
    ):
        """
        Initialize the file watcher.

        Args:
            auto_index: If True, automatically index processed documents.
            debounce_delay: Delay before processing file changes.
        """
        self.auto_index = auto_index
        self.debounce_delay = debounce_delay

        # Components
        self.processor = BDDocumentProcessor()
        self.store = BDKnowledgeStore() if auto_index else None
        self.indexer = BDIndexer(self.store) if auto_index else None

        # State
        self.stats = WatcherStats(start_time=datetime.now())
        self.recent_events: Dict[str, WatchEvent] = {}
        self.observers: List = []
        self._running = False
        self._lock = threading.Lock()

        # Callbacks
        self.on_file_processed: Optional[Callable[[ProcessedDocument], None]] = None
        self.on_error: Optional[Callable[[str, Exception], None]] = None

    def start(
        self,
        directories: Optional[Dict[str, Dict]] = None,
        blocking: bool = True
    ):
        """
        Start watching directories.

        Args:
            directories: Dict of directory configs to watch. Uses defaults if None.
            blocking: If True, block until stopped. If False, run in background.
        """
        if not WATCHDOG_AVAILABLE:
            logger.error("watchdog library required for file watching")
            return

        directories = directories or WATCH_DIRECTORIES
        self._running = True

        # Initialize knowledge store collections
        if self.store:
            self.store.initialize_collections()

        # Create observers for each directory
        for name, config in directories.items():
            path = config['path']
            if not path.exists():
                logger.warning(f"Watch directory not found: {path}")
                continue

            # Create event handler
            handler = _BDEventHandler(
                watcher=self,
                extensions=config.get('extensions', []),
                collection=config.get('collection', 'documents')
            )

            # Create and start observer
            observer = Observer()
            observer.schedule(handler, str(path), recursive=True)
            observer.start()
            self.observers.append(observer)

            logger.info(f"Watching: {path}")

        logger.info(f"File watcher started ({len(self.observers)} directories)")

        if blocking:
            try:
                while self._running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop watching directories."""
        self._running = False

        for observer in self.observers:
            observer.stop()
            observer.join()

        self.observers = []
        logger.info("File watcher stopped")

    def process_event(self, event: WatchEvent, collection: str):
        """
        Process a file system event.

        Args:
            event: The file event to process.
            collection: Target collection for indexing.
        """
        file_path = event.file_path

        with self._lock:
            # Check for debounce
            path_key = str(file_path)
            if path_key in self.recent_events:
                last_event = self.recent_events[path_key]
                time_diff = (event.timestamp - last_event.timestamp).total_seconds()
                if time_diff < self.debounce_delay:
                    logger.debug(f"Debouncing: {file_path}")
                    return

            self.recent_events[path_key] = event
            self.stats.events_received += 1
            self.stats.last_event_time = event.timestamp

        # Process the file
        try:
            logger.info(f"Processing: {file_path}")

            # Use document processor
            doc = self.processor.process_file(file_path)

            if doc:
                self.stats.files_processed += 1
                logger.info(f"Processed: {doc.title} ({len(doc.chunks)} chunks)")

                # Index if enabled
                if self.auto_index and self.store:
                    self._index_document(doc, collection)

                # Call callback
                if self.on_file_processed:
                    self.on_file_processed(doc)
            else:
                logger.warning(f"Failed to process: {file_path}")
                self.stats.errors += 1

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.stats.errors += 1

            if self.on_error:
                self.on_error(str(file_path), e)

    def _index_document(self, doc: ProcessedDocument, collection: str):
        """Index a processed document."""
        if collection == 'all':
            # Trigger full re-index (for dashboard data changes)
            logger.info("Dashboard data changed - scheduling full re-index")
            # Don't do full re-index on every change, just log
            return

        try:
            if collection == 'documents':
                indexed, errors = self.store.index_documents([doc.to_dict()])
            elif collection == 'contacts':
                indexed, errors = self.store.index_contacts([doc.to_dict()])
            else:
                indexed, errors = self.store.index_documents([doc.to_dict()])

            if indexed > 0:
                self.stats.files_indexed += 1
                logger.info(f"Indexed: {doc.title} -> {collection}")
            else:
                logger.warning(f"Indexing failed: {doc.title}")

        except Exception as e:
            logger.error(f"Indexing error: {e}")

    def get_stats(self) -> Dict:
        """Get watcher statistics."""
        return self.stats.to_dict()

    def run_manual_sync(self):
        """Manually sync all watched directories."""
        if not self.indexer:
            logger.warning("Auto-index not enabled")
            return

        logger.info("Running manual sync...")
        self.indexer.index_all()


# =========================================
# EVENT HANDLER (WATCHDOG)
# =========================================

if WATCHDOG_AVAILABLE:
    class _BDEventHandler(FileSystemEventHandler):
        """Watchdog event handler for BD file watcher."""

        def __init__(
            self,
            watcher: BDFileWatcher,
            extensions: List[str],
            collection: str
        ):
            self.watcher = watcher
            self.extensions = [e.lower() for e in extensions]
            self.collection = collection
            super().__init__()

        def _should_process(self, path: str) -> bool:
            """Check if file should be processed."""
            ext = Path(path).suffix.lower()
            return ext in self.extensions

        def on_created(self, event):
            """Handle file creation."""
            if event.is_directory:
                return

            if self._should_process(event.src_path):
                watch_event = WatchEvent(
                    event_type='created',
                    file_path=Path(event.src_path),
                    timestamp=datetime.now()
                )
                # Process in thread to avoid blocking
                threading.Thread(
                    target=self.watcher.process_event,
                    args=(watch_event, self.collection)
                ).start()

        def on_modified(self, event):
            """Handle file modification."""
            if event.is_directory:
                return

            if self._should_process(event.src_path):
                watch_event = WatchEvent(
                    event_type='modified',
                    file_path=Path(event.src_path),
                    timestamp=datetime.now()
                )
                threading.Thread(
                    target=self.watcher.process_event,
                    args=(watch_event, self.collection)
                ).start()


# =========================================
# SIMPLE POLLING WATCHER (FALLBACK)
# =========================================

class SimpleFileWatcher:
    """
    Simple polling-based file watcher (fallback when watchdog unavailable).

    Less efficient but works everywhere.
    """

    def __init__(
        self,
        auto_index: bool = True,
        poll_interval: float = 10.0
    ):
        self.auto_index = auto_index
        self.poll_interval = poll_interval

        self.processor = BDDocumentProcessor()
        self.store = BDKnowledgeStore() if auto_index else None

        self._running = False
        self._known_files: Dict[str, float] = {}  # path -> mtime

    def start(
        self,
        directories: Optional[Dict[str, Dict]] = None,
        blocking: bool = True
    ):
        """Start polling directories for changes."""
        directories = directories or WATCH_DIRECTORIES
        self._running = True

        if self.store:
            self.store.initialize_collections()

        # Initial scan
        for name, config in directories.items():
            path = config['path']
            if path.exists():
                self._scan_directory(path, config.get('extensions', []))

        logger.info(f"Simple watcher started ({len(directories)} directories)")

        if blocking:
            try:
                while self._running:
                    for name, config in directories.items():
                        path = config['path']
                        if path.exists():
                            self._check_directory(
                                path,
                                config.get('extensions', []),
                                config.get('collection', 'documents')
                            )
                    time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the watcher."""
        self._running = False
        logger.info("Simple watcher stopped")

    def _scan_directory(self, directory: Path, extensions: List[str]):
        """Scan directory and record file mtimes."""
        for f in directory.rglob('*'):
            if f.is_file() and f.suffix.lower() in extensions:
                self._known_files[str(f)] = f.stat().st_mtime

    def _check_directory(self, directory: Path, extensions: List[str], collection: str):
        """Check directory for new/modified files."""
        for f in directory.rglob('*'):
            if not f.is_file() or f.suffix.lower() not in extensions:
                continue

            path_key = str(f)
            current_mtime = f.stat().st_mtime

            if path_key not in self._known_files:
                # New file
                logger.info(f"New file detected: {f}")
                self._process_file(f, collection)
                self._known_files[path_key] = current_mtime

            elif current_mtime > self._known_files[path_key]:
                # Modified file
                logger.info(f"Modified file detected: {f}")
                self._process_file(f, collection)
                self._known_files[path_key] = current_mtime

    def _process_file(self, path: Path, collection: str):
        """Process a file and optionally index it."""
        doc = self.processor.process_file(path)

        if doc and self.auto_index and self.store:
            self.store.index_documents([doc.to_dict()])
            logger.info(f"Indexed: {doc.title}")


# =========================================
# CLI INTERFACE
# =========================================

def main():
    """CLI for the BD File Watcher."""
    import argparse

    parser = argparse.ArgumentParser(description='BD File Watcher')
    parser.add_argument('--no-index', action='store_true', help='Disable auto-indexing')
    parser.add_argument('--simple', action='store_true', help='Use simple polling watcher')
    parser.add_argument('--interval', type=float, default=10.0, help='Poll interval (simple mode)')
    parser.add_argument('--sync', action='store_true', help='Run manual sync and exit')

    args = parser.parse_args()

    auto_index = not args.no_index

    if args.sync:
        # Manual sync mode
        watcher = BDFileWatcher(auto_index=True)
        watcher.run_manual_sync()
        return

    # Choose watcher type
    if args.simple or not WATCHDOG_AVAILABLE:
        watcher = SimpleFileWatcher(auto_index=auto_index, poll_interval=args.interval)
    else:
        watcher = BDFileWatcher(auto_index=auto_index)

    print(f"\nStarting file watcher (auto-index: {auto_index})")
    print("Press Ctrl+C to stop\n")

    watcher.start(blocking=True)


if __name__ == '__main__':
    main()
