# Cloud Migration Simulation

A conversational simulation system for practicing cloud migration decision-making. Users interact with personas (PM, DevOps, CTO) in a **web GUI** to practice migrating AWS code to alternative cloud providers.

## Features

- **Web GUI**: Group-chat style interface (Streamlit); no CLI mode
- **LLM required**: Uses OpenAI or Anthropic APIs for parsing and persona responses (no fallback without LLM)
- **API validation**: Checks that the API key and model work before starting the simulation
- **Multiple Personas**: Interact with Product Manager, DevOps Engineer, and CTO
- **Scenario Generation**: Randomized AWS service combinations and business contexts
- **Evaluation & feedback**: Score (0–10), strengths, gaps, and recommendations; end-of-simulation animation (balloons / snow / failure) based on score

## Installation

1. Clone or navigate to this directory:
```bash
cd CloudMigrationSimulation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your LLM API key (required):

For OpenAI:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

For Anthropic:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Alternatively, create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## Usage

### Basic Usage

Run the simulation (launches the web GUI):
```bash
python main.py
```

The terminal will show "Checking LLM API..." and "API OK." then start Streamlit. Open the URL shown (usually http://localhost:8501). The GUI shows a group chat with you and each persona (PM, DevOps, CTO).

### Command-Line Options

```bash
python main.py --help
```

Options:
- `--user-id USER_ID`: User ID for the session (default: default_user)
- `--max-rounds N`: Maximum number of rounds (default: 3)
- `--llm-provider {openai,anthropic}`: LLM provider (default: openai)
- `--llm-model MODEL`: LLM model (default: gpt-4o-mini)

### Example

```bash
python main.py --user-id alice --max-rounds 5 --llm-provider openai --llm-model gpt-4o-mini
```

## How It Works

1. **Initialization**: The simulation generates a random AWS migration scenario with:
   - AWS code snippet (S3+SNS, Lambda+SQS, DynamoDB+IAM, etc.)
   - Business context (deadlines, team size, constraints)
   - Base constraints (time, cost, security, performance, downtime)

2. **User Interaction**: You respond with your migration strategy and considerations.

3. **Persona Responses**: Different personas (PM, DevOps, CTO) join the conversation with:
   - Time pressure and deadline concerns (PM)
   - Security and infrastructure concerns (DevOps)
   - Cost and strategic concerns (CTO)
   
   The system ensures **variety** - each round features a different persona from the previous one, preventing repetition and providing diverse perspectives throughout the simulation.

4. **Final Review Round**: Before the simulation ends, you enter a final review round where:
   - Your current strategy and constraints are summarized
   - Potential gaps are highlighted
   - You can confirm or refine your migration strategy
   - This gives you a chance to address any missing considerations

5. **Evaluation**: After the final review, you receive a detailed evaluation with:
   - Score (0–10) based on reasoning quality
   - Strengths, gaps, and recommendations
   - **End animation** by score: high (7+) → balloons; medium (4–6) → snow; low (0–3) → failure message

## Migration Strategies

The system recognizes these strategies:
- **adapter_layer**: Using an adapter/wrapper pattern
- **abstraction**: Creating abstraction layers
- **hybrid**: Mixed approach
- **rewrite**: Complete rewrite from scratch

## Constraints Tracked

- **time**: Time pressure, deadlines
- **cost**: Budget, pricing concerns
- **security**: Security, compliance, access control
- **perf**: Performance, latency, throughput
- **downtime**: Availability, zero-downtime requirements
- **partial_docs**: Incomplete or missing documentation (some services lack proper documentation)

## Project Structure

```
CloudMigrationSimulation/
├── main.py                 # Entry point (launches GUI only)
├── gui.py                  # Web GUI (Streamlit, group chat style)
├── simulation.py           # Main simulation controller
├── state.py                # State management
├── scenario.py             # Scenario generation
├── parser.py               # User response parsing (LLM only)
├── personas.py             # Persona system (LLM only)
├── evaluation.py           # Evaluation and feedback
├── config.py               # Configuration + API validation
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Configuration

Edit `config.py` to customize:
- Completion conditions (MIN_PERSONAS, MIN_CONSTRAINTS, REQUIRE_STRATEGY)
- Default LLM provider and model
- Maximum rounds

## Troubleshooting

### API Key Not Found
The app requires an LLM and will not run without a key. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (or add them to a `.env` file).

### API Check Failed
Before the GUI starts, the app runs a minimal API call to verify the key and model. If you see "Invalid API key", "Model not found", or "quota exceeded", fix the key, model name, or billing and try again.

### Import Errors
Install dependencies:
```bash
pip install -r requirements.txt
```

### LLM API Errors
- Ensure the API key is valid and has credits
- Try a different model (e.g., `gpt-3.5-turbo` for OpenAI)

## License

This project is provided as-is for educational purposes.
