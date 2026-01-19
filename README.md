# Hello Pipeline Optimization Demo

This is a demonstration of the **scientific-optimizer** Claude Code skill using the simple Nextflow `hello` pipeline.

## Overview

The original `hello` pipeline simply prints greetings. We've enhanced it to demonstrate parameter optimization by:

1. **Adding optimizable parameters:**
   - `greeting_style` (categorical): uppercase, lowercase, or titlecase
   - `batch_size` (integer): how many greetings to process per batch (1-6)
   - `repeat_count` (integer): how many times to repeat each greeting (1-5)
   - `delay` (float): simulated processing delay in seconds (0.1-1.0)

2. **Computing metrics:**
   - Throughput (greetings per second)
   - Efficiency score (throughput normalized by delay)
   - Total processing time

3. **Outputting results:**
   - Individual greeting outputs per batch
   - Per-process metrics in JSON format
   - Aggregated final metrics in `final_metrics.json`

## Pipeline Behavior

The pipeline:
1. Takes 6 greetings: 'Bonjour', 'Ciao', 'Hello', 'Hola', 'Namaste', 'Salaam'
2. Batches them according to `batch_size`
3. For each batch:
   - Applies the `greeting_style` transformation
   - Simulates processing with `delay`
   - Repeats each greeting `repeat_count` times
   - Outputs metrics
4. Aggregates metrics across all batches
5. Calculates final efficiency score (target for optimization)

## Optimization Goal

**Maximize the efficiency score** by finding the optimal combination of:
- Greeting style (doesn't affect efficiency much, but demonstrates categorical optimization)
- Batch size (larger batches = more parallel efficiency)
- Repeat count (more work per batch)
- Delay (lower delay = higher throughput, but might have quality trade-offs in real scenarios)

## Using the Scientific-Optimizer Skill

### Prerequisites

1. **Seqera Platform account** with:
   - A configured workspace
   - A compute environment (AWS, GCP, Azure, or HPC)
   - Access credentials configured

2. **Python environment** with dependencies:
   ```bash
   pip install -r ../.claude/skills/scientific-optimizer/requirements.txt
   ```

3. **Update configuration** in `strategy.yaml`:
   - Set your `workspace_id`
   - Set your `compute_env_id`
   - Set your `work_dir` (S3/GCS path)

### Quick Test (Local)

Test the pipeline locally first:

```bash
cd hello
nextflow run main.nf
```

Expected output:
- `results/greetings_*.txt` - greeting outputs
- `results/metrics_*.json` - per-process metrics
- `results/final_metrics.json` - aggregated metrics

Check the efficiency score:
```bash
cat results/final_metrics.json
```

### Run Optimization

1. **Via Claude Code** (recommended):

```bash
# In the variant-optimization directory, ask Claude Code:
# "Use the scientific-optimizer skill to optimize the hello pipeline"
```

Claude Code will:
- Read the `strategy.yaml` configuration
- Launch the orchestrator
- Suggest parameter combinations using Bayesian optimization
- Submit workflows to Seqera Platform
- Monitor execution
- Extract metrics
- Log results to MLflow
- Continue until max_trials or convergence

2. **Via Python script** (manual):

```bash
cd /Users/evanfloden/projects/variant-optimization

python .claude/skills/scientific-optimizer/scripts/optimize_pipeline.py \
    --strategy hello/strategy.yaml \
    --experiment-name hello_demo
```

### What to Expect

With the default configuration (20 trials, 2 parallel):
- **Duration**: ~30-60 minutes (depends on compute environment)
- **Cost**: < $5 (each trial is very fast)
- **Best parameters**: Likely:
  - `batch_size`: 6 (process all at once)
  - `delay`: 0.1 (minimum delay)
  - `repeat_count`: 5 (maximum work per batch)
  - `greeting_style`: any (doesn't affect efficiency)

The optimizer will quickly learn that:
1. Larger batches are more efficient (parallelization)
2. Lower delays increase throughput
3. More repeats = more work per batch = higher efficiency score
4. Greeting style doesn't matter for efficiency

### Viewing Results

1. **MLflow UI**:
```bash
cd /Users/evanfloden/projects/variant-optimization
mlflow ui
```
Open http://localhost:5000 to see:
- Trial parameters and metrics
- Optimization progress over time
- Parameter importance

2. **Best configuration**:
```bash
python .claude/skills/scientific-optimizer/scripts/visualize_results.py \
    --experiment-name hello_demo \
    --output-dir hello/results/plots
```

3. **Optuna dashboard** (optional):
```bash
optuna-dashboard sqlite:///optuna.db
```

## What This Demonstrates

This demo showcases all key features of the scientific-optimizer skill:

1. **Mixed parameter types**: Categorical, integer, and float parameters
2. **Bayesian optimization**: Sample-efficient parameter search
3. **Seqera Platform integration**: Cloud execution with monitoring
4. **Metrics extraction**: Automated scoring from JSON outputs
5. **Experiment tracking**: Complete MLflow logging
6. **Parallel execution**: Multiple trials running simultaneously
7. **Budget control**: Cost limits and early stopping

## Files

```
hello/
├── main.nf              # Modified pipeline with parameters and metrics
├── nextflow.config      # Nextflow configuration
├── strategy.yaml        # Optimization strategy for scientific-optimizer
├── README.md            # This file
└── results/             # Output directory (created during execution)
    ├── greetings_*.txt
    ├── metrics_*.json
    └── final_metrics.json
```

## Extending the Demo

To make this more realistic, you could:

1. **Add real computational work** instead of `time.sleep()`
2. **Add quality metrics** that trade off with speed (e.g., accuracy vs throughput)
3. **Add resource constraints** (CPU, memory limits)
4. **Add cost models** that reflect actual cloud pricing
5. **Add more complex parameter interactions** (e.g., batch_size affects optimal delay)

## Next Steps

After understanding this demo:

1. **Try the real use case**: Optimize `nf-core/sarek` for variant calling
   - See: `/variant-optimization/sarek-optimization/`
   - Much more complex parameter space
   - Real biological metrics (F1 score)
   - Significant cost/performance trade-offs

2. **Adapt to your pipeline**:
   - Copy `strategy-template.yaml` from scientific-optimizer/references/
   - Define your parameters and metrics
   - Run optimization with Claude Code

3. **Read the full documentation**:
   - `.claude/skills/scientific-optimizer/SKILL.md`
   - `.claude/skills/scientific-optimizer/references/optimization-overview.md`

## Support

This demo is part of the scientific-optimizer Claude Code skill.
For issues or questions, see the main skill documentation.

---

**Happy optimizing!** 🚀 
