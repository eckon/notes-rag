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
    question_answer_pairs: list[tuple[str, str]],
) -> None:
    score = 0
    results: list[EvaluationResult] = []
    start_time = time.time()
    total_questions = len(question_answer_pairs)

    print(f"Total questions:  {YELLOW}{total_questions}{RESET}\n")

    for i, (question, answer) in enumerate(question_answer_pairs):
        question_start_time = time.time()

        print(
            f"{YELLOW}{i + 1}. Question [{i + 1}/{total_questions}]{RESET}:\n{question}\n"
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

            quality_score_match = re.search(
                r"Quality Score:\s*(\d+)", evaluation_result, re.IGNORECASE
            )

            quality_score = (
                int(quality_score_match.group(1)) if quality_score_match else None
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

    # Validate test case range if specified
    if args.test_case is not None and (
        args.test_case < 1 or args.test_case > len(qa_pairs)
    ):
        print(
            f"{RED}Error: Test case {args.test_case} is out of range (1-{len(qa_pairs)}){RESET}"
        )
        return

    try:
        os.chdir(expanded_notes_root)

        print(f"Notes directory:  {CYAN}{str(expanded_notes_root)}{RESET}")
        print(f"Evaluation model: {MAGENTA}{args.model}{RESET}")

        qa_pairs_to_run = [qa_pairs[args.test_case - 1]] if args.test_case else qa_pairs
        evaluate(args.model, qa_pairs_to_run)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Operation cancelled{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
