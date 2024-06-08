import time

from app.qt.chat_window import chat_windows_wrapper


@chat_windows_wrapper
def test_gen():
    for i in range(10):
        yield f"Test sentence {i}\n"
        yield "#refresh"
    time.sleep(1)
    for i in range(10):
        yield f"Test sentence {i}\n"
        yield "#refresh"


if __name__ == '__main__':
    test_gen()
