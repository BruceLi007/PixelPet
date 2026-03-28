"""
================================================================================
跟随处理器 - 处理鼠标跟随逻辑
================================================================================

【文件作用】
    实现鼠标跟随功能：
    - 当启用跟随模式时，宠物每帧向鼠标位置移动
    - 支持 ESC 退出跟随模式
    - 穿墙逻辑由调用方处理

【依赖关系】
    被导入：features.mouse_follow
================================================================================
"""

# ================================================================================
# 导入 PyQt6 组件
# ================================================================================

from PyQt6.QtGui import QCursor
# QCursor：鼠标光标类


# ================================================================================
# 跟随处理器类
# ================================================================================

class FollowHandler:
    """
    跟随处理器类

    负责鼠标跟随模式的逻辑处理

    主要职责：
        1. 管理跟随模式的开关状态
        2. 计算向鼠标方向的移动量
        3. 检测 ESC 退出跟随

    使用方式：
        follow_handler = FollowHandler(window, pet, input_handler)

        # 在游戏循环中调用：
        dx, dy = follow_handler.update()
    """

    def __init__(self, window, pet, input_handler):
        """
        构造函数 - 初始化跟随处理器

        参数：
            window：主窗口对象（用于获取鼠标位置）
            pet：宠物对象（用于获取位置信息）
            input_handler：输入处理器（用于检测 ESC）
        """

        self.window = window
        self.pet = pet
        self.input_handler = input_handler


        # --------------------------------------------------------------------------
        # 跟随模式配置
        # --------------------------------------------------------------------------

        self.follow_enabled = False
        self.lerp_factor = 0.15
        self.max_speed = 15
        self.stop_threshold = 30


    # ==========================================================================
    # 公开方法
    # ==========================================================================

    def is_follow_enabled(self) -> bool:
        """
        检查跟随模式是否启用

        返回：
            bool：True 启用，False 未启用
        """

        return self.follow_enabled


    def enable_follow(self):
        """
        启用跟随模式
        """

        self.follow_enabled = True


    def disable_follow(self):
        """
        禁用跟随模式
        """

        self.follow_enabled = False


    def toggle_follow(self):
        """
        切换跟随模式
        """

        self.follow_enabled = not self.follow_enabled


    def check_escape(self) -> bool:
        """
        检查是否按下了 ESC 键

        返回：
            bool：True 表示按下了 ESC
        """

        return self.input_handler.is_escape_pressed()


    def update(self) -> tuple:
        """
        更新跟随状态，计算移动量

        在游戏循环的每一帧调用

        返回：
            tuple：(dx, dy)
                   dx：x 方向移动量
                   dy：y 方向移动量
                   如果未启用跟随或距离太近，返回 (0, 0)
        """

        # 如果未启用跟随模式，返回 (0, 0)
        if not self.follow_enabled:
            return (0, 0)


        # 获取鼠标位置
        pos = QCursor.pos()
        mouse_x = pos.x()
        mouse_y = pos.y()


        # 计算宠物中心位置
        pet_center_x = self.pet.x + self.pet.width // 2
        pet_center_y = self.pet.y + self.pet.height // 2


        # 计算到鼠标的方向向量
        dir_x = mouse_x - pet_center_x
        dir_y = mouse_y - pet_center_y


        # 计算距离
        distance = (dir_x ** 2 + dir_y ** 2) ** 0.5

        # 停止阈值：当距离小于此值时停止移动
        if distance <= self.stop_threshold:
            return (0, 0)

        # 使用 Lerp 插值实现平滑跟随
        dx = dir_x * self.lerp_factor
        dy = dir_y * self.lerp_factor

        # 限制最大速度
        speed = (dx ** 2 + dy ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            dx *= scale
            dy *= scale


        return (dx, dy)