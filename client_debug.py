import sys
import cv2
import torch
from PyQt5.QtWidgets import QApplication
from client_ui import RobotControlUI
from utils.general import non_max_suppression, scale_boxes
from utils.plots import Annotator
from models.experimental import attempt_load
import pathlib
import os
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

# Fix for Windows path issue
pathlib.PosixPath = pathlib.WindowsPath

class DebugRobotControlUI(RobotControlUI):
    def __init__(self):
        super().__init__()
        
        # 加载YOLOv5模型
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "best.pt")
        self.model = attempt_load(model_path, device='cpu')
        self.model.conf = 0.5  # 设置置信度阈值
        
        # 用于存储检测结果
        self.frame_count = 0
        self.label_counts = {}

    def process_frame(self, frame):
        """使用YOLOv5模型进行手势识别并渲染结果"""
        self.frame_count += 1
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

    def update_frame(self, frame):
        """重写更新帧的方法，添加手势识别"""
        # 处理帧并进行手势识别
        processed_frame, gesture_class = self.process_frame(frame)
        
        # 如果检测到有效的手势，发送对应的命令
        if gesture_class >= 0 and self.video_thread and self.video_thread.isRunning():
            self.send_command(str(gesture_class))
            print(f"检测到手势: {gesture_class}")

        # 显示处理后的帧
        height, width, channel = processed_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(processed_frame.data, width, height, bytes_per_line, 
                        QImage.Format_RGB888).rgbSwapped()
        self.video_label.setPixmap(QPixmap.fromImage(q_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 使用扩展的调试UI类
    window = DebugRobotControlUI()
    # 修改为本地调试地址
    window.SERVER_IP = "127.0.0.1"
    window.SERVER_PORT = 11113
    
    window.show()
    sys.exit(app.exec_()) 