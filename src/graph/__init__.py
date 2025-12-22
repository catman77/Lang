"""Модуль анализа графов конфигураций"""

import sys
import os
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from graph.builder import Graph, GraphBuilder
from graph.scc import SCC, TarjanSCC, AttractorAnalyzer

__all__ = [
    'Graph',
    'GraphBuilder',
    'SCC',
    'TarjanSCC',
    'AttractorAnalyzer'
]
