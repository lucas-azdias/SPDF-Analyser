from abc import ABC, abstractmethod
from collections import Counter, defaultdict, deque
from datetime import datetime
from enum import Enum
from more_itertools import collapse
from pathlib import Path
from re import Match, Pattern, compile, escape, finditer, match
from tabulate import tabulate
from time import time_ns
from typing import Callable, Dict, Generator, Generic, Iterable, List, Optional, Tuple, Type, TypeVar, Self, SupportsIndex, Any