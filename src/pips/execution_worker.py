"""Internal subprocess worker. Process isolation is not a security sandbox."""
import contextlib
import io
import json
import sys


class BoundedOutput(io.StringIO):
    def __init__(self, limit=65536):
        super().__init__()
        self.limit = limit
        self.truncated = False

    def write(self, text):
        room = max(0, self.limit - self.tell())
        if len(text) > room:
            self.truncated = True
        super().write(text[:room])
        return len(text)

    def captured(self):
        return self.getvalue() + ('\n[output truncated]' if self.truncated else '')


def main():
    request = json.load(sys.stdin)
    output = BoundedOutput()
    namespace = {'__name__': '__main__'}
    answer, error = None, None
    try:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            if request.get('context'):
                exec(request['context'], namespace, namespace)
            exec(request['code'], namespace, namespace)
        answer = namespace.get('answer')
        try:
            json.dumps(answer, allow_nan=False)
        except (TypeError, ValueError):
            answer = repr(answer)
        if len(json.dumps(answer)) > 1048576:
            answer, error = None, 'Error: answer exceeds the 1 MiB result limit'
    except BaseException as exc:
        error = f'Error: {type(exc).__name__}: {exc}'
    json.dump([answer, output.captured(), error], sys.stdout, allow_nan=False)


if __name__ == '__main__':
    main()
