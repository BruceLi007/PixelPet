"""
================================================================================
系统托盘管理器 - 创建和管理系统托盘图标
================================================================================

【文件作用】
    管理系统托盘图标和右键菜单：
    - 创建托盘图标
    - 提供"鼠标跟随（ESC停止）"和"退出"菜单
    - 处理双击托盘图标显示/隐藏窗口

【使用技术】
    - PyQt6.QtWidgets.QSystemTrayIcon：系统托盘图标
    - PyQt6.QtWidgets.QMenu：右键弹出菜单
    - PyQt6.QtGui.QAction：菜单项动作
    - PyQt6.QtGui.QIcon：图标类

【依赖关系】
    被导入：features.tray
    导入：PyQt6.QtWidgets, PyQt6.QtGui
================================================================================
"""

# ================================================================================
# 导入 PyQt6 组件
# ================================================================================

import os
# os 模块：用于处理文件路径

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QWidget
# QSystemTrayIcon：系统托盘图标类
# QMenu：右键弹出菜单类

from PyQt6.QtGui import QIcon, QAction
# QIcon：图标类
# QAction：动作类（菜单项）


# ================================================================================
# 托盘管理器类
# ================================================================================

class TrayManager:
    """
    系统托盘管理器类

    负责创建和管理系统托盘图标及其菜单

    主要职责：
        1. 创建托盘图标
        2. 创建右键菜单
        3. 提供菜单项触发信号的回调

    使用方式：
        tray_manager = TrayManager(parent_widget, quit_callback)
        tray_manager.show()
    """

    def __init__(self, parent_widget: QWidget, on_quit: callable):
        """
        构造函数 - 初始化托盘管理器

        参数：
            parent_widget (QWidget)：父窗口部件，用于获取资源路径
            on_quit (callable)：退出程序回调函数
        """

        self.parent_widget = parent_widget
        # 保存父窗口引用

        self.on_quit = on_quit
        # 保存退出回调函数


        # --------------------------------------------------------------------------
        # 创建托盘图标
        # --------------------------------------------------------------------------

        # 获取资源目录路径
        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "stay"
        )
        icon_path = os.path.join(assets_dir, "stay-1.png")

        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(parent_widget)

        # 如果图标文件存在，使用它作为托盘图标
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # 使用默认图标
            self.tray_icon.setIcon(
                parent_widget.app.style().standardIcon(
                    parent_widget.app.style().StandardPixmap.SP_ComputerIcon
                )
            )


        # --------------------------------------------------------------------------
        # 创建右键菜单
        # --------------------------------------------------------------------------

        self.tray_menu = QMenu()

        # 创建"鼠标跟随（ESC停止）"菜单项（带勾选标记）
        self.follow_mouse_action = QAction("鼠标跟随（ESC停止）", self.tray_menu)
        self.follow_mouse_action.setCheckable(True)
        # setCheckable(True)：菜单项显示勾选框
        self.mouse_follow_enabled = False
        # mouse_follow_enabled：标记是否启用鼠标跟随
        self.follow_mouse_action.triggered.connect(self.toggle_mouse_follow)
        self.tray_menu.addAction(self.follow_mouse_action)

        self.tray_menu.addSeparator()
        # 添加分隔线

        # 创建"退出"菜单项
        self.quit_action = QAction("退出", self.tray_menu)
        self.quit_action.triggered.connect(self.quit)
        self.tray_menu.addAction(self.quit_action)

        # 将菜单设置为托盘图标的右键菜单
        self.tray_icon.setContextMenu(self.tray_menu)

        # 双击托盘图标显示/隐藏窗口
        self.tray_icon.activated.connect(self.on_tray_activated)

        # 显示托盘图标
        self.tray_icon.show()


    # ==========================================================================
    # 公开方法
    # ==========================================================================

    def toggle_mouse_follow(self):
        """
        切换鼠标跟随模式

        点击托盘菜单的"鼠标跟随"时调用
        切换跟随状态的开启/关闭
        """

        self.mouse_follow_enabled = not self.mouse_follow_enabled
        # 切换状态

        self.follow_mouse_action.setChecked(self.mouse_follow_enabled)
        # 更新菜单项的勾选状态


    def on_tray_activated(self, reason):
        """
        处理托盘图标被激活的事件（双击）

        参数：
            reason：激活原因（QSystemTrayIcon.ActivationReason）

        实现：
            - DoubleClick：切换窗口显示/隐藏
            - 其他：什么都不做
        """

        # DoubleClick = 3，双击托盘图标切换窗口显示状态
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.parent_widget.isVisible():
                self.parent_widget.hide()
            else:
                self.parent_widget.show()


    def quit(self):
        """
        退出程序

        调用保存的退出回调函数
        """

        self.on_quit()