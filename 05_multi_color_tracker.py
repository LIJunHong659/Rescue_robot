# 05_multi_color_tracker.py
# 功能：多颜色球体追踪（红/绿/蓝），圆形度过滤，PnP测距，串口发送偏差和距离
# 整合：01的曝光/白平衡 + 02的多颜色blob查找 + 03的PnP测距 + 04的阈值参考

import time, gc
from media.sensor import *
from media.display import *
from media.media import *
import cv_lite
from machine import UART

# ==================== 图像尺寸配置 ====================
# 图像尺寸 [高, 宽]，16:9 比例，画面无变形
image_shape = [360, 640]      # 高360，宽640
IMG_W = 640
IMG_H = 360
CENTER_X = IMG_W // 2         # 320
CENTER_Y = IMG_H // 2         # 180

# ==================== 多颜色阈值（RGB格式）====================
# 每个阈值为 [R_min, R_max, G_min, G_max, B_min, B_max]
# 这些值为示例，实际使用前请用 04_Color_threshold_tool.py 获取准确阈值
COLOR_THRESHOLDS = {
    'red':   [120, 255,   0,  80,   0,  80],   # 红色球
    'green': [  0,  80, 120, 255,   0,  80],   # 绿色球
    'blue':  [  0,  80,   0,  80, 120, 255]    # 蓝色球
}

# 不同颜色在画面上的绘制颜色（BGR格式）
DRAW_COLORS = {
    'red':   (0, 0, 255),     # 红色外圈
    'green': (0, 255, 0),     # 绿色外圈
    'blue':  (255, 0, 0)      # 蓝色外圈
}

# ==================== 相机标定参数（需要用户用棋盘格标定后替换）====================
# 当前为 640x360 分辨率的示例参数（不准确），使用前请按照末尾的标定步骤重新标定！
# 标定后替换 camera_matrix 和 dist_coeffs，并删除代码中原有的 `/3` 修正
camera_matrix = [640.0, 0.0, 320.0, 0.0, 640.0, 180.0, 0.0, 0.0, 1.0]   # 临时值，需标定
dist_coeffs   = [0.0, 0.0, 0.0, 0.0, 0.0]                                 # 临时值，需标定

# 小球真实直径（单位：cm），根据实际球体填写
BALL_REAL_SIZE = 4.3   # 4.3cm 乒乓球

# ==================== 形状识别增强参数 ====================
# 圆形度阈值：4π·面积 / 周长²，越接近1越圆
CIRCULARITY_THRESHOLD = 0.7

# 长宽比过滤范围（保留接近正方形的 blob）
MIN_ASPECT_RATIO = 0.7
MAX_ASPECT_RATIO = 1.4

# ==================== 串口配置（与 STM32/Arduino 通信）====================
# 使用 UART3，TX=GPIO19, RX=GPIO20，波特率115200
uart = UART(UART.UART3, baudrate=115200, bits=8, parity=None, stop=1, tx=19, rx=20)

def send_ball_data(color, err_x, err_y, distance):
    """
    通过串口发送球体数据给下位机
    格式: 颜色代码,水平偏差,垂直偏差,距离\n
    颜色代码: R/G/B/N (N表示未找到)
    """
    data = "{},{},{},{}\n".format(color, int(err_x), int(err_y), int(distance))
    uart.write(data)
    # 同时在IDE串口终端打印，方便调试
    print("UART send: {}".format(data.strip()))

# ==================== 圆形度计算（基于矩形近似）====================
def compute_circularity_from_rect(w, h):
    """
    使用外接矩形的宽高近似计算圆形度。
    对于真正的圆形，面积 = π*r^2，周长 = 2πr，圆形度 = 1。
    用矩形面积 (w*h) 和矩形周长 2*(w+h) 代入公式，得到近似值。
    该近似对接近正方形的 blob 有效，性能好，适合实时处理。
    """
    if w == 0 or h == 0:
        return 0.0
    area = w * h
    perimeter = 2 * (w + h)
    if perimeter == 0:
        return 0.0
    circularity = 4 * 3.14159 * area / (perimeter * perimeter)
    # 限制在 [0,1] 区间
    return min(1.0, circularity)

# ==================== 初始化摄像头 ====================
# 使用 GC2093 传感器，ID=2，原生 1920x1080@60fps，ISP 下采样到 640x360
sensor = Sensor(id=2, width=1920, height=1080, fps=60)
sensor.reset()
sensor.set_framesize(width=IMG_W, height=IMG_H)
sensor.set_pixformat(Sensor.RGB888)   # RGB888 格式

# 初始化显示（虚拟模式，图像发送到 IDE 帧缓冲区）
Display.init(Display.VIRT, to_ide=True)
sensor.run()

# ==================== 曝光与白平衡参数 ====================
exposure_gain = 1.5          # 曝光增益，可调节以适应室内光线

# ==================== 主循环 ====================
clock = time.clock()

while True:
    clock.tick()
    
    # ----- 1. 采集一帧图像 -----
    img = sensor.snapshot()
    img_np = img.to_numpy_ref()
    
    # ----- 2. 曝光调整与白平衡（从 01_env_calibration.py 移植）-----
    # 调整曝光以增强画面亮度
    exposed_np = cv_lite.rgb888_adjust_exposure_fast(image_shape, img_np, exposure_gain)
    # 应用快速白平衡，消除环境光偏色
    balanced_np = cv_lite.rgb888_white_balance_gray_world_fast(image_shape, exposed_np)
    # 将处理后的 numpy 数组重新包装成 image 对象（用于显示和绘制）
    img_processed = image.Image(IMG_W, IMG_H, image.RGB888, alloc=image.ALLOC_REF, data=balanced_np)
    
    # ----- 3. 多颜色追踪 -----
    found_balls = []   # 存储本帧找到的所有球体信息
    
    for color_name, threshold in COLOR_THRESHOLDS.items():
        # 在当前帧中查找指定颜色的色块
        # 参数：图像shape, numpy图像, 阈值, 最小面积(100), 合并距离(1)
        blobs = cv_lite.rgb888_find_blobs(image_shape, balanced_np, threshold, 100, 1)
        
        # 遍历所有找到的色块（每个色块用4个整数表示: x, y, w, h）
        for i in range(len(blobs) // 4):
            x = blobs[4*i]
            y = blobs[4*i+1]
            w = blobs[4*i+2]
            h = blobs[4*i+3]
            
            # 跳过无效尺寸
            if w == 0 or h == 0:
                continue
            
            # 长宽比过滤：只保留接近正方形的块（圆形投影应为正方形）
            aspect = w / h
            if not (MIN_ASPECT_RATIO < aspect < MAX_ASPECT_RATIO):
                continue
            
            # ----- 4. 形状识别增强：圆形度判断 -----
            circularity = compute_circularity_from_rect(w, h)
            if circularity < CIRCULARITY_THRESHOLD:
                continue   # 形状不够圆，过滤掉
            
            # ----- 5. 计算球心坐标和偏差 -----
            cx = x + w // 2
            cy = y + h // 2
            err_x = cx - CENTER_X
            err_y = cy - CENTER_Y
            
            # ----- 6. PnP 测距（去掉了 /3 修正）-----
            # 注意：使用准确的相机内参后，测距结果才可靠。当前内参为占位符，测距会不准。
            roi = [x, y, w, h]
            # 调用 PnP 距离计算函数，不再除以 3
            distance = cv_lite.rgb888_pnp_distance(image_shape, balanced_np, roi,
                                                   camera_matrix, dist_coeffs, 5,
                                                   BALL_REAL_SIZE, BALL_REAL_SIZE)
            # 可选：对距离做限幅，避免异常值
            if distance < 0:
                distance = 0
            elif distance > 500:
                distance = 500
            
            # 存储找到的球体信息
            ball_info = {
                'color': color_name,
                'cx': cx, 'cy': cy,
                'w': w, 'h': h,
                'err_x': err_x,
                'err_y': err_y,
                'distance': distance
            }
            found_balls.append(ball_info)
            
            # ----- 7. 在画面上绘制标记 -----
            # 画圆（半径取宽高的一半）
            radius = min(w, h) // 2
            img_processed.draw_circle(cx, cy, radius, color=DRAW_COLORS[color_name], thickness=2)
            # 画十字标记球心
            img_processed.draw_cross(cx, cy, color=(255, 255, 255), size=8, thickness=1)
            # 在球上方显示颜色和距离
            label = "{} {:.0f}cm".format(color_name, distance)
            img_processed.draw_string_advanced(x, y - 20, 20, label, color=(255, 255, 255))
    
    # ----- 8. 串口发送数据（只发送面积最大的球，或按需发送全部）-----
    # 这里选择发送面积最大的球（即最可能的目标）。也可以循环发送所有球，但会增加串口负载。
    if len(found_balls) > 0:
        # 找出面积最大的球（面积 = w*h）
        best_ball = max(found_balls, key=lambda b: b['w'] * b['h'])
        color_code = best_ball['color'][0].upper()   # 'R', 'G', 'B'
        send_ball_data(color_code, best_ball['err_x'], best_ball['err_y'], int(best_ball['distance']))
    else:
        # 没有找到任何球，发送 'N' 表示 none
        send_ball_data('N', 0, 0, 0)
    
    # ----- 9. 画面显示信息（FPS、找到球的数量）-----
    fps = clock.fps()
    img_processed.draw_string_advanced(5, 5, 20, "Balls found: {}".format(len(found_balls)),
                                       color=(255, 255, 255))
    img_processed.draw_string_advanced(5, IMG_H - 25, 16, "FPS: {:.1f}".format(fps),
                                       color=(0, 255, 0))
    
    # 显示处理后的图像
    Display.show_image(img_processed)
    
    # 垃圾回收，防止内存泄漏
    gc.collect()

# ==================== 相机标定说明 ====================
"""
【为什么需要标定】
样例代码中的 camera_matrix 是 1920x1080 分辨率下的参数，不适用于 640x360。
直接使用会导致 PnP 测距严重错误。代码中已去掉 /3 修正，因此必须提供正确的内参。

【标定步骤】
1. 准备棋盘格图片（例如 9x6 个内角点，格子边长 25mm）。
2. 固定摄像头分辨率 640x360，拍摄 20~30 张不同角度、不同距离的棋盘格图片。
3. 在电脑上使用 OpenCV 运行以下脚本，获得 camera_matrix 和 dist_coeffs。
4. 将输出的矩阵填入本文件开头的 camera_matrix 和 dist_coeffs 中。

标定脚本（在电脑上运行）：
```python
import cv2
import numpy as np

CHECKERBOARD = (9, 6)
SQUARE_SIZE = 25  # mm

objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1], 3), np.float32)
objp[:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1,2) * SQUARE_SIZE

objpoints = []
imgpoints = []

for i in range(1, 21):  # 假设你有 20 张图片 calib_1.jpg ... calib_20.jpg
    img = cv2.imread(f'calib_{i}.jpg')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, None)
    if ret:
        objpoints.append(objp)
        imgpoints.append(corners)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
print("camera_matrix =", mtx.tolist())
print("dist_coeffs =", dist.tolist())
