import mss
import mss.tools
import cv2
import numpy as np
import time
import pygetwindow as gw
import keyboard

# 用一个变量来存储最后一张检测到变化的帧
single_saved_frame = None

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
                        'top': int(window.top+window.height*0.05),
                        'left': int(window.left+window.width*0.37),
                        'width': int(window.width*0.26),
                        'height': int(window.height*0.1)
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
        0: 'd',
        1: 'f',
        2: 'j',
        3: 'k'
    }

    last_frame = None
    single_saved_frame = None
    
    print("程序已启动，正在实时监控屏幕变化。")
    print("检测到显著变化时，将更新内存中的图片。")
    print("按 'q' 键退出程序。")

    timer = [[0] for i in range(4)]
    in_screen = [False]*4
    lasttime_in_screen = [False]*4
    latetime = 1000
    fps_breath = 8

    key_down = [False]*4

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
        if last_frame is not None:
            gray_last = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
            gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            frame_diff = cv2.absdiff(gray_last, gray_current)
            _, thresh = cv2.threshold(frame_diff, 150, 255, cv2.THRESH_BINARY)
            
            kernel = np.ones((5, 5), np.uint8)
            thresh = cv2.dilate(thresh, kernel, iterations=2)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                if cv2.contourArea(contour) > 500:
                    (x, y, w, h) = cv2.boundingRect(contour)
                    #print(x, y, w, h)
                    #print(window_width)
                    if(x+w*0.5>0 and x+w*0.5<window_width*0.25):
                        in_screen[0] = True
                        if not lasttime_in_screen[0]:
                            #d键
                            timer[0].append(latetime)
                        lasttime_in_screen[0] = True
                    elif(x+w*0.5<window_width*0.5):
                        in_screen[1] = True
                        if not lasttime_in_screen[1]:
                            #f键
                            timer[1].append(latetime)
                        lasttime_in_screen[1] = True
                    elif(x+w*0.5<window_width*0.75):
                        in_screen[2] = True
                        if not lasttime_in_screen[2]:
                            #j键
                            timer[2].append(latetime)
                        lasttime_in_screen[2] = True
                    elif(x+w*0.5<window_width):
                        in_screen[3] = True
                        if not lasttime_in_screen[3]:
                            #k键
                            timer[3].append(latetime)
                        lasttime_in_screen[3] = True
                    cv2.rectangle(current_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    has_significant_diff = True

        # 如果有显著变化，就更新内存中的单张图片
        if has_significant_diff:
            single_saved_frame = current_frame.copy()
            print("检测到显著变化，内存中的图片已更新。")

        #缩放显示的图片
        show_current_frame = cv2.resize(current_frame, (640, 140))

        cv2.imshow("camera", show_current_frame)

        last_frame = current_frame.copy()

        for i in range(timer.__len__()):
            if not in_screen[i]:
                lasttime_in_screen[i] = False
            in_screen[i] = False
            for j in range(timer[i].__len__()):
                timer[i][j] -= fps_breath
            if(timer[i].__len__()>0 and timer[i][0]>1 and timer[i][0]<=32):
                if(key_down[i]):
                    key_down[i] = False
                    #松开按键
                    keyboard.release(keys[i])
            elif(timer[i].__len__()>0 and timer[i][0]>32):
                if(not key_down[i]):
                    key_down[i] = True
                    #按住按键
                    keyboard.press(keys[i])
            elif(timer[i].__len__()>0 and timer[i][0]<1):
                if(not key_down[i]):
                    key_down[i] = True
                    #按住按键
                    keyboard.press(keys[i])
            if(timer[i].__len__()>0 and timer[i][0]<0):
                timer[i].pop(0)
        # 按 'q' 键退出
        if cv2.waitKey(fps_breath) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    print("\n程序已退出。")
    

if __name__ == "__main__":
    main()
