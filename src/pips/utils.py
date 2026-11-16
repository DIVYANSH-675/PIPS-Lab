"""
Utility functions and data structures for Per-Instance Program Synthesis (PIPS).
"""

from dataclasses import dataclass
from typing import Any, Optional
from io import BytesIO
import base64
import contextlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
from io import StringIO
from contextlib import redirect_stdout
from PIL import Image


@dataclass
class RawInput:
    """Dataclass to store raw input for a function."""
    image_input: Optional[Image.Image] = None
    text_input: Optional[str] = None


def img2base64(img):
    """Convert PIL Image to base64 string."""
    buffer = BytesIO()
    if img.mode != "RGB":
        img = img.convert("RGB")

    # if width or height < 28, resize it keeping aspect ratio
    if img.width < 28 or img.height < 28:
        # make smallest dimension 28
        new_width = 28
        new_height = 28
        if img.width < img.height:
            new_height = int((28 / img.width) * img.height)
        else:
            new_width = int((28 / img.height) * img.width)
        img = img.resize((new_width, new_height))

    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


def base642img(base64_str):
    """Convert base64 string to PIL Image."""
    imgdata = base64.b64decode(base64_str)
    return Image.open(BytesIO(imgdata))


def run_with_timeout(code, timeout, code_context=None):
    """Execute in a fresh process, returning (answer, captured output, error).

    This limits duration and captured output; it does not isolate files or network.
    JSON-compatible answers retain their types; other answers use their repr.
    """
    if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a finite positive number")
    if not isinstance(code, str) or (code_context is not None and not isinstance(code_context, str)):
        raise TypeError("code and code_context must be strings")
    worker = Path(__file__).with_name('execution_worker.py')
    process = subprocess.Popen([sys.executable, '-I', str(worker)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=(os.name == 'posix'))
    try:
        stdout, stderr = process.communicate(json.dumps({'code': code, 'context': code_context}), timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.communicate()
        return None, '', 'Error: Code execution timed out'
    if process.returncode:
        return None, '', f'Error: execution worker exited with code {process.returncode}: {stderr[-2000:]}'
    try:
        answer, output, error = json.loads(stdout)
        return answer, output, error
    except (ValueError, TypeError):
        return None, '', 'Error: execution worker returned an invalid result'


def python_eval(code: str, code_context: str = None, max_execution_time: float = 5):
    """Execute code exactly once. Assign the desired result to ``answer``."""
    return run_with_timeout(code, max_execution_time, code_context)


def eval_extracted_code(code):
    answer, _, error = python_eval(code)
    return "None" if error else answer
