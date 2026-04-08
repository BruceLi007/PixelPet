"""
================================================================================
像素小人数据模型 - 管理角色的数据、状态、动画和位置
================================================================================

【文件作用】
    本文件定义了像素小人的核心数据模型，是项目的核心模块之一：
    - 管理角色的位置（x, y 坐标）
    - 管理角色的朝向（面向方向，用于上下移动时保持之前的左右方向）
    - 管理动画帧（加载、切换、播放）
    - 提供移动接口和方向设置接口

【使用技术】
    - PyQt6.QtGui.QPixmap：Qt 的图片类，用于加载和显示精灵图
    - PyQt6.QtCore.QTimer：Qt 的定时器类，用于驱动动画帧切换
    - Python enum.Enum：枚举类型，定义角色的方向状态
    - Python os 模块：用于拼接文件路径，查找资源文件

【核心概念】
    1. 【面向方向 (facing)】：角色最后一次向左还是向右移动
       - 用于解决"上下移动时保持什么方向"的问题
       - 例如：向右走时按上，角色应该面朝右，向上走但动画播放向右

    2. 【动画帧】：角色每个动作由多张图片循环播放实现
       - stay 目录：站立待机动画（4帧循环）
       - left 目录：向左移动动画（4帧循环）
       - right 目录：向右移动动画（4帧循环）

    3. 【动画定时器】：每 100ms 切换到下一帧，实现动画效果

【依赖关系】
    被导入：main.py, controllers/game_loop.py
    导入：config.settings（获取路径和动画间隔配置）

================================================================================
"""

# ================================================================================
# 导入标准库模块
# ================================================================================

import os
# os 模块：用于拼接文件路径，检查文件是否存在

import math
# math 模块：用于数学计算（如 sqrt 平方根）


# ================================================================================
# 导入项目模块
# ================================================================================

from enum import Enum
# Enum（枚举）：用于定义一组有名字的常量值
# 比用数字或字符串常量更具可读性和安全性

from PyQt6.QtGui import QPixmap
# QPixmap：Qt 中用于图像显示的类
# 特点：
#   - 针对屏幕显示优化，加载和渲染速度快
#   - 支持多种图片格式（PNG、JPG、BMP 等）
#   - 内置 Alpha 通道支持，实现透明效果

from PyQt6.QtCore import QTimer
# QTimer：Qt 的定时器类
# 特点：
#   - 基于事件循环，精确度高
#   - 可设置定时间隔和回调函数
#   - 支持 start() 和 stop() 控制

from config.settings import (
    ANIM_STAY_PATH,
    ANIM_LEFT_PATH,
    ANIM_RIGHT_PATH,
    ANIM_JUMP_PATH,
    ANIM_STAY_FPS,
    ANIM_LEFT_FPS,
    ANIM_RIGHT_FPS,
    ANIM_JUMP_FPS
)
# 从配置模块导入：
#   - ANIM_STAY_PATH：静止动画帧目录路径
#   - ANIM_LEFT_PATH：向左动画帧目录路径
#   - ANIM_RIGHT_PATH：向右动画帧目录路径
#   - ANIM_JUMP_PATH：跳跃动画帧目录路径
#   - ANIM_INTERVAL：动画帧切换的时间间隔（毫秒）


# ================================================================================
# 定义枚举类型 - 角色的方向状态
# ================================================================================

class Direction(Enum):
    """
    角色方向枚举类

    使用枚举定义角色的可能方向状态，替代直接使用字符串或数字：
    - 代码更清晰：Direction.LEFT 比 'left' 更明确
    - 防止错误：IDE 会提示可选值，减少拼写错误
    - 易于扩展：添加新方向时只需修改这里
    """

    LEFT = "left"
    # 向左方向
    # 值 "left" 用于字符串匹配和路径拼接

    RIGHT = "right"
    # 向右方向

    STAY = "stay"
    # 静止状态（站立待机）

    JUMP = "jump"
    # 原地跳跃状态


# ================================================================================
# 像素小人模型类
# ================================================================================

class PixelPet:
    """
    像素小人数据模型类

    负责管理像素小人的所有数据：
    - 位置信息：x, y 坐标
    - 方向状态：当前方向、面向方向
    - 动画帧：各方向的帧图片列表、当前帧索引
    - 动画定时器：驱动帧循环播放

    使用方式：
        pet = PixelPet(100, 200)  # 创建在 (100, 200) 位置
        pet.set_direction(5, 0)   # 设置向右移动
        pet.move(5, 0)            # 执行移动
    """

    # ==========================================================================
    # 初始化 - 创建像素小人实例
    # ==========================================================================

    def __init__(self, x: int, y: int, parent=None):
        """
        构造函数 - 初始化像素小人的所有属性

        参数：
            x (int)：初始 x 坐标
            y (int)：初始 y 坐标
            parent (QObject)：父对象（用于 Qt 对象层级，可选）

        初始化流程：
            1. 设置位置坐标
            2. 初始化方向状态
            3. 加载所有动画帧
            4. 设置初始显示帧
            5. 获取图片尺寸
            6. 创建动画定时器
        """

        # --------------------------------------------------------------------------
        # 位置坐标
        # --------------------------------------------------------------------------
        self.x = x
        # 角色在屏幕上的 x 坐标（像素单位，原点左上角向右为正）

        self.y = y
        # 角色在屏幕上的 y 坐标（像素单位，原点左上角向下为正）


        # --------------------------------------------------------------------------
        # 方向状态
        # --------------------------------------------------------------------------
        self.direction = Direction.STAY
        # 当前方向状态
        # 初始为静止状态，程序启动时播放站立动画

        self.facing = Direction.RIGHT
        # 面向方向（仅左右方向）
        # 解决"上下移动时保持什么方向"的问题
        # 初始默认面向右，程序启动时角色先面向右


        # --------------------------------------------------------------------------
        # 移动状态
        # --------------------------------------------------------------------------
        self.is_moving = False
        # 标记角色是否正在移动
        # 用于动画播放控制：移动时播放动画帧，静止时播放待机帧

        self.is_jumping = False
        # 标记角色是否正在跳跃
        # 跳跃时位置不变，但播放跳跃动画

        # 跳跃物理参数
        self.jump_velocity = 0
        # 当前跳跃垂直速度（负数=向上，正数=向下）
        self.jump_initial_y = 0
        # 跳跃起始y坐标
        self.jump_height = 120
        # 跳跃目标高度（像素）- 宠物会跳到这个高度然后落下
        self.gravity = 2.0
        # 重力加速度（增大使跳跃更稳定）


        # --------------------------------------------------------------------------
        # 父对象引用（Qt 相关）
        # --------------------------------------------------------------------------
        self.parent = parent
        # 保存父对象引用
        # 可用于访问父对象的数据或方法


        # --------------------------------------------------------------------------
        # 加载所有方向的动画帧
        # --------------------------------------------------------------------------
        # 使用字典存储每个方向对应的帧列表
        # 字典的 key 是 Direction 枚举值，value 是 QPixmap 图片列表
        self.frames = {
            # 加载静止动画帧：stay-1.png, stay-2.png, stay-3.png, stay-4.png
            Direction.STAY: self._load_frames(ANIM_STAY_PATH, "stay"),

            # 加载向左动画帧：left-1.png, left-2.png, left-3.png, left-4.png
            Direction.LEFT: self._load_frames(ANIM_LEFT_PATH, "left"),

            # 加载向右动画帧：right-1.png, right-2.png, right-3.png, right-4.png
            Direction.RIGHT: self._load_frames(ANIM_RIGHT_PATH, "right"),

            # 加载跳跃动画帧：jump-1.png, jump-2.png, jump-3.png, jump-4.png
            Direction.JUMP: self._load_frames(ANIM_JUMP_PATH, "jump"),
        }


        # --------------------------------------------------------------------------
        # 设置当前显示的动画
        # --------------------------------------------------------------------------
        # 从静止动画帧列表中取第一帧作为初始显示
        self.current_frames = self.frames[Direction.STAY]
        # current_frames：当前播放的动画帧列表

        self.frame_index = 0
        # frame_index：当前播放到第几帧（从0开始）
        # 例如：0 表示第1帧，1 表示第2帧

        self.current_sprite = self.current_frames[0]
        # current_sprite：当前实际显示的 QPixmap 图片对象


        # --------------------------------------------------------------------------
        # 获取图片尺寸
        # --------------------------------------------------------------------------
        # 从第一帧图片获取宽高，后续所有帧应该尺寸一致
        self.width = self.current_sprite.width()
        # 角色宽度（像素），用于碰撞检测和屏幕边界计算

        self.height = self.current_sprite.height()
        # 角色高度（像素），用于碰撞检测和屏幕边界计算


        # --------------------------------------------------------------------------
        # 创建动画定时器
        # --------------------------------------------------------------------------
        # QTimer：Qt 定时器类，基于事件循环驱动
        self.anim_timer = QTimer()
        # 创建定时器实例

        self.anim_timer.setInterval(1000 // ANIM_STAY_FPS)
        # setInterval()：设置定时器触发的时间间隔（毫秒）
        # 初始使用静止动画的帧率

        self.anim_timer.timeout.connect(self._next_frame)
        # timeout.connect()：连接超时信号到回调函数
        # 每当定时器触发（达到间隔时间），会自动调用 self._next_frame()


    # ==========================================================================
    # 私有方法 - 加载动画帧
    # ==========================================================================

    def _load_frames(self, path: str, prefix: str) -> list:
        """
        加载指定目录下的一组动画帧图片

        参数：
            path (str)：动画帧目录的完整路径
                       例如：'C:/project/.../assets/stay'
            prefix (str)：文件名前缀，用于拼接完整的文件名
                         例如：'stay' → 'stay-1.png', 'stay-2.png', ...

        返回：
            list：QPixmap 图片对象的列表，每项是一帧动画

        实现逻辑：
            1. 遍历 1-4 的帧编号
            2. 拼接完整的文件路径
            3. 检查文件是否存在
            4. 加载为 QPixmap 对象并添加到列表
        """

        frames = []
        # 存储加载的图片对象

        for i in range(1, 5):
            # 遍历帧编号 1, 2, 3, 4
            # range(1, 5) 生成 [1, 2, 3, 4]

            # 拼接文件名：prefix + '-' + 编号 + '.png'
            # 例如：'stay' + '-' + '1' + '.png' = 'stay-1.png'
            filename = f"{prefix}-{i}.png"

            # 拼接完整路径：目录路径 + 文件名
            # os.path.join() 自动处理不同操作系统的路径分隔符
            filepath = os.path.join(path, filename)

            # 检查文件是否存在，避免加载不存在的文件导致错误
            if os.path.exists(filepath):
                # QPixmap(filepath)：直接加载 PNG 图片
                # PNG 格式自带 Alpha 通道，背景透明部分会自动处理
                frames.append(QPixmap(filepath))

        return frames
        # 返回加载的图片列表，如果全部加载成功应该有 4 项


    # ==========================================================================
    # 私有方法 - 切换到下一帧动画
    # ==========================================================================

    def _next_frame(self):
        """
        切换到当前动画的下一帧

        定时器每触发一次调用此方法，实现动画循环播放：
            1. 检查是否应该播放动画（移动中或静止待机时或跳跃中）
            2. 帧索引 +1，并循环回到 0（超过列表长度时）
            3. 更新当前显示的图片对象

        注意：
            - 停止移动时不调用此方法，保持在第 1 帧
            - 切换方向时会重置帧索引，从第一帧开始播放
            - 跳跃动画播放完后自动切换回静止状态
        """

        # 检查是否应该播放动画
        # 条件：正在移动 或 当前是静止动画 或 正在跳跃
        # 这样设计是为了让角色静止时也播放待机动画，更有活力
        if self.is_moving or self.direction == Direction.STAY or self.is_jumping:

            # 如果没有动画帧，不播放
            if len(self.current_frames) == 0:
                return

            # 帧索引循环递增
            # 例如：3 + 1 = 4，4 % 4 = 0（回到第一帧）
            # 例如：0 + 1 = 1，1 % 4 = 1（继续播放）
            self.frame_index = (self.frame_index + 1) % len(self.current_frames)

            # len(self.current_frames)：当前动画的总帧数（通常为4）
            # %：取模运算，确保索引不会超出列表范围

            # 更新当前显示的图片
            # 从帧列表中取出对应索引的图片
            self.current_sprite = self.current_frames[self.frame_index]


    # ==========================================================================
    # 公开方法 - 动画控制
    # ==========================================================================

    def start_animation(self):
        """
        启动动画定时器，开始循环播放动画帧

        使用方式：
            pet.start_animation()  # 在程序启动或宠物可见时调用

        实现逻辑：
            检查定时器是否已经在运行
            如果没有运行，则启动定时器
        """

        if not self.anim_timer.isActive():
            # isActive()：检查定时器是否处于运行状态
            # not self.anim_timer.isActive()：定时器未运行

            self.anim_timer.start()
            # start()：启动定时器，开始按照设定的间隔触发


    def stop_animation(self):
        """
        停止动画定时器，暂停动画播放

        使用方式：
            pet.stop_animation()  # 在退出程序时调用，避免定时器继续运行

        实现逻辑：
            检查定时器是否正在运行
            如果正在运行，则停止定时器
        """

        if self.anim_timer.isActive():
            # isActive()：检查定时器是否处于运行状态
            # 如果定时器在运行，则停止它

            self.anim_timer.stop()
            # stop()：停止定时器，不再触发 timeout 信号


    # ==========================================================================
    # 公开方法 - 移动控制
    # ==========================================================================

    def move(self, dx: float, dy: float):
        """
        移动像素小人的位置

        参数：
            dx (float)：x 方向移动量（正数向右，负数向左）
            dy (float)：y 方向移动量（正数向下，负数向上）

        实现逻辑：
            1. 检查是否有移动量（dx 或 dy 不为 0）
            2. 如果有移动，更新 x, y 坐标，并标记为移动状态
            3. 如果没有移动，标记为静止状态

        注意：
            - 移动量是相对于当前位置的增量，不是目标位置
            - 实际像素位移 = dx * MOVE_SPEED（在 InputHandler 中处理）
            - 这里只负责更新坐标值
        """

        if dx != 0 or dy != 0:
            # 检查是否有移动量
            # dx != 0 表示水平方向有移动
            # dy != 0 表示垂直方向有移动

            # 更新位置坐标
            self.x += dx
            # x += dx：将 dx 加到当前 x 坐标上

            self.y += dy
            # y += dy：将 dy 加到当前 y 坐标上

            self.is_moving = True
            # 标记为移动状态，用于动画播放控制

        else:
            # 没有移动量（dx 和 dy 都是 0）

            self.is_moving = False
            # 标记为静止状态


    def jump(self):
        """
        触发原地跳跃

        实现逻辑：
            1. 如果已经在跳跃中，不重复触发
            2. 如果没有跳跃动画帧，不执行跳跃
            3. 记录跳跃起始位置
            4. 根据目标高度计算初速度（v = sqrt(2 * g * h)）
            5. 切换到跳跃动画状态
        """
        if self.is_jumping:
            # 已经在跳跃中，不重复触发
            return

        # 如果没有跳跃动画帧，不执行跳跃
        if len(self.frames[Direction.JUMP]) == 0:
            return

        self.is_jumping = True
        self.jump_initial_y = self.y
        # 根据目标高度计算初速度：v = sqrt(2 * g * h)
        # 向上的速度是负数
        self.jump_velocity = -math.sqrt(2 * self.gravity * self.jump_height)
        self.direction = Direction.JUMP
        self.current_frames = self.frames[Direction.JUMP]
        self.frame_index = 0
        self._update_anim_interval()


    def update_jump(self):
        """
        更新跳跃物理（每帧调用）

        使用简单的抛物线运动模拟跳跃：
            - 初始给予向上的速度
            - 每帧速度减少（重力作用）
            - 速度变正后开始下落
            - 落回原位时停止跳跃
        """
        if not self.is_jumping:
            return

        # 应用重力
        self.jump_velocity += self.gravity

        # 更新y坐标
        self.y += self.jump_velocity

        # 检测是否落地：y坐标回到或超过初始位置 且 正在下落（velocity > 0）
        if self.y >= self.jump_initial_y and self.jump_velocity > 0:
            self.y = self.jump_initial_y
            self.is_jumping = False
            self.direction = Direction.STAY
            self.current_frames = self.frames[Direction.STAY]
            self._update_anim_interval()


    def set_direction(self, dx: float, dy: float):
        """
        根据移动方向设置角色的动画和面向方向

        参数：
            dx (float)：x 方向移动量（负数向左，正数向右，0 无水平移动）
            dy (float)：y 方向移动量（负数向上，正数向下，0 无垂直移动）

        【核心逻辑 - 面向方向保持】

            左右移动时：立即更新面向方向和动画
            ------------------------------------------------------------
            按左键 → facing=LEFT, direction=LEFT → 播放 left 动画
            按右键 → facing=RIGHT, direction=RIGHT → 播放 right 动画

            上下移动时：保持之前的面向方向
            ------------------------------------------------------------
            面向右时按上键 → facing=RIGHT, direction=RIGHT → 播放 right 动画
            面向左时按上键 → facing=LEFT, direction=LEFT → 播放 left 动画

            这样设计让角色在上下移动时保持之前的左右朝向，更自然

        实现流程：
            1. 检查是否完全静止（dx=0 且 dy=0）
            2. 如果有移动，根据 dx 更新面向方向
            3. 根据方向设置对应的动画帧列表
            4. 如果方向改变，重置帧索引到 0
        """

        # --------------------------------------------------------------------------
        # 情况1：完全静止（松开所有方向键）
        # --------------------------------------------------------------------------
        if dx == 0 and dy == 0:
            # 同时按住了多个方向键时松开，可能出现 dx=0 dy=0
            # 例如：同时按左右然后松左右，或者同时按上下然后松上下

            new_direction = Direction.STAY
            # 切换到静止状态，播放待机动画


        # --------------------------------------------------------------------------
        # 情况2：向左移动
        # --------------------------------------------------------------------------
        elif dx < 0:
            # dx < 0 表示按下了左方向键

            self.facing = Direction.LEFT
            # 更新面向方向为左
            # 即使是斜向移动（dx<0 且 dy≠0），也要更新面向

            new_direction = Direction.LEFT
            # 播放向左动画


        # --------------------------------------------------------------------------
        # 情况3：向右移动
        # --------------------------------------------------------------------------
        elif dx > 0:
            # dx > 0 表示按下了右方向键

            self.facing = Direction.RIGHT
            # 更新面向方向为右

            new_direction = Direction.RIGHT
            # 播放向右动画


        # --------------------------------------------------------------------------
        # 情况4：纯上下移动（dx=0 但 dy≠0）
        # --------------------------------------------------------------------------
        elif dy != 0:
            # dy != 0 且 dx == 0 表示只按了上或下方向键

            new_direction = self.facing
            # 保持之前的面向方向
            # 如果之前面向右，就播放右动画；面向左就播放左动画


        # --------------------------------------------------------------------------
        # 情况5：其他情况（理论上不应该发生）
        # --------------------------------------------------------------------------
        else:
            # 兜底逻辑：设置为静止
            new_direction = Direction.STAY


        # --------------------------------------------------------------------------
        # 方向改变时切换动画
        # --------------------------------------------------------------------------
        # 只有当方向真正改变时才切换动画
        # 这样可以避免每次都重置帧索引导致动画卡顿

        if new_direction != self.direction:
            # 比较新方向和当前方向

            self.direction = new_direction
            # 更新当前方向

            self.current_frames = self.frames[self.direction]
            # 从字典中取出新方向对应的帧列表

            self.frame_index = 0
            # 重置帧索引，从第一帧开始播放
            # 这样每次切换方向都从头开始播放动画

            self.current_sprite = self.current_frames[0]
            # 立即更新显示的图片

            # 更新动画帧率
            self._update_anim_interval()


    def _update_anim_interval(self):
        """
        根据当前方向更新动画帧间隔
        """
        fps_map = {
            Direction.STAY: ANIM_STAY_FPS,
            Direction.LEFT: ANIM_LEFT_FPS,
            Direction.RIGHT: ANIM_RIGHT_FPS,
            Direction.JUMP: ANIM_JUMP_FPS,
        }
        fps = fps_map.get(self.direction, 10)
        self.anim_timer.setInterval(1000 // fps)


    # ==========================================================================
    # 公开方法 - 位置和尺寸查询
    # ==========================================================================

    def get_position(self) -> tuple:
        """
        获取角色当前位置坐标

        返回：
            tuple：(x, y) 元组
                   x：水平位置（像素）
                   y：垂直位置（像素）

        使用方式：
            x, y = pet.get_position()
        """

        return (self.x, self.y)
        # 返回位置元组


    def set_position(self, x: int, y: int):
        """
        设置角色的位置坐标

        参数：
            x (int)：新的 x 坐标
            y (int)：新的 y 坐标

        使用方式：
            pet.set_position(100, 200)  # 移动到 (100, 200)

        注意：
            这是绝对定位，直接设置坐标值
            不同于 move() 的相对移动
        """

        self.x = x
        # 更新 x 坐标

        self.y = y
        # 更新 y 坐标


    def get_rect(self):
        """
        获取角色的碰撞矩形（用于碰撞检测）

        返回：
            tuple：(x, y, width, height)
                   x, y：左上角坐标
                   width, height：矩形的宽高

        注意：
            当前实现只是返回位置和尺寸的元组
            如果需要真正的碰撞检测，可以用这个数据创建 QRect 对象
        """

        return (self.x, self.y, self.width, self.height)
        # 返回一个表示矩形的元组


    def get_size(self) -> tuple:
        """
        获取角色的尺寸

        返回：
            tuple：(width, height)
                   width：角色宽度（像素）
                   height：角色高度（像素）

        使用方式：
            w, h = pet.get_size()
        """

        return (self.width, self.height)
        # 返回尺寸元组
