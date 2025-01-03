# RoboArmLink - 机械臂控制系统

GDUT 信工课设任务

## 项目结构

```plaintext
RoboArmLink/
├── best.pt        # YOLOv5训练模型
├── client.py      # 客户端（带手势识别）
├── client_ui.py   # 客户端UI界面
├── server.py      # 服务器端（机械臂控制）
├── models/        # YOLOv5模型文件
└── utils/         # 工具函数
```

## 环境要求

```bash
pip install PyQt5 opencv-python torch
```

## 使用说明

### 1. 服务器端（机械臂端）

1. 修改 `server.py` 中的配置：

```python
SERVER_IP = "0.0.0.0"  # 监听所有网络接口
SERVER_PORT = 8000     # 设置端口号
```

2. 运行服务器：

```bash
python server.py
```

### 2. 客户端（控制端）

#### 使用 UI 界面（推荐）

1. 修改 `client_ui.py` 中的服务器配置：

```python
self.SERVER_IP = "192.168.xxx.xxx"  # 改为机械臂所在电脑的IP地址
self.SERVER_PORT = 8000            # 与服务器端口保持一致
```

2. 运行 UI 客户端：

```bash
python client_ui.py
```

3. UI界面功能：
   - 点击 **"连接服务器"** 建立连接
   - 视频显示区域显示机械臂端摄像头画面
   - 点击 **"动作1"** 和 **"动作2"** 按钮发送控制命令
   - 点击 **"断开连接"** 断开与服务器的连接

#### 使用手势识别客户端

1. 修改 `client.py` 中的服务器配置：

```python
SERVER_IP = "192.168.xxx.xxx"  # 改为机械臂所在电脑的IP地址
SERVER_PORT = 8000            # 与服务器端口保持一致
```

2. 运行手势识别客户端：

```bash
python client.py
```

## 注意事项

1. **网络连接**：
   - 确保服务器和客户端在同一局域网内
   - 检查防火墙设置，确保端口通信正常
   - 可以使用 `ipconfig`（Windows）或 `ifconfig`（Linux/Mac） 查看IP地址

2. **调试建议**：
   - 首次测试可在本地进行，将 `SERVER_IP` 设置为 `"127.0.0.1"`
   - 使用 `server_debug.py` 进行调试
   - 检查端口占用情况，必要时更换端口

3. **常见问题**：
   - **连接超时**：检查网络连接和IP地址配置
   - **端口被占用**：等待几分钟或更换端口
   - **视频显示问题**：检查摄像头配置和分辨率设置

## 开发说明

- 服务器端支持自定义动作序列
- 客户端UI界面可根据需求扩展功能
- 手势识别使用 YOLOv5 模型，可替换自己训练的模型
```
