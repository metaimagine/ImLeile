from typing import Generator
from .speech.asr.stream_microphone import AsrHandler
from .agent.pure_communicator import PureCommunicator
from .qt.chat_window import chat_windows_wrapper


@chat_windows_wrapper
def main_handler() -> Generator:
    asr_handler = AsrHandler(model_path=".models/asr/sherpa/sherpa-onnx-streaming-paraformer-bilingual-zh-en")
    communicator = PureCommunicator()
    gen = asr_handler.handle()

    for sentence in gen:
        print("Q:\n", sentence)
        reply_gen = communicator.chat(sentence)
        print("A:")
        for reply in reply_gen:
            print(reply, end="")
            yield reply
        yield "#refresh"
        print()
        print("==================")

