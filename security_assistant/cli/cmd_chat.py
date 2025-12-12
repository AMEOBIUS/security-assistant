"""
Chat command implementation.

Interactive AI chat for security discussions:
- Security guidance
- Technical discussions
- Best practices
"""

import json
from pathlib import Path

try:
    import asyncio
except ImportError:
    asyncio = None

from security_assistant.ci.base import get_logger, print_error, print_info
from security_assistant.config import load_config
from security_assistant.services.llm_service import LLMService


def cmd_chat(args):
    """
    Interactive AI chat session.

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
            print_info("Please configure LLM provider and AI API key in config")
            return 1
        
        print_info(f"🤖 Security Assistant Chat (Provider: {config.llm.provider})")
        print_info("Type '/exit' to end chat. Type '/help' for commands.")
        print_info("💬 Press Tab for suggestions, Enter to send.")
        print("-" * 50)
        
        # Initialize chat session
        session_id = f"session_{int(Path().timestamp() % 10000)}"
        chat_history = []
        
        if args.model:
            try:
                llm_service.set_model(args.model)
                print_info(f"Using model: {args.model}")
            except Exception as e:
                print_info(f"Could not set model: {e}")
        
        # Load previous session if exists
        if args.load_session:
            session_file = Path(config.report.output_dir) / "chat_session.json"
            if session_file.exists():
                with open(session_file) as f:
                    chat_history = json.load(f)
                session_id = chat_history[-1].get("session_id", session_id)
                print_info("📋 Loaded previous chat session")
                print_info(f"Last prompt: {chat_history[-1].get('prompt', 'N/A')}")
        
        # Interactive chat loop
        while True:
            try:
                # Get user input
                user_input = input("\n💬 Chat: ").strip()
                
                if not user_input:
                    print_info("Please type a message or use commands:")
                    print_info("  /help - Show available commands")
                    print_info("  /exit - End chat")
                    print_info("  /save - Save session")
                    continue
                
                # Handle commands
                if user_input == "/exit":
                    break
                elif user_input == "/help":
                    print("\n🛠️ Available commands:")
                    print("  /help    - Show this help")
                    print("  /exit   - End chat session")
                    print("  /save   - Save current session")
                    print("  /clear  - Clear chat history")
                    print("  /model  - Switch AI model")
                    print("  /status - Show session status")
                    continue
                elif user_input == "/save":
                    session_file = Path(config.report.output_dir) / "chat_session.json"
                    session_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(session_file, "w") as f:
                        json.dump(chat_history + [
                            {"session_id": session_id, "prompt": "Session ended"}
                        ], f, indent=2)
                    print_info(f"Session saved to {session_file.name}")
                    continue
                elif user_input == "/clear":
                    chat_history = []
                    session_id = f"session_{int(Path().timestamp() % 10000)}"
                    print_info("📄 Chat history cleared")
                    continue
                elif user_input == "/clear":
                    chat_history = []
                    session_id = f"session_{int(Path().timestamp() % 10000)}"
                    print_info("📄 Chat history cleared")
                    continue
                elif user_input.startswith("/model "):
                    model = user_input.split(" ", 1)[1] if " " in user_input else None
                    if not model:
                        print_error("❌ Usage: /model <model_name>")
                        continue
                    
                    try:
                        llm_service.set_model(model)
                        print_info(f"Switched to model: {model}")
                    except Exception as e:
                        print_error(f"❌ Failed to switch model: {e}")
                    continue
                elif user_input == "/status":
                    print_info("📊 Session Status:")
                    print_info(f"  Session ID: {session_id}")
                    print_info(f"  Messages: {len(chat_history)}")
                    chat_size = sum(len(msg.get("prompt", "")) + len(msg.get("response", "")) for msg in chat_history)
                    print_info(f"  Chat size: ~{chat_size} characters")
                    continue
                else:
                    # Regular chat message
                    print("\n💬 User: " + user_input)
                    print("🤖 Assistant: ", end="")
                    
                    # Add to history
                    chat_history.append({
                        "session_id": session_id,
                        "prompt": user_input,
                        "timestamp": Path().timestamp()
                    })
                    
                    # Get AI response
                    try:
                        response = asyncio.run(llm_service.chat(
                            chat_history,
                            system_prompt="You are Security Assistant, a helpful AI assistant focused on cybersecurity and application security. Provide clear, actionable advice about security best practices, vulnerabilities, compliance, and security tool usage. Be concise and professional."
                        ))
                        
                        print(response)
                        chat_history[-1]["response"] = response
                        print()  # Add spacing
                        
                    except Exception as e:
                        print_error(f"❌ Response failed: {e}")
                        print_info("Try /clear to reset chat")
                        continue
                        
            except KeyboardInterrupt:
                print_info("\n👋 Chat ended by user")
                break
            except Exception as e:
                logger.error(f"Chat error: {e}")
                print_info("Continue chatting or /exit to end")
                continue
        
        # Final save if there's history
        if chat_history:
            session_file = Path(config.report.output_dir) / "chat_session.json"
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(session_file, "w") as f:
                json.dump(chat_history + [
                    {"session_id": session_id, "prompt": "Session ended"}
                ], f, indent=2)
        
        print_info("Chat session ended")
        return 0

    except Exception as e:
        logger = get_logger(__name__)
        print_error(f"❌ Chat failed: {e}")
        if args.verbose:
            logger.debug("Exception details:", exc_info=True)
        return 1
