# Opentrons Code Generation Benchmark Tests

This directory contains benchmark testing tools for evaluating the performance of the AI-powered Opentrons protocol code generation system.

## Files

- `benchmark_dataset.json` - Contains 27 test cases with varying difficulties and categories
- `benchmark_runner.py` - Complete benchmark suite that runs all test cases
- `benchmark_quick_test.py` - Quick test script for running a subset of test cases
- `error_patterns_summary.md` - Analysis of common error patterns
- `benchmark_results/` - Output directory (created automatically)

## Test Dataset

The benchmark dataset includes 27 test cases categorized by:

### Difficulty Levels
- **easy** (4 cases): Basic single-step operations
- **easy-medium** (2 cases): Simple goal-oriented tasks
- **medium** (6 cases): Multi-step protocols requiring biological knowledge
- **medium-hard** (5 cases): Complex protocols with specialized techniques
- **hard** (3 cases): Advanced multi-step assays with timing requirements
- **expert** (7 cases): Professional-grade protocols requiring expert knowledge

### Categories
- **error-test**: Cases designed to trigger common errors
- **step-by-step**: Detailed procedural instructions
- **goal-oriented**: High-level experiment descriptions
- **goal-oriented-immunostaining**: Immunostaining protocols
- **complex-protocol-*****: Various complex experimental workflows

## Prerequisites

Before running the benchmark tests, ensure you have:

1. **pandas library installed**:
   ```bash
   pip install pandas
   ```

2. **Proper environment setup**:
   - Virtual environment activated (`.venv` or `OTcoder`)
   - All dependencies from `requirements.txt` installed
   - Backend modules properly configured

3. **API Configuration**:
   - Ensure `backend/config.py` has valid API keys and endpoints
   - The system should be able to connect to your LLM provider

## Running Tests

### Quick Test (Recommended for initial validation)

Run a subset of 5 representative test cases:

```bash
cd tests/evaluation
python benchmark_quick_test.py
```

This takes ~5-15 minutes and tests:
- `v1` (easy step-by-step)
- `error_labware_name` (easy error-test) 
- `pcr_setup_basic` (medium step-by-step)
- `v2` (easy-medium goal-oriented)
- `dna_extraction` (medium-hard goal-oriented)

### Full Benchmark Suite

Run all 27 test cases:

```bash
cd tests/evaluation
python benchmark_runner.py
```

**Warning**: This can take 2-4 hours depending on your system and LLM response times.

## 🎯 Latest Benchmark Results (2025-07-09)

### Overall Performance
- ✅ **Final Success Rate**: 100% (27/27 test cases)
- ✅ **First Pass Rate**: 85.2% (23/27 test cases)
- ✅ **Self-Repair Capability**: 100% (all failed cases fixed through iteration)
- ⏱️ **Average Response Time**: 136-150 seconds per protocol

### Critical Configuration Requirements
- **Timeout Setting**: 300 seconds (CRITICAL - 60s causes expert-level failures)
- **Max Iterations**: 10 attempts
- **Hardware Config**: Standard OT-2 configuration

### Performance by Difficulty Level
| Difficulty | Success Rate | First Pass Rate | Avg Iterations |
|-----------|--------------|-----------------|----------------|
| Easy | 100% | 100% | 1.0 |
| Easy-Medium | 100% | 100% | 1.0 |
| Medium | 100% | 85.7% | 1.2 |
| Medium-Hard | 100% | 100% | 1.0 |
| Hard | 100% | 66.7% | 1.7 |
| Expert | 100% | 57.1% | 2.9 |

### Key Findings
1. **System is production-ready** with 100% ultimate success rate
2. **Timeout configuration is critical** - 300s vs 60s makes the difference
3. **Iterative repair works excellently** - AI can fix all error types:
   - OutOfTipsError (resource management)
   - AttributeError (API usage)
   - KeyError (data access)
   - TypeError (object handling)
4. **Complex protocols need patience** - Expert level averages 2.9 iterations

### Test Individual Cases

To test specific cases, modify the test selection in `benchmark_runner.py`:

```python
# Uncomment and modify this line in main():
test_cases = [tc for tc in test_cases if tc['id'] in ['v1', 'pcr_setup_basic']]
```

## Output

Both scripts generate detailed outputs:

### Console Output
- Real-time progress for each test case
- Iteration logs showing AI attempts and results
- Final summary statistics

### File Outputs (Full Benchmark Only)

```
benchmark_results/
├── summary.md              # Comprehensive markdown report
├── summary.csv             # Data table (for further analysis)
└── details/
    ├── v1_code.py          # Generated code for each test
    ├── v1_log.json         # Detailed iteration logs
    ├── error_labware_name_code.py
    ├── error_labware_name_log.json
    └── ...
```

### Summary Report Includes

1. **Overall Statistics**:
   - Pass rate (% of successful generations)
   - First pass rate (% passing on first attempt)
   - Average generation time
   - Average number of attempts

2. **Performance by Difficulty**: Pass rates for each difficulty level

3. **Performance by Category**: Pass rates for each test category

4. **Error Analysis**: Breakdown of common error types

5. **Detailed Results Table**: Complete results for all test cases

## Metrics Tracked

For each test case, the system records:

- **Status**: PASS, PASS_WITH_WARNINGS, FAIL, or CRASH
- **Generation Time**: Total time from prompt to final result
- **Attempts**: Number of AI iterations required
- **First Pass**: Whether it succeeded on the first attempt
- **Error Category**: Type of error (if failed)
- **Generated Code**: Final Python protocol code
- **Iteration Logs**: Complete log of AI decision-making process

## Error Categories

The system automatically categorizes errors into:

- `LabwareLoadError`: Invalid labware names
- `InstrumentLoadError`: Invalid pipette names
- `ModuleLoadError`: Invalid module names
- `SyntaxError`: Python syntax issues
- `AttributeError`: API usage errors
- `VolumeError`: Volume out of range
- `TipError`: Tip management issues
- `RobotTypeError`: Robot type mismatches
- `AgentFailure`: AI system failures
- `Other`: Uncategorized errors

## Interpreting Results

### Good Performance Indicators
- **Pass Rate > 70%**: System handles most protocols correctly
- **First Pass Rate > 40%**: AI generates good code initially
- **Average Time < 60s**: Reasonable response times
- **Average Attempts < 3**: Efficient iteration

### Areas for Improvement
- **High LabwareLoadError**: Need better hardware knowledge
- **High SyntaxError**: Need better code generation templates
- **High AgentFailure**: System reliability issues
- **Low First Pass Rate**: Initial prompts need improvement

## Troubleshooting

### Import Errors
```
Error: Could not import from 'backend'
```
- Ensure you're running from the correct directory
- Check that virtual environment is activated
- Verify `backend/` directory exists and has proper `__init__.py`

### API Errors
```
Timeout or connection errors
```
- Check `backend/config.py` for valid API credentials
- Verify network connectivity
- Consider increasing timeout values

### Performance Issues
```
Tests taking too long
```
- Start with `benchmark_quick_test.py`
- Check your LLM provider's rate limits
- Consider reducing `MAX_ITERATIONS` in the config

## Advanced Usage

### Custom Test Cases

Add new test cases to `benchmark_dataset.json`:

```json
{
  "id": "my_custom_test",
  "category": "goal-oriented",
  "difficulty": "medium",
  "prompt": "Write a protocol for...",
  "description": "Custom test case",
  "source": "custom"
}
```

### Custom Hardware Config

Modify the `DEFAULT_OT2_HARDWARE_CONFIG` in either script to test with different hardware setups.

### Batch Analysis

Use the CSV output for statistical analysis:

```python
import pandas as pd
df = pd.read_csv('benchmark_results/summary.csv')
print(df.groupby('Difficulty')['Status'].value_counts())
```

## Contributing

When adding new test cases or modifying the benchmark:

1. Ensure test cases have clear, unambiguous requirements
2. Include expected error types for error-test cases
3. Test your changes with the quick test first
4. Update this README if adding new features

## Notes

- The benchmark uses a standardized OT-2 hardware configuration to ensure consistency
- All test cases are run with the same maximum iteration limit (5 by default)
- Generated code is automatically validated using the Opentrons simulator
- Results may vary between runs due to LLM non-determinism 