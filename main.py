"""Main entry point for the Cloud Migration Simulation (GUI only)."""

import argparse
import os
import sys

from config import config


def main():
    """Main entry point - launches the web GUI."""
    parser = argparse.ArgumentParser(
        description="Cloud Migration Simulation - Practice migrating AWS code to alternative cloud providers"
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
        default=4,
        help="Maximum number of rounds (default: 4)"
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
    
    # LLM is required
    if not config.llm_config.api_key:
        print("Error: LLM API key not found! This application requires an LLM and cannot run without it.")
        print(f"\nPlease set one of the following environment variables:")
        if args.llm_provider == "openai":
            print("  export OPENAI_API_KEY='your-api-key-here'")
        else:
            print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with the API key.")
        sys.exit(1)

    # Validate API before starting
    print("Checking LLM API...")
    try:
        config.llm_config.validate_api()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    print("API OK.\n")
    
    os.environ["SIMULATION_USER_ID"] = args.user_id
    os.environ["SIMULATION_MAX_ROUNDS"] = str(config.max_rounds)
    import subprocess
    this_dir = os.path.dirname(os.path.abspath(__file__))
    gui_path = os.path.join(this_dir, "gui.py")
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", gui_path, "--server.headless", "true"]))


if __name__ == "__main__":
    main()
