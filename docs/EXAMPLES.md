# Usage Examples

## Basic Examples

### 1. Run with default settings
```bash
source venv/bin/activate
python main.py
```

### 2. Run with custom user ID
```bash
source venv/bin/activate
python main.py --user-id alice
```

### 3. Run with more rounds (longer simulation)
```bash
source venv/bin/activate
python main.py --max-rounds 12
```

### 4. Run with Anthropic instead of OpenAI
```bash
source venv/bin/activate
python main.py --llm-provider anthropic
```

### 5. Run with a different OpenAI model
```bash
source venv/bin/activate
python main.py --llm-model gpt-4
```

### 6. Run with Anthropic and specific model
```bash
source venv/bin/activate
python main.py --llm-provider anthropic --llm-model claude-3-5-sonnet-20241022
```

### 7. Combine multiple arguments
```bash
source venv/bin/activate
python main.py --user-id bob --max-rounds 10 --llm-provider openai --llm-model gpt-4o-mini
```

## Complete Example Session

```bash
# Activate virtual environment
source venv/bin/activate

# Set API key (if not already set)
export OPENAI_API_KEY='your-api-key-here'

# Run simulation
python main.py --user-id developer1 --max-rounds 8
```

## Example Output

When you run the simulation, you'll see:

```
============================================================
Cloud Migration Simulation
============================================================

Type 'exit' or press Ctrl+C to quit at any time.

Welcome to the Cloud Migration Simulation! 🌐

You've been tasked with migrating an AWS-based service to an alternative cloud provider.

**Context:**
[Business context here...]

**Current AWS Implementation:**
The service uses: S3, SNS
Module name: file_processor

[Python code snippet here...]

**Your Task:**
Plan and discuss your migration strategy...

Session ID: [uuid]
User ID: developer1

------------------------------------------------------------

[Round 1/8]
Strategy: None
Constraints: 
Personas: 

You: [Your response here]
```

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
