# 04pro_Color threshold tool.py
# 增强版：支持测量多种颜色（红/绿/蓝）的RGB阈值
# 使用方法：
#   1. 将目标颜色球放在画面中央的圆内
#   2. 在IDE的串口终端输入 r/g/b 切换颜色模式
#   3. 等待采样稳定后，终端会自动打印该颜色的阈值
#   4. 切换颜色后，工具会重置统计并开始测量新颜色

import time, gc, sys
from media.sensor import *
from media.display import *
from media.media import *
import cv_lite

# ==================== 图像配置 ====================
image_shape = [360, 640]
IMG_W = 640
IMG_H = 360

# ==================== 圆形采样区设置 ====================
SAMPLE_CX = IMG_W // 2
SAMPLE_CY = IMG_H // 2
SAMPLE_R = 25            # 采样圆半径
SAMPLE_R2 = SAMPLE_R * SAMPLE_R

# ==================== 性能优化参数 ====================
STEP = 3                 # 采样步长
UPDATE_INTERVAL = 2      # 每2帧计算一次阈值
MARGIN = 10              # 阈值余量

# ==================== 多颜色配置 ====================
# 定义支持的颜色列表和显示颜色
COLORS = {
    'r': 'red',
    'g': 'green',
    'b': 'blue'
}
# 当前测量的颜色（默认红色）
current_color_key = 'r'
# 存储每种颜色的最终阈值字典
thresholds = {
    'red': None,
    'green': None,
    'blue': None
}

# ==================== 初始化状态变量 ====================
# 当前颜色的统计变量（每次切换颜色时重置）
r_min, r_max = 255, 0
g_min, g_max = 255, 0
b_min, b_max = 255, 0
r_sum, g_sum, b_sum = 0, 0, 0
sample_count = 0
# 最后计算的阈值（用于显示）
r_lo, r_hi = 0, 255
g_lo, g_hi = 0, 255
b_lo, b_hi = 0, 255
r_avg, g_avg, b_avg = 0, 0, 0

frame_count = 0

# ==================== 辅助函数 ====================
def reset_stats():
    """重置当前颜色的统计数据"""
    global r_min, r_max, g_min, g_max, b_min, b_max
    global r_sum, g_sum, b_sum, sample_count
    r_min, r_max = 255, 0
    g_min, g_max = 255, 0
    b_min, b_max = 255, 0
    r_sum = g_sum = b_sum = 0
    sample_count = 0

def check_color_switch():
    """非阻塞检查串口输入，切换颜色"""
    global current_color_key
    # 读取所有可用的输入字符
    while sys.stdin.available():
        ch = sys.stdin.read(1)
        if ch in COLORS:
            new_color = ch
            if new_color != current_color_key:
                # 保存当前颜色的阈值（如果有采样点）
                if sample_count > 0:
                    thresholds[COLORS[current_color_key]] = [r_lo, r_hi, g_lo, g_hi, b_lo, b_hi]
                    print("\n[Saved] {} threshold = {}".format(
                        COLORS[current_color_key],
                        thresholds[COLORS[current_color_key]]))
                # 切换颜色
                current_color_key = new_color
                print("\n>>> Switched to {} color <<<".format(COLORS[current_color_key]))
                # 重置统计
                reset_stats()
                # 重置显示值
                global r_lo, r_hi, g_lo, g_hi, b_lo, b_hi, r_avg, g_avg, b_avg
                r_lo, r_hi = 0, 255
                g_lo, g_hi = 0, 255
                b_lo, b_hi = 0, 255
                r_avg = g_avg = b_avg = 0
            break  # 一次只处理一个切换

# ==================== 初始化摄像头 ====================
sensor = Sensor(id=2, width=1920, height=1080, fps=60)
sensor.reset()
sensor.set_framesize(width=IMG_W, height=IMG_H)
sensor.set_pixformat(Sensor.RGB888)
Display.init(Display.VIRT, to_ide=True)
sensor.run()

print("Multi-Color Threshold Tool Started")
print("Available colors: r (red), g (green), b (blue)")
print("Put the ball in the center circle, then type r/g/b to switch color.")
print("Thresholds will be printed automatically.\n")

