"""Standalone CLI for running MIRA workflow evaluations.

Usage:
    python -m evals.run_eval [OPTIONS]

Options:
    --model-id TEXT      Model to assess (default: claude-sonnet-4-6)
    --all-models         Run across all configured models
    --examples TEXT      Comma-separated example names or "all" (default: all)
    --workflow TEXT       "wf1", "wf2", "wf3", "chain", or "all" (default: all)
    --judge-model TEXT   Model for LLM-as-Judge (default: claude-opus-4-6)
    --save-golden        Save LLM responses as golden files for mock mode
"""

import argparse
import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

ALL_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "gpt-5.2",
    "gpt-5.4",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MIRA workflow assessments")
    parser.add_argument("--model-id", default="claude-sonnet-4-6", help="Model to assess")
    parser.add_argument(
        "--all-models", action="store_true", help="Run across all configured models"
    )
    parser.add_argument("--examples", default="all", help="Comma-separated example names or 'all'")
    parser.add_argument(
        "--workflow",
        default="all",
        choices=["wf1", "wf2", "wf3", "chain", "all"],
        help="Which workflow(s) to assess",
    )
    parser.add_argument("--judge-model", default="claude-opus-4-6", help="Model for LLM-as-Judge")
    parser.add_argument(
        "--save-golden",
        action="store_true",
        help="Save LLM responses as golden files",
    )
    return parser.parse_args()


async def run_single_assessment(
    example,
    model_id: str,
    workflow: str,
    judge_model: str,
    save_golden: bool,
) -> dict:
    """Run assessment for a single example + model + workflow combination."""
    from evals.evaluators.accuracy import evaluate as assess_accuracy
    from evals.evaluators.completeness import evaluate as assess_completeness
    from evals.evaluators.composite import compute_composite_score
    from evals.evaluators.cross_entity import evaluate as assess_cross_entity
    from evals.evaluators.schema_compliance import evaluate as assess_schema
    from evals.evaluators.semantic import evaluate as assess_semantic
    from evals.evaluators.structural import evaluate as assess_structural
    from evals.runner.auto_approver import run_graph_with_auto_approve
    from evals.runner.graph_harness import (
        build_wf1_state,
        build_wf2_state,
        build_wf3_state,
        compile_eval_graph,
        eval_patches,
    )
    from evals.runner.workflow_chain import run_full_chain

    result = {"example": example.name, "model": model_id, "workflow": workflow}

    try:
        if workflow == "chain":
            chain = await run_full_chain(example, model_id, eval_patches)
            result["wf1_state"] = chain["wf1"]
            result["wf2_state"] = chain["wf2"]
            result["wf3_state"] = chain["wf3"]
        elif workflow == "wf1":
            graph = compile_eval_graph("product_meter_aggregation")
            state = build_wf1_state(example, model_id)
            config = {"configurable": {"thread_id": f"run-{example.name}-{model_id}"}}
            with eval_patches(example):
                result["wf1_state"] = await run_graph_with_auto_approve(graph, state, config)
        elif workflow == "wf2":
            # Need WF1 first
            wf1_graph = compile_eval_graph("product_meter_aggregation")
            wf1_state = build_wf1_state(example, model_id)
            wf1_config = {"configurable": {"thread_id": f"run-pre-{example.name}"}}
            with eval_patches(example):
                wf1_result = await run_graph_with_auto_approve(wf1_graph, wf1_state, wf1_config)
            wf2_graph = compile_eval_graph("plan_pricing")
            wf2_state = build_wf2_state(example, wf1_result, model_id)
            wf2_config = {"configurable": {"thread_id": f"run-wf2-{example.name}"}}
            with eval_patches(example, wf1_state=wf1_result):
                result["wf2_state"] = await run_graph_with_auto_approve(
                    wf2_graph, wf2_state, wf2_config
                )
            result["wf1_state"] = wf1_result
        elif workflow == "wf3":
            # Need WF1 + WF2 first
            wf1_graph = compile_eval_graph("product_meter_aggregation")
            wf1_state = build_wf1_state(example, model_id)
            wf1_config = {"configurable": {"thread_id": f"run-pre1-{example.name}"}}
            with eval_patches(example):
                wf1_result = await run_graph_with_auto_approve(wf1_graph, wf1_state, wf1_config)
            wf2_graph = compile_eval_graph("plan_pricing")
            wf2_state = build_wf2_state(example, wf1_result, model_id)
            wf2_config = {"configurable": {"thread_id": f"run-pre2-{example.name}"}}
            with eval_patches(example, wf1_state=wf1_result):
                wf2_result = await run_graph_with_auto_approve(wf2_graph, wf2_state, wf2_config)
            wf3_graph = compile_eval_graph("account_setup")
            wf3_state = build_wf3_state(example, wf1_result, wf2_result, model_id)
            wf3_config = {"configurable": {"thread_id": f"run-wf3-{example.name}"}}
            with eval_patches(example, wf1_state=wf1_result, wf2_state=wf2_result):
                result["wf3_state"] = await run_graph_with_auto_approve(
                    wf3_graph, wf3_state, wf3_config
                )
            result["wf1_state"] = wf1_result
            result["wf2_state"] = wf2_result

        # Save golden if requested
        if save_golden:
            golden_dir = Path(__file__).parent / "golden"
            golden_dir.mkdir(exist_ok=True)
            for key in ["wf1_state", "wf2_state", "wf3_state"]:
                if key in result and result[key]:
                    golden_path = golden_dir / f"{example.name}_{model_id}_{key}.json"
                    with open(golden_path, "w") as f:
                        json.dump(result[key], f, indent=2, default=str)
                    logger.info("Saved golden: %s", golden_path)

        # Run evaluators
        wf_configs = []
        if "wf1_state" in result and result.get("wf1_state"):
            wf_configs.append(
                ("wf1", result["wf1_state"], example.wf1_reference, "product_meter_aggregation")
            )
        if "wf2_state" in result and result.get("wf2_state"):
            wf_configs.append(("wf2", result["wf2_state"], example.wf2_reference, "plan_pricing"))
        if "wf3_state" in result and result.get("wf3_state"):
            wf_configs.append(("wf3", result["wf3_state"], example.wf3_reference, "account_setup"))

        result["scores"] = {}
        for wf_name, state, reference, wf_type in wf_configs:
            evaluator_results = {
                "structural": assess_structural(state, reference, wf_type),
                "schema_compliance": assess_schema(state, reference, wf_type),
                "completeness": assess_completeness(state, reference, wf_type),
                "accuracy": assess_accuracy(state, reference, wf_type),
                "cross_entity": assess_cross_entity(state, reference, wf_type),
            }

            # Run semantic assessment
            try:
                semantic_result = await assess_semantic(
                    state, reference, wf_type, judge_model=judge_model
                )
                evaluator_results["semantic"] = semantic_result
                composite = compute_composite_score(evaluator_results, include_semantic=True)
            except Exception:
                logger.warning("Semantic assessment failed, computing without it")
                composite = compute_composite_score(evaluator_results, include_semantic=False)

            result["scores"][wf_name] = {
                "composite": composite.score,
                "details": {k: v.score for k, v in evaluator_results.items()},
            }

        result["status"] = "success"

    except Exception as e:
        logger.error("Assessment failed for %s/%s/%s: %s", example.name, model_id, workflow, e)
        result["status"] = "error"
        result["error"] = str(e)

    return result


