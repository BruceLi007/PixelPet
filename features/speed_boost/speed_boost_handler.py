"""
================================================================================
双击加速处理器 - 处理双击方向键速度提升逻辑
================================================================================

【文件作用】
    实现双击加速功能：
    - 0.5秒内连续按2次同一方向键，移动速度增加4倍
    - 只有真正的第二次按下（松开后再次按下）才触发加速
    - key repeat（长按自动重复）不会触发加速
    - 按住不放会一直保持加速，直到松开才恢复

【使用技术】
    - time.time()：获取当前时间戳
    - set 集合：存储方向键，用于检测是否有键被按下

【双击检测原理】
    1. 记录上次按下的方向键（last_pressed_key）和时间（last_press_time）
    2. 当新的按键按下时：
       - 检查是否在 0.5 秒内
       - 检查是否和上次是同一个键
       - 检查该键之前是否已按下（排除 key repeat）
    3. 如果满足条件，触发 4 倍加速

【Qt Key Repeat 处理】
    Qt 的 key repeat 机制会发送交替的 KeyRelease 和 KeyPress 事件
    为了区分 Qt 的 repeat 和用户真正的松开：
    1. 收到触发加速键的 KeyRelease 时，开始等待 0.15 秒
    2. 等待期间如果收到该键的 KeyPress (auto=True)，说明是 Qt repeat，忽略
    3. 等待期间如果收到该键的 KeyPress (auto=False)，说明用户重新按下，清除加速状态
    4. 等待超时后确认用户真的松开了，重置加速

【依赖关系】
    被导入：features.speed_boost
    导入：PyQt6.QtCore.Qt（方向键常量）
================================================================================
"""

# ================================================================================
# 导入标准库
# ================================================================================

import time
# time：时间模块，用于检测双击间隔和定时器


# ================================================================================
# 导入 PyQt6 组件
# ================================================================================

from PyQt6.QtCore import Qt
# Qt：Qt 常量，包含键码（Key_Up, Key_Down 等）


# ================================================================================
# 双击加速处理器类
# ================================================================================

