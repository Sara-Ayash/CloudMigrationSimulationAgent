"""Web GUI for Cloud Migration Simulation - group chat style."""

import os
import re
import streamlit as st

from simulation import SimulationController
from config import config

# Apply max_rounds from main entry point (when launched via main.py --gui)
if os.environ.get("SIMULATION_MAX_ROUNDS"):
    config.max_rounds = int(os.environ["SIMULATION_MAX_ROUNDS"])

# Persona display names and roles
PERSONA_DISPLAY = {
    "Scenario": ("Scenario", "הקשר המיגרציה", "📋"),
    "PM": ("Sarah", "Product Manager (PM)", "📅"),
    "DevOps": ("Alex", "DevOps Engineer", "🔧"),
    "CTO": ("Michael", "CTO", "👔"),
}


def _parse_agent_message(content: str) -> tuple[str, str]:
    """Parse '[Name (Role)]: message' into (speaker, message)."""
    match = re.match(r"^\[([^\]]+)\]:\s*(.*)", content, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "Scenario", content


def _speaker_to_display(speaker: str) -> tuple[str, str, str]:
    """Map speaker string to (display_name, role_label, avatar)."""
    if speaker == "Scenario":
        return PERSONA_DISPLAY["Scenario"]
    # Match known personas by name or role in "Name (Role)" format
    s = speaker.lower()
    if "Sarah" in s or "pm" in s or "product manager" in s:
        name, role, avatar = PERSONA_DISPLAY["PM"]
        return name, role, avatar
    if "Alex" in s or "devops" in s:
        name, role, avatar = PERSONA_DISPLAY["DevOps"]
        return name, role, avatar
    if "Michael" in s or "cto" in s:
        name, role, avatar = PERSONA_DISPLAY["CTO"]
        return name, role, avatar
    # Fallback: try to parse "Name (Role)" for display
    match = re.match(r"^([^(]+)\s*\(([^)]+)\)\s*$", speaker.strip())
    if match:
        return match.group(1).strip(), match.group(2).strip(), "👤"
    return speaker, "", "👤"


def init_session():
    """Initialize simulation and session state."""
    if "simulation" not in st.session_state:
        user_id = (
            os.environ.get("SIMULATION_USER_ID")
            or st.session_state.get("user_id")
            or st.session_state.get("user_id_input")
            or "default_user"
        )
        try:
            st.session_state.simulation = SimulationController(user_id)
            initial_message = st.session_state.simulation.initialize()
            st.session_state.messages = []
            # Append initial context as "Scenario"
            st.session_state.messages.append({"role": "agent", "content": initial_message})
        except Exception as e:
            st.error(f"Error initializing simulation: {e}")
            st.info("Ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set (or create a .env file)")
            st.stop()
    return st.session_state.simulation


def _persona_label(display_name: str, role_label: str) -> str:
    """Chat header: name only (role shown below in caption)."""
    return display_name


def _get_user_display_name() -> str:
    """Get the current user name for chat display."""
    return (
        st.session_state.get("user_id")
        or (st.session_state.get("simulation") and st.session_state.simulation.get_state().user_id)
        or os.environ.get("SIMULATION_USER_ID", "default_user")
    )


def render_chat():
    """Render chat messages with conditional name display for the Candidate."""
    messages = st.session_state.get("messages", [])
    
    # Get the user ID from the sidebar input
    user_id = st.session_state.get("user_id_input", "").strip()

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        
        if role == "user":
            # Determine display name: use ID if provided and not default, otherwise generic label
            is_valid_name = user_id and user_id != "default_user"
            display_label = user_id if is_valid_name else "Candidate"
            
            with st.chat_message(display_label, avatar="🧑"):
                # If no name is provided, only show the Role
                if is_valid_name:
                    st.caption(f"**Name:** {user_id}  \n**Role:** Candidate")
                else:
                    st.caption(f"**Role:** Candidate")
                st.markdown(content)
        else:
            # Agent rendering logic (stays the same)
            speaker, body = _parse_agent_message(content)
            display_name, role_label, avatar = _speaker_to_display(speaker)
            label = _persona_label(display_name, role_label)
            with st.chat_message(label, avatar=avatar):
                if role_label and speaker != "Scenario":
                    st.caption(f"**Name:** {display_name}  \n**Role:** {role_label}")
                st.markdown(body)


def main():
    st.set_page_config(
        page_title="Cloud Migration Simulation",
        page_icon="☁️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )

    # Optional user ID in sidebar
    with st.sidebar:
        st.header("Settings")
        default_uid = os.environ.get("SIMULATION_USER_ID", "default_user")
        user_id = st.text_input("User ID", value=default_uid, key="user_id_input")
        if "user_id" not in st.session_state or st.session_state.user_id != user_id:
            st.session_state.user_id = user_id
        st.session_state.user_id = user_id

        if st.session_state.get("simulation"):
            state = st.session_state.simulation.get_state()
            round_info = st.session_state.simulation.get_round_info()
            st.metric("Round", f"{round_info['round'] + 1} / {round_info['max_rounds']}")
            if round_info["strategy"]:
                st.caption(f"Strategy: {round_info['strategy']}")
            if round_info["personas_triggered"]:
                st.caption(f"Personas: {', '.join(round_info['personas_triggered'])}")
            if state.in_final_review:
                st.warning("Final Review Round")

    # Title
    st.title("☁️ Cloud Migration Simulation")
    st.caption("Group chat with PM, DevOps, and CTO – practice cloud migration decisions")

    simulation = init_session()
    render_chat()

    if prompt := st.chat_input("Write your response..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Check if we have a valid custom name
        user_id = st.session_state.get("user_id_input", "").strip()
        is_valid_name = user_id and user_id != "default_user"
        display_label = user_id if is_valid_name else "Candidate"
        
        with st.chat_message(display_label, avatar="🧑"):
            # Conditional header based on name existence
            if is_valid_name:
                st.caption(f"**Name:** {user_id}  \n**Role:** Candidate")
            else:
                st.caption(f"**Role:** Candidate")
            st.markdown(prompt)

        with st.spinner("Waiting for team response..."):
            try:
                # Process simulation logic
                agent_response, should_end = simulation.process_user_input(prompt)
            except Exception as e:
                st.error(f"Error: {e}")
                agent_response = None
                should_end = False

        if agent_response:
            # Store and display the agent's response
            st.session_state.messages.append({"role": "agent", "content": agent_response})
            speaker, body = _parse_agent_message(agent_response)
            display_name, role_label, avatar = _speaker_to_display(speaker)
            label = _persona_label(display_name, role_label)
            
            with st.chat_message(label, avatar=avatar):
                if role_label and speaker != "Scenario":
                    st.caption(f"**Name:** {display_name}  \n**Role:** {role_label}")
                st.markdown(body)

        if should_end:
            st.balloons()
            st.success("Simulation complete. Read the feedback above.")
            if st.button("Start new simulation"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    # API key hint at bottom
    if not config.llm_config.api_key:
        st.sidebar.warning("API key not configured - responses will be template-based only.")


if __name__ == "__main__":
    main()