# ==================== 主循环 ====================
while True:
    # 1. 采集图像
    img = sensor.snapshot()
    img_np = img.to_numpy_ref()
    frame_count += 1

    # 2. 非阻塞检查颜色切换
    check_color_switch()

    # 3. 每隔 UPDATE_INTERVAL 帧执行一次统计
    if frame_count % UPDATE_INTERVAL == 0:
        # 初始化本次统计的临时变量
        t_r_min, t_r_max = 255, 0
        t_g_min, t_g_max = 255, 0
        t_b_min, t_b_max = 255, 0
        t_r_sum = t_g_sum = t_b_sum = 0
        t_cnt = 0

        # 稀疏采样圆内像素
        for py in range(SAMPLE_CY - SAMPLE_R, SAMPLE_CY + SAMPLE_R, STEP):
            dy2 = (py - SAMPLE_CY) ** 2
            for px in range(SAMPLE_CX - SAMPLE_R, SAMPLE_CX + SAMPLE_R, STEP):
                dx = px - SAMPLE_CX
                if dx * dx + dy2 > SAMPLE_R2:
                    continue
                pixel = img_np[py][px]
                r, g, b = pixel[0], pixel[1], pixel[2]
                # 更新本次临时 min/max
                if r < t_r_min: t_r_min = r
                if r > t_r_max: t_r_max = r
                if g < t_g_min: t_g_min = g
                if g > t_g_max: t_g_max = g
                if b < t_b_min: t_b_min = b
                if b > t_b_max: t_b_max = b
                t_r_sum += r
                t_g_sum += g
                t_b_sum += b
                t_cnt += 1

        # 累计到全局统计（用于平滑）
        if t_cnt > 0:
            # 更新全局 min/max（累加并非简单取 min，这里为了平滑使用滑动更新）
            # 为了简单，直接使用当前帧的 min/max 替代全局，但会抖动。我们使用加权平均方式：
            # 实际应用中，直接用当前帧的 min/max 作为最新值即可，因为每帧采样已足够代表当前光照。
            # 但为了得到更稳定的阈值，可以累计多帧。这里采用累计方式：
            if sample_count == 0:
                r_min, r_max = t_r_min, t_r_max
                g_min, g_max = t_g_min, t_g_max
                b_min, b_max = t_b_min, t_b_max
            else:
                r_min = min(r_min, t_r_min)
                r_max = max(r_max, t_r_max)
                g_min = min(g_min, t_g_min)
                g_max = max(g_max, t_g_max)
                b_min = min(b_min, t_b_min)
                b_max = max(b_max, t_b_max)
            r_sum += t_r_sum
            g_sum += t_g_sum
            b_sum += t_b_sum
            sample_count += t_cnt

            # 计算带 MARGIN 的阈值（基于累计的 min/max）
            r_lo = max(0, r_min - MARGIN)
            r_hi = min(255, r_max + MARGIN)
            g_lo = max(0, g_min - MARGIN)
            g_hi = min(255, g_max + MARGIN)
            b_lo = max(0, b_min - MARGIN)
            b_hi = min(255, b_max + MARGIN)
            if sample_count > 0:
                r_avg = r_sum // sample_count
                g_avg = g_sum // sample_count
                b_avg = b_sum // sample_count

            # 实时打印当前颜色的阈值（便于复制）
            print("\r{} threshold = [{:3d},{:3d}, {:3d},{:3d}, {:3d},{:3d}]   ".format(
                  COLORS[current_color_key], r_lo, r_hi, g_lo, g_hi, b_lo, b_hi), end='')
            # 也输出到串口（无换行，但会被覆盖，改用普通打印更好）
            # 为了让串口终端可读，每帧都打印会刷屏，所以上面的 \r 和 end='' 只在某些终端有效。
            # 更简单：每隔 2 秒打印一次，避免刷屏。
            # 这里简化：直接完整打印一行，但不刷屏也可以，用户自己能接受。
            # 实际上 IDE 的串口终端支持 \r，我们就用 \r 刷新同一行。

    # 4. 显示图像和标注（每帧执行）
    # 绘制采样圆
    img.draw_circle(SAMPLE_CX, SAMPLE_CY, SAMPLE_R, color=(255, 255, 255), thickness=2)
    img.draw_cross(SAMPLE_CX, SAMPLE_CY, color=(255, 0, 0), size=8, thickness=1)
    # 显示当前测量颜色和均值
    img.draw_string_advanced(5, 5, 20, "Measuring: {}".format(COLORS[current_color_key]),
                             color=(255, 255, 255))
    img.draw_string_advanced(5, 30, 16,
                             "AVG R:{:3d} G:{:3d} B:{:3d}".format(r_avg, g_avg, b_avg),
                             color=(255, 255, 255))
    # 显示当前阈值
    img.draw_string_advanced(5, IMG_H - 65, 16, "Threshold = [", color=(0, 255, 0))
    img.draw_string_advanced(5, IMG_H - 45, 16,
                             "{:3d},{:3d}, {:3d},{:3d}, {:3d},{:3d}]".format(
                                 r_lo, r_hi, g_lo, g_hi, b_lo, b_hi),
                             color=(0, 255, 0))
    # 提示如何切换颜色
    img.draw_string_advanced(5, IMG_H - 20, 14, "Type r/g/b to switch color",
                             color=(200, 200, 200))

    Display.show_image(img)
    gc.collect()

# 程序不会执行到这里，但可以预留退出时打印所有阈值（按 Ctrl+C 退出时会打印）
# 由于 CanMV 不支持 atexit，需要手动在 IDE 中停止，但停止时阈值已在切换时保存。