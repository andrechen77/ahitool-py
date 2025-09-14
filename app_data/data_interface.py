"""
This module provides a data interface for storing and retrieving data from a
file.

The data is stored in a JSON file, and the data is serialized using jsonpickle.
"""

from dataclasses import dataclass
import os
from typing import Callable, TypeVar, Generic
import jsonpickle
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

T = TypeVar('T')
class DataInterface(Generic[T]):
    def __init__(self, filepath: str, default_data: T, fixer: Callable[[T], T] = lambda x: x):
        self.filepath = filepath

        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                # test jsonpickle failing
                from job_nimbus.activities import JnActivityJobCreated
                self.cache = fixer(jsonpickle.decode(f.read(), keys=True))
        else:
            self.cache = default_data

    def write_back(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            f.write(jsonpickle.encode(self.cache, indent=2, keys=True))

    @property
    def value(self) -> T:
        return self.cache

    @value.setter
    def value(self, val: T):
        self.cache = val
        self.write_back()
