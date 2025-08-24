import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict

from config import CYAN, GREEN, GREY, MAGENTA, RED, RESET, YELLOW
from evaluator_prompt import evaluation_prompt, qa_pairs


class EvaluationResult(TypedDict):
    question: str
    expected: str
    generated: str
    evaluation: str
    correct: bool
    quality_score: int | None
    duration: float
    answer_duration: float
    evaluation_duration: float


def evaluate(
    model: str,
    notes_root: Path,
    output_file: str | None = None,
    test_case: int | None = None,
) -> None:
    print(f"Notes directory:  {CYAN}{str(notes_root)}{RESET}")
    print(f"Evaluation model: {MAGENTA}{model}{RESET}")

    # Filter qa_pairs if specific test case is requested, otherwise run all
    if test_case is not None:
        if test_case < 1 or test_case > len(qa_pairs):
            print(
                f"{RED}Error: Test case {test_case} is out of range (1-{len(qa_pairs)}){RESET}"
            )
            return
        qa_pairs_to_run = [qa_pairs[test_case - 1]]
        print(f"Running Question: {YELLOW}{test_case}{RESET}\n")
    else:
        qa_pairs_to_run = qa_pairs
        print(f"Total questions:  {YELLOW}{len(qa_pairs_to_run)}{RESET}\n")

    score = 0
    current_dir = os.getcwd()
    results: list[EvaluationResult] = []
    start_time = time.time()
    total_questions = len(qa_pairs_to_run)

    try:
        os.chdir(notes_root)
    except Exception as e:
        print(f"{RED}Error changing to notes directory: {e}{RESET}")
        return

    for i, (question, answer) in enumerate(qa_pairs_to_run):
        question_start_time = time.time()

        # Show original question number if running specific test case otherwise show current question
        display_number = test_case if test_case is not None else i + 1
        print(
            f"{YELLOW}{display_number}. Question [{i + 1}/{total_questions}]{RESET}:\n{question}\n"
        )
        print(f"{GREEN}Expected Answer{RESET}:\n{answer}\n")

        try:
            print(f"{GREY}Generating answer...{RESET}")
            answer_start_time = time.time()
            generated_answer = run_opencode(question, model)
            answer_duration = time.time() - answer_start_time

            print(f"{MAGENTA}Generated Answer{RESET}:\n{generated_answer}\n")

            print(f"{GREY}Evaluating answer...{RESET}")
            evaluation_start_time = time.time()
            evaluation_result = run_opencode(
                evaluation_prompt.substitute(
                    question=question,
                    answer=answer,
                    answer_to_evaluate=generated_answer,
                ),
                model,
            )
            evaluation_duration = time.time() - evaluation_start_time

            print(f"{CYAN}Evaluation{RESET}:\n{evaluation_result}\n")

            evaluation_result_match = re.search(
                r"Evaluation Result:\s*(true|false)", evaluation_result, re.IGNORECASE
            )

            is_correct = bool(
                evaluation_result_match
                and evaluation_result_match.group(1).lower() == "true"
            )

            quality_scora_match = re.search(
                r"Quality Score:\s*(\d+)", evaluation_result, re.IGNORECASE
            )

            quality_score = (
                int(quality_scora_match.group(1)) if quality_scora_match else None
            )

            if is_correct:
                score += 1
                status = f"{GREEN}✓ PASS{RESET}"
                status_color = GREEN
            else:
                status = f"{RED}✗ FAIL{RESET}"
                status_color = RED

            question_duration = time.time() - question_start_time
            score_text = (
                f" (Quality Score: {quality_score}/100)"
                if quality_score is not None
                else ""
            )
            print(
                f"{status} - Current Score: {status_color}{score}/{i + 1} ({score / (i + 1) * 100:.1f}%){RESET}{score_text} "
                f"(Answer: {answer_duration:.1f}s, Eval: {evaluation_duration:.1f}s, Total: {question_duration:.1f}s)\n"
            )

            # Store result for potential file output
            results.append(
                {
                    "question": question,
                    "expected": answer,
                    "generated": generated_answer,
                    "evaluation": evaluation_result,
                    "correct": is_correct,
                    "quality_score": quality_score,
                    "duration": question_duration,
                    "answer_duration": answer_duration,
                    "evaluation_duration": evaluation_duration,
                }
            )

        except Exception as e:
            question_duration = time.time() - question_start_time
            print(
                f"{RED}Error processing question {i + 1}: {e}{RESET} ({question_duration:.1f}s)\n"
            )
            results.append(
                {
                    "question": question,
                    "expected": answer,
                    "generated": f"ERROR: {e}",
                    "evaluation": "ERROR",
                    "correct": False,
                    "quality_score": None,
                    "duration": question_duration,
                    "answer_duration": 0,
                    "evaluation_duration": 0,
                }
            )

    # Always change back to original directory
    os.chdir(current_dir)

    end_time = time.time()
    duration = end_time - start_time
    percentage = (score / total_questions) * 100

    quality_scores = [
        r["quality_score"] for r in results if r["quality_score"] is not None
    ]

    avg_quality_score = (
        sum(quality_scores) / len(quality_scores) if quality_scores else 0
    )

    print(f"{CYAN}EVALUATION COMPLETE{RESET}")
    print(
        f"Final Score:     {GREEN}{score}/{total_questions} ({percentage:.1f}%){RESET}"
    )
    print(f"Quality Average: {MAGENTA}{avg_quality_score:.1f}/100{RESET}")
    print(f"Duration:     {YELLOW}{duration:.1f} seconds{RESET}")
    print(f"Average time: {YELLOW}{duration / total_questions:.1f} seconds{RESET}")

    incorrect_question_numbers = [
        i + 1 for i, result in enumerate(results) if not result["correct"]
    ]

    if incorrect_question_numbers:
        print(
            f"Incorrect:    {RED}{', '.join(map(str, incorrect_question_numbers))}{RESET}"
        )

    error_question_numbers = [
        i + 1 for i, result in enumerate(results) if "ERROR:" in result["generated"]
    ]

    if error_question_numbers:
        print(
            f"Errors:       {MAGENTA}{', '.join(map(str, error_question_numbers))}{RESET}"
        )

    if output_file:
        save_results_to_file(
            results, output_file, model, score, total_questions, duration
        )