class SpeedBoostHandler:
    """
    双击加速处理器类

    负责检测双击方向键并提供速度倍率：

    主要职责：
        1. 检测双击（0.5秒内同一键再次按下）
        2. 排除 key repeat 触发的重复按下
        3. 提供当前速度倍率

    使用方式：
        speed_boost = SpeedBoostHandler()

        # 在 keyPressEvent 中调用
        speed_boost.check_double_tap(key, key_in_keys_pressed)

        # 在 keyReleaseEvent 中调用
        speed_boost.reset_if_no_direction_keys(keys_pressed)

        # 获取当前加速倍率
        boost = speed_boost.get_boost()
    """

    # ==========================================================================
    # 类常量
    # ==========================================================================

    # 双击间隔时间（秒）
    DOUBLE_TAP_INTERVAL = 0.5

    # 速度提升倍率
    SPEED_BOOST_MULTIPLIER = 4.0

    # 正常速度倍率
    NORMAL_SPEED = 1.0

    # Qt repeat 检测等待时间（秒）
    # Qt repeat 间隔约 0.1 秒，用 0.15 秒区分真正的松开和 Qt repeat
    QT_REPEAT_WAIT_TIME = 0.15

    # 方向键集合
    DIRECTION_KEYS = {
        Qt.Key.Key_Up, Qt.Key.Key_Down,
        Qt.Key.Key_Left, Qt.Key.Key_Right,
        Qt.Key.Key_W, Qt.Key.Key_A,
        Qt.Key.Key_S, Qt.Key.Key_D
    }

    # ==========================================================================
    # 初始化
    # ==========================================================================

    def __init__(self):
        """
        构造函数 - 初始化双击加速处理器
        """

        self.enabled = True
        # enabled：双击加速功能是否启用

        self.last_pressed_key = None
        # last_pressed_key：上次按下的方向键

        self.last_press_time = 0
        # last_press_time：上次按键时间（时间戳）

        self.speed_boost = self.NORMAL_SPEED
        # speed_boost：当前速度倍率，1.0 为正常速度，4.0 为加速

        self.boosted_key = None
        # boosted_key：记录当前哪个键触发了加速

        self.release_waiting = False
        # release_waiting：是否在等待 Qt repeat 检测

        self.release_wait_start = 0
        # release_wait_start：等待开始的时间戳


    # ==========================================================================
    # 公开方法
    # ==========================================================================

    def is_enabled(self) -> bool:
        """
        检查双击加速功能是否启用

        返回：
            bool：True 启用，False 未启用
        """

        return self.enabled


    def enable(self):
        """
        启用双击加速功能
        """

        self.enabled = True


    def disable(self):
        """
        禁用双击加速功能
        """

        self.enabled = False


    def toggle(self):
        """
        切换双击加速功能
        """

        self.enabled = not self.enabled


    def check_double_tap(self, key: int, is_auto_repeat: bool):
        """
        检测双击

        在 keyPressEvent 中调用

        参数：
            key：当前按下的键的 Qt 键码
            is_auto_repeat：是否是 key repeat 触发的重复按下

        逻辑：
            1. 只对方向键检测双击
            2. 排除 key repeat 触发的重复按下（由 Qt 自动过滤）
        """

        # 如果功能未启用，不检测双击
        if not self.enabled:
            return

        # 如果该键已触发过加速
        if key == self.boosted_key:
            # 如果是非 auto repeat 的 KeyPress，说明用户重新按下了这个键
            # 清除所有状态，恢复正常速度
            if not is_auto_repeat:
                self.release_waiting = False
                self.boosted_key = None
                self.last_pressed_key = None  # 防止再次触发双击
                self.speed_boost = self.NORMAL_SPEED  # 恢复正常速度
            return

        # 排除 key repeat 事件（长按自动重复）
        if is_auto_repeat:
            return

        # 只对方向键检测双击
        if key in self.DIRECTION_KEYS:
            current_time = time.time()

            # 检查是否在0.5秒内再次按下同一键
            if (key == self.last_pressed_key and
                current_time - self.last_press_time < self.DOUBLE_TAP_INTERVAL):
                # 触发加速
                self.speed_boost = self.SPEED_BOOST_MULTIPLIER
                self.boosted_key = key
            else:
                # 更新记录
                self.last_pressed_key = key
                self.last_press_time = current_time


    def reset_if_no_direction_keys(self, keys_pressed: set, released_key: int = None):
        """
        检查是否需要重置加速

        在 keyReleaseEvent 中调用

        参数：
            keys_pressed：当前按下的所有键的集合
            released_key：释放的键

        逻辑：
            - 如果释放的是触发加速的键，开始 Qt repeat 检测等待
            - 等待期间收到该键的 KeyPress 取消等待（是 Qt repeat）
            - 等待超时后确认用户真的松开了，重置加速
            - 如果所有方向键都释放了，也重置加速
        """

        # 如果已经加速了
        if self.speed_boost > self.NORMAL_SPEED:
            current_time = time.time()

            # 如果释放的是触发加速的键
            if released_key == self.boosted_key:
                # 如果已经在等待检测中，说明这是 Qt repeat，不做任何事
                if self.release_waiting:
                    return
                # 开始等待检测
                self.release_waiting = True
                self.release_wait_start = current_time
                return

            # 如果在等待检测中
            if self.release_waiting:
                elapsed = current_time - self.release_wait_start
                # 超过 QT_REPEAT_WAIT_TIME 秒，确认用户真的松开了
                if elapsed >= self.QT_REPEAT_WAIT_TIME:
                    self.speed_boost = self.NORMAL_SPEED
                    self.boosted_key = None
                    self.release_waiting = False
                return

            # 如果所有方向键都释放了，重置加速
            if not (keys_pressed & self.DIRECTION_KEYS):
                self.speed_boost = self.NORMAL_SPEED
                self.boosted_key = None


    def get_boost(self) -> float:
        """
        获取当前速度倍率

        返回：
            float：当前速度倍率（1.0 或 4.0）
        """
        return self.speed_boost


    def reset(self):
        """
        重置加速状态

        用于程序退出时清理状态
        """

        self.enabled = True
        self.speed_boost = self.NORMAL_SPEED
        self.last_pressed_key = None
        self.last_press_time = 0
        self.boosted_key = None
        self.release_waiting = False
