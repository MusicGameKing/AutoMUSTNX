import mss
import mss.tools
import cv2
import numpy as np
import time
import pygetwindow as gw
import keyboard

# 用一个变量来存储最后一张检测到变化的帧
single_saved_frame = None

key_list = []
def add_key(key,press_key = True,late = 0):
    key_list.append((key,press_key,late))
def refresh_time(time):
    i = 0
    while i < len(key_list):
        key,press_key,late = key_list[i]
        late = late - time
        if late > 0:
            key_list[i] = (key,press_key,late)
            i += 1
        else:
            key_list.pop(i)
            if press_key:
                keyboard.press(key)
                print(f"按下按键: {key}")
            else:
                keyboard.release(key)
                print(f"松开按键: {key}")


def is_musynx_open(window_title="MUSYNX"):
    try:
        # 获取所有窗口
        windows = gw.getWindowsWithTitle(window_title)
        
        # 如果有匹配的窗口
        if windows:
            for window in windows:
                # 检查窗口是否可见（不是最小化）
                if window.visible:
                    return True
        return False
    except Exception as e:
        print(f"检测窗口时出错: {e}")
        return False
    
def get_musynx_window_region(window_title="MUSYNX"):
    """
    获取MUSYNX窗口的位置和大小
    
    参数:
    window_title (str): 窗口标题或部分标题，默认为"MUSYNX"
    
    返回:
    dict: 包含窗口位置和大小的字典，格式为{'top': y, 'left': x, 'width': w, 'height': h}
          如果找不到窗口，返回None
    """
    try:
        # 获取所有窗口
        windows = gw.getWindowsWithTitle(window_title)
        
        # 如果有匹配的窗口
        if windows:
            for window in windows:
                # 检查窗口是否可见（不是最小化）
                if window.visible:
                    # 返回窗口位置和大小
                    return {
                        'top': int(window.top+window.height*0.45),
                        'left': int(window.left+window.width*0.37),
                        'width': int(window.width*0.26),
                        'height': int(window.height*0.07)
                    }
        return None
    except Exception as e:
        print(f"获取窗口区域时出错: {e}")
        return None

def main():
    if not is_musynx_open():
        print("MUSYNX窗口未打开，程序将退出。")
        return

    sct = mss.mss()
    # monitor = sct.monitors[1]

    # 获取MUSYNX窗口区域
    window_region = None
    while window_region is None:
        print("正在查找MUSYNX窗口...")
        window_region = get_musynx_window_region()
        if window_region is None:
            print("未找到MUSYNX窗口，5秒后重试...")
            time.sleep(5)
        else:
            print(f"找到MUSYNX窗口: {window_region}")

    window_width = window_region['width']

    keys = {
        0: 's',
        1: 'd',
        2: 'f',
        3: 'j',
        4: 'k',
        5: 'l'
    }

    last_frame = None
    single_saved_frame = None
    
    print("程序已启动，正在实时监控屏幕变化。")
    print("检测到显著变化时，将更新内存中的图片。")
    print("按 'q' 键退出程序。")

    cut = 6
    key_down_edge = 0.05
    threshold_edge = 200

    late_press = 72

    fps_breath = 6

    in_screen = [False]*cut
    key_down = [False]*cut

    while True:
        #time.sleep(1)
        current_region = get_musynx_window_region()
        if current_region is None:
            print("MUSYNX窗口已关闭，程序退出。")
            break
        screenshot = sct.grab(window_region)
        current_frame = np.array(screenshot, dtype=np.uint8)
        current_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGRA2BGR)
        
        has_significant_diff = False
        #删除图片红色通道
        #current_frame = current_frame[:, :, :2]
        # 转为灰度图
        gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        #show_current_frame = gray_current
        #二值化
        _, binary_current = cv2.threshold(gray_current, threshold_edge, 255, cv2.THRESH_BINARY) 
        show_current_frame = binary_current
        #纵向拆分图片为cut数量
        binary_current = np.array_split(binary_current, cut, axis=1)
        #计算白色像素的比例
        white_ratios = []
        for i in range(cut):
            white_ratio = np.sum(binary_current[i] == 255) / (binary_current[i].size + 1e-6)
            white_ratios.append(white_ratio)
        print(f"当前白色像素比例: {white_ratios}")

        #大于阈值，按下对应按键
        for i in range(cut):
            if white_ratios[i] > key_down_edge:
                if not key_down[i]:
                    key_down[i] = True
                    # 按住按键
                    #keyboard.press(keys[i])
                    add_key(keys[i],press_key=True,late=late_press)
            else:
                if key_down[i]:
                    key_down[i] = False
                    # 松开按键
                    #keyboard.release(keys[i])
                    add_key(keys[i],press_key=False,late=late_press)

        single_saved_frame = current_frame.copy()
        #缩放显示的图片binary_current
        show_current_frame = cv2.resize(show_current_frame, (640, 140))
        cv2.imshow("camera", show_current_frame)

        refresh_time(fps_breath)
        # 按 'q' 键退出
        if cv2.waitKey(fps_breath) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    print("\n程序已退出。")
    

if __name__ == "__main__":
    main()
