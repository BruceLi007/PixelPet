"""
================================================================================
主窗口视图 - 创建和管理透明窗口，负责界面显示
================================================================================

【文件作用】
    本文件是项目的视图层（View），负责所有与界面显示相关的工作：
    - 创建全屏透明窗口（覆盖桌面，让用户看到真正的桌面背景）
    - 管理宠物的显示（使用 QLabel 作为容器显示图片）
    - 获取屏幕尺寸（用于计算居中位置和穿墙边界）
    - 提供更新显示的接口（供主循环调用）

【使用技术】
    - PyQt6.QtWidgets.QWidget：Qt 的基础窗口控件类
    - PyQt6.QtWidgets.QApplication：Qt 应用程序类，每个 Qt 应用只需一个
    - PyQt6.QtWidgets.QLabel：Qt 的标签控件，用于显示图片（pixmap）
    - PyQt6.QtCore.QTimer：Qt 定时器（备用，用于未来扩展）
    - PyQt6.QtCore.Qt：Qt 的常量定义，如窗口标志、焦点策略等
    - PyQt6.QtGui.QPixmap：Qt 图片类（由 PixelPet 传入）
    - screeninfo 库：跨平台的屏幕信息获取库

【窗口透明实现原理】
    使用 Qt 的 WA_TranslucentBackground 属性，让窗口背景完全透明：
    1. 设置 FramelessWindowHint：无边框、无标题栏
    2. 设置 WindowStaysOnTopHint：始终在顶层，不被其他窗口遮挡
    3. 设置 WA_TranslucentBackground：窗口背景透明
    4. 用 QLabel 显示 PNG 图片，PNG 自带 Alpha 通道透明
    5. 窗口本身无任何不透明元素，透过去就能看到桌面

【依赖关系】
    被导入：main.py
    导入：config.settings（获取屏幕尺寸配置）

================================================================================
"""

# ================================================================================
# 导入标准库模块
# ================================================================================

import os
# os 模块：用于处理文件路径（当前版本未使用，保留用于扩展）


# ================================================================================
# 导入 PyQt6 组件
# ================================================================================

from PyQt6.QtWidgets import QApplication, QLabel, QWidget
# QApplication：Qt 应用程序类
#   - 每个 Qt GUI 程序必须创建一个 QApplication 实例
#   - 负责应用程序级别的设置和事件循环管理
#   - 必须先创建，再创建其他控件

from PyQt6.QtCore import Qt, QTimer
# Qt：包含 Qt 框架的各种常量定义
#   - WindowType.FramelessWindowHint：无边框窗口
#   - WindowType.WindowStaysOnTopHint：窗口始终在最顶层
#   - WindowType.Tool：工具窗口（不显示在任务栏）
#   - WidgetAttribute.WA_TranslucentBackground：窗口背景透明
#   - FocusPolicy.StrongFocus：强焦点策略（可接收键盘事件）

from PyQt6.QtGui import QPixmap
# QPixmap：Qt 图片类，用于在 QLabel 中显示
#   - 支持多种图片格式
#   - 针对屏幕显示优化，加载快速
#   - 支持透明通道（PNG 的 Alpha）

from PyQt6.QtCore import pyqtSignal, QObject
# pyqtSignal：Qt 信号机制，用于组件间通信（当前版本未使用）
# QObject：Qt 所有对象的基类（当前版本未直接使用）

import screeninfo
# screeninfo：跨平台的屏幕信息获取库
#   - get_monitors()：获取所有显示器信息
#   - 返回 Monitor 对象，包含 width、height 等属性


# ================================================================================
# 导入项目配置模块
# ================================================================================

from config.settings import FPS, MOVE_INTERVAL
# 从配置模块导入：
#   - FPS：帧率（当前版本未直接使用）
#   - MOVE_INTERVAL：移动间隔（毫秒）


# ================================================================================
# 信号类（备用，当前版本未使用）
# ================================================================================

class InputSignal(QObject):
    """
    输入信号发射器类

    【设计目的】
        这是 Qt 信号槽机制的一个示例实现
        保留用于未来扩展功能，例如：
        - 发送移动信号给其他组件
        - 发送退出信号通知程序结束
        - 实现更复杂的组件间通信

    信号定义：
        moved：移动信号，携带位置信息
        exited：退出信号
    """

    # pyqtSignal：定义一个信号
    # 格式：信号名 = pyqtSignal(参数类型)
    # 当信号被发射时，会调用所有连接的槽函数

    moved = pyqtSignal(float, float)
    # 移动信号，携带 (dx, dy) 两个浮点数参数
    # 使用方式：self.moved.emit(5.0, 0.0)

    exited = pyqtSignal()
    # 退出信号，无参数
    # 使用方式：self.exited.emit()


# ================================================================================
# 主窗口类
# ================================================================================

class MainWindow:
    """
    主窗口视图类

    负责创建和管理透明窗口，是程序界面的核心：

    主要职责：
        1. 创建 Qt 应用实例（每个程序只需一个）
        2. 创建全屏透明窗口，覆盖整个桌面
        3. 创建 QLabel 容器用于显示宠物图片
        4. 提供更新显示的接口（set_pet_pixmap, set_pet_position）
        5. 获取屏幕尺寸用于居中和穿墙计算

    使用方式：
        window = MainWindow()      # 创建窗口
        window.show()              # 显示窗口
        window.set_pet_pixmap()   # 更新宠物图片
        window.set_pet_position()  # 更新宠物位置
        window.exec()              # 进入事件循环
    """

    # ==========================================================================
    # 初始化 - 创建应用和窗口
    # ==========================================================================

    def __init__(self):
        """
        构造函数 - 初始化 Qt 应用和窗口

        初始化流程：
            1. 创建 QApplication 实例（必须先创建）
            2. 获取屏幕尺寸
            3. 创建 QWidget 作为主窗口
            4. 设置窗口标志（无边框、顶层等）
            5. 设置窗口透明属性
            6. 设置焦点策略
            7. 创建 QLabel 用于显示宠物
        """

        # --------------------------------------------------------------------------
        # 创建 Qt 应用程序实例
        # --------------------------------------------------------------------------
        # QApplication：每个 Qt GUI 程序只需要一个实例
        # 必须在创建任何窗口控件之前创建
        # 参数 argv：命令行参数列表（用于 Qt 的标准参数处理）
        self.app = QApplication([])
        # QApplication([]) 创建应用程序实例
        # [] 是空的命令行参数列表


        # --------------------------------------------------------------------------
        # 获取屏幕尺寸（带容错机制）
        # --------------------------------------------------------------------------
        # 优先使用 Qt 原生的方法获取屏幕尺寸，更加可靠
        # screeninfo 作为备用（某些系统上可能不准确）

        # 先用默认值
        self.screen_width = 1920
        self.screen_height = 1080

        # 方法1：使用 Qt 的 primaryScreen() 获取主屏幕
        try:
            primary_screen = self.app.primaryScreen()
            if primary_screen:
                screen_geometry = primary_screen.geometry()
                self.screen_width = screen_geometry.width()
                self.screen_height = screen_geometry.height()
        except Exception as e:
            # 如果 Qt 方法失败，使用默认值
            print(f"Qt screen detection failed: {e}")

        # 方法2：如果 screeninfo 可用且返回值合理，验证一下
        try:
            screen = screeninfo.get_monitors()[0]
            # 验证 screeninfo 的值是否合理（与 Qt 的值偏差超过 100 像素）
            if abs(screen.width - self.screen_width) > 100 or abs(screen.height - self.screen_height) > 100:
                print(f"Warning: screeninfo returned {screen.width}x{screen.height}, "
                      f"but Qt returned {self.screen_width}x{self.screen_height}. Using Qt value.")
            else:
                # 如果值接近，使用 screeninfo 的值（它可能更准确）
                self.screen_width = screen.width
                self.screen_height = screen.height
        except Exception:
            pass  # 继续使用 Qt 的值或默认值
            pass  # 继续使用 Qt 的值


        # --------------------------------------------------------------------------
        # 创建主窗口
        # --------------------------------------------------------------------------
        # QWidget：Qt 中所有用户界面对象的基类
        # 创建一个 QWidget 实例作为我们的透明窗口
        self.window = QWidget()
        # self.window 是主窗口对象，所有后续设置都针对它

        # 设置窗口标题（仅影响任务栏显示，因为无边框所以窗口上不显示）
        self.window.setWindowTitle("PixelPet")


        # --------------------------------------------------------------------------
        # 设置窗口标志（Window Flags）
        # --------------------------------------------------------------------------
        # 窗口标志定义窗口的类型和行为
        # 使用 | 操作符组合多个标志

        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            # FramelessWindowHint：无边框窗口
            #   - 移除标准的窗口标题栏和边框
            #   - 用户无法通过标题栏拖动窗口
            #   - 这是实现透明窗口的基础

            Qt.WindowType.WindowStaysOnTopHint |
            # WindowStaysOnTopHint：窗口始终保持在最顶层
            #   - 不会被其他窗口遮挡
            #   - 即使焦点在其他窗口上，透明宠物仍然可见
            #   - 类似于 QQ 桌面的宠物效果

            Qt.WindowType.Tool
            # Tool：工具窗口类型
            #   - 不显示在任务栏
            #   - 不会出现在 Alt+Tab 切换列表中
            #   - 用户不会觉得这是一个"应用程序"
        )


        # --------------------------------------------------------------------------
        # 设置窗口透明属性
        # --------------------------------------------------------------------------
        # WA_TranslucentBackground：使窗口背景透明
        #   - 窗口本身的背景变为完全透明
        #   - 透过窗口可以看到下方的桌面或其他窗口
        #   - 需要配合无边框窗口才能正常工作
        self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


        # --------------------------------------------------------------------------
        # 设置窗口几何尺寸（全屏）
        # --------------------------------------------------------------------------
        # setGeometry(x, y, width, height)：
        #   - x, y：窗口左上角位置
        #   - width, height：窗口宽高
        # 设置为 (0, 0, 屏幕宽, 屏幕高) 覆盖整个屏幕
        self.window.setGeometry(0, 0, self.screen_width, self.screen_height)


        # --------------------------------------------------------------------------
        # 设置焦点策略
        # --------------------------------------------------------------------------
        # 焦点策略决定窗口如何接收键盘输入事件
        # StrongFocus：窗口在显示时会获得键盘焦点
        #   - 点击窗口后，窗口会接收所有键盘事件
        #   - 这对于键盘控制宠物移动至关重要
        self.window.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


        # --------------------------------------------------------------------------
        # 创建宠物显示标签（QLabel）
        # --------------------------------------------------------------------------
        # QLabel：用于显示文本或图片的标签控件
        # 我们用它来承载宠物的像素精灵图
        self.pet_label = QLabel(self.window)
        # 创建 QLabel，并指定 self.window 为其父控件
        # 父控件负责子控件的销毁管理

        # 设置标签内容的对齐方式
        # AlignCenter：内容居中对齐
        # 这里主要是让图片在标签内居中（虽然标签和窗口一样大）
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --------------------------------------------------------------------------
        # 初始化其他属性
        # --------------------------------------------------------------------------
        self.running = False
        # running：标记窗口是否处于运行状态
        # 用于控制程序的主循环


    # ==========================================================================
    # 公开方法 - 尺寸和位置
    # ==========================================================================

    def get_screen_size(self) -> tuple:
        """
        获取屏幕尺寸

        返回：
            tuple：(screen_width, screen_height)
                   screen_width：屏幕宽度（像素）
                   screen_height：屏幕高度（像素）

        使用方式：
            width, height = window.get_screen_size()

        用途：
            - 计算宠物的初始居中位置
            - 计算穿墙边界的阈值
        """

        return (self.screen_width, self.screen_height)
        # 返回屏幕尺寸元组


    # ==========================================================================
    # 公开方法 - 宠物显示更新
    # ==========================================================================

    def set_pet_pixmap(self, pixmap: QPixmap):
        """
        设置宠物显示的图片

        参数：
            pixmap (QPixmap)：要显示的图片对象

        实现流程：
            1. 调用 QLabel.setPixmap() 设置显示的图片
            2. 调用 resize() 根据图片尺寸调整标签大小
            3. QLabel 会自动显示图片内容

        使用方式：
            window.set_pet_pixmap(pet.current_sprite)

        注意：
            每次宠物动画帧切换时都需要调用此方法
        """

        # setPixmap()：设置 QLabel 显示的图片
        # 替换之前设置的任何图片
        self.pet_label.setPixmap(pixmap)

        # resize()：调整 QLabel 的大小以适应图片
        # 这样宠物图片有多大，QLabel 就有多大
        self.pet_label.resize(pixmap.width(), pixmap.height())


    def set_pet_position(self, x: int, y: int):
        """
        设置宠物的屏幕位置

        参数：
            x (int)：x 坐标（水平位置，像素）
            y (int)：y 坐标（垂直位置，像素）

        实现：
            调用 QLabel.move() 移动标签到指定位置
            注意：这是移动 QLabel（显示宠物的容器）
                  窗口本身是全屏固定的

        使用方式：
            window.set_pet_position(100, 200)  # 移动到 (100, 200)
        """

        # move()：移动 QLabel 到 (x, y) 位置
        # 位置是相对于父窗口（左上角为原点）的偏移
        self.pet_label.move(x, y)


    def get_pet_size(self) -> tuple:
        """
        获取宠物的尺寸

        返回：
            tuple：(width, height)
                   width：宠物宽度（像素）
                   height：宠物高度（像素）

        使用方式：
            w, h = window.get_pet_size()

        用途：
            - 计算穿墙边界
            - 居中定位
        """

        # 返回 QLabel 的当前尺寸
        # 尺寸由最近一次 set_pet_pixmap() 调用设置
        return (self.pet_label.width(), self.pet_label.height())


    # ==========================================================================
    # 公开方法 - 窗口控制
    # ==========================================================================

    def show(self):
        """
        显示窗口

        实现：
            调用 QWidget.show() 显示窗口
            窗口被设为 running 状态

        使用方式：
            window.show()
        """

        self.window.show()
        # show()：显示窗口
        # 窗口被设为可见状态并立即绘制

        self.running = True
        # 标记为运行状态


    def hide(self):
        """
        隐藏窗口

        实现：
            调用 QWidget.hide() 隐藏窗口
            窗口从屏幕上消失但未销毁

        使用方式：
            window.hide()
        """

        self.window.hide()
        # hide()：隐藏窗口
        # 窗口不可见但仍然存在，可以再次 show()

        self.running = False
        # 标记为非运行状态


    # ==========================================================================
    # 公开方法 - 定时器控制（备用）
    # ==========================================================================

    def start_move_timer(self, callback):
        """
        启动移动定时器（备用方法，当前版本未使用）

        参数：
            callback：定时器触发时要调用的回调函数

        实现：
            1. 将回调函数连接到定时器的 timeout 信号
            2. 启动定时器

        备注：
            当前版本使用主循环的 QTimer 进行更新
            此方法保留用于未来扩展
        """

        self.move_timer.timeout.connect(callback)
        # timeout.connect()：连接定时器超时信号到回调函数
        # 每当定时器触发时，会自动调用 callback

        self.move_timer.start()
        # start()：启动定时器


    def stop_move_timer(self):
        """
        停止移动定时器（备用方法，当前版本未使用）

        实现：
            调用定时器的 stop() 方法停止定时器
        """

        self.move_timer.stop()
        # stop()：停止定时器
        # 定时器不再触发


    def connect_key_events(self, callback):
        """
        连接键盘事件（备用方法，当前版本未使用）

        参数：
            callback：键盘事件触发时的回调函数

        备注：
            当前版本使用事件过滤器处理键盘输入
            此方法保留用于未来扩展
        """

        self.keypress_callback = callback
        # 保存回调函数引用


    # ==========================================================================
    # 公开方法 - 状态查询和控制
    # ==========================================================================

    def is_running(self) -> bool:
        """
        检查窗口是否处于运行状态

        返回：
            bool：True 表示正在运行，False 表示已停止
        """

        return self.running
        # 返回运行状态标志


    def quit(self):
        """
        退出程序

        实现：
            1. 标记为非运行状态
            2. 调用 QApplication.quit() 退出应用
            3. Qt 事件循环结束，程序终止

        使用方式：
            window.quit()
        """

        self.running = False
        # 标记为非运行状态

        self.app.quit()
        # quit()：退出 Qt 应用程序
        # 会关闭所有窗口并终止事件循环


    def process_events(self):
        """
        处理待处理的 Qt 事件（备用）

        实现：
            调用 QApplication.processEvents() 处理事件队列

        备注：
            当前版本使用 Qt 的事件循环机制
            此方法保留用于强制刷新显示等特殊需求
        """

        self.app.processEvents()
        # processEvents()：处理所有待处理的事件
        # 通常不需要手动调用，除非在某些阻塞场景下强制刷新


    def exec(self):
        """
        进入 Qt 事件循环

        实现：
            调用 QApplication.exec() 启动事件循环
            事件循环会持续运行直到调用 quit() 或关闭窗口

        注意：
            exec() 是阻塞调用
            它会一直运行直到程序退出
            这行代码之后的代码要等到事件循环结束才会执行

        使用方式：
            window.exec()  # 这行代码会阻塞，直到程序退出
        """

        self.app.exec()
        # exec()：进入 Qt 的主事件循环
        # 这是 Qt GUI 程序的入口点
        # 程序会在此处等待用户的操作和系统事件
