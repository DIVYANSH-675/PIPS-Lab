# PIPS Lab

A maintained extension of [PIPS by Adam Stein and Neelay Velingker](https://github.com/adaminsky/pips), the implementation of **Once Upon an Input: Reasoning via Per-Instance Program Synthesis** (NeurIPS 2025). Extensions by Divyansh Gupta; original authorship, history and MIT notices are retained.

PIPS selects between direct LLM reasoning and generated Python programs for each input. This version improves the execution and API paths around that research method.

## Improvements

- Run candidate programs in fresh subprocesses, including when called from UI/background threads.
- Eliminate the queue-before-join deadlock on large outputs and unreliable `queue.empty()` result detection.
- Apply execution timeouts to both setup context and generated code. On POSIX, timeout cleanup kills the worker process group.
- Capture stdout/stderr with a 64 KiB limit and bound serialized answers to 1 MiB.
- Report context exceptions, abrupt worker exits, invalid results, and timeouts explicitly.
- Preserve valid answers beginning with `Error:` instead of misclassifying them as exceptions.
- Execute code exactly once; remove text substitutions that could call `main()` twice or change program meaning.
- Correctly quote string-valued symbols in the solver, accept text-only `RawInput`, and validate solver settings and probability scores.
- Keep tests entirely offline using fake model responses, with CI on Linux and Windows.

These changes improve software reliability; they do not establish better reasoning benchmark scores.

## Install and use

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
```

```python
from pips import PIPSSolver, get_model
from pips.utils import RawInput

# Supply your provider credential through its environment variable.
model = get_model('gpt-4o')
solver = PIPSSolver(model=model, max_iterations=8)
answer, telemetry, decision = solver.solve(
    RawInput(text_input='What is the sum of the first ten prime numbers?'),
    stream=False,
)
```

Provider-backed runs require credentials and incur the provider's costs. No paid model calls were used for validation. See the [upstream usage guide](UPSTREAM_README.md) for the Gradio app, provider setup, and interactive solving.

## Execution contract

`python_eval(code, code_context=None, max_execution_time=5)` returns `(answer, output, error)`. Code must assign its result to `answer`. JSON-compatible results preserve their types; other objects use `repr`. Infinite or NaN numeric answers also use a string representation. Captured output includes stderr and a truncation marker when needed.

The worker uses the standard library in an isolated interpreter; code relying on arbitrary installed third-party packages may need a different execution backend. A subprocess timeout is **not a security sandbox**: local execution still has access to the current user's files and network. Do not expose this executor as an unrestricted public service. No containment against deliberately hostile generated code is claimed.

## Validation

The suite covers full fake-model solver flows, string symbols, context errors, error-shaped answers, large outputs, abrupt process exit, timeouts, threaded execution, and one-time program execution. Live provider APIs and hosted Gradio behavior have not been exercised in this revision.

License: [original MIT](LICENSE). New contributions: [MIT additions](ADDITIONS_LICENSE). Original paper and citations remain in [UPSTREAM_README.md](UPSTREAM_README.md).
