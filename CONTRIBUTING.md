# Contributing to Opentrons-Lab-Agent

This repository provides Agent Skills for working with Opentrons robots. Contributions are welcome!

## Skill Development Guidelines

### Structure

All skills follow the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/           # Optional: executable code
├── references/        # Optional: documentation
├── assets/           # Optional: templates, resources
└── evals/            # Recommended: test cases
```

### SKILL.md Frontmatter

Required fields:
- `name`: 1-64 characters, lowercase letters, numbers, and hyphens only
- `description`: 1-1024 characters, describes what the skill does and when to use it

Optional fields:
- `license`: License name (e.g., `Apache-2.0`)
- `compatibility`: Environment requirements (Python version, tools, network access)
- `metadata`: Arbitrary key-value pairs for additional properties

### Progressive Disclosure

Skills should be structured for efficient context usage:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup
2. **Instructions** (< 500 lines): Full `SKILL.md` body loaded on activation
3. **Resources** (as needed): Scripts, references, and assets loaded only when required

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

### Evaluation

Include `evals/evals.json` with test cases:

```json
{
  "skill_name": "your-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "A realistic user message",
      "expected_output": "Description of what success looks like",
      "files": ["optional/input/file.csv"],
      "assertions": [
        "Verifiable statement about the output"
      ]
    }
  ]
}
```

See the [Agent Skills evaluation guide](https://agentskills.io/docs/skill-creation/evaluating-skills) for best practices.

### Python Environment

- Use `uv` for package management
- Run scripts with `uv run python ...`
- Add new dependencies to `requirements.txt` if needed

## Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes following the guidelines above
4. Add test cases to `evals/evals.json`
5. Submit a pull request with a clear description

## Validation

Validate your skill before submitting:

```bash
skills-ref validate ./path/to/your-skill
```

Requires [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref) to be installed.
