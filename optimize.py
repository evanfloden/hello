#!/usr/bin/env python3
"""
Run full optimization loop for hello pipeline.
This script manages parallel trial execution on Seqera Platform.
"""

import sys
import json
import logging
import boto3
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add scientific-optimizer scripts to path
skill_path = Path(__file__).parent.parent / ".claude/skills/scientific-optimizer/scripts"
sys.path.insert(0, str(skill_path))

from claude_orchestrator import create_orchestrator, ParallelTrialManager

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def extract_hello_scores(workflow_id: str, workflow_status: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, float]:
    """Extract metrics from hello pipeline's final_metrics.json in S3."""
    logger.info(f"Extracting scores from workflow: {workflow_id}")

    work_dir = config['seqera']['work_dir']
    work_dir_clean = work_dir.replace('s3://', '')
    parts = work_dir_clean.split('/', 1)
    bucket = parts[0]

    # The workflow publishes to results/ which goes to the outdir parameter location
    # We need to find it in the work directory structure

    # Possible paths where Seqera might publish outputs
    possible_keys = [
        # Published to outdir
        f"scidev-playground-eu-west-2/work/hello_optimization/trial_{workflow_id[-3:]}/results/final_metrics.json",
        # In work directory
        f"scidev-playground-eu-west-2/work/hello_optimization/{workflow_id}/results/final_metrics.json",
    ]

    s3 = boto3.client('s3', region_name='eu-west-2')

    # Try to list objects to find the actual path
    try:
        prefix = f"scidev-playground-eu-west-2/work/hello_optimization/"
        logger.info(f"Searching for metrics in s3://{bucket}/{prefix}")

        response = s3.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix,
            MaxKeys=100
        )

        if 'Contents' in response:
            # Find any final_metrics.json files
            metrics_files = [obj['Key'] for obj in response['Contents']
                           if 'final_metrics.json' in obj['Key']]

            if metrics_files:
                logger.info(f"Found metrics files: {metrics_files}")
                # Use the most recent one
                metrics_key = sorted(metrics_files, reverse=True)[0]

                with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json') as tmp:
                    s3.download_file(bucket, metrics_key, tmp.name)
                    with open(tmp.name, 'r') as f:
                        metrics = json.load(f)

                logger.info(f"✓ Successfully extracted metrics: {metrics}")

                return {
                    'target_metric': metrics.get('target_metric', 0.0),
                    'average_efficiency_score': metrics.get('average_efficiency_score', 0.0),
                    'average_throughput': metrics.get('average_throughput', 0.0),
                    'total_greetings_processed': metrics.get('total_greetings_processed', 0),
                    'total_elapsed_seconds': metrics.get('total_elapsed_seconds', 0.0),
                    'duration_hours': workflow_status.get('duration_hours', 0.0),
                    'tasks_completed': workflow_status.get('tasks_completed', 0),
                    'tasks_cached': workflow_status.get('tasks_cached', 0)
                }

    except Exception as e:
        logger.error(f"Failed to list/download metrics: {str(e)}")

    logger.warning("Could not find metrics file, returning defaults")
    return {
        'target_metric': 0.0,
        'duration_hours': workflow_status.get('duration_hours', 0.0),
        'tasks_completed': workflow_status.get('tasks_completed', 0)
    }


# Store the MCP call function reference
_mcp_call_function = None

def set_mcp_caller(func):
    """Set the MCP call function (provided by Claude Code)."""
    global _mcp_call_function
    _mcp_call_function = func

def mcp_call(**params):
    """Make MCP API call using the provided function."""
    if _mcp_call_function is None:
        raise RuntimeError("MCP call function not set. This script must be run by Claude Code.")
    return _mcp_call_function(**params)


def main():
    """Main optimization loop."""
    # Initialize
    strategy_path = Path(__file__).parent / "configs/strategy.yaml"

    logger.info("="*60)
    logger.info("HELLO PIPELINE OPTIMIZATION")
    logger.info("="*60)

    # Create orchestrator
    orchestrator = create_orchestrator(strategy_path)

    # Print summary
    summary = orchestrator.get_optimization_summary()
    logger.info("\nConfiguration:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    logger.info("="*60 + "\n")

    # Create parallel trial manager
    manager = ParallelTrialManager(orchestrator, parallel_trials=2)

    logger.info("Starting optimization...")
    logger.info("This will launch 20 trials with 2 running in parallel")
    logger.info("Press Ctrl+C to stop (progress will be saved)\n")

    # Run optimization
    # Note: This needs the MCP call function from Claude Code
    try:
        manager.run_optimization(
            mcp_call_func=mcp_call,
            extract_scores_func=extract_hello_scores,
            check_interval=60  # Check every 60 seconds
        )

        logger.info("\n" + "="*60)
        logger.info("OPTIMIZATION COMPLETE!")
        logger.info("="*60)

        # Get best results
        best = orchestrator.get_best_parameters()
        if best:
            logger.info(f"\n🏆 Best Trial: #{best.get('trial_id')}")
            logger.info(f"   Best {best.get('metric')}: {best.get('value'):.4f}")
            logger.info("\n   Best Parameters:")
            for param, value in best.get('parameters', {}).items():
                logger.info(f"     {param}: {value}")

            logger.info(f"\n   Total cost: ${orchestrator.total_cost:.2f}")
            logger.info(f"   Trials completed: {orchestrator.trials_completed}")

    except KeyboardInterrupt:
        logger.info("\n\nOptimization interrupted by user")
        logger.info(f"Progress saved. Completed {orchestrator.trials_completed} trials")
        logger.info("To resume, run this script again")


if __name__ == "__main__":
    # This script is designed to be imported and controlled by Claude Code
    # But we can also provide some info if run directly
    logger.info("This script should be run by Claude Code with MCP access")
    logger.info("To run manually, the MCP caller function must be provided")
