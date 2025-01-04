import sys
import cv2
import socket
import pickle
import struct
import threading
import torch
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QGroupBox, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QFont
from utils.general import non_max_suppression, scale_boxes
from utils.plots import Annotator
from models.experimental import attempt_load
import pathlib
import os

# Fix for Windows path issue
pathlib.PosixPath = pathlib.WindowsPath

"""
Global
"""
move_status = 0

class VideoThread(QThread):
    frame_ready = pyqtSignal(object)
    status_update = pyqtSignal(str)
    
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

    def receive_status(self):
        try:
            status_size = struct.unpack("!Q", self.client_socket.recv(8))[0]
            # print(status_size)
            # status = self.client_socket.recv(status_size).decode()
            return str(status_size)
        except Exception as e:
            print(f"接收状态错误: {e}")
            return None

    def send_command(self, command):
        try:
            if self.client_socket:
                self.client_socket.send(str(command).encode())
        except Exception as e:
            print(f"发送命令错误: {e}")

    def run(self):
        global move_status
        if not self.connect_to_server():
            return

        while self.running:
            status = self.receive_status()
            if status is not None:
                self.status_update.emit(status)
                move_status = status
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

        # 加载YOLOv5模型
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "best.pt")
        self.model = attempt_load(model_path, device='cpu')
        self.model.conf = 0.5  # 设置置信度阈值
        
        # 初始化计数器
        self.frame_count = 0
        self.label_counts = {}
        self.detecting = False

        # 创建主窗口部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        # 创建视频显示标签
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("border: 2px solid black;")
        layout.addWidget(self.video_label, 0, 0, 1, 2)

        # 创建按钮布局
        button_layout = QVBoxLayout()
        
        # 创建控制按钮
        self.action0_button = QPushButton("动作0")
        self.action1_button = QPushButton("动作1")
        self.action2_button = QPushButton("动作2")
        self.action3_button = QPushButton("动作3")
        self.action4_button = QPushButton("动作4")
        self.connect_button = QPushButton("连接服务器")
        
        buttons = [self.action0_button, self.action1_button, self.action2_button, self.action3_button, self.action4_button, self.connect_button]
        for button in buttons:
            button.setFont(QFont("Arial", 12))
            button.setStyleSheet("background-color: #4CAF50; color: white; border: none; padding: 10px;")
            button_layout.addWidget(button)
        
        layout.addLayout(button_layout, 1, 0, 1, 1)

        # 创建状态栏布局
        status_layout = QVBoxLayout()
        
        # 创建状态栏标签
        self.status_label = QLabel("检测结果: 无")
        self.arm_status_label = QLabel("机械臂状态: 未知")
        self.detect_button = QPushButton("开始检测")
        
        labels = [self.status_label, self.arm_status_label]
        for label in labels:
            label.setFont(QFont("Arial", 12))
            label.setStyleSheet("color: blue;")
            status_layout.addWidget(label)
        
        self.detect_button.setFont(QFont("Arial", 12))
        self.detect_button.setStyleSheet("background-color: #f44336; color: white; border: none; padding: 10px;")
        
        layout.addLayout(status_layout, 0, 2, 1, 1)
        layout.addWidget(self.detect_button, 1, 2, 1, 1)

        # 设置按钮点击事件
        self.action0_button.clicked.connect(lambda: self.send_button_command("0"))
        self.action1_button.clicked.connect(lambda: self.send_button_command("1"))
        self.action2_button.clicked.connect(lambda: self.send_button_command("2"))
        self.action3_button.clicked.connect(lambda: self.send_button_command("3"))
        self.action4_button.clicked.connect(lambda: self.send_button_command("4"))
        self.connect_button.clicked.connect(self.connect_to_server)
        self.detect_button.clicked.connect(self.toggle_detection)

        # 初始化视频线程
        self.video_thread = None
        self.SERVER_IP = "192.168.136.209"  # 修改为你的服务器IP
        self.SERVER_PORT = 11113  # 修改为你的服务器端口

    def process_frame(self, frame):
        """使用YOLOv5模型进行手势识别并渲染结果"""
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = torch.from_numpy(img).to('cpu').float() / 255.0
        img = img.unsqueeze(0) if img.ndimension() == 3 else img
        img = img.permute(0, 3, 1, 2)

        # 进行预测
        pred = self.model(img)[0]
        pred = non_max_suppression(pred, self.model.conf, 0.45)

        # 处理预测结果
        temp = -1
        for det in pred:
            if len(det):
                det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], frame.shape).round()
                for *xyxy, conf, cls in det:
                    # 记录检测到的标签
                    label_id = int(cls)
                    temp = label_id
                    self.label_counts[label_id] = self.label_counts.get(label_id, 0) + 1
                    
                    if self.frame_count % 1 == 0:
                        # 在图像上绘制检测框和标签
                        if self.label_counts:
                            most_common_label = max(self.label_counts, key=self.label_counts.get)
                        annotator = Annotator(frame, line_width=2, example=str(self.model.names))
                        label = f'{self.model.names[most_common_label]} {conf:.2f}'
                        annotator.box_label(xyxy, label, color=(255, 0, 0))
                        frame = annotator.result()
                        self.label_counts.clear()


        return frame, temp

    def connect_to_server(self):
        if self.video_thread is None or not self.video_thread.isRunning():
            self.video_thread = VideoThread(self.SERVER_IP, self.SERVER_PORT)
            self.video_thread.frame_ready.connect(self.update_frame)
            self.video_thread.status_update.connect(self.update_status)
            self.video_thread.start()
            self.connect_button.setText("断开连接")
            self.detect_button.setEnabled(True)  # Enable detection button after connecting
        else:
            self.video_thread.stop()
            self.video_thread = None
            self.connect_button.setText("连接服务器")
            self.video_label.clear()
            self.detect_button.setEnabled(False)  # Disable detection button after disconnecting
            self.arm_status_label.setText("机械臂状态: 未知")

    def send_button_command(self, command):
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.send_command(command)
            # Continue displaying frames after sending command
            self.video_thread.frame_ready.connect(self.update_frame)

    def send_detection_command(self, command):
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.send_command(command)

    def update_frame(self, frame):
        """更新帧并进行手势识别"""
        global move_status
        if self.detecting and move_status:
            # 处理帧并进行手势识别
            processed_frame, gesture_class = self.process_frame(frame)
            # 如果检测到有效的手势，发送对应的命令
            if gesture_class >= 0 and self.video_thread and self.video_thread.isRunning():
                self.send_detection_command(str(gesture_class))
                print(f"检测到手势: {gesture_class}")
                self.status_label.setText(f"检测结果: {gesture_class}")

            # 显示处理后的帧
            height, width, channel = processed_frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(processed_frame.data, width, height, bytes_per_line, 
                            QImage.Format_RGB888).rgbSwapped()
            self.video_label.setPixmap(QPixmap.fromImage(q_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # 仅显示原始帧
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, 
                            QImage.Format_RGB888).rgbSwapped()
            self.video_label.setPixmap(QPixmap.fromImage(q_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def toggle_detection(self):
        self.detecting = not self.detecting
        if self.detecting:
            self.detect_button.setText("取消检测")
            self.set_action_buttons_enabled(False)
        else:
            self.detect_button.setText("开始检测")
            self.set_action_buttons_enabled(True)

    def set_action_buttons_enabled(self, enabled):
        self.action0_button.setEnabled(enabled)
        self.action1_button.setEnabled(enabled)
        self.action2_button.setEnabled(enabled)
        self.action3_button.setEnabled(enabled)
        self.action4_button.setEnabled(enabled)

    def update_status(self, status):
        if status == "0":
            self.arm_status_label.setText("机械臂状态: 静止")
        elif status == "1":
            self.arm_status_label.setText("机械臂状态: 运动")
        else:
            self.arm_status_label.setText(f"机械臂状态: {status}")

    def closeEvent(self, event):
        if self.video_thread:
            self.video_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobotControlUI()
    window.show()
    sys.exit(app.exec_()) 