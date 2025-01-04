import cv2
import socket
import struct
import pickle
import time
import signal
import sys
import threading
import queue

# 创建一个全局队列用于线程间通信
command_queue = queue.Queue()
move_flag = 0  # 全局移动标志

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

def worker_thread():
    global move_flag
    move_flag = 0
    print("调试模式：工作线程启动")
    
    while True:
        try:
            # 从队列中获取命令
            if not command_queue.empty():
                command = command_queue.get()
                
                # 根据命令执行不同的操作
                if command == "0":
                    move_flag = 1
                    print("执行动作0: 模拟机械臂上下运动")
                    # 模拟机械臂动作时间
                    time.sleep(1.0)
                    print("- 恢复初始位置")
                    time.sleep(1.0)
                    print("- 执行上下运动")
                    time.sleep(1.0)
                    print("- 返回初始位置")
                    time.sleep(1.0)
                    move_flag = 0
                    
                elif command == "1":
                    move_flag = 1
                    print("执行动作1: 模拟机械臂夹取动作")
                    time.sleep(0.5)
                    print("- 夹紧")
                    time.sleep(0.5)
                    print("- 松开")
                    move_flag = 0

            time.sleep(0.1)  # 防止CPU占用过高

        except Exception as e:
            print(f"工作线程错误: {e}")

def send_frame(client_socket, frame, max_retries=3):
    # 调整图像大小为256x256
    frame = cv2.resize(frame, (256, 256))

    # 压缩图像以减少数据大小
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
    data = pickle.dumps(encoded_frame)

    # 确保数据长度不超过预定义的最大值
    MAX_MESSAGE_SIZE = 256 * 256  # 1MB
    if len(data) > MAX_MESSAGE_SIZE:
        raise ValueError(f"数据大小 ({len(data)} bytes) 超过最大限制 ({MAX_MESSAGE_SIZE} bytes)")

    try:
        message_size = struct.pack("!Q", len(data))
        client_socket.sendall(message_size)

        chunk_size = 1024
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            client_socket.sendall(chunk)

        return True

    except Exception as e:
        print(f"发送失败: {e}")
        return False

def send_video_stream(server_ip, server_port, retry_delay=5):
    global server_socket, client_socket, cap

    # 启动工作线程
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((server_ip, server_port))
        server_socket.listen(2)
        print(f"调试服务器启动在 {server_ip}:{server_port}")

        while True:
            print("等待连接...")
            client_socket, addr = server_socket.accept()
            print(f"连接建立: {addr}")

            try:
                client_socket.settimeout(30.0)

                cap = cv2.VideoCapture(0)  # 使用本地摄像头
                if not cap.isOpened():
                    raise Exception("无法打开摄像头")

                params = pickle.dumps((256, 256))
                param_size = struct.pack("!Q", len(params))
                client_socket.sendall(param_size)
                client_socket.sendall(params)

                while True:
                    try:
                        client_socket.settimeout(0.001)
                        flag = client_socket.recv(1024)
                        if flag and not move_flag:
                            command = flag.decode()
                            command_queue.put(command)
                            print(f"收到命令: {command}")
                    except socket.timeout:
                        pass
                    finally:
                        client_socket.settimeout(30.0)

                    ret, frame = cap.read()
                    if not ret:
                        print("无法获取视频帧")
                        break

                    if not send_frame(client_socket, frame):
                        break

                    time.sleep(1/20)  # 30 FPS

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
                print("连接已关闭")

            print(f"{retry_delay} 秒后重试...")
            time.sleep(retry_delay)

    finally:
        server_socket.close()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    SERVER_IP = "127.0.0.1"  # 本地调试
    SERVER_PORT = 11113

    try:
        send_video_stream(SERVER_IP, SERVER_PORT)
    except KeyboardInterrupt:
        handle_exit(None, None)