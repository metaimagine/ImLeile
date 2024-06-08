#!/usr/bin/env python3

# Please refer to
# https://k2-fsa.github.io/sherpa/onnx/pretrained_models/online-paraformer/paraformer-models.html#
# to download pre-trained sherpa
import os.path
import queue
from typing import Generator

import sounddevice as sd
import sys
import logging
import sherpa_onnx

logger = logging.getLogger(__name__)


class AsrHandler:
    def __init__(self, model_path, debug=False):
        self.recognizer = None
        self.sentence_q = queue.Queue()
        self.init_recognizer(model_path)
        self.debug = debug

    def init_recognizer(self, model_path):
        encoder = os.path.join(model_path, "encoder.int8.onnx")
        decoder = os.path.join(model_path, "decoder.int8.onnx")
        tokens = os.path.join(model_path, "tokens.txt")
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_paraformer(
            tokens=tokens,
            encoder=encoder,
            decoder=decoder,
            num_threads=2,
            sample_rate=16000,
            feature_dim=80,
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=2.4,
            rule2_min_trailing_silence=1.2,
            rule3_min_utterance_length=300,  # it essentially disables this rule
        )

    @staticmethod
    def show_devices():
        devices = sd.query_devices()
        if len(devices) == 0:
            logger.info("No microphone devices found")
            sys.exit(0)

        logger.info(devices)
        default_input_device_idx = sd.default.device[0]
        logger.info(f'Use default device: {devices[default_input_device_idx]["name"]}')

    def handle(self) -> Generator:
        logger.info("Microphone Asr Started! Please speak...")

        # The model is using 16 kHz, we use 48 kHz here to demonstrate that
        # sherpa-onnx will do resampling inside.
        sample_rate = 48000
        samples_per_read = int(0.5 * sample_rate)  # 0.1 second = 100 ms

        stream = self.recognizer.create_stream()

        last_result = ""
        segment_id = 0
        try:
            with sd.InputStream(
                channels=1, dtype="float32", samplerate=sample_rate
            ) as s:
                while True:
                    samples, _ = s.read(samples_per_read)  # a blocking read
                    samples = samples.reshape(-1)
                    stream.accept_waveform(sample_rate, samples)
                    while self.recognizer.is_ready(stream):
                        self.recognizer.decode_stream(stream)

                    is_endpoint = self.recognizer.is_endpoint(stream)

                    result = self.recognizer.get_result(stream)

                    if result and (last_result != result):
                        last_result = result
                        if self.debug: logger.info("\r{}:{}".format(segment_id, result))
                    if is_endpoint:
                        if result:
                            if self.debug:logger.info("\r{}:{}".format(segment_id, result))
                            segment_id += 1
                            # generator result
                            yield result

                        self.recognizer.reset(stream)
        except sd.PortAudioError as e:
            logger.exception(f"no input device found: {e}")
