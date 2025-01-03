import socket
import cv2
import pickle
import struct
import torch
import signal
import sys
from utils.general import non_max_suppression, scale_boxes
from utils.plots import Annotator
from models.experimental import attempt_load
import pathlib
import os

# Fix for Windows path issue
pathlib.PosixPath = pathlib.WindowsPath

# 加载 YOLOv5 模型
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "best.pt")
model = attempt_load(model_path, device='cpu')
model.conf = 0.5  # 设置置信度阈值


def process_frame(frame):
    """使用 YOLOv5 模型进行手势识别并渲染结果"""
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = torch.from_numpy(img).to('cpu').float() / 255.0  # Convert to tensor
    img = img.unsqueeze(0) if img.ndimension() == 3 else img

    # Permute the dimensions to [batch_size, channels, height, width]
    img = img.permute(0, 3, 1, 2)

    pred = model(img)[0]
    pred = non_max_suppression(pred, model.conf, 0.45)  # NMS

    for det in pred:
        if len(det):
            det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], frame.shape).round()
            for *xyxy, conf, cls in det:
                return int(cls), xyxy, conf

    return -1, -1, -1

def handle_exit(signum, frame):
    print("\n正在清理资源并退出...")
    if 'client_socket' in globals():
        client_socket.close()
    cv2.destroyAllWindows()
    sys.exit(0)

def receive_frame(client_socket):
    try:
        # 接收数据大小
        message_size = struct.unpack("!Q", client_socket.recv(8))[0]

        # 分块接收数据
        data = b''
        remaining = message_size
        chunk_size = 1024

        while remaining > 0:
            chunk = client_socket.recv(min(remaining, chunk_size))
            if not chunk:
                raise ConnectionError("连接中断")
            data += chunk
            remaining -= len(chunk)

        # 解析数据
        encoded_frame = pickle.loads(data)
        return cv2.imdecode(encoded_frame, cv2.IMREAD_COLOR)

    except Exception as e:
        print(f"接收失败: {e}")
        return None

def receive_video_stream(server_ip, server_port):
    global client_socket

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
        client_socket.settimeout(5.0)

        # 接收视频参数
        param_size = struct.unpack("!Q", client_socket.recv(8))[0]
        params = client_socket.recv(param_size)
        width, height = pickle.loads(params)
        print(f"视频分辨率: {width}x{height}")

        frame_count = 0
        label_counts = {}

        while True:
            frame = receive_frame(client_socket)
            if frame is None:
                break

            cls, xy, conf = process_frame(frame)
            frame_count += 1

            # 每一帧都记录label
            if cls != -1:
                label_counts[cls] = label_counts.get(cls, 0) + 1

            # 每20帧绘制一次
            if frame_count % 20 == 0:
                if label_counts:
                    most_common_label = max(label_counts, key=label_counts.get)
                    annotator = Annotator(frame, line_width=2, example=str(model.names))
                    label = f'{model.names[int(most_common_label)]} {conf:.2f}'
                    annotator.box_label(xy, label, color=(255, 0, 0))
                    frame = annotator.result()
                label_counts.clear()  # Reset label counts

            # 显示视频帧
            cv2.imshow('Video Stream', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # 发送分类结果
            cls_to_send = most_common_label if frame_count % 20 == 0 else -1
            client_socket.send(str(cls_to_send).encode())

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        client_socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    SERVER_IP = "192.168.136.164"  # 或服务器 IP
    SERVER_PORT = 11113  # 或服务器端口

    try:
        receive_video_stream(SERVER_IP, SERVER_PORT)
    except KeyboardInterrupt:
        handle_exit(None, None)
