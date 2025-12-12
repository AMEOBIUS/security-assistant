"""
Query command implementation.

AI-powered security queries:
- Natural language searches
- Security policy questions
- Compliance checks
"""

from pathlib import Path

try:
    import asyncio
except ImportError:
    asyncio = None

from security_assistant.ci.base import (
    get_logger,
    print_error,
    print_info,
    print_success,
)
from security_assistant.config import load_config
from security_assistant.services.llm_service import LLMService


def cmd_query(args):
    """
    Query security assistant with natural language.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Load configuration
        config = load_config()
        logger = get_logger(__name__)
        
        # Initialize LLM service
        llm_service = LLMService(config)
        if not asyncio or not asyncio.run(llm_service.is_available()):
            print_error("❌ AI service not available")
            print_info("Please configure LLM provider and API key in config")
            return 1
        
        print_info(f"🤖 Querying security assistant (Provider: {config.llm.provider})")
        print_info(f"📝 Question: {args.query}")
        
        # Query the LLM
        try:
            response = asyncio.run(llm_service.query(args.query))
            
            print("\n" + "=" * 60)
            print(response)
            print("=" * 60)
            
            # Save query and response if requested
            if args.save:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                query_file = Path(config.report.output_dir) / f"query_{timestamp}.txt"
                query_file.parent.mkdir(parents=True, exist_ok=True)
                
                with open(query_file, "w") as f:
                    f.write(f"Query: {args.query}\n\n")
                    f.write(f"Response: {response}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                print_info(f"💾 Saved to: {query_file.name}")
            
            print_success("✅ Query completed")
            return 0
            
        except Exception as e:
            print_error(f"❌ Query failed: {e}")
            return 1
        
    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Query command failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
