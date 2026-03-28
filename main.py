"""
================================================================================
程序入口 - 应用程序的主程序文件
================================================================================

【文件作用】
    本文件是整个应用程序的入口点，负责：
    - 初始化所有组件（窗口、角色、输入、游戏循环）
    - 配置 Qt 事件过滤器，捕获所有键盘事件
    - 设置主定时器，驱动游戏循环
    - 启动 Qt 事件循环，使程序运行

【程序运行流程】

    ┌─────────────────────────────────────────────────────────────┐
    │                        程序启动                              │
    │                           │                                 │
    │                           ▼                                 │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │ 1. 创建组件                                         │   │
    │  │    - MainWindow（透明窗口）                          │   │
    │  │    - PixelPet（像素小人）                            │   │
    │  │    - InputHandler（输入处理器）                      │   │
    │  │    - GameLoop（游戏循环控制器）                       │   │
    │  │    - TrayManager（系统托盘）                          │   │
    │  │    - DragHandler（鼠标拖动）                         │   │
    │  │    - FollowHandler（鼠标跟随）                        │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                           │                                 │
    │                           ▼                                 │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │ 2. 启动程序                                         │   │
    │  │    - window.show() 显示窗口                         │   │
    │  │    - update_timer.start() 启动定时器                 │   │
    │  │    - pet.start_animation() 启动动画                 │   │
    │  │    - app.exec() 进入事件循环                       │   │
    │  └─────────────────────────────────────────────────────┘   │
    │                           │                                 │
    │                           ▼                                 │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │ 3. 主循环（定时器触发，每帧执行）                     │   │
    │  │    - on_timer() 回调函数                             │   │
    │  │      ├─ 读取键盘输入                                 │   │
    │  │      ├─ 鼠标跟随处理                                 │   │
    │  │      ├─ 更新角色位置                                 │   │
    │  │      ├─ 穿墙检测                                     │   │
    │  │      └─ 更新显示                                     │   │
    │  └─────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────┘

【依赖关系】
    导入：
        - sys, os：标准库
        - PyQt6.QtCore：Qt 核心模块
        - views.main_window：视图层
        - models.pixel_pet：模型层
        - controllers.*：控制器层
        - features.*：功能模块（托盘、拖动、跟随）
        - config.settings：配置模块

================================================================================
"""

# ================================================================================
# 导入标准库模块
# ================================================================================

import sys
import os

# 设置模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ================================================================================
# 导入 PyQt6 组件
# ================================================================================

from PyQt6.QtCore import QTimer, QObject
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QKeyEvent


# ================================================================================
# 导入项目模块
# ================================================================================

from views.main_window import MainWindow
from models.pixel_pet import PixelPet
from controllers.input_handler import InputHandler
from controllers.game_loop import GameLoop
from features.tray import TrayManager
from features.mouse_drag import DragHandler
from features.mouse_follow import FollowHandler
from config.settings import MOVE_INTERVAL


# ================================================================================
# 主函数 - 程序入口点
# ================================================================================

def main():
    """
    应用程序的主函数
    """

    # ==========================================================================
    # 第一步：初始化窗口
    # ==========================================================================

    window = MainWindow()
    screen_width, screen_height = window.get_screen_size()


    # ==========================================================================
    # 第二步：创建像素小人
    # ==========================================================================

    pet = PixelPet(0, 0)

    # 计算居中位置
    start_x = (screen_width - pet.width) // 2
    start_y = (screen_height - pet.height) // 2
    pet.set_position(start_x, start_y)


    # ==========================================================================
    # 第三步：创建输入处理器和游戏循环
    # ==========================================================================

    input_handler = InputHandler()
    game_loop = GameLoop(window, pet, input_handler)


    # ==========================================================================
    # 第四步：初始化功能模块
    # ==========================================================================

    # 鼠标跟随
    follow_handler = FollowHandler(window, pet, input_handler)

    # 系统托盘
    tray_manager = TrayManager(window.window, window.quit)

    # 鼠标拖动
    drag_handler = DragHandler(window.window, window.pet_label, pet, follow_handler, tray_manager)


    # ==========================================================================
    # 第五步：设置初始显示
    # ==========================================================================

    window.set_pet_pixmap(pet.current_sprite)
    window.set_pet_position(pet.x, pet.y)


    # ==========================================================================
    # 第六步：创建并配置主定时器
    # ==========================================================================

    update_timer = QTimer()
    update_timer.setInterval(MOVE_INTERVAL)


    def on_timer():
        """
        定时器回调函数 - 每帧执行一次
        """

        # 检查 ESC 是否按下，退出鼠标跟随模式
        if follow_handler.check_escape():
            if follow_handler.is_follow_enabled():
                follow_handler.disable_follow()
                tray_manager.follow_mouse_action.setChecked(False)

        # 获取移动方向
        dx, dy = 0, 0

        if follow_handler.is_follow_enabled():
            # 鼠标跟随模式
            dx, dy = follow_handler.update()

            # 计算总移动距离，距离太小视为停止
            move_distance = (dx ** 2 + dy ** 2) ** 0.5
            if move_distance < 1.0:
                dx, dy = 0, 0
        else:
            # 读取键盘输入
            dx, dy = input_handler.handle_input()

        # 更新角色方向和位置
        pet.set_direction(dx, dy)
        pet.move(dx, dy)

        # 处理穿墙逻辑
        if dx != 0 or dy != 0:
            game_loop.wrap_position()

        # 更新显示
        window.set_pet_pixmap(pet.current_sprite)
        window.set_pet_position(pet.x, pet.y)

    update_timer.timeout.connect(on_timer)


    # ==========================================================================
    # 第七步：配置键盘事件过滤器
    # ==========================================================================

    class EventFilter(QObject):

        def __init__(self, handler):
            super().__init__()
            self.handler = handler

        def eventFilter(self, obj, event):
            if event.type() == QKeyEvent.Type.KeyPress:
                self.handler.keyPressEvent(event)
                return True
            elif event.type() == QKeyEvent.Type.KeyRelease:
                self.handler.keyReleaseEvent(event)
                return True
            return False

    event_filter = EventFilter(input_handler)
    window.app.installEventFilter(event_filter)


    # ==========================================================================
    # 第八步：启动程序
    # ==========================================================================

    window.show()
    update_timer.start()
    pet.start_animation()

    # 连接托盘菜单的跟随选项到 follow_handler
    tray_manager.follow_mouse_action.triggered.connect(follow_handler.toggle_follow)

    sys.exit(window.app.exec())


# ================================================================================
# 程序入口点
# =============================================================================

if __name__ == "__main__":
    main()