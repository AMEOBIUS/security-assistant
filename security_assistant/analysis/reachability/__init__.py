"""
Reachability Analysis Module

Determines if vulnerable dependencies or code paths are actually reachable/executed
by the application.

Submodules:
- ast_parser: Language-specific AST parsing
- import_tracker: Tracks imports and dependencies
- call_graph: Builds call graphs
- analyzer: Main reachability analysis logic
"""
