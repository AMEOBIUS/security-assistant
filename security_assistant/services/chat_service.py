"""
Security Chatbot Service.

Provides interactive chat interface for querying security findings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from security_assistant.config import SecurityAssistantConfig
from security_assistant.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatService:
    """
    Manages chat session state and context for security analysis.
    """

    def __init__(self, config: SecurityAssistantConfig, report_path: Optional[str] = None):
        self.config = config
        self.llm_service = LLMService(config)
        self.history: List[Dict[str, str]] = []
        self.context = ""
        
        if report_path:
            self._load_context(report_path)

    def _load_context(self, report_path: str):
        """Load scan results into context."""
        try:
            path = Path(report_path)
            if not path.exists():
                logger.warning(f"Report not found: {report_path}")
                return

            with open(path, encoding='utf-8') as f:
                data = json.load(f)
                
            # Summarize findings for context window efficiency
            stats = data.get("findings_by_severity", {})
            total = data.get("total_findings", 0)
            
            summary = f"Scan Summary:\nTotal Findings: {total}\n"
            for sev, count in stats.items():
                summary += f"- {sev}: {count}\n"
                
            # Add top findings
            summary += "\nTop Critical/High Issues:\n"
            
            # Flatten findings if needed
            findings = []
            if "results" in data and isinstance(data["results"], list):
                for target in data["results"]:
                    findings.extend(target.get("findings", []))
            elif "findings" in data:
                findings = data.get("findings", [])
                
            # Sort by severity
            findings.sort(key=lambda f: self._severity_rank(f.get("severity", "LOW")))
            
            for i, f in enumerate(findings[:10]):
                summary += f"{i+1}. [{f.get('severity')}] {f.get('title')} ({f.get('file')}:{f.get('line_start')})\n"
                
            self.context = summary
            logger.info("Loaded scan context successfully")
            
        except Exception as e:
            logger.error(f"Failed to load context: {e}")

    def _severity_rank(self, severity: str) -> int:
        ranks = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        return ranks.get(severity.upper(), 5)

    async def send_message(self, message: str) -> str:
        """
        Send user message and get response.
        
        Args:
            message: User input
            
        Returns:
            Assistant response
        """
        if not await self.llm_service.is_available():
            return "❌ LLM service is not available. Check your configuration."

        # Build messages list
        messages = [
            {"role": "system", "content": f"You are Security Assistant, an expert AI security engineer. Analyze the following scan results and answer user questions.\n\n{self.context}"}
        ]
        
        # Add history
        messages.extend(self.history[-10:]) # Keep last 10 turns
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.llm_service.chat(messages)
            
            # Update history
            self.history.append({"role": "user", "content": message})
            self.history.append({"role": "assistant", "content": response})
            
            return response
        except Exception as e:
            return f"❌ Error: {str(e)}"
