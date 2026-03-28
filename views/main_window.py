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
# 导入 PyQt6 组件
# ================================================================================

from PyQt6.QtWidgets import QApplication, QLabel, QWidget
# QApplication：Qt 应用程序类
# QLabel：标签控件，用于显示宠物图片
# QWidget：基础窗口控件

from PyQt6.QtCore import Qt
# Qt：包含 Qt 框架的各种常量定义

from PyQt6.QtGui import QPixmap
# QPixmap：Qt 图片类

import screeninfo
# screeninfo：跨平台的屏幕信息获取库


# ================================================================================
# 导入项目配置模块
# ================================================================================

from config.settings import FPS, MOVE_INTERVAL


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
        """

        # --------------------------------------------------------------------------
        # 创建 Qt 应用程序实例
        # --------------------------------------------------------------------------
        self.app = QApplication([])
        # 每个 Qt GUI 程序只需要一个 QApplication 实例


        # --------------------------------------------------------------------------
        # 获取屏幕尺寸（带容错机制）
        # --------------------------------------------------------------------------
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
            print(f"Qt screen detection failed: {e}")

        # 方法2：如果 screeninfo 可用且返回值合理，验证一下
        try:
            screen = screeninfo.get_monitors()[0]
            if abs(screen.width - self.screen_width) > 100 or abs(screen.height - self.screen_height) > 100:
                print(f"Warning: screeninfo returned {screen.width}x{screen.height}, "
                      f"but Qt returned {self.screen_width}x{self.screen_height}. Using Qt value.")
            else:
                self.screen_width = screen.width
                self.screen_height = screen.height
        except Exception:
            pass


        # --------------------------------------------------------------------------
        # 创建主窗口
        # --------------------------------------------------------------------------
        self.window = QWidget()
        self.window.setWindowTitle("PixelPet")

        # 设置窗口标志（无边框、顶层、工具窗口）
        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        # 设置窗口透明属性
        self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 设置窗口几何尺寸（全屏）
        self.window.setGeometry(0, 0, self.screen_width, self.screen_height)

        # 设置焦点策略
        self.window.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


        # --------------------------------------------------------------------------
        # 创建宠物显示标签（QLabel）
        # --------------------------------------------------------------------------
        self.pet_label = QLabel(self.window)
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --------------------------------------------------------------------------
        # 初始化其他属性
        # --------------------------------------------------------------------------
        self.running = False
        # running：标记窗口是否处于运行状态


    # ==========================================================================
    # 公开方法 - 尺寸和位置
    # ==========================================================================

    def get_screen_size(self) -> tuple:
        """
        获取屏幕尺寸

        返回：
            tuple：(screen_width, screen_height)
        """

        return (self.screen_width, self.screen_height)


    # ==========================================================================
    # 公开方法 - 宠物显示更新
    # ==========================================================================

    def set_pet_pixmap(self, pixmap: QPixmap):
        """
        设置宠物显示的图片

        参数：
            pixmap (QPixmap)：要显示的图片对象
        """

        self.pet_label.setPixmap(pixmap)
        self.pet_label.resize(pixmap.width(), pixmap.height())


    def set_pet_position(self, x: int, y: int):
        """
        设置宠物的屏幕位置

        参数：
            x (int)：x 坐标
            y (int)：y 坐标
        """

        self.pet_label.move(x, y)


    def get_pet_size(self) -> tuple:
        """
        获取宠物的尺寸

        返回：
            tuple：(width, height)
        """

        return (self.pet_label.width(), self.pet_label.height())


    # ==========================================================================
    # 公开方法 - 窗口控制
    # ==========================================================================

    def show(self):
        """
        显示窗口
        """

        self.window.show()
        self.running = True


    def hide(self):
        """
        隐藏窗口
        """

        self.window.hide()
        self.running = False


    def is_running(self) -> bool:
        """
        检查窗口是否处于运行状态

        返回：
            bool：True 表示正在运行，False 表示已停止
        """

        return self.running


    def quit(self):
        """
        退出程序
        """

        self.running = False
        self.app.quit()


    def process_events(self):
        """
        处理待处理的 Qt 事件
        """

        self.app.processEvents()


    def exec(self):
        """
        进入 Qt 事件循环
        """

        self.app.exec()