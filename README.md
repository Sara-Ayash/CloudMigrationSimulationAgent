# Cloud Migration Simulation

A conversational simulation system for practicing cloud migration decision-making. Users interact with personas (PM, DevOps, CTO) to practice migrating AWS code to alternative cloud providers.

## Features

- **Interactive Simulation**: Practice cloud migration scenarios through conversation
- **Multiple Personas**: Interact with Product Manager, DevOps Engineer, and CTO
- **LLM-Powered**: Uses OpenAI or Anthropic APIs for intelligent parsing and persona responses
- **Scenario Generation**: Randomized AWS service combinations and business contexts
- **Evaluation System**: Get feedback on your migration strategy and reasoning

## Installation

1. Clone or navigate to this directory:
```bash
cd CloudMigrationSimulation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your LLM API key:

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

Run the simulation with default settings (CLI):
```bash
python main.py
```

**Web GUI (group chat style):**  
To use a browser-based group-chat interface instead of the CLI:
```bash
python main.py --gui 
```
Then open the URL shown in the terminal (usually http://localhost:8501). The GUI shows messages from you and from each persona (PM, DevOps, CTO) in a chat layout.

### Command-Line Options

```bash
python main.py --help
```

Options:
- `--user-id USER_ID`: Set user ID for the session (default: default_user)
- `--max-rounds N`: Set maximum number of rounds (default: 8)
- `--llm-provider {openai,anthropic}`: Choose LLM provider (default: openai)
- `--llm-model MODEL`: Choose LLM model (default: gpt-4o-mini)

### Example

```bash
python main.py --user-id alice --max-rounds 10 --llm-provider openai --llm-model gpt-4o-mini
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
   - Score (0-10) based on reasoning quality
   - Strengths identified
   - Gaps to improve
   - Recommendations for next iteration

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
├── main.py                 # Entry point (--gui for web UI)
├── cli.py                  # CLI interface
├── gui.py                  # Web GUI (group chat style)
├── simulation.py           # Main simulation loop
├── state.py                # State management
├── scenario.py             # Scenario generation
├── parser.py               # User response parsing (LLM)
├── personas.py             # Persona system
├── evaluation.py           # Evaluation and feedback
├── config.py               # Configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Configuration

Edit `config.py` to customize:
- Completion conditions (MIN_PERSONAS, MIN_CONSTRAINTS, REQUIRE_STRATEGY)
- Default LLM settings
- Maximum rounds

## Troubleshooting

### API Key Not Found
Make sure you've set the environment variable or created a `.env` file with your API key.

### Import Errors
Install dependencies:
```bash
pip install -r requirements.txt
```

### LLM API Errors
- Check your API key is valid
- Verify you have API credits/quota
- Try a different model (e.g., `gpt-3.5-turbo` for OpenAI)

## License

This project is provided as-is for educational purposes.
