"""Main simulation controller."""

from typing import Optional

from state import State, init_state
from scenario import scenario_generator, present_context, ScenarioPacket
from parser import UserResponseParser
from personas import choose_next_persona, get_persona_instance, generate_complication
from evaluation import evaluate_session, format_feedback, format_final_review_message, detect_gaps, EvaluationReport
from config import config


class SimulationController:
    """Main simulation controller."""
    
    def __init__(self, user_id: str):
        """Initialize simulation with user ID."""
        self.state = init_state(user_id)
        self.parser = UserResponseParser(config.llm_config)
        self.context_packet: Optional[ScenarioPacket] = None
        self._last_report: Optional[EvaluationReport] = None
    
    def initialize(self) -> str:
        """Initialize simulation and return initial context message."""
        self.context_packet = scenario_generator(self.state)
        agent_message = present_context(self.context_packet)
        self.state.add_message("agent", agent_message)
        return agent_message
    
    def process_user_input(self, user_message: str) -> tuple[Optional[str], bool]:
        """
        Process user input and return agent response.
        Returns: (agent_response, should_end)
        """
        # Add user message to history
        self.state.add_message("user", user_message)
        self.state.round_count += 1
        
        # If we're in final review round, process the user's response to final review
        if self.state.in_final_review:
            # Parse user response to final review
            extracted = self.parser.parse_user_response(user_message)
            self.state.update_from_extracted(extracted)
            
            # Now end the simulation with final evaluation
            report = evaluate_session(self.state)
            self._last_report = report
            feedback = format_feedback(report, self.state)
            self.state.add_message("agent", feedback)
            return feedback, True
        
        # Parse user response
        extracted = self.parser.parse_user_response(user_message)
        self.state.update_from_extracted(extracted)
        
        # Check if simulation should end (but not if we're already in final review)
        if self.state.should_end(config.completion_conditions) and not self.state.in_final_review:
            # Enter final review round instead of ending immediately
            self.state.in_final_review = True
            review_message = format_final_review_message(self.state)
            self.state.add_message("agent", review_message)
            return review_message, False
        
        # Choose next persona and generate complication
        persona_name = choose_next_persona(self.state)
        persona = get_persona_instance(persona_name, config.llm_config)
        complication = generate_complication(self.state, persona)
        self.state.personas_triggered.add(persona_name)
        self.state.last_persona = persona_name  # Track last persona for variety
        
        # Generate persona response
        agent_reply = persona.respond_as_persona(complication, self.state, user_message)
        
        # Format with persona name
        formatted_reply = f"[{persona.name} ({persona.role})]: {agent_reply}"
        self.state.add_message("agent", formatted_reply)
        
        return formatted_reply, False
    
    def get_state(self) -> State:
        """Get current simulation state."""
        return self.state
    
    def get_round_info(self) -> dict:
        """Get current round information."""
        return {
            "round": self.state.round_count,
            "max_rounds": self.state.max_rounds,
            "personas_triggered": list(self.state.personas_triggered),
            "constraints_addressed": list(self.state.constraints_addressed),
            "strategy": self.state.strategy_selected
        }

    def get_last_report(self) -> Optional[EvaluationReport]:
        """Return the evaluation report from the last completed simulation (if any)."""
        return self._last_report


def run_simulation(user_id: str) -> SimulationController:
    """Create and initialize a new simulation."""
    simulation = SimulationController(user_id)
    return simulation
