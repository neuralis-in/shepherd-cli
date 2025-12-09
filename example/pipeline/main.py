from langfuse import observe, get_client
import os
import sys
from typing import Optional

# Load .env BEFORE any langfuse imports (langfuse reads env vars at import time)
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))


# Make repo root importable for local package (aiobs)
_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Support running as a module or a script
try:  # package-relative imports (when run with -m example.pipeline.main)
    from .client import make_client, default_model  # type: ignore
    from .tasks.research import research  # type: ignore
    from .tasks.summarize import summarize  # type: ignore
    from .tasks.critique import critique  # type: ignore
except Exception:  # fallback for direct script run: python example/pipeline/main.py
    _example_dir = os.path.dirname(os.path.dirname(__file__))
    if _example_dir not in sys.path:
        sys.path.insert(0, _example_dir)
    from pipeline.client import make_client, default_model  # type: ignore
    from pipeline.tasks.research import research  # type: ignore
    from pipeline.tasks.summarize import summarize  # type: ignore
    from pipeline.tasks.critique import critique  # type: ignore


@observe(name="pipeline")
def main(query: Optional[str] = None) -> str:
    client = make_client()
    model = default_model()

    q = query or "In one sentence, explain what an API is."
    print(f"Query: {q}\n")

    notes = research(q, client, model)
    print("Notes:")
    for n in notes:
        print(f"- {n}")
    print()

    draft = summarize(notes, client, model)
    print("Draft:\n" + draft + "\n")

    improved = critique(draft, client, model)
    print("Improved:\n" + improved + "\n")

    return improved


def generate_questions(num_questions: int = 50) -> list[str]:
    """Generate diverse questions using OpenAI."""
    from openai import OpenAI as RawOpenAI
    
    client = RawOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = default_model()
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that generates diverse, interesting questions on various topics."
            },
            {
                "role": "user",
                "content": f"""Generate exactly {num_questions} diverse questions covering different topics such as:
- Science and technology
- History and culture
- Philosophy and ethics
- Business and economics
- Health and wellness
- Arts and entertainment
- Nature and environment
- Education and learning

Return ONLY the questions, one per line, numbered 1-{num_questions}. No other text."""
            }
        ],
        temperature=0.9,
        max_tokens=4000
    )
    
    content = response.choices[0].message.content or ""
    # Parse numbered questions, strip numbers and whitespace
    questions = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if line:
            # Remove numbering like "1.", "1)", "1:" etc.
            import re
            cleaned = re.sub(r"^\d+[\.\)\:]\s*", "", line)
            if cleaned:
                questions.append(cleaned)
    
    return questions[:num_questions]


def run_single_pipeline(args: tuple[int, str, int]) -> tuple[int, bool, str]:
    """Run a single pipeline. Returns (index, success, error_message)."""
    idx, question, total = args
    try:
        print(f"[{idx}/{total}] Starting: {question[:60]}...")
        main(question)
        print(f"[{idx}/{total}] ✓ Completed")
        return (idx, True, "")
    except Exception as e:
        print(f"[{idx}/{total}] ✗ Error: {e}")
        return (idx, False, str(e))


def run_batch(num_questions: int = 50, max_workers: int = 10) -> None:
    """Run the pipeline for multiple generated questions in parallel."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    print(f"Generating {num_questions} questions using OpenAI...\n")
    questions = generate_questions(num_questions)
    print(f"Generated {len(questions)} questions. Starting parallel pipeline runs with {max_workers} workers...\n")
    print("=" * 80)
    
    # Prepare args: (index, question, total)
    tasks = [(i, q, len(questions)) for i, q in enumerate(questions, 1)]
    
    successes = 0
    failures = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(run_single_pipeline, task): task for task in tasks}
        
        for future in as_completed(futures):
            idx, success, error = future.result()
            if success:
                successes += 1
            else:
                failures += 1
    
    print(f"\n{'='*80}")
    print(f"Completed {len(questions)} pipeline runs: {successes} succeeded, {failures} failed.")
    print("=" * 80)


if __name__ == "__main__":
    # Usage: 
    #   python main.py                      -> runs batch of 50 questions (10 parallel workers)
    #   python main.py --single             -> runs single default query
    #   python main.py "query"              -> runs single custom query
    #   python main.py --batch N            -> runs batch of N questions
    #   python main.py --batch N --workers W -> runs batch of N questions with W parallel workers
    # Required env vars: OPENAI_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
    # Optional: LANGFUSE_HOST (defaults to https://cloud.langfuse.com)
    
    args = sys.argv[1:]
    
    if not args:
        # Default: run batch of 50 questions
        run_batch(50)
    elif args[0] == "--single":
        # Run single default query
        main()
    elif args[0] == "--batch":
        # Run batch with custom count and optional workers
        count = 50
        workers = 10
        if len(args) > 1:
            try:
                count = int(args[1])
            except ValueError:
                print(f"Invalid batch count: {args[1]}")
                sys.exit(1)
        if "--workers" in args:
            try:
                w_idx = args.index("--workers")
                workers = int(args[w_idx + 1])
            except (ValueError, IndexError):
                print("Invalid workers count")
                sys.exit(1)
        run_batch(count, workers)
    else:
        # Run single custom query
        main(args[0])

    # Flush Langfuse events before exit (important for short-lived scripts)
    langfuse = get_client()
    langfuse.flush()