def run_opencode(prompt: str, model: str) -> str:
    command = ["opencode", "--model", model, "run", prompt]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else "Unknown error"
        raise Exception(f"Command failed with exit code {e.returncode}: {error_msg}")
    except FileNotFoundError:
        raise Exception(
            "opencode command not found. Make sure it's installed and in your PATH."
        )


def save_results_to_file(
    results: list[EvaluationResult],
    filename: str,
    model: str,
    score: int,
    total: int,
    duration: float,
) -> None:
    try:
        # Calculate average quality score
        quality_scores = [
            r["quality_score"] for r in results if r["quality_score"] is not None
        ]
        avg_quality_score = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0
        )

        with open(filename, "w") as f:
            f.write("Evaluation Results\n")
            f.write(f"Model: {model}\n")
            f.write(f"Score: {score}/{total} ({score / total * 100:.1f}%)\n")
            f.write(f"Quality Average: {avg_quality_score:.1f}/100\n")
            f.write(f"Duration: {duration:.1f} seconds\n")
            f.write(f"Average: {duration / total:.1f} seconds per question\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"Question {i}:\n{result['question']}\n\n")
                f.write(f"Expected:\n{result['expected']}\n\n")
                f.write(f"Generated:\n{result['generated']}\n\n")
                f.write(f"Evaluation:\n{result['evaluation']}\n\n")
                f.write(f"Result: {'PASS' if result['correct'] else 'FAIL'}\n")
                quality_score = result.get("quality_score")
                if quality_score is not None:
                    f.write(f"Quality Score: {quality_score}/100\n")
                f.write(f"Answer Duration: {result.get('answer_duration', 0):.1f}s\n")
                f.write(
                    f"Evaluation Duration: {result.get('evaluation_duration', 0):.1f}s\n"
                )
                f.write(f"Total Duration: {result.get('duration', 0):.1f}s\n")
                f.write("-" * 80 + "\n\n")

        print(f"{GREEN}Results saved to {filename}{RESET}")
    except Exception as e:
        print(f"{RED}Error saving results to file: {e}{RESET}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate AI model performance on Q&A tasks"
    )

    parser.add_argument(
        "--model",
        default="anthropic/claude-sonnet-4-20250514",
        help="AI model to use for evaluation (default: anthropic/claude-sonnet-4-20250514)",
    )

    parser.add_argument(
        "--notes-root",
        default="~/Documents/notes",
        help="Root directory of notes (default: ~/Documents/notes)",
    )

    parser.add_argument("--output", help="Save detailed results to file")
    parser.add_argument(
        "--test-case",
        type=int,
        help="Run only a specific test case by number (1-based index)",
    )

    args = parser.parse_args()

    expanded_notes_root = Path(os.path.expanduser(args.notes_root))
    if not expanded_notes_root.exists():
        print(f"{RED}Error: Notes directory '{expanded_notes_root}' not found{RESET}")
        return

    try:
        evaluate(args.model, expanded_notes_root, args.output, args.test_case)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Operation cancelled{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
