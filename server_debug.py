import cv2
import socket
import struct
import pickle
import time
import signal
import sys


def handle_exit(signum, frame):
    print("\n正在清理资源并退出...")
    if 'cap' in globals():
        cap.release()
    if 'server_socket' in globals():
        server_socket.close()
    if 'client_socket' in globals():
        client_socket.close()
    cv2.destroyAllWindows()
    sys.exit(0)


def send_frame(client_socket, frame, max_retries=3):
    # 调整图像大小为640x640
    frame = cv2.resize(frame, (640, 640))

    # 压缩图像以减少数据大小
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
    data = pickle.dumps(encoded_frame)

    # 确保数据长度不超过预定义的最大值
    MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB
    if len(data) > MAX_MESSAGE_SIZE:
        raise ValueError(f"数据大小 ({len(data)} bytes) 超过最大限制 ({MAX_MESSAGE_SIZE} bytes)")

    # 发送数据大小和数据
    try:
        # 使用固定长度（8字节）发送数据大小
        message_size = struct.pack("!Q", len(data))
        client_socket.sendall(message_size)

        # 等待接收端确认
        ack = client_socket.recv(2)
        if ack != b'OK':
            raise ConnectionError("未收到接收端确认")

        # 分块发送数据
        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            client_socket.sendall(chunk)

        # 等待接收端确认完整接收
        final_ack = client_socket.recv(2)
        if final_ack != b'OK':
            raise ConnectionError("数据传输可能不完整")

        return True

    except Exception as e:
        print(f"发送失败: {e}")
        return False


def send_video_stream(server_ip, server_port, retry_delay=5):
    global server_socket, client_socket, cap

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((server_ip, server_port))
        server_socket.listen(5)

        while True:
            print(f"等待连接 {server_ip}:{server_port}")
            client_socket, addr = server_socket.accept()
            print(f"收到来自 {addr} 的连接")

            try:
                # 设置超时
                client_socket.settimeout(5.0)

                # 配置视频捕获
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise Exception("无法打开视频捕获设备")

                # 发送视频参数
                params = pickle.dumps((640, 640))  # 固定发送640x640
                param_size = struct.pack("!Q", len(params))
                client_socket.sendall(param_size)
                client_socket.sendall(params)

                while True:
                    # 尝试接收客户端标志（非阻塞）
                    try:
                        client_socket.settimeout(0.001)
                        flag = client_socket.recv(1024)
                        if flag:
                            print(f"收到客户端标志: {flag.decode()}")
                    except socket.timeout:
                        pass
                    finally:
                        client_socket.settimeout(5.0)

                    ret, frame = cap.read()
                    if not ret:
                        print("无法获取视频帧")
                        break

                    if not send_frame(client_socket, frame):
                        break

                    # 控制帧率
                    time.sleep(1 / 30)  # 30 FPS

            except socket.timeout:
                print("连接超时")
            except ConnectionResetError:
                print("连接被重置")
            except BrokenPipeError:
                print("连接断开")
            except Exception as e:
                print(f"发生错误: {e}")
            finally:
                if 'cap' in locals():
                    cap.release()
                client_socket.close()

            print(f"{retry_delay} 秒后重试...")
            time.sleep(retry_delay)

    finally:
        server_socket.close()


if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    SERVER_IP = "0.0.0.0"  # 或指定 IP
    SERVER_PORT = 8000  # 或指定端口

    try:
        send_video_stream(SERVER_IP, SERVER_PORT)
    except KeyboardInterrupt:
        handle_exit(None, None)