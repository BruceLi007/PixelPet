"""
================================================================================
跳跃处理器 - 管理角色的跳跃物理和状态
================================================================================

【文件作用】
    本文件负责处理角色的跳跃功能：
    - 管理跳跃状态（是否正在跳跃）
    - 计算跳跃物理（初速度、重力、落地检测）
    - 提供跳跃触发和更新接口

【跳跃物理原理】
    1. 跳跃开始时，根据目标高度和重力计算初速度
       v = sqrt(2 * g * h)
    2. 每帧应用重力，更新速度和位置
       velocity += gravity
       y += velocity
    3. 检测落地：y >= initial_y 且 velocity > 0

【依赖关系】
    被导入：main.py
    导入：models.pixel_pet（Direction 枚举）

================================================================================
"""

import math

from models.pixel_pet import Direction


# ================================================================================
# 跳跃处理器类
# ================================================================================

class JumpHandler:
    """
    跳跃处理器类

    负责管理角色的跳跃物理和状态：
    - 触发跳跃，设置初速度和初始位置
    - 每帧更新跳跃物理（应用重力）
    - 检测落地并重置跳跃状态

    使用方式：
        jump_handler = JumpHandler()
        jump_handler.jump(pet)           # 触发跳跃
        jump_handler.update_jump(pet)     # 每帧调用
        if jump_handler.is_jumping(pet):  # 检查状态
            ...
    """

    # ==========================================================================
    # 初始化
    # ==========================================================================

    def __init__(self):
        """
        初始化跳跃处理器
        """
        # 跳跃物理参数
        self.jump_height = 120
        # 跳跃目标高度（像素）- 宠物会跳到这个高度然后落下

        self.gravity = 2.0
        # 重力加速度（增大使跳跃更稳定）

    # ==========================================================================
    # 公开方法
    # ==========================================================================

    def jump(self, pet):
        """
        触发原地跳跃

        参数：
            pet：宠物对象，需要有以下属性：
                - is_jumping：跳跃状态标志
                - y：当前y坐标
                - direction：当前方向
                - current_frames：当前动画帧列表
                - frame_index：当前帧索引

        实现逻辑：
            1. 如果已经在跳跃中，不重复触发
            2. 如果没有跳跃动画帧，不执行跳跃
            3. 记录跳跃起始位置
            4. 根据目标高度计算初速度（v = sqrt(2 * g * h)）
            5. 切换到跳跃动画状态
        """
        if pet.is_jumping:
            # 已经在跳跃中，不重复触发
            return

        # 如果没有跳跃动画帧，不执行跳跃
        if len(pet.frames[Direction.JUMP]) == 0:
            return

        pet.is_jumping = True
        pet.jump_initial_y = pet.y
        # 根据目标高度计算初速度：v = sqrt(2 * g * h)
        # 向上的速度是负数
        pet.jump_velocity = -math.sqrt(2 * self.gravity * self.jump_height)
        pet.direction = Direction.JUMP
        pet.current_frames = pet.frames[Direction.JUMP]
        pet.frame_index = 0
        pet._update_anim_interval()


    def update_jump(self, pet):
        """
        更新跳跃物理（每帧调用）

        参数：
            pet：宠物对象

        实现逻辑：
            1. 如果不在跳跃中，直接返回
            2. 应用重力，更新速度
            3. 更新y坐标
            4. 检测落地，重置跳跃状态
        """
        if not pet.is_jumping:
            return

        # 应用重力
        pet.jump_velocity += self.gravity

        # 更新y坐标
        pet.y += pet.jump_velocity

        # 检测是否落地：y坐标回到或超过初始位置 且 正在下落（velocity > 0）
        if pet.y >= pet.jump_initial_y and pet.jump_velocity > 0:
            pet.y = pet.jump_initial_y
            pet.is_jumping = False
            pet.direction = Direction.STAY
            pet.current_frames = pet.frames[Direction.STAY]
            pet._update_anim_interval()


    def is_jumping(self, pet) -> bool:
        """
        检查宠物是否正在跳跃

        参数：
            pet：宠物对象

        返回：
            bool：True 表示正在跳跃
        """
        return pet.is_jumping
