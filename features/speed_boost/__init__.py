"""
================================================================================
速度加速模块 - 双击方向键触发速度提升
================================================================================

【文件作用】
    提供双击加速功能：
    - 0.5秒内连续按2次同一方向键，移动速度增加20%
    - 松开所有方向键后恢复原速度

【使用方式】
    from features.speed_boost import SpeedBoostHandler

    speed_boost = SpeedBoostHandler()

    # 在 keyPressEvent 中调用
    speed_boost.check_double_tap(key, key_in_keys_pressed)

    # 在 keyReleaseEvent 中调用
    speed_boost.reset_if_no_direction_keys(keys_pressed)

    # 获取当前加速倍率
    boost = speed_boost.get_boost()
================================================================================
"""

from .speed_boost_handler import SpeedBoostHandler

__all__ = ['SpeedBoostHandler']
