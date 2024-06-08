from app.speech.asr.stream_microphone import AsrHandler

if __name__ == "__main__":
    try:
        AsrHandler(model_path=".models/asr/sherpa/sherpa-onnx-streaming-paraformer-bilingual-zh-en").handle()
    except KeyboardInterrupt:
        print("\nCaught Ctrl + C. Exiting")