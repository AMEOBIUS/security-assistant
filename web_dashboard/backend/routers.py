"""
API Routers for Dashboard
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

router = APIRouter()

RESULTS_DIR = Path("../../security-reports")

@router.get("/scans", response_model=List[Dict[str, Any]])
async def list_scans():
    """List available scan reports."""
    if not RESULTS_DIR.exists():
        return []
    
    scans = []
    # Logic to list scan files
    # For now, we might just look for scan-results.json
    scan_file = RESULTS_DIR / "scan-results.json"
    if scan_file.exists():
        try:
            with open(scan_file) as f:
                data = json.load(f)
                scans.append({
                    "id": "latest",
                    "date": data.get("metadata", {}).get("generated_at", "Unknown"),
                    "target": data.get("metadata", {}).get("target", "Unknown"),
                    "total_findings": data.get("summary", {}).get("total_findings", 0)
                })
        except Exception as e:
            print(f"Error reading scan file: {e}")
            
    return scans

@router.get("/scans/{scan_id}")
async def get_scan_details(scan_id: str):
    """Get details for a specific scan."""
    # Mock implementation for "latest"
    if scan_id == "latest":
        scan_file = RESULTS_DIR / "scan-results.json"
        if scan_file.exists():
            with open(scan_file) as f:
                return json.load(f)
    
    raise HTTPException(status_code=404, detail="Scan not found")
