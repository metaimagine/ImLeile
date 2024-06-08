"""
实现一个从外部输入数据即可在windows窗口中逐字打印显示的功能
1. 接受外部数据输入
2. 在窗口中逐字打印显示
3. 逐字打印完成后，窗口渐隐
4. 渐隐完成后，清空窗口内容
5. 有新的输入时，重新显示窗口继续<4>
"""

import queue
import sys
import logging
import time

from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget, QStyle
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve

logger = logging.getLogger(__name__)

SENTENCE_Q = queue.Queue()


class ChatWindow(QMainWindow):
    def __init__(self, debug=False):
        super().__init__()
        self.initUI()
        self.input_queue = queue.Queue()
        self.is_debug = debug

        self.input_thread = InputThread()
        self.input_thread.input_signal.connect(self.input_queue_in)
        self.input_thread.start()

    def initUI(self):
        self.setWindowTitle('聊天框')
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DesktopIcon))
        self.setGeometry(1460, 280, 600, 200)  # 按照1920*1080设置右下角位置
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景为透明
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)  # 隐藏窗口边框

        layout = QVBoxLayout()

        self.text = ""
        self.text_color = "#00FF00"
        self.char_count_per_line = 0
        self.is_sentence_end = False

        self.label = QLabel(self)
        self.label.setFont(QFont('Arial', 10))
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 允许鼠标选择文本
        self.label.resizeEvent = self.label_resized  # 监听标签大小变化
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        container.setAttribute(Qt.WA_TranslucentBackground)  # 设置容器背景为透明
        container.setStyleSheet("""
            background-color: rgba(128, 128, 128, 0.5);
            padding: 10px; border-radius: 10px;
        """)
        container.setStyleSheet(container.styleSheet() + f"color: {self.text_color};")
        self.setCentralWidget(container)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.timer = QTimer()
        self.timer.timeout.connect(self.typing_writer)
        self.timer.start(100)  # 100毫秒触发一次

        self.fade_out_timer = QTimer()
        self.fade_out_timer.timeout.connect(self.fade_out)
        self.fade_out_step = 0.1  # 每步透明度减少的值

        self.setWindowOpacity(0)

        self.label_size = (self.label.sizeHint().width(), self.label.sizeHint().height())

    def resize_label_to_initial(self):
        self.resize(self.label_size[0], self.label_size[1])

    def label_resized(self, event):
        self.resize(self.label.sizeHint())

    def input_queue_in(self, text):
        if self.is_debug:
            # print("[ChatWindow] input_queue_in: ", text)
            logger.info(f"input_queue_in: {text}")
        if text == "#refresh":
            self.input_queue.put(text)
            return
        if text:
            for c in text:
                self.input_queue.put(c)
                # print(f"[input_queue_in] Putting '{c}' into input_queue")  # MODIFY

    def input_queue_out(self):
        if not self.input_queue.empty():
            return self.input_queue.get()
        return None

    def typing_writer(self):
        text = self.input_queue_out()
        if text == "#refresh":
            self.is_sentence_end = True
            return

        if text is None:
            return

        if self.is_sentence_end:
            self.flash_all()
            # self.text = ""
            # self.char_count_per_line = 0
            # self.is_sentence_end = False
            # self.resize_label_to_initial()

        self.fade_out_timer.stop()
        self.setWindowOpacity(1)

        if self.is_debug:
            logger.info(f"[typing_writer] Retrieved '{text}' from input_queue")

        # 文本大于20个字则换行
        limit_len_per_line = 60
        self.text += text
        self.char_count_per_line += len(text.encode("utf-8"))
        if self.char_count_per_line >= limit_len_per_line:
            self.text += "\n"
            self.char_count_per_line = 0
        self.label.setText(self.text)
        self.fade_out_timer.start(5000)  # 5秒后开始渐变消失

    def flash_all(self):
        # self.input_queue.queue.clear()
        self.is_sentence_end = False
        self.text = ""
        self.char_count_per_line = 0
        self.label.setText(self.text)
        self.resize_label_to_initial()

    def fade_out(self):
        if self.windowOpacity() == 0:
            self.fade_out_timer.stop()
            return
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(3000)  # 设置动画持续时间，例如2000毫秒
        self.animation.setStartValue(1.0)  # 设置起始透明度
        self.animation.setEndValue(0.0)  # 设置结束透明度
        self.animation.setEasingCurve(QEasingCurve.OutQuad)  # 设置缓动曲线，使动画更自然
        self.animation.finished.connect(self.on_animation_finished)  # 动画完成后执行清理操作
        self.animation.start()  # 开始动画

    def on_animation_finished(self):
        self.flash_all()


class InputThread(QThread):
    input_signal = pyqtSignal(str)

    def run(self):
        while True:
            if SENTENCE_Q.empty():
                time.sleep(0.1)
                continue
            input_text = SENTENCE_Q.get()
            logger.info(f"[InputThread] get input text: {input_text}")
            self.input_signal.emit(input_text)


class ChatWindowHandler:
    def __init__(self, debug=False):
        self.app = QApplication(sys.argv)
        self.chat_window = ChatWindow(debug=debug)
        self.chat_window.show()

    def __enter__(self):
        return self

    def _exit(self):
        sys.exit(self.app.exec_())

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit()


def chat_windows_wrapper(f, *args, **kwargs):
    with ChatWindowHandler(debug=False) as _:
        def _g():
            for sentence in f(*args, **kwargs):
                SENTENCE_Q.put(sentence)

        t = QThread()
        t.run = _g
        t.start()
