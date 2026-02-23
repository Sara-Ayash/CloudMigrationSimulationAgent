# Usage Examples

The application runs **only in GUI mode** (Streamlit). Running `python main.py` checks the LLM API and then opens the web interface.

## Basic Examples

### 1. Run with default settings
```bash
source venv/bin/activate   # if using a venv
python main.py
```
The terminal will show "Checking LLM API..." and "API OK." then start Streamlit. Open the URL (e.g. http://localhost:8501).

### 2. Run with custom user ID
```bash
python main.py --user-id alice
```

### 3. Run with more rounds (longer simulation)
```bash
python main.py --max-rounds 12
```

### 4. Run with Anthropic instead of OpenAI
```bash
python main.py --llm-provider anthropic
```
Set `ANTHROPIC_API_KEY` in the environment or in a `.env` file.

### 5. Run with a different OpenAI model
```bash
python main.py --llm-model gpt-4
```

### 6. Run with Anthropic and specific model
```bash
python main.py --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022
```

### 7. Combine multiple arguments
```bash
python main.py --user-id bob --max-rounds 10 --llm-provider openai --llm-model gpt-4o-mini
```

## Complete Example Session

```bash
# Activate virtual environment (optional)
source venv/bin/activate

# Set API key (required)
export OPENAI_API_KEY='your-api-key-here'

# Run simulation (opens GUI)
python main.py --user-id developer1 --max-rounds 8
```

## What You See

1. **Terminal**: "Checking LLM API..." → "API OK." → Streamlit starts with a local URL.
2. **Browser**: Cloud Migration Simulation page with a group chat. The scenario message appears first (AWS context and code). You type your responses; the PM, DevOps, and CTO reply in turn.
3. **End of simulation**: After the final review round you get feedback and a score. The UI shows:
   - **Score 7–10**: Balloons and a success message.
   - **Score 4–6**: Snow animation and a “room to improve” message.
   - **Score 0–3**: No animation and a message that you can try again.
4. **Start new simulation**: Button at the bottom to clear the session and start over.

## Environment Setup

### Option 1: Environment Variable
```bash
export OPENAI_API_KEY='your-api-key-here'
# or
export ANTHROPIC_API_KEY='your-api-key-here'
```

### Option 2: .env File
Create a `.env` file in the project directory:
```
OPENAI_API_KEY=your-api-key-here
```

## Available Models

### OpenAI Models
- `gpt-4o-mini` (default, cheaper)
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### Anthropic Models
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
