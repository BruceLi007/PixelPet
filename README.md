# PixelPet - 像素桌面宠物

一个轻量级的 Windows 桌面宠物程序，在桌面上显示一个可自由移动的像素风格小人。

## 功能特点

- **透明窗口** - 覆盖整个桌面，背景完全透明，仅显示宠物
- **8方向移动** - 支持上下左右四个方向，以及四个斜向方向
- **帧动画** - 流畅的走路动画效果
- **穿墙循环** - 从屏幕一侧移出会从另一侧进入
- **面向保持** - 上下移动时保持之前的左右面向方向

## 操作方式

| 按键 | 功能 |
|------|------|
| ↑ / W | 向上移动 |
| ↓ / S | 向下移动 |
| ← / A | 向左移动 |
| → / D | 向右移动 |
| ESC | 退出程序 |

## 快速开始

### 方式一：直接运行 exe

下载 `dist/PixelPet.exe` 并双击运行。

### 方式二：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/BruceLi007/PixelPet.git
cd PixelPet

# 2. 创建虚拟环境（推荐）
python -m venv venv
.\venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py
```

## 项目结构

```
PixelPet/
├── main.py                 # 程序入口
├── config/
│   └── settings.py        # 配置文件
├── models/
│   └── pixel_pet.py       # 像素宠物模型
├── views/
│   └── main_window.py     # 主窗口视图
├── controllers/
│   ├── input_handler.py   # 键盘输入处理
│   └── game_loop.py       # 游戏循环逻辑
├── assets/                # 精灵图资源
│   ├── stay/             # 静止动画（4帧）
│   ├── left/              # 向左动画（4帧）
│   └── right/             # 向右动画（4帧）
└── requirements.txt       # 依赖清单
```

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

## 自定义精灵图

如需更换角色外观，替换 `assets/` 目录下的图片：

| 目录 | 文件名 | 用途 |
|------|--------|------|
| `stay/` | `stay-1.png` ~ `stay-4.png` | 静止待机动画 |
| `left/` | `left-1.png` ~ `left-4.png` | 向左移动动画 |
| `right/` | `right-1.png` ~ `right-4.png` | 向右移动动画 |

**图片要求**：
- 格式：PNG（支持透明背景）
- 尺寸：建议保持一致（如 32x32、64x64）

## License

MIT License
