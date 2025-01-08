import socket
import struct
import pickle
import time
import signal
import sys
import threading
import queue
import move_servo

# 创建一个全局队列用于线程间通信
command_queue = queue.Queue()

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

    print("工作线程启动")
    while True:
        try:
            # 从队列中获取命令
            if not command_queue.empty():
                command = command_queue.get()
                # 在这里处理命令或执行其他任务
                # 根据命令执行不同的操作
                if command == "0":
                    move_flag = 1
                    move_servo.nod()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "1":
                    move_flag = 1
                    move_servo.clip()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "2":
                    move_flag = 1
                    move_servo.wiggle()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "3":
                    move_flag = 1
                    move_servo.turned()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "4":
                    move_flag = 1
                    move_servo.rapper()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "5":
                    move_flag = 1
                    move_servo.bow()
                    command = "-1"
                    move_flag = 0
                    pass

            time.sleep(0.1)  # 防止CPU占用过高

        except Exception as e:
            print(f"工作线程错误: {e}")


def send_frame(client_socket, frame, max_retries=3):
    # 调整图像大小为640x640
    frame = cv2.resize(frame, (320, 320))

    # 压缩图像以减少数据大小
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
    _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
    data = pickle.dumps(encoded_frame)

    try:
        state_move = struct.pack("!Q", move_flag)
        client_socket.sendall(state_move)
            
        message_size = struct.pack("!Q", len(data))
        client_socket.sendall(message_size)

        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            client_socket.sendall(chunk)

        return True

    except Exception as e:
        print(f"发送失败: {e}")
        return False


def send_video_stream(server_ip, server_port, retry_delay=5):
    global server_socket, client_socket, cap, move_flag

    # 启动工作线程
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((server_ip, server_port))
        server_socket.listen(2)

        while True:
            print(f"等待连接 {server_ip}:{server_port}")
            client_socket, addr = server_socket.accept()
            print(f"收到来自 {addr} 的连接")

            try:
                client_socket.settimeout(30.0)
                
                cap = cv2.VideoCapture(1)
                if not cap.isOpened():
                    raise Exception("无法打开视频捕获设备")
                    
                cap.set(cv2.CAP_PROP_FPS, 30)

                params = pickle.dumps((320, 320))
                param_size = struct.pack("!Q", len(params))
                client_socket.sendall(param_size)
                client_socket.sendall(params)

                while True:
                    try:
                        client_socket.settimeout(0.001)
                        flag = client_socket.recv(1024).decode()
                        print(flag)
                        if flag and not move_flag:
                            # 将收到的标志放入队列，供工作线程处理
                            command_queue.put(flag)
                            # print(f"收到客户端标志: {flag.decode()}")
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

                    time.sleep(1 / 20)  # 30 FPS

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
    SERVER_PORT = 11111  # 或指定端口
    
    move_servo.servo_init()

    try:
        send_video_stream(SERVER_IP, SERVER_PORT)
    except KeyboardInterrupt:
        handle_exit(None, None)
            if not command_queue.empty():
                command = command_queue.get()
                # 在这里处理命令或执行其他任务
                # 根据命令执行不同的操作
                if command == "0":
                    move_flag = 1
                    move_servo.nod()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "1":
                    move_flag = 1
                    move_servo.clip()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "2":
                    move_flag = 1
                    move_servo.wiggle()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "3":
                    move_flag = 1
                    move_servo.turned()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "4":
                    move_flag = 1
                    move_servo.rapper()
                    command = "-1"
                    move_flag = 0
                    pass
                elif command == "5":
                    move_flag = 1
                    move_servo.bow()
                    command = "-1"
                    move_flag = 0
                    pass

            time.sleep(0.1)  # 防止CPU占用过高

        except Exception as e:
            print(f"工作线程错误: {e}")


def send_frame(client_socket, frame, max_retries=3):
    # 调整图像大小为640x640
    frame = cv2.resize(frame, (320, 320))

    # 压缩图像以减少数据大小
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
    _, encoded_frame = cv2.imencode('.jpg', frame, encode_param)
    data = pickle.dumps(encoded_frame)

    #     # 确保数据长度不超过预定义的最大值
    #     MAX_MESSAGE_SIZE = 256 * 256  # 1MB
    #     if len(data) > MAX_MESSAGE_SIZE:
    #         raise ValueError(f"数据大小 ({len(data)} bytes) 超过最大限制 ({MAX_MESSAGE_SIZE} bytes)")

    try:
        state_move = struct.pack("!Q", move_flag)
        client_socket.sendall(state_move)
        ##################################################
        for id in range(1, 7):
            servo_data = struct.pack("!Q", move_servo.read_angle(id))
            client_socket.sendall(servo_data)
        ####################################################
        message_size = struct.pack("!Q", len(data))
        client_socket.sendall(message_size)

        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            client_socket.sendall(chunk)

        return True

    except Exception as e:
        print(f"发送失败: {e}")
        return False


def send_video_stream(server_ip, server_port, retry_delay=5):
    global server_socket, client_socket, cap, move_flag

    # 启动工作线程
    worker = threading.Thread(target=worker_thread, daemon=True)
    worker.start()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((server_ip, server_port))
        server_socket.listen(2)

        while True:
            print(f"等待连接 {server_ip}:{server_port}")
            client_socket, addr = server_socket.accept()
            print(f"收到来自 {addr} 的连接")

            try:
                client_socket.settimeout(30.0)

                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise Exception("无法打开视频捕获设备")

                cap.set(cv2.CAP_PROP_FPS, 30)

                params = pickle.dumps((320, 320))
                param_size = struct.pack("!Q", len(params))
                client_socket.sendall(param_size)
                client_socket.sendall(params)

                while True:
                    try:
                        client_socket.settimeout(0.001)
                        flag = client_socket.recv(1024).decode()
                        print(flag)
                        if flag and not move_flag:
                            # 将收到的标志放入队列，供工作线程处理
                            command_queue.put(flag)
                            # print(f"收到客户端标志: {flag.decode()}")
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

                    time.sleep(1 / 20)  # 30 FPS

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
    SERVER_PORT = 11113  # 或指定端口

    move_servo.servo_init()

    try:
        send_video_stream(SERVER_IP, SERVER_PORT)
    except KeyboardInterrupt:
        handle_exit(None, None)
