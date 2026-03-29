"""
================================================================================
拖动处理器 - 处理鼠标拖动宠物
================================================================================

【文件作用】
    实现鼠标拖动功能：
    - 鼠标按下时检测是否在宠物上
    - 鼠标移动时更新宠物位置
    - 鼠标右键点击宠物弹出菜单

【使用技术】
    - PyQt6.QtCore.QObject：Qt 对象基类（事件过滤器需要）
    - PyQt6.QtCore.QEvent：Qt 事件类
    - PyQt6.QtCore.Qt：Qt 常量
    - PyQt6.QtWidgets.QMenu：右键菜单

【依赖关系】
    被导入：features.mouse_drag
================================================================================
"""

# ================================================================================
# 导入 PyQt6 组件
# ================================================================================

from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction


# ================================================================================
# 拖动处理器类
# ================================================================================

class DragHandler(QObject):
    """
    拖动处理器类

    负责处理鼠标拖动宠物的事件

    主要职责：
        1. 安装事件过滤器到窗口
        2. 检测鼠标是否在宠物上按下
        3. 拖动时更新宠物位置
        4. 右键点击宠物弹出菜单

    使用方式：
        drag_handler = DragHandler(window, pet_label, pet, follow_handler, tray_manager)
    """

    def __init__(self, window: QObject, pet_label, pet, follow_handler, tray_manager, quit_callback, speed_boost_handler):
        """
        构造函数 - 初始化拖动处理器

        参数：
            window (QObject)：主窗口对象
            pet_label：宠物的 QLabel 显示部件
            pet：宠物对象
            follow_handler：跟随处理器（用于菜单操作）
            tray_manager：托盘管理器（用于菜单操作）
            quit_callback：退出程序回调函数
            speed_boost_handler：双击加速处理器（用于菜单操作）
        """

        super().__init__()
        self.window = window
        self.pet_label = pet_label
        self.pet = pet
        self.follow_handler = follow_handler
        self.tray_manager = tray_manager
        self.quit_callback = quit_callback
        self.speed_boost_handler = speed_boost_handler


        # --------------------------------------------------------------------------
        # 初始化拖动状态
        # --------------------------------------------------------------------------

        self.is_dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0


        # --------------------------------------------------------------------------
        # 启用鼠标跟踪
        # --------------------------------------------------------------------------

        window.setMouseTracking(True)
        pet_label.setMouseTracking(True)


        # --------------------------------------------------------------------------
        # 安装事件过滤器
        # --------------------------------------------------------------------------

        window.installEventFilter(self)


    # ==========================================================================
    # 事件过滤器
    # ==========================================================================

    def eventFilter(self, obj, event):
        """
        事件过滤器 - 处理鼠标事件
        """

        event_type = event.type()


        if event_type == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self._start_drag(event)
                return True

            elif event.button() == Qt.MouseButton.RightButton:
                # 记录右键按下的位置
                self._right_button_pos = (event.position().x(), event.position().y())
                return True


        elif event_type == QEvent.Type.MouseMove:
            if self.is_dragging:
                self._update_drag(event)
                return True


        elif event_type == QEvent.Type.MouseButtonRelease:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = False
                return True

            elif event.button() == Qt.MouseButton.RightButton:
                # 右键释放时显示菜单
                self._show_context_menu(event)
                return True


        return super().eventFilter(obj, event)


    # ==========================================================================
    # 私有方法
    # ==========================================================================

    def _is_mouse_on_pet(self, mouse_x, mouse_y) -> bool:
        """
        检查鼠标是否在宠物上
        """
        pet_x = self.pet_label.x()
        pet_y = self.pet_label.y()
        pet_width = self.pet_label.width()
        pet_height = self.pet_label.height()

        return (pet_x <= mouse_x <= pet_x + pet_width and
                pet_y <= mouse_y <= pet_y + pet_height)


    def _start_drag(self, event):
        """
        开始拖动
        """
        mouse_x = event.position().x()
        mouse_y = event.position().y()

        if self._is_mouse_on_pet(mouse_x, mouse_y):
            self.is_dragging = True
            self.drag_offset_x = mouse_x - self.pet_label.x()
            self.drag_offset_y = mouse_y - self.pet_label.y()


    def _update_drag(self, event):
        """
        更新拖动位置
        """
        mouse_x = event.position().x()
        mouse_y = event.position().y()

        new_x = int(mouse_x - self.drag_offset_x)
        new_y = int(mouse_y - self.drag_offset_y)

        self.pet_label.move(new_x, new_y)
        self.pet.x = new_x
        self.pet.y = new_y


    def _show_context_menu(self, event):
        """
        显示右键菜单
        """
        # 使用记录的右键按下位置
        mouse_x, mouse_y = self._right_button_pos

        # 只在宠物上显示菜单
        if not self._is_mouse_on_pet(mouse_x, mouse_y):
            return

        # 创建菜单
        menu = QMenu()

        # 添加"双击方向键加速"提示（不可点击）
        speed_boost_action = QAction("双击方向键加速", menu)
        speed_boost_action.setEnabled(False)
        menu.addAction(speed_boost_action)

        # 添加"鼠标跟随（ESC退出）"菜单项
        follow_action = QAction("鼠标跟随（ESC退出）", menu)
        follow_action.setCheckable(True)
        follow_action.setChecked(self.follow_handler.is_follow_enabled())

        # 点击时切换跟随模式
        def toggle_follow():
            self.follow_handler.toggle_follow()
            is_enabled = self.follow_handler.is_follow_enabled()
            follow_action.setChecked(is_enabled)
            self.tray_manager.follow_mouse_action.setChecked(is_enabled)

        follow_action.triggered.connect(toggle_follow)
        menu.addAction(follow_action)

        menu.addSeparator()
        # 添加分隔线

        # 添加"退出"菜单项
        exit_action = QAction("退出", menu)
        exit_action.triggered.connect(self.quit_callback)
        menu.addAction(exit_action)

        # 显示菜单（在当前鼠标位置）
        from PyQt6.QtGui import QCursor
        menu.exec(QCursor.pos())