# 导入所需模块
import time, gc
from media.sensor import *
from media.display import *
from media.media import *
import cv_lite

# 图像尺寸 [高, 宽]，16:9 比例，画面无变形
image_shape = [360, 640]
IMG_W = 640
IMG_H = 360

# 初始化摄像头：GC2093 原生 1920x1080 @ 60fps，ISP 下采样到 640x360
sensor = Sensor(id=2, width=1920, height=1080, fps=60)
sensor.reset()
sensor.set_framesize(width=IMG_W, height=IMG_H)
sensor.set_pixformat(Sensor.RGB888)

# 初始化显示
Display.init(Display.VIRT, to_ide=True)
sensor.run()

# 红色小球 RGB 阈值（根据实验二修改）
ball_threshold = [126, 199, 20, 74, 20, 85]

# 画面中心坐标
CENTER_X = IMG_W // 2   # 320
CENTER_Y = IMG_H // 2   # 180

# 主循环
while True:
    # 采集一帧图像
    img = sensor.snapshot()
    img_np = img.to_numpy_ref()

    # 高斯滤波去噪
    blurred = cv_lite.rgb888_gaussian_blur_fast(image_shape, img_np, 3)
    # 查找红色色块
    blobs = cv_lite.rgb888_find_blobs(image_shape, blurred, ball_threshold, 100, 1)

    # 初始化最大球信息
    best_x, best_y, best_w, best_h, best_area = 0, 0, 0, 0, 0

    # 遍历所有色块，找出面积最大的圆形区域
    for i in range(len(blobs) // 4):
        x, y, w, h = blobs[4*i : 4*i+4]
        if w == 0 or h == 0:
            continue
        # 长宽比过滤：只保留接近正方形（即圆形）的块
        if not (0.7 < w / h < 1.4):
            continue
        area = w * h
        if area > best_area:
            best_x, best_y, best_w, best_h, best_area = x, y, w, h, area

    # 如果找到了球
    if best_area > 0:
        # 球心坐标（像素）
        cx = best_x + best_w // 2
        cy = best_y + best_h // 2

        # 计算归一化偏移量（范围 -1 ~ 1）
        # 水平偏移：-1（最左）→ 0（中心）→ +1（最右）
        # 垂直偏移：-1（最上）→ 0（中心）→ +1（最下）
        offset_x = (cx - CENTER_X) / CENTER_X
        offset_y = (cy - CENTER_Y) / CENTER_Y

        # 可选：限制偏移量在 [-1, 1] 区间（防止边缘溢出）
        offset_x = max(-1.0, min(1.0, offset_x))
        offset_y = max(-1.0, min(1.0, offset_y))

        # 画圆标记球
        radius = min(best_w, best_h) // 2
        img.draw_circle(cx, cy, radius, color=(255, 0, 0), thickness=2)
        img.draw_cross(cx, cy, color=(0, 255, 0), size=8, thickness=2)

        # 在画面上显示偏移量和球的高度（像素）
        img.draw_string_advanced(5, 5, 20, "Ball detected", color=(0, 255, 0))
        img.draw_string_advanced(5, 30, 16, "Offset X: {:.2f}".format(offset_x), color=(255, 255, 255))
        img.draw_string_advanced(5, 50, 16, "Offset Y: {:.2f}".format(offset_y), color=(255, 255, 255))
        img.draw_string_advanced(5, 70, 16, "Height: {} px".format(best_h), color=(255, 255, 255))

        # 串口输出（下位机可解析）
        # 格式：offset_x,offset_y,ball_h
        print("{:.3f},{:.3f},{}".format(offset_x, offset_y, best_h))
    else:
        # 没有找到球
        img.draw_string_advanced(5, 5, 20, "No ball", color=(255, 0, 0))
        print("no ball")

    # 显示图像
    Display.show_image(img)
    gc.collect()