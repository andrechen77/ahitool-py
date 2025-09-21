"""
This module provides a data interface for storing and retrieving data from a
file.

The data is stored in a JSON file, and the data is serialized using jsonpickle.
"""

from dataclasses import dataclass
import os
from typing import Callable, Optional, TypeVar, Generic
import jsonpickle
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

T = TypeVar('T')
class DataInterface(Generic[T]):
    def __init__(self, filepath: str, fixer: Callable[[T], T] = lambda x: x):
        self.filepath = filepath
        self.refresher = None

        if os.path.exists(self.filepath):
            logger.info(f"Loading from {self.filepath}")
            self.last_updated = datetime.fromtimestamp(os.path.getmtime(self.filepath))
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self._cache = fixer(jsonpickle.decode(f.read(), keys=True))
        else:
            logger.info(f"Missing data for {self.filepath}")
            self._cache = None
            self.last_updated = None

    def write_back(self):
        if self._cache is None:
            logger.warning(f"No data to save for {self.filepath}")
            return
        logger.info(f"Saving {self.filepath}")
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(jsonpickle.encode(self._cache, indent=2, keys=True))
        self.last_updated = datetime.now()

    @property
    def val(self) -> Optional[T]:
        if self._cache is None and self.refresher is not None:
            self.val = self.refresher()
        return self._cache

    @val.setter
    def val(self, val: T):
        logger.debug(f"Setting val for {self.filepath}: {val}")
        self._cache = val
        self.write_back()

    def set_refresher(self, refresher: Callable[[], T]):
        logger.debug(f"Setting refresher for {self.filepath}")
        if self.refresher is not None:
            logger.warning(f"Refresher already set for {self.filepath}")
        self.refresher = refresher

    def refresh(self):
        if self.refresher is None:
            logger.warning(f"No refresher set for {self.filepath}")
            return
        logger.debug(f"Refreshing {self.filepath}")
        self.val = self.refresher()
