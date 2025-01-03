import sys
import cv2
import socket
import pickle
import struct
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap

class VideoThread(QThread):
    frame_ready = pyqtSignal(object)
    
    def __init__(self, server_ip, server_port):
        super().__init__()
        self.server_ip = server_ip
        self.server_port = server_port
        self.running = True
        self.client_socket = None

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.client_socket.settimeout(5.0)
            
            # 接收视频参数
            param_size = struct.unpack("!Q", self.client_socket.recv(8))[0]
            params = self.client_socket.recv(param_size)
            width, height = pickle.loads(params)
            print(f"视频分辨率: {width}x{height}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def receive_frame(self):
        try:
            message_size = struct.unpack("!Q", self.client_socket.recv(8))[0]
            data = b''
            remaining = message_size
            
            while remaining > 0:
                chunk = self.client_socket.recv(min(remaining, 1024))
                if not chunk:
                    return None
                data += chunk
                remaining -= len(chunk)
                
            encoded_frame = pickle.loads(data)
            return cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"接收帧错误: {e}")
            return None

    def send_command(self, command):
        try:
            if self.client_socket:
                self.client_socket.send(str(command).encode())
        except Exception as e:
            print(f"发送命令错误: {e}")

    def run(self):
        if not self.connect_to_server():
            return

        while self.running:
            frame = self.receive_frame()
            if frame is not None:
                self.frame_ready.emit(frame)

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()

class RobotControlUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("机械臂控制界面")
        self.setGeometry(100, 100, 800, 600)

        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建视频显示标签
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label)

        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建控制按钮
        self.action1_button = QPushButton("动作1")
        self.action2_button = QPushButton("动作2")
        self.connect_button = QPushButton("连接服务器")
        
        button_layout.addWidget(self.action1_button)
        button_layout.addWidget(self.action2_button)
        button_layout.addWidget(self.connect_button)
        
        layout.addLayout(button_layout)

        # 设置按钮点击事件
        self.action1_button.clicked.connect(lambda: self.send_command("1"))
        self.action2_button.clicked.connect(lambda: self.send_command("2"))
        self.connect_button.clicked.connect(self.connect_to_server)

        # 初始化视频线程
        self.video_thread = None
        self.SERVER_IP = "192.168.136.164"  # 修改为你的服务器IP
        self.SERVER_PORT = 8000  # 修改为你的服务器端口

    def connect_to_server(self):
        if self.video_thread is None or not self.video_thread.isRunning():
            self.video_thread = VideoThread(self.SERVER_IP, self.SERVER_PORT)
            self.video_thread.frame_ready.connect(self.update_frame)
            self.video_thread.start()
            self.connect_button.setText("断开连接")
        else:
            self.video_thread.stop()
            self.video_thread = None
            self.connect_button.setText("连接服务器")
            self.video_label.clear()

    def send_command(self, command):
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.send_command(command)

    def update_frame(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        self.video_label.setPixmap(QPixmap.fromImage(q_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        if self.video_thread:
            self.video_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobotControlUI()
    window.show()
    sys.exit(app.exec_()) 