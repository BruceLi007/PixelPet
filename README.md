# PixelPet - 像素桌面宠物

一个轻量级的 Windows 桌面宠物程序，在桌面上显示一个可自由移动的像素风格小人。

## 功能特点

- **透明窗口** - 覆盖整个桌面，背景完全透明，仅显示宠物
- **键盘移动** - 支持上下左右四个方向移动（WASD/方向键）
- **双击加速** - 0.5秒内连续按两次同一方向键，移动速度提升4倍
- **帧动画** - 流畅的走路动画效果，各方向动画速度可独立调整
- **穿墙循环** - 从屏幕一侧移出会从另一侧进入
- **面向保持** - 上下移动时保持之前的左右面向方向
- **鼠标拖动** - 左键按住宠物可拖动到任意位置
- **鼠标跟随** - 宠物会平滑跟随鼠标移动
- **系统托盘** - 托盘图标+右键菜单，方便退出程序

## 操作方式

| 操作 | 功能 |
|------|------|
| ↑ / W | 向上移动 |
| ↓ / S | 向下移动 |
| ← / A | 向左移动 |
| → / D | 向右移动 |
| 双击方向键（按住不松） | 持续加速移动（4倍速度） |
| 左键拖动 | 拖动宠物到任意位置 |
| 右键点击宠物 | 弹出菜单（鼠标跟随、双击加速提示） |
| 鼠标跟随（菜单） | 宠物跟随鼠标移动，ESC退出 |
| 退出（托盘菜单） | 退出程序 |

## 项目结构

```
PixelPet/
├── main.py                     # 程序入口
├── config/
│   └── settings.py            # 配置文件（速度、路径、动画帧率）
├── models/
│   └── pixel_pet.py           # 像素宠物模型（位置、方向、动画）
├── views/
│   └── main_window.py         # 主窗口视图（透明窗口）
├── controllers/
│   └── input_handler.py       # 键盘输入处理（双击加速逻辑）
├── features/                  # 功能模块
│   ├── speed_boost/          # 双击加速
│   │   ├── __init__.py
│   │   └── speed_boost_handler.py
│   ├── tray/                 # 系统托盘
│   │   ├── __init__.py
│   │   └── tray_manager.py
│   ├── mouse_drag/          # 鼠标拖动
│   │   ├── __init__.py
│   │   └── drag_handler.py
│   └── mouse_follow/         # 鼠标跟随
│       ├── __init__.py
│       └── follow_handler.py
└── assets/                   # 精灵图资源
    ├── stay/                # 静止动画（4帧）
    ├── left/                # 向左动画（4帧）
    └── right/               # 向右动画（4帧）
```

## 快速开始

### 方式一：从源码运行

```bash
# 1. 进入项目目录
cd DeskTopMan

# 2. 创建虚拟环境（推荐）
python -m venv venv
.\venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py
```

### 方式二：直接运行 exe

下载 `dist/PixelPet.exe` 并双击运行。

## 配置说明

### 双击加速参数

双击间隔和加速倍率可在 `features/speed_boost/speed_boost_handler.py` 中调整：

```python
DOUBLE_TAP_INTERVAL = 0.5      # 双击间隔时间（秒）
SPEED_BOOST_MULTIPLIER = 4.0   # 速度提升倍率
QT_REPEAT_WAIT_TIME = 0.15     # Qt repeat 检测等待时间
```

### 动画帧率

动画帧率可在 `config/settings.py` 中调整：

```python
ANIM_STAY_FPS = 4    # 静止动画帧率（越小越慢）
ANIM_LEFT_FPS = 10   # 向左动画帧率
ANIM_RIGHT_FPS = 10  # 向右动画帧率
```

### 鼠标跟随参数

鼠标跟随参数可在 `features/mouse_follow/follow_handler.py` 中调整：

```python
self.lerp_factor = 0.15     # 平滑跟随系数
self.max_speed = 15         # 最大移动速度
self.stop_threshold = 30     # 停止距离阈值
```

## 自定义精灵图

如需更换角色外观，替换 `assets/` 目录下的图片：

| 目录 | 文件名 | 用途 |
|------|--------|------|
| `stay/` | `stay-1.png` ~ `stay-4.png` | 静止待机动画 |
| `left/` | `left-1.png` ~ `left-4.png` | 向左移动动画 |
| `right/` | `right-1.png` ~ `right-4.png` | 向右移动动画 |

**图片要求**：
- 格式：PNG（支持透明背景）
- 建议尺寸一致（如 64x64）

## 技术栈

- **PyQt6** - GUI 框架，实现透明窗口
- **screeninfo** - 获取屏幕尺寸
- **Python 3.8+** - 运行环境

## 打包发布

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包为单个 exe
pyinstaller --onefile --windowed --name PixelPet --add-data "assets;assets" --collect-all screeninfo main.py
```

打包后的文件在 `dist/PixelPet.exe`。

## License

MIT License
