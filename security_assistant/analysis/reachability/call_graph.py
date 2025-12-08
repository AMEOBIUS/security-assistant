"""
Call Graph Builder

Builds call graph to track function call relationships.

Maps which functions call which other functions.

Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CallGraphNode:
    """Node in call graph."""

    function_name: str
    module: Optional[str] = None
    callers: Set[str] = field(default_factory=set)  # Functions that call this
    callees: Set[str] = field(default_factory=set)  # Functions this calls
    file_path: Optional[str] = None
    line_number: int = 0


class CallGraph:
    """
    Call graph representation.

    Tracks function call relationships:
    - Which functions call which other functions
    - Transitive call paths
    - Reachability from entry points

    Example:
        >>> graph = CallGraph()
        >>> graph.add_call("main", "process_data")
        >>> graph.add_call("process_data", "requests.get")
        >>> is_reachable = graph.is_reachable("main", "requests.get")
        >>> print(is_reachable)  # True
    """

    def __init__(self):
        """Initialize call graph."""
        self.nodes: Dict[str, CallGraphNode] = {}
        logger.info("Initialized CallGraph")

    def add_node(
        self,
        function_name: str,
        module: Optional[str] = None,
        file_path: Optional[str] = None,
    ) -> None:
        """
        Add node to call graph.

        Args:
            function_name: Function name
            module: Optional module name
            file_path: Optional file path
        """
        if function_name not in self.nodes:
            self.nodes[function_name] = CallGraphNode(
                function_name=function_name,
                module=module,
                file_path=file_path,
            )

    def add_call(self, caller: str, callee: str) -> None:
        """
        Add call edge to graph.

        Args:
            caller: Function that makes the call
            callee: Function that is called

        Example:
            >>> graph = CallGraph()
            >>> graph.add_call("main", "process_data")
        """
        # Ensure nodes exist
        self.add_node(caller)
        self.add_node(callee)

        # Add edge
        self.nodes[caller].callees.add(callee)
        self.nodes[callee].callers.add(caller)

    def is_reachable(self, source: str, target: str) -> bool:
        """
        Check if target is reachable from source.

        Uses BFS to find path from source to target.

        Args:
            source: Source function name
            target: Target function name

        Returns:
            True if target is reachable from source, False otherwise

        Example:
            >>> graph = CallGraph()
            >>> graph.add_call("main", "process")
            >>> graph.add_call("process", "requests.get")
            >>> graph.is_reachable("main", "requests.get")  # True
        """
        if source not in self.nodes or target not in self.nodes:
            return False

        # BFS from source
        visited = set()
        queue = [source]

        while queue:
            current = queue.pop(0)

            if current == target:
                return True

            if current in visited:
                continue

            visited.add(current)

            # Add callees to queue
            if current in self.nodes:
                for callee in self.nodes[current].callees:
                    if callee not in visited:
                        queue.append(callee)

        return False

    def get_call_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Get call path from source to target.

        Args:
            source: Source function name
            target: Target function name

        Returns:
            List of function names in path, or None if not reachable

        Example:
            >>> graph = CallGraph()
            >>> graph.add_call("main", "process")
            >>> graph.add_call("process", "requests.get")
            >>> path = graph.get_call_path("main", "requests.get")
            >>> print(path)  # ["main", "process", "requests.get"]
        """
        if source not in self.nodes or target not in self.nodes:
            return None

        # BFS with path tracking
        visited = set()
        queue = [(source, [source])]

        while queue:
            current, path = queue.pop(0)

            if current == target:
                return path

            if current in visited:
                continue

            visited.add(current)

            # Add callees to queue
            if current in self.nodes:
                for callee in self.nodes[current].callees:
                    if callee not in visited:
                        queue.append((callee, path + [callee]))

        return None

    def get_reachable_functions(self, source: str) -> Set[str]:
        """
        Get all functions reachable from source.

        Args:
            source: Source function name

        Returns:
            Set of reachable function names

        Example:
            >>> graph = CallGraph()
            >>> graph.add_call("main", "process")
            >>> graph.add_call("process", "requests.get")
            >>> reachable = graph.get_reachable_functions("main")
            >>> print(reachable)  # {"process", "requests.get"}
        """
        if source not in self.nodes:
            return set()

        # BFS from source
        visited = set()
        queue = [source]

        while queue:
            current = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Add callees to queue
            if current in self.nodes:
                for callee in self.nodes[current].callees:
                    if callee not in visited:
                        queue.append(callee)

        # Remove source from result
        visited.discard(source)

        return visited

    def get_statistics(self) -> Dict[str, int]:
        """
        Get call graph statistics.

        Returns:
            Dictionary with graph statistics

        Example:
            >>> graph = CallGraph()
            >>> stats = graph.get_statistics()
            >>> print(stats["nodes"])  # Number of nodes
        """
        total_edges = sum(len(node.callees) for node in self.nodes.values())

        return {
            "nodes": len(self.nodes),
            "edges": total_edges,
        }
