from concurrent.futures import ThreadPoolExecutor
import pytest
from pips.utils import RawInput, python_eval
from pips import PIPSSolver


def test_text_only_input():
    assert RawInput(text_input='hello').image_input is None


def test_error_shaped_answer_is_not_an_error():
    assert python_eval("answer = 'Error: this is a valid answer'") == ('Error: this is a valid answer', '', None)


def test_context_exception_is_reported():
    result = python_eval('answer = 42', 'raise ValueError("bad context")')
    assert result[0] is None and 'bad context' in result[2]


def test_large_output_does_not_deadlock():
    answer, output, error = python_eval("print('x' * 200000); answer = 7")
    assert answer == 7 and error is None
    assert len(output) < 66000 and '[output truncated]' in output


def test_timeout_and_abrupt_exit_are_errors():
    assert 'timed out' in python_eval('while True: pass', max_execution_time=0.1)[2]
    assert 'exited with code 3' in python_eval('import os; os._exit(3)')[2]


def test_main_is_not_called_twice():
    code = "calls = 0\ndef main():\n    global calls\n    calls += 1\nif __name__ == '__main__':\n    main()\nanswer = calls"
    assert python_eval(code)[0] == 1


def test_threaded_execution():
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(python_eval, ['answer = 1', 'answer = 2']))
    assert [r[0] for r in results] == [1, 2]


@pytest.mark.parametrize('timeout', [0, -1, float('nan'), float('inf')])
def test_invalid_timeout(timeout):
    with pytest.raises(ValueError):
        python_eval('answer = 1', max_execution_time=timeout)


def test_string_symbols_are_quoted_and_execution_logged():
    solver = PIPSSolver(model=object())
    logs = {}
    answer, _, error = solver._run_code('hello', 'def solve(symbols): return symbols.upper()', 0, {}, logs)
    assert answer == 'HELLO' and error is None
    assert logs['execution_results'][0]['output'] == 'HELLO'


def test_boolean_probability_list_is_rejected():
    solver = PIPSSolver(model=object())
    assert solver._parse_probability_scores(str([True] * 10)) is None