async def main() -> None:
    args = parse_args()

    from evals.datasets.registry import ALL_EXAMPLES, get_example

    # Resolve examples
    if args.examples == "all":
        examples = ALL_EXAMPLES
    else:
        example_names = [n.strip() for n in args.examples.split(",")]
        examples = [get_example(n) for n in example_names]

    # Resolve models
    models = ALL_MODELS if args.all_models else [args.model_id]

    # Resolve workflows
    if args.workflow == "all":
        workflows = ["wf1", "wf2", "wf3"]
    else:
        workflows = [args.workflow]

    logger.info(
        "Running assessments: %d examples x %d models x %d workflows",
        len(examples),
        len(models),
        len(workflows),
    )

    all_results = []
    for model_id in models:
        for example in examples:
            for workflow in workflows:
                logger.info("Assessing: %s / %s / %s", example.name, model_id, workflow)
                result = await run_single_assessment(
                    example, model_id, workflow, args.judge_model, args.save_golden
                )
                all_results.append(result)

                if result["status"] == "success" and "scores" in result:
                    for wf_name, scores in result["scores"].items():
                        logger.info(
                            "  %s composite: %.2f | %s",
                            wf_name,
                            scores["composite"],
                            " | ".join(f"{k}={v:.2f}" for k, v in scores["details"].items()),
                        )
                else:
                    logger.error("  FAILED: %s", result.get("error", "unknown error"))

    # Summary
    print("\n" + "=" * 80)
    print("ASSESSMENT SUMMARY")
    print("=" * 80)
    print(f"Timestamp: {datetime.now(UTC).isoformat()}")
    print(f"Models: {', '.join(models)}")
    print(f"Examples: {', '.join(e.name for e in examples)}")
    print(f"Workflows: {', '.join(workflows)}")
    print("-" * 80)

    for result in all_results:
        status = result["status"]
        name = result["example"]
        model = result["model"]
        if status == "success" and "scores" in result:
            for wf_name, scores in result["scores"].items():
                print(
                    f"  {name:20s} | {model:25s} | {wf_name:5s} | "
                    f"composite={scores['composite']:.3f}"
                )
        else:
            print(f"  {name:20s} | {model:25s} | FAILED: {result.get('error', '?')}")

    print("=" * 80)

    # Save results JSON
    results_path = Path(__file__).parent / "golden" / "latest_results.json"
    results_path.parent.mkdir(exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    logger.info("Results saved to %s", results_path)


if __name__ == "__main__":
    asyncio.run(main())
