"""CLI interface for the simulation."""

import sys
from typing import Optional

from simulation import SimulationController


class CLI:
    """Command-line interface for the simulation."""
    
    def __init__(self):
        """Initialize CLI."""
        self.simulation: Optional[SimulationController] = None
    
    def print_message(self, message: str, prefix: str = ""):
        """Print a formatted message."""
        if prefix:
            print(f"{prefix} {message}")
        else:
            print(message)
    
    def print_separator(self):
        """Print a visual separator."""
        print("\n" + "-" * 60 + "\n")
    
    def get_user_input(self) -> str:
        """Get user input from command line."""
        try:
            return input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "exit"
    
    def display_round_info(self, round_info: dict, state=None):
        """Display current round information."""
        if state and state.in_final_review:
            print(f"\n[Final Review Round]")
        else:
            print(f"\n[Round {round_info['round']+1}/{round_info['max_rounds']}]")
        if round_info['strategy']:
            print(f"Strategy: {round_info['strategy']}")
        if round_info['constraints_addressed']:
            print(f"Constraints: {', '.join(round_info['constraints_addressed'])}")
        if round_info['personas_triggered']:
            print(f"Personas: {', '.join(round_info['personas_triggered'])}")
        print()
    
    def run(self, user_id: str = "default_user"):
        """Run the CLI simulation."""
        print("=" * 60)
        print("Cloud Migration Simulation")
        print("=" * 60)
        print("\nType 'exit' or press Ctrl+C to quit at any time.\n")
        
        # Initialize simulation
        try:
            self.simulation = SimulationController(user_id)
            initial_message = self.simulation.initialize()
            
            self.print_message(initial_message)
            self.print_separator()
            
            # Display session info
            state = self.simulation.get_state()
            print(f"Session ID: {state.session_id}")
            print(f"User ID: {state.user_id}")
             
        except Exception as e:
            print(f"Error initializing simulation: {e}")
            print("\nMake sure you have:")
            print("  1. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
            print("  2. Installed required packages: pip install -r requirements.txt")
            sys.exit(1)
        
        # Main loop
        while True:
            try:
                # Display round info
                round_info = self.simulation.get_round_info()
                self.display_round_info(round_info, self.simulation.get_state())
                
                # Get user input
                user_message = self.get_user_input()
                
                if user_message.lower() in ["exit", "quit", "q"]:
                    print("\nExiting simulation. Goodbye!")
                    break
                
                if not user_message:
                    print("Please enter a response.")
                    continue
                
                # Process user input
                agent_response, should_end = self.simulation.process_user_input(user_message)
                
                if agent_response:
                    self.print_separator()
                    self.print_message(agent_response)
                    self.print_separator()
                
                if should_end:
                    # Simulation ended
                    print("\nSimulation complete!")
                    break
                
            except KeyboardInterrupt:
                print("\n\nExiting simulation. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Continuing simulation...\n")
                continue


def main_cli(user_id: str = "default_user"):
    """Main CLI entry point."""
    cli = CLI()
    cli.run(user_id)
