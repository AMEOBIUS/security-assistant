"""
Scan Coordinator Service for Security Scanners.

Provides parallel scanner execution coordination with:
- Thread pool management
- Progress reporting
- Error handling and recovery
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Set, Optional, Any, List
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ScannerType(str, Enum):
    """Available scanner types."""
    BANDIT = "bandit"
    SEMGREP = "semgrep"
    TRIVY = "trivy"


class ScanCoordinatorService:
    """
    Coordinates parallel scanner execution.
    
    Features:
    - Thread pool management
    - Progress reporting with tqdm (optional)
    - Safe scanner execution with error handling
    - Support for directory and file scanning
    
    Example:
        >>> coordinator = ScanCoordinatorService(max_workers=3)
        >>> coordinator.register_scanner(ScannerType.BANDIT, bandit_scanner)
        >>> results = coordinator.scan_directory("/path/to/project")
    """
    
    def __init__(self, max_workers: int = 3):
        """
        Initialize scan coordinator.
        
        Args:
            max_workers: Maximum parallel scanner threads
        """
        self.max_workers = max_workers
        self._scanners: Dict[ScannerType, Any] = {}
        self._enabled_scanners: Set[ScannerType] = set()
    
    def register_scanner(
        self,
        scanner_type: ScannerType,
        scanner_instance: Any,
    ) -> None:
        """
        Register a scanner instance.
        
        Args:
            scanner_type: Type of scanner
            scanner_instance: Scanner instance
        """
        self._scanners[scanner_type] = scanner_instance
        self._enabled_scanners.add(scanner_type)
        logger.info(f"Registered scanner: {scanner_type.value}")
    
    def unregister_scanner(self, scanner_type: ScannerType) -> None:
        """
        Unregister a scanner.
        
        Args:
            scanner_type: Type of scanner to remove
        """
        if scanner_type in self._enabled_scanners:
            self._enabled_scanners.remove(scanner_type)
            if scanner_type in self._scanners:
                del self._scanners[scanner_type]
            logger.info(f"Unregistered scanner: {scanner_type.value}")
    
    @property
    def enabled_scanners(self) -> Set[ScannerType]:
        """Get set of enabled scanners."""
        return self._enabled_scanners.copy()
    
    @property
    def scanner_count(self) -> int:
        """Get count of enabled scanners."""
        return len(self._enabled_scanners)
    
    def get_scanner(self, scanner_type: ScannerType) -> Optional[Any]:
        """Get scanner instance by type."""
        return self._scanners.get(scanner_type)
    
    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
    ) -> Dict[ScannerType, Any]:
        """
        Run all enabled scanners on a directory in parallel.
        
        Args:
            directory: Directory path to scan
            recursive: Scan subdirectories
            
        Returns:
            Dictionary mapping scanner type to result
        """
        if not self._enabled_scanners:
            raise ValueError("No scanners enabled. Call register_scanner() first.")
        
        return self._run_scanners_parallel(
            directory,
            recursive,
            is_file=False
        )
    
    def scan_file(self, file_path: str) -> Dict[ScannerType, Any]:
        """
        Run all enabled scanners on a single file in parallel.
        
        Args:
            file_path: File path to scan
            
        Returns:
            Dictionary mapping scanner type to result
        """
        if not self._enabled_scanners:
            raise ValueError("No scanners enabled. Call register_scanner() first.")
        
        return self._run_scanners_parallel(
            file_path,
            recursive=False,
            is_file=True
        )
    
    def _run_scanners_parallel(
        self,
        target: str,
        recursive: bool,
        is_file: bool,
    ) -> Dict[ScannerType, Any]:
        """Run all enabled scanners in parallel."""
        results = {}
        
        # Try to use tqdm for progress
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_scanner = {}
            
            for scanner_type in self._enabled_scanners:
                scanner = self._scanners[scanner_type]
                
                if is_file:
                    future = executor.submit(
                        self._run_scanner_file_safe,
                        scanner_type,
                        scanner,
                        target
                    )
                else:
                    future = executor.submit(
                        self._run_scanner_safe,
                        scanner_type,
                        scanner,
                        target,
                        recursive
                    )
                future_to_scanner[future] = scanner_type
            
            # Collect results
            desc = "Scanning file" if is_file else "Running scanners"
            if use_tqdm:
                futures_iter = tqdm(
                    as_completed(future_to_scanner),
                    total=len(future_to_scanner),
                    desc=desc,
                    unit="scanner"
                )
            else:
                futures_iter = as_completed(future_to_scanner)
            
            for future in futures_iter:
                scanner_type = future_to_scanner[future]
                try:
                    result = future.result()
                    results[scanner_type] = result
                    logger.info(f"Scanner {scanner_type.value} completed")
                except Exception as e:
                    logger.error(f"Scanner {scanner_type.value} failed: {e}")
                    results[scanner_type] = None
        
        return results
    
    def _run_scanner_safe(
        self,
        scanner_type: ScannerType,
        scanner: Any,
        directory: str,
        recursive: bool,
    ) -> Any:
        """Safely run a scanner on directory."""
        try:
            logger.debug(f"Running {scanner_type.value} on {directory}")
            return scanner.scan_directory(directory, recursive=recursive)
        except Exception as e:
            logger.error(f"Error in {scanner_type.value}: {e}")
            raise
    
    def _run_scanner_file_safe(
        self,
        scanner_type: ScannerType,
        scanner: Any,
        file_path: str,
    ) -> Any:
        """Safely run a scanner on a file."""
        try:
            logger.debug(f"Running {scanner_type.value} on {file_path}")
            return scanner.scan_file(file_path)
        except Exception as e:
            logger.error(f"Error in {scanner_type.value} on file: {e}")
            raise
