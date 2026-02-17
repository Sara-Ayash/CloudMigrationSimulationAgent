"""Main entry point for the Cloud Migration Simulation."""

import argparse
import os
import sys

from cli import main_cli
from config import config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cloud Migration Simulation - Practice migrating AWS code to alternative cloud providers"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch web GUI (group chat style) instead of CLI"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="default_user",
        help="User ID for the simulation session (default: default_user)"
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=3,
        help="Maximum number of rounds (default: 3)"
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (default: openai)"
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)"
    )
    
    args = parser.parse_args()
    
    # Update config
    config.max_rounds = args.max_rounds
    config.llm_config.provider = args.llm_provider
    config.llm_config.model = args.llm_model
    
    # Check for API key (skip for GUI so it can show in-app message)
    if not config.llm_config.api_key and not args.gui:
        print("Error: LLM API key not found!")
        print(f"\nPlease set one of the following environment variables:")
        if args.llm_provider == "openai":
            print("  export OPENAI_API_KEY='your-api-key-here'")
        else:
            print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with the API key.")
        sys.exit(1)
    
    if args.gui:
        os.environ["SIMULATION_USER_ID"] = args.user_id
        os.environ["SIMULATION_MAX_ROUNDS"] = str(args.max_rounds)
        import subprocess
        this_dir = os.path.dirname(os.path.abspath(__file__))
        gui_path = os.path.join(this_dir, "gui.py")
        sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", gui_path, "--server.headless", "true"]))
    
    # Run CLI
    try:
        main_cli(args.user_id)
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
