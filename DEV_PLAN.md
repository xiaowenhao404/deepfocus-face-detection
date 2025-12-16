# DeepFocus 开发计划文档

<div align="center">

**人脸识别与定位系统 - 详细开发任务清单**

版本管理 | 任务追踪 | AI 提示词库

</div>

---

## 📋 目录

- [版本规划概览](#版本规划概览)
- [开发规范](#开发规范)
- [任务状态说明](#任务状态说明)
- [Version 1.0 - MVP 最小可行产品](#version-10---mvp最小可行产品)
- [Version 2.0 - 功能增强版](#version-20---功能增强版)
- [Version 3.0 - 高级优化版](#version-30---高级优化版)
- [附录：技术参考](#附录技术参考)

---

## 版本规划概览

| 版本    | 目标             | 核心功能            | 预计工作量 | 状态      |
| ------- | ---------------- | ------------------- | ---------- | --------- |
| **1.0** | MVP 最小可行产品 | 核心识别 + 基础 GUI | 5-7 天     | 🟡 计划中 |
| **2.0** | 功能增强版       | 批量处理 + 参数调节 | 3-4 天     | ⚪ 未开始 |
| **3.0** | 高级优化版       | 性能优化 + 完善文档 | 2-3 天     | ⚪ 未开始 |

**任务编号规则**：

- TASK001-TASK006: 1.0 版本
- TASK007-TASK012: 2.0 版本
- TASK013-TASK018: 3.0 版本

---

## 开发规范

### 代码规范

- ✅ 遵循 PEP 8 编码规范
- ✅ 使用 Type Hints 类型注解
- ✅ 编写完整的 docstring 文档
- ✅ 函数名使用 snake_case
- ✅ 类名使用 PascalCase

### Git 工作流

```
main (主分支，稳定版本)
  ↑
dev (开发分支)
  ↑
feature/task-xxx (功能分支)
```

### 提交规范

```bash
# 功能开发
git commit -m "feat(task001): 创建项目基础结构"

# Bug修复
git commit -m "fix(task002): 修复中文路径读取问题"

# 文档更新
git commit -m "docs: 更新API文档"
```

---

## 任务状态说明

| 状态图标 | 状态名称       | 说明               |
| -------- | -------------- | ------------------ |
| 🟡       | 计划中         | 任务已规划，待开始 |
| 🔵       | 测试单元编写中 | 正在编写单元测试   |
| 🟢       | 开发中         | 正在开发实现       |
| ✅       | 已完成         | 开发和测试完成     |
| ⚪       | 未开始         | 尚未启动           |

---

# Version 1.0 - MVP 最小可行产品

**版本目标**：实现核心人脸识别功能，构建基础 GUI 界面，能够完成单张图像的识别任务。

**核心功能**：

- ✅ 项目基础架构搭建
- ✅ 核心人脸识别引擎
- ✅ 图像预处理模块
- ✅ 基础 PyQt5 界面
- ✅ 多线程支持
- ✅ 结果可视化

---

## TASK001: 项目基础架构搭建

**版本**: 1.0  
**状态**: 🟡 计划中  
**优先级**: ⭐⭐⭐⭐⭐ (最高)  
**预计时间**: 1-2 小时

### 任务描述

创建完整的项目目录结构，配置开发环境，初始化 Git 仓库，设置依赖管理。

### 子任务清单

#### 子任务 1.1: 创建目录结构

- [ ] 创建 core/、gui/、utils/、tests/目录
- [ ] 创建所有`__init__.py`文件
- [ ] 创建 outputs/results/和 outputs/logs/输出目录
- [ ] 创建 docs/文档目录

#### 子任务 1.2: 配置依赖文件

- [ ] 创建 requirements.txt 并列出所有依赖
- [ ] 创建 config.py 全局配置文件
- [ ] 创建.gitignore 文件

#### 子任务 1.3: 初始化 Git 仓库

- [ ] 初始化本地 Git 仓库
- [ ] 配置远程仓库（GitHub）
- [ ] 创建 dev 开发分支

#### 子任务 1.4: 创建主入口文件

- [ ] 创建 main.py 应用入口
- [ ] 添加基础异常捕获
- [ ] 添加日志初始化

### AI 提示词

```
作为Python开发专家，请帮我完成DeepFocus项目的基础架构搭建。

**任务目标**：
创建完整的项目目录结构，配置开发环境，确保项目能够正常启动。

**具体要求**：

1. **创建目录结构**：
   - 按照README.md中的目录树创建所有必要的文件夹
   - 为每个Python包创建__init__.py文件
   - 创建outputs/results/和outputs/logs/目录用于存储输出

2. **编写requirements.txt**：
```

face-recognition>=1.3.0
opencv-python>=4.5.0
PyQt5>=5.15.0
numpy>=1.21.0
dlib>=19.22.0

```

3. **创建config.py配置文件**：
- DEFAULT_MODEL_METHOD = 'hog'
- DEFAULT_TOLERANCE = 0.45
- DEFAULT_UPSAMPLE = 1
- IMAGES_DIR = 'Images/'
- OUTPUTS_DIR = 'outputs/results/'
- LOGS_DIR = 'outputs/logs/'

4. **编写.gitignore**：
- Python缓存文件 (__pycache__, *.pyc)
- 虚拟环境 (venv/, .venv/)
- 输出文件 (outputs/)
- IDE配置 (.vscode/, .idea/)
- 系统文件 (.DS_Store, Thumbs.db)

5. **创建main.py入口文件**：
- 包含基础的异常捕获
- 添加日志初始化
- 预留GUI启动代码位置

**注意事项**：
- 确保所有目录都有合适的README或说明
- config.py应该包含详细的注释
- .gitignore要考虑Windows系统的特殊文件
- main.py应该包含if __name__ == "__main__":入口

**验收标准**：
- 目录结构完整，符合README.md规划
- requirements.txt包含所有必要依赖
- config.py配置项齐全且有注释
- .gitignore覆盖常见不需要提交的文件
- main.py能够正常运行（即使还没有实际功能）
```

### 验收标准

- [ ] 所有目录和文件按照规划创建完成
- [ ] requirements.txt 包含所有必要依赖
- [ ] config.py 配置完整且有详细注释
- [ ] .gitignore 正确配置
- [ ] Git 仓库初始化并连接到远程
- [ ] main.py 能够正常执行（无语法错误）
- [ ] 运行`python main.py`不报错

### 注意事项

⚠️ **关键注意点**：

1. **中文路径问题**：Windows 系统下项目路径避免包含中文
2. **依赖版本**：dlib 在 Windows 上安装需要预编译 wheel
3. **Git 配置**：PowerShell 编码设置为 UTF-8 避免中文乱码
4. **目录权限**：确保 outputs 目录有写入权限

📌 **技术难点**：

- dlib 安装：Windows 用户需要从 GitHub 下载预编译版本
- PowerShell 编码：`$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding`

---

## TASK002: 核心人脸识别引擎开发

**版本**: 1.0  
**状态**: 🟡 计划中  
**优先级**: ⭐⭐⭐⭐⭐ (最高)  
**预计时间**: 4-6 小时

### 任务描述

开发核心人脸识别引擎，实现人脸检测、特征提取、特征匹配等核心功能。

### 子任务清单

#### 子任务 2.1: 创建 FaceEngine 类框架

- [ ] 定义 FaceEngine 类结构
- [ ] 实现**init**初始化方法
- [ ] 定义类属性（model_method, tolerance, target_encoding）

#### 子任务 2.2: 实现目标人脸加载

- [ ] 实现 load_target_face()方法
- [ ] 支持中文路径读取
- [ ] 自动选择最大人脸作为目标
- [ ] 提取并保存目标特征向量

#### 子任务 2.3: 实现场景图处理

- [ ] 实现 process_scene()方法
- [ ] 检测场景中所有人脸
- [ ] 批量提取特征向量
- [ ] 与目标特征进行匹配

#### 子任务 2.4: 实现结果可视化

- [ ] 绘制人脸检测框
- [ ] 标注匹配结果（绿色/红色）
- [ ] 显示匹配距离
- [ ] 生成结果信息字符串

### AI 提示词

````
作为计算机视觉专家，请帮我开发DeepFocus项目的核心人脸识别引擎。

**任务目标**：
创建core/face_engine.py文件，实现FaceEngine类，提供人脸检测、特征提取和匹配功能。

**具体要求**：

1. **类结构设计**：
```python
import face_recognition
import cv2
import numpy as np
from typing import Tuple, Optional, List

class FaceEngine:
    """人脸识别引擎核心类"""

    def __init__(self, model_method: str = 'hog', tolerance: float = 0.45):
        """
        初始化人脸引擎

        Args:
            model_method: 检测方法 'hog' 或 'cnn'
            tolerance: 匹配容忍度，默认0.45适合亚洲人脸
        """
        self.model_method = model_method
        self.tolerance = tolerance
        self.target_encoding = None

    def load_target_face(self, image_path: str) -> bool:
        """加载并编码目标人脸"""
        # TODO: 实现

    def process_scene(self, scene_path: str, upsample: int = 1) -> Tuple[np.ndarray, str]:
        """处理场景图像，搜索目标人脸"""
        # TODO: 实现
````

2. **load_target_face 实现要点**：

   - 使用 np.fromfile + cv2.imdecode 处理中文路径
   - BGR 转 RGB（face_recognition 需要 RGB 格式）
   - 调用 face_recognition.face_locations 检测人脸
   - 如果检测到多个人脸，选择面积最大的
   - 调用 face_recognition.face_encodings 提取特征
   - 保存特征向量到 self.target_encoding
   - 返回 True/False 表示成功/失败

3. **process_scene 实现要点**：

   - 检查 self.target_encoding 是否已加载
   - 读取场景图像（支持中文路径）
   - 使用 face_locations 检测所有人脸（注意 upsample 参数）
   - 使用 face_encodings 批量提取特征
   - 遍历每个人脸，计算与目标的欧氏距离
   - 绘制检测框（匹配的用绿色，其他用红色）
   - 添加标签文字
   - 返回标注后的图像和统计信息

4. **关键技术细节**：
   - 人脸坐标格式：(top, right, bottom, left)
   - face_distance 返回的是距离数组，距离<tolerance 表示匹配
   - 绘图使用 cv2.rectangle 和 cv2.putText
   - 注意 cv2 使用 BGR 格式，face_recognition 使用 RGB

**代码模板**：

```python
def load_target_face(self, image_path: str) -> bool:
    # 1. 读取图像（中文路径支持）
    img_data = np.fromfile(image_path, dtype=np.uint8)
    img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
    if img is None:
        return False

    # 2. BGR转RGB
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 3. 检测人脸
    boxes = face_recognition.face_locations(rgb_img, model=self.model_method)
    if not boxes:
        return False

    # 4. 选择最大人脸
    boxes.sort(key=lambda x: (x[2]-x[0]) * (x[1]-x[3]), reverse=True)
    target_box = boxes[0]

    # 5. 提取特征
    encodings = face_recognition.face_encodings(rgb_img, [target_box])
    if not encodings:
        return False

    self.target_encoding = encodings[0]
    return True
```

**验收标准**：

- FaceEngine 类结构完整，类型注解齐全
- load_target_face 能够正确加载并编码目标人脸
- process_scene 能够检测场景中所有人脸并正确匹配
- 支持中文路径
- 代码有完整的 docstring 文档
- 能够处理异常情况（文件不存在、无人脸等）

**注意事项**：

- face_recognition 使用 RGB，cv2 使用 BGR，需要转换
- 亚洲人脸建议 tolerance=0.40-0.45
- 教室场景建议 upsample=2 以检测小人脸
- 注意内存管理，大图可能占用大量内存

```

### 验收标准

- [ ] FaceEngine类完整实现
- [ ] load_target_face方法正常工作
- [ ] process_scene方法正常工作
- [ ] 支持中文路径读取
- [ ] 正确处理RGB/BGR转换
- [ ] 能够检测并匹配人脸
- [ ] 结果可视化正确（绿色/红色框）
- [ ] 代码有完整的类型注解和docstring
- [ ] 能够处理边界情况（无人脸、文件不存在等）

### 注意事项

⚠️ **关键注意点**：
1. **色彩空间转换**：face_recognition要求RGB，OpenCV默认BGR
2. **人脸坐标格式**：(top, right, bottom, left) 不是常见的(x,y,w,h)
3. **内存管理**：大图处理时注意内存占用
4. **阈值调优**：亚洲人脸推荐tolerance=0.40-0.45

📌 **技术难点**：
- 中文路径：使用`np.fromfile` + `cv2.imdecode`组合
- 小人脸检测：`number_of_times_to_upsample=2`
- 特征距离：使用`face_recognition.face_distance`计算欧氏距离

---

## TASK003: 图像预处理模块开发

**版本**: 1.0
**状态**: 🟡 计划中
**优先级**: ⭐⭐⭐⭐ (高)
**预计时间**: 2-3小时

### 任务描述
开发图像预处理模块，实现CLAHE增强、色彩空间转换、安全读取等功能。

### 子任务清单

#### 子任务3.1: 实现CLAHE增强
- [ ] 实现apply_clahe()函数
- [ ] 支持灰度图和彩色图
- [ ] 可配置clip_limit和tile_size参数

#### 子任务3.2: 实现安全图像读取
- [ ] 实现safe_imread()函数
- [ ] 支持中文路径
- [ ] 错误处理和日志记录

#### 子任务3.3: 实现图像工具函数
- [ ] 实现resize_image()缩放函数
- [ ] 实现convert_color_space()转换函数
- [ ] 实现save_image()保存函数

#### 子任务3.4: 编写单元测试
- [ ] 测试CLAHE增强效果
- [ ] 测试中文路径读取
- [ ] 测试各种色彩空间转换

### AI提示词

```

作为图像处理专家，请帮我开发 DeepFocus 项目的图像预处理模块。

**任务目标**：
创建 core/preprocessing.py 和 core/image_utils.py 文件，实现图像预处理和工具函数。

**具体要求**：

1. **preprocessing.py - CLAHE 增强**：

```python
import cv2
import numpy as np
from typing import Optional

def apply_clahe(image: np.ndarray,
                clip_limit: float = 2.0,
                tile_size: int = 8) -> np.ndarray:
    """
    应用CLAHE自适应直方图均衡化

    Args:
        image: 输入图像（BGR或灰度）
        clip_limit: 对比度限制阈值，默认2.0
        tile_size: 分块大小，默认8x8

    Returns:
        增强后的图像

    原理：
        - CLAHE将图像分成若干小块（tiles）
        - 每块独立进行直方图均衡化
        - 使用clip_limit防止噪声放大
        - 适合处理光照不均的图像
    """
    # 如果是彩色图，转换到LAB空间，只增强L通道
    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=clip_limit,
                                tileGridSize=(tile_size, tile_size))
        l = clahe.apply(l)

        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        # 灰度图直接处理
        clahe = cv2.createCLAHE(clipLimit=clip_limit,
                                tileGridSize=(tile_size, tile_size))
        return clahe.apply(image)
```

2. **image_utils.py - 图像工具函数**：

```python
import cv2
import numpy as np
from typing import Optional, Tuple

def safe_imread(file_path: str) -> Optional[np.ndarray]:
    """
    安全读取图像，支持中文路径

    Args:
        file_path: 图像文件路径

    Returns:
        图像数组，失败返回None
    """
    try:
        # 使用numpy读取二进制，再用cv2解码
        img_data = np.fromfile(file_path, dtype=np.uint8)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"读取图像失败 {file_path}: {e}")
        return None

def resize_image(image: np.ndarray,
                 max_dimension: int = 1920) -> Tuple[np.ndarray, float]:
    """
    等比例缩放图像到指定最大尺寸

    Args:
        image: 输入图像
        max_dimension: 最大边长

    Returns:
        (缩放后图像, 缩放比例)
    """
    height, width = image.shape[:2]
    max_dim = max(height, width)

    if max_dim <= max_dimension:
        return image, 1.0

    scale = max_dimension / max_dim
    new_width = int(width * scale)
    new_height = int(height * scale)

    resized = cv2.resize(image, (new_width, new_height),
                        interpolation=cv2.INTER_AREA)
    return resized, scale

def convert_color_space(image: np.ndarray,
                        target: str = 'RGB') -> np.ndarray:
    """
    色彩空间转换

    Args:
        image: 输入图像（假设为BGR）
        target: 目标空间 'RGB', 'GRAY', 'HSV', 'LAB'

    Returns:
        转换后的图像
    """
    conversions = {
        'RGB': cv2.COLOR_BGR2RGB,
        'GRAY': cv2.COLOR_BGR2GRAY,
        'HSV': cv2.COLOR_BGR2HSV,
        'LAB': cv2.COLOR_BGR2LAB
    }

    if target not in conversions:
        raise ValueError(f"不支持的色彩空间: {target}")

    return cv2.cvtColor(image, conversions[target])

def save_image(image: np.ndarray, file_path: str) -> bool:
    """
    保存图像，支持中文路径

    Args:
        image: 图像数组
        file_path: 保存路径

    Returns:
        成功返回True
    """
    try:
        # 编码为图像格式
        _, img_encode = cv2.imencode('.jpg', image)
        # 写入文件
        img_encode.tofile(file_path)
        return True
    except Exception as e:
        print(f"保存图像失败 {file_path}: {e}")
        return False
```

3. **编写测试用例** (tests/test_preprocessing.py)：

```python
import unittest
import numpy as np
from core.preprocessing import apply_clahe
from core.image_utils import safe_imread, resize_image

class TestPreprocessing(unittest.TestCase):

    def test_clahe_on_color_image(self):
        """测试彩色图CLAHE增强"""
        # 创建测试图像
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        enhanced = apply_clahe(img)
        self.assertEqual(enhanced.shape, img.shape)

    def test_safe_imread_chinese_path(self):
        """测试中文路径读取"""
        img = safe_imread("Images/目标脸.jpg")
        self.assertIsNotNone(img)

    def test_resize_image(self):
        """测试图像缩放"""
        img = np.zeros((2000, 3000, 3), dtype=np.uint8)
        resized, scale = resize_image(img, max_dimension=1920)
        self.assertLessEqual(max(resized.shape[:2]), 1920)

if __name__ == '__main__':
    unittest.main()
```

**验收标准**：

- apply_clahe 正确增强图像对比度
- safe_imread 能读取中文路径
- 所有工具函数正常工作
- 单元测试全部通过
- 代码有完整文档和类型注解

**注意事项**：

- CLAHE 在 LAB 空间的 L 通道处理效果最好
- 中文路径使用 np.fromfile + cv2.imdecode 组合
- 缩放时使用 INTER_AREA 插值避免失真
- 保存时使用 imencode + tofile 支持中文路径

```

### 验收标准

- [ ] apply_clahe函数正确实现
- [ ] safe_imread支持中文路径
- [ ] resize_image正确缩放图像
- [ ] convert_color_space支持常见色彩空间
- [ ] save_image支持中文路径保存
- [ ] 单元测试覆盖主要功能
- [ ] 所有函数有类型注解和docstring
- [ ] 测试用例全部通过

### 注意事项

⚠️ **关键注意点**：
1. **CLAHE处理**：彩色图在LAB空间的L通道处理
2. **中文路径**：读取用fromfile+imdecode，保存用imencode+tofile
3. **缩放插值**：缩小用INTER_AREA，放大用INTER_CUBIC
4. **内存效率**：大图处理时注意内存占用

📌 **技术难点**：
- CLAHE参数调优：clip_limit=2.0, tile_size=8是经验值
- LAB色彩空间：L通道表示亮度，独立增强不影响色彩

---

## TASK004: 基础GUI界面开发

**版本**: 1.0
**状态**: 🟡 计划中
**优先级**: ⭐⭐⭐⭐ (高)
**预计时间**: 4-5小时

### 任务描述
使用PyQt5开发图形用户界面，实现主窗口布局、控件设计和基本交互。

### 子任务清单

#### 子任务4.1: 创建主窗口框架
- [ ] 创建MainWindow类
- [ ] 设计窗口布局（使用QVBoxLayout/QHBoxLayout）
- [ ] 设置窗口标题、图标、大小

#### 子任务4.2: 添加图像显示区域
- [ ] 创建QLabel用于显示图像
- [ ] 实现图像自适应缩放
- [ ] 支持图像切换显示

#### 子任务4.3: 添加控制按钮
- [ ] "加载目标人脸"按钮
- [ ] "加载场景图像"按钮
- [ ] "开始识别"按钮
- [ ] "保存结果"按钮

#### 子任务4.4: 添加状态栏和信息显示
- [ ] 状态栏显示操作提示
- [ ] 结果信息面板
- [ ] 日志显示区域（可选）

#### 子任务4.5: 实现基本事件处理
- [ ] 文件选择对话框
- [ ] 按钮点击事件
- [ ] 图像显示更新

### AI提示词

```

作为 PyQt5 开发专家，请帮我开发 DeepFocus 项目的图形用户界面。

**任务目标**：
创建 gui/main_window.py 文件，实现 MainWindow 类，构建现代简洁的用户界面。

**具体要求**：

1. **MainWindow 类结构**：

```python
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QStatusBar,
                             QTextEdit, QGroupBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import numpy as np
from core.face_engine import FaceEngine

class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.engine = FaceEngine()
        self.current_image = None
        self.target_loaded = False
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepFocus - 人脸识别与定位系统")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout()

        # 左侧：图像显示区域
        left_panel = self.create_image_panel()

        # 右侧：控制面板
        right_panel = self.create_control_panel()

        # 添加到主布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)  # 图像区域占3份
        splitter.setStretchFactor(1, 1)  # 控制区域占1份

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def create_image_panel(self) -> QWidget:
        """创建图像显示面板"""
        panel = QWidget()
        layout = QVBoxLayout()

        # 图像显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        self.image_label.setText("请加载图像")
        self.image_label.setMinimumSize(800, 600)

        layout.addWidget(self.image_label)
        panel.setLayout(layout)
        return panel

    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()

        # 标题
        title = QLabel("控制面板")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 操作按钮组
        btn_group = QGroupBox("操作")
        btn_layout = QVBoxLayout()

        self.btn_load_target = QPushButton("📸 加载目标人脸")
        self.btn_load_target.clicked.connect(self.load_target)
        self.btn_load_target.setMinimumHeight(40)

        self.btn_load_scene = QPushButton("🖼️ 加载场景图像")
        self.btn_load_scene.clicked.connect(self.load_scene)
        self.btn_load_scene.setMinimumHeight(40)

        self.btn_process = QPushButton("🔍 开始识别")
        self.btn_process.clicked.connect(self.process_image)
        self.btn_process.setMinimumHeight(40)
        self.btn_process.setEnabled(False)

        self.btn_save = QPushButton("💾 保存结果")
        self.btn_save.clicked.connect(self.save_result)
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setEnabled(False)

        btn_layout.addWidget(self.btn_load_target)
        btn_layout.addWidget(self.btn_load_scene)
        btn_layout.addWidget(self.btn_process)
        btn_layout.addWidget(self.btn_save)
        btn_group.setLayout(btn_layout)
        layout.addWidget(btn_group)

        # 结果信息
        info_group = QGroupBox("识别信息")
        info_layout = QVBoxLayout()

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        self.info_text.setText("等待加载图像...")

        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def load_target(self):
        """加载目标人脸"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择目标人脸图像", "Images/",
            "图像文件 (*.jpg *.jpeg *.png *.bmp)"
        )

        if file_path:
            success = self.engine.load_target_face(file_path)
            if success:
                self.target_loaded = True
                self.status_bar.showMessage(f"✅ 目标人脸加载成功: {file_path}")
                self.info_text.append(f"[成功] 目标人脸已加载\n路径: {file_path}")
                self.btn_process.setEnabled(True)
            else:
                self.status_bar.showMessage("❌ 未检测到人脸，请重新选择")
                self.info_text.append("[失败] 未在目标图像中检测到人脸")

    def load_scene(self):
        """加载场景图像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择场景图像", "Images/",
            "图像文件 (*.jpg *.jpeg *.png *.bmp)"
        )

        if file_path:
            from core.image_utils import safe_imread
            self.current_image = safe_imread(file_path)
            if self.current_image is not None:
                self.display_image(self.current_image)
                self.status_bar.showMessage(f"场景图像已加载: {file_path}")
                self.info_text.append(f"[信息] 场景图像已加载\n路径: {file_path}")

    def process_image(self):
        """处理图像（占位，后续集成多线程）"""
        self.status_bar.showMessage("🔄 处理中...")
        self.info_text.append("[信息] 开始识别处理...")
        # 实际处理逻辑在TASK005中集成

    def save_result(self):
        """保存结果"""
        if self.current_image is not None:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存结果", "outputs/results/result.jpg",
                "JPEG图像 (*.jpg);;PNG图像 (*.png)"
            )
            if file_path:
                from core.image_utils import save_image
                if save_image(self.current_image, file_path):
                    self.status_bar.showMessage(f"✅ 结果已保存: {file_path}")
                else:
                    self.status_bar.showMessage("❌ 保存失败")

    def display_image(self, cv_img: np.ndarray):
        """在界面上显示图像"""
        # BGR转RGB
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        bytes_per_line = ch * w

        # 转换为QImage
        q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # 缩放到合适大小
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(scaled_pixmap)
```

2. **样式美化** (gui/styles.qss)：

```css
/* 现代简洁风格 */
QMainWindow {
  background-color: #ffffff;
}

QPushButton {
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: bold;
}

QPushButton:hover {
  background-color: #0051d5;
}

QPushButton:pressed {
  background-color: #003d99;
}

QPushButton:disabled {
  background-color: #cccccc;
  color: #888888;
}

QGroupBox {
  font-weight: bold;
  border: 2px solid #d0d0d0;
  border-radius: 8px;
  margin-top: 10px;
  padding: 10px;
}

QGroupBox::title {
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 5px;
}

QTextEdit {
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  background-color: #f9f9f9;
  font-family: Consolas, monospace;
  font-size: 12px;
}

QStatusBar {
  background-color: #f0f0f0;
  color: #333333;
}
```

3. **在 main.py 中集成**：

```python
import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 加载样式表
    try:
        with open('gui/styles.qss', 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

**验收标准**：

- 主窗口正常显示，布局合理
- 所有按钮和控件正常显示
- 文件选择对话框工作正常
- 图像能够正确显示在界面上
- 状态栏正常显示消息
- 界面风格现代简洁

**注意事项**：

- QImage 需要 RGB 格式，OpenCV 是 BGR 需要转换
- 使用 QSplitter 实现可调整大小的布局
- 按钮状态管理（enabled/disabled）提升用户体验
- 使用 QFileDialog 选择文件，支持中文路径

```

### 验收标准

- [ ] MainWindow类完整实现
- [ ] 界面布局合理美观
- [ ] 图像显示功能正常
- [ ] 按钮和事件处理正常
- [ ] 文件选择对话框工作
- [ ] 状态栏显示正确
- [ ] 样式表加载正确
- [ ] main.py能够启动GUI
- [ ] 界面响应流畅

### 注意事项

⚠️ **关键注意点**：
1. **色彩转换**：OpenCV BGR → PyQt5 RGB
2. **图像缩放**：使用Qt.KeepAspectRatio保持比例
3. **内存管理**：QImage需要保持数据引用
4. **线程安全**：GUI更新必须在主线程

📌 **技术难点**：
- QImage构造：需要正确的格式和步长（bytes_per_line）
- 布局管理：使用QSplitter实现灵活布局
- 样式表：QSS语法类似CSS但有差异

---

## TASK005: 多线程集成

**版本**: 1.0
**状态**: 🟡 计划中
**优先级**: ⭐⭐⭐⭐ (高)
**预计时间**: 3-4小时

### 任务描述
集成QThread多线程机制，防止GUI在处理大图时卡顿，实现流畅的用户体验。

### 子任务清单

#### 子任务5.1: 创建工作线程类
- [ ] 创建RecognitionWorker类继承QThread
- [ ] 定义信号（update_signal, progress_signal, error_signal）
- [ ] 实现run()方法执行识别任务

#### 子任务5.2: 集成进度反馈
- [ ] 添加进度条控件
- [ ] 发送处理进度信号
- [ ] 更新状态栏显示

#### 子任务5.3: 错误处理
- [ ] 捕获线程中的异常
- [ ] 通过信号传递错误信息
- [ ] 在主线程显示错误对话框

#### 子任务5.4: 在主窗口集成线程
- [ ] 修改process_image方法启动线程
- [ ] 连接信号与槽函数
- [ ] 线程完成后更新UI

### AI提示词

```

作为 PyQt5 多线程专家，请帮我为 DeepFocus 项目集成多线程支持。

**任务目标**：
创建 gui/worker_threads.py 文件，实现 RecognitionWorker 线程类，防止 GUI 卡顿。

**具体要求**：

1. **RecognitionWorker 类实现**：

```python
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from core.face_engine import FaceEngine

class RecognitionWorker(QThread):
    """人脸识别工作线程"""

    # 定义信号
    update_signal = pyqtSignal(np.ndarray, str)  # (结果图像, 信息文本)
    progress_signal = pyqtSignal(int)  # 进度百分比
    error_signal = pyqtSignal(str)  # 错误消息

    def __init__(self, engine: FaceEngine, scene_path: str, upsample: int = 1):
        """
        初始化工作线程

        Args:
            engine: 人脸引擎实例
            scene_path: 场景图像路径
            upsample: 上采样次数
        """
        super().__init__()
        self.engine = engine
        self.scene_path = scene_path
        self.upsample = upsample

    def run(self):
        """在后台线程执行识别任务"""
        try:
            # 发送开始进度
            self.progress_signal.emit(10)

            # 执行识别
            result_img, info = self.engine.process_scene(
                self.scene_path,
                upsample=self.upsample
            )

            # 发送完成进度
            self.progress_signal.emit(100)

            # 发送结果
            self.update_signal.emit(result_img, info)

        except Exception as e:
            # 发送错误信号
            self.error_signal.emit(f"识别失败: {str(e)}")
```

2. **批处理线程类**：

```python
class BatchProcessWorker(QThread):
    """批量处理工作线程"""

    update_signal = pyqtSignal(int, str, np.ndarray)  # (索引, 文件名, 结果图像)
    progress_signal = pyqtSignal(int, int)  # (当前, 总数)
    finished_signal = pyqtSignal(list)  # 所有结果
    error_signal = pyqtSignal(str)

    def __init__(self, engine: FaceEngine, scene_paths: list, upsample: int = 1):
        super().__init__()
        self.engine = engine
        self.scene_paths = scene_paths
        self.upsample = upsample

    def run(self):
        """批量处理多个场景图"""
        results = []
        total = len(self.scene_paths)

        try:
            for i, scene_path in enumerate(self.scene_paths):
                # 处理单张图像
                result_img, info = self.engine.process_scene(
                    scene_path,
                    upsample=self.upsample
                )

                # 保存结果
                results.append({
                    'path': scene_path,
                    'image': result_img,
                    'info': info
                })

                # 发送进度
                self.progress_signal.emit(i + 1, total)
                self.update_signal.emit(i, scene_path, result_img)

            # 发送完成信号
            self.finished_signal.emit(results)

        except Exception as e:
            self.error_signal.emit(f"批处理失败: {str(e)}")
```

3. **在 MainWindow 中集成线程**：

```python
# 在MainWindow类中添加

def process_image(self):
    """处理图像（使用多线程）"""
    if not self.target_loaded:
        self.status_bar.showMessage("⚠️ 请先加载目标人脸")
        return

    if self.current_image is None:
        self.status_bar.showMessage("⚠️ 请先加载场景图像")
        return

    # 禁用按钮防止重复点击
    self.btn_process.setEnabled(False)
    self.status_bar.showMessage("🔄 正在识别中，请稍候...")

    # 创建并启动工作线程
    self.worker = RecognitionWorker(
        self.engine,
        self.current_scene_path,
        upsample=2  # 教室场景使用upsample=2
    )

    # 连接信号
    self.worker.update_signal.connect(self.on_recognition_complete)
    self.worker.error_signal.connect(self.on_recognition_error)
    self.worker.progress_signal.connect(self.on_progress_update)

    # 启动线程
    self.worker.start()

def on_recognition_complete(self, result_img: np.ndarray, info: str):
    """识别完成回调"""
    self.current_image = result_img
    self.display_image(result_img)
    self.info_text.append(f"\n[结果] {info}")
    self.status_bar.showMessage("✅ 识别完成")

    # 恢复按钮状态
    self.btn_process.setEnabled(True)
    self.btn_save.setEnabled(True)

def on_recognition_error(self, error_msg: str):
    """识别错误回调"""
    self.info_text.append(f"\n[错误] {error_msg}")
    self.status_bar.showMessage(f"❌ {error_msg}")
    self.btn_process.setEnabled(True)

def on_progress_update(self, progress: int):
    """进度更新回调"""
    # 可以在这里更新进度条
    pass
```

4. **添加进度条（可选）**：

```python
from PyQt5.QtWidgets import QProgressBar

# 在create_control_panel中添加
self.progress_bar = QProgressBar()
self.progress_bar.setVisible(False)
layout.addWidget(self.progress_bar)

# 在on_progress_update中
def on_progress_update(self, progress: int):
    self.progress_bar.setVisible(True)
    self.progress_bar.setValue(progress)
    if progress >= 100:
        self.progress_bar.setVisible(False)
```

**验收标准**：

- RecognitionWorker 类正确实现
- 信号槽机制正常工作
- GUI 在处理时不卡顿
- 进度反馈正常显示
- 错误能被正确捕获和显示
- 线程完成后 UI 正确更新

**注意事项**：

- 只能在主线程更新 GUI，使用信号槽传递数据
- 工作线程不要直接持有 GUI 对象的引用
- 注意线程的生命周期管理，防止内存泄漏
- 多次点击按钮要防止创建多个线程

```

### 验收标准

- [ ] RecognitionWorker类正确实现
- [ ] BatchProcessWorker类正确实现
- [ ] 信号和槽正确连接
- [ ] GUI在处理时不卡顿
- [ ] 进度反馈正常工作
- [ ] 错误处理机制完善
- [ ] 线程完成后UI正确更新
- [ ] 没有内存泄漏

### 注意事项

⚠️ **关键注意点**：
1. **线程安全**：GUI更新只能在主线程，使用信号槽通信
2. **生命周期**：避免线程对象被过早销毁
3. **状态管理**：禁用按钮防止重复操作
4. **异常处理**：线程中的异常要通过信号传递

📌 **技术难点**：
- PyQt信号必须在类定义时声明，不能动态创建
- numpy数组通过信号传递时要注意引用计数
- QThread要在线程完成后正确清理

---

## TASK006: 特征匹配与结果显示完善

**版本**: 1.0
**状态**: 🟡 计划中
**优先级**: ⭐⭐⭐ (中)
**预计时间**: 2-3小时

### 任务描述
完善特征匹配算法，优化结果可视化，完成1.0版本的最后收尾工作。

### 子任务清单

#### 子任务6.1: 完善matcher.py
- [ ] 实现欧氏距离计算函数
- [ ] 实现批量匹配优化
- [ ] 添加相似度评分函数

#### 子任务6.2: 优化结果可视化
- [ ] 优化检测框绘制（颜色、粗细）
- [ ] 优化标签文字（字体、大小、位置）
- [ ] 添加匹配置信度显示

#### 子任务6.3: 集成测试
- [ ] 使用提供的8张测试图测试
- [ ] 验证识别准确率
- [ ] 调优参数（tolerance, upsample）

#### 子任务6.4: 文档和清理
- [ ] 更新README使用说明
- [ ] 清理调试代码
- [ ] 准备1.0版本发布

### AI提示词

```

作为项目收尾专家，请帮我完善 DeepFocus 项目的 1.0 版本。

**任务目标**：
完善 matcher.py 模块，优化结果显示，进行全面测试，准备 1.0 版本发布。

**具体要求**：

1. **matcher.py 实现**：

```python
import numpy as np
from typing import List, Tuple

def euclidean_distance(feat1: np.ndarray, feat2: np.ndarray) -> float:
    """
    计算两个特征向量的欧氏距离

    Args:
        feat1: 特征向量1 (128维)
        feat2: 特征向量2 (128维)

    Returns:
        欧氏距离
    """
    return np.linalg.norm(feat1 - feat2)

def batch_compare(target_encoding: np.ndarray,
                  face_encodings: List[np.ndarray],
                  tolerance: float = 0.45) -> List[Tuple[bool, float]]:
    """
    批量比对特征

    Args:
        target_encoding: 目标特征向量
        face_encodings: 待比对的特征向量列表
        tolerance: 匹配阈值

    Returns:
        [(是否匹配, 距离), ...] 列表
    """
    results = []
    for encoding in face_encodings:
        distance = euclidean_distance(target_encoding, encoding)
        is_match = distance <= tolerance
        results.append((is_match, distance))
    return results

def compute_confidence(distance: float, tolerance: float = 0.45) -> float:
    """
    将距离转换为置信度百分比

    Args:
        distance: 欧氏距离
        tolerance: 阈值

    Returns:
        置信度 (0-100)
    """
    if distance >= tolerance:
        return 0.0
    # 距离越小，置信度越高
    confidence = (1 - distance / tolerance) * 100
    return min(100.0, max(0.0, confidence))
```

2. **优化 face_engine.py 中的结果可视化**：

```python
def process_scene(self, scene_path: str, upsample: int = 1) -> Tuple[np.ndarray, str]:
    """处理场景图像（优化版）"""
    if self.target_encoding is None:
        raise ValueError("请先加载目标人脸！")

    from core.image_utils import safe_imread
    scene_img = safe_imread(scene_path)
    if scene_img is None:
        raise ValueError(f"无法读取图像: {scene_path}")

    rgb_scene = cv2.cvtColor(scene_img, cv2.COLOR_BGR2RGB)

    # 检测人脸
    scene_boxes = face_recognition.face_locations(
        rgb_scene,
        number_of_times_to_upsample=upsample,
        model=self.model_method
    )

    # 提取特征
    scene_encodings = face_recognition.face_encodings(rgb_scene, scene_boxes)

    match_count = 0
    min_distance = 1.0
    best_match_box = None

    # 遍历比对
    for (top, right, bottom, left), face_encoding in zip(scene_boxes, scene_encodings):
        distance = face_recognition.face_distance([self.target_encoding], face_encoding)[0]
        is_match = distance <= self.tolerance

        if is_match:
            match_count += 1
            if distance < min_distance:
                min_distance = distance
                best_match_box = (top, right, bottom, left)

            # 匹配的人脸：绿色粗框
            color = (0, 255, 0)
            thickness = 3

            # 计算置信度
            from core.matcher import compute_confidence
            confidence = compute_confidence(distance, self.tolerance)
            label = f"Target {confidence:.1f}%"
        else:
            # 非匹配：红色细框
            color = (0, 0, 255)
            thickness = 1
            label = "Unknown"

        # 绘制矩形框
        cv2.rectangle(scene_img, (left, top), (right, bottom), color, thickness)

        # 绘制标签背景
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.6, 1)[0]
        cv2.rectangle(
            scene_img,
            (left, bottom - label_size[1] - 10),
            (right, bottom),
            color,
            cv2.FILLED
        )

        # 绘制标签文字
        cv2.putText(
            scene_img,
            label,
            (left + 6, bottom - 6),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1
        )

    # 生成结果信息
    result_info = (
        f"检测到人脸: {len(scene_boxes)} 个 | "
        f"匹配目标: {match_count} 个 | "
        f"最佳匹配距离: {min_distance:.3f}"
    )

    return scene_img, result_info
```

3. **测试脚本** (test_integration.py)：

```python
"""集成测试脚本"""
import os
from core.face_engine import FaceEngine
from core.image_utils import save_image

def test_all_scenes():
    """测试所有场景图"""
    engine = FaceEngine(model_method='hog', tolerance=0.45)

    # 加载目标人脸
    target_path = "Images/目标脸.jpg"
    print(f"加载目标人脸: {target_path}")
    success = engine.load_target_face(target_path)
    if not success:
        print("❌ 目标人脸加载失败")
        return
    print("✅ 目标人脸加载成功\n")

    # 处理所有场景图
    for i in range(1, 9):
        scene_path = f"Images/Image-{i}.jpg"
        print(f"处理场景图 {i}: {scene_path}")

        try:
            result_img, info = engine.process_scene(scene_path, upsample=2)
            print(f"   {info}")

            # 保存结果
            output_path = f"outputs/results/Image-{i}_result.jpg"
            save_image(result_img, output_path)
            print(f"   ✅ 结果已保存: {output_path}\n")

        except Exception as e:
            print(f"   ❌ 处理失败: {e}\n")

if __name__ == "__main__":
    # 确保输出目录存在
    os.makedirs("outputs/results", exist_ok=True)
    test_all_scenes()
```

**验收标准**：

- matcher.py 完整实现
- 结果可视化美观清晰
- 所有 8 张测试图都能正确处理
- 识别准确率达到预期
- 测试脚本运行正常
- 1.0 版本功能完整

**注意事项**：

- 标签文字位置要避免超出图像边界
- 置信度计算要合理
- 测试时记录各图的识别结果
- 根据测试结果调优 tolerance 和 upsample 参数

```

### 验收标准

- [ ] matcher.py模块完整实现
- [ ] 结果可视化优化完成
- [ ] 置信度计算正确
- [ ] 所有8张测试图测试通过
- [ ] 识别准确率符合预期
- [ ] 测试脚本正常运行
- [ ] 文档更新完成
- [ ] 1.0版本准备就绪

### 注意事项

⚠️ **关键注意点**：
1. **标签位置**：确保文字不超出图像边界
2. **颜色选择**：绿色表示匹配，红色表示未匹配
3. **参数调优**：根据测试结果调整tolerance
4. **性能测试**：记录处理时间和内存占用

📌 **测试重点**：
- 每张图的识别结果准确性
- 小人脸检测效果（使用upsample=2）
- 不同光照条件下的鲁棒性
- 侧脸和遮挡情况的处理

---

# Version 2.0 - 功能增强版

**版本目标**：增强用户体验，添加批量处理、参数调节、结果保存等高级功能。

**核心功能**：
- ✅ 批量图像处理
- ✅ 检测器模式切换（HOG/CNN）
- ✅ 参数实时调节
- ✅ 结果保存和导出
- ✅ 界面美化增强
- ✅ 识别统计报告

---

## TASK007: 批量处理功能

**版本**: 2.0
**状态**: ⚪ 未开始
**优先级**: ⭐⭐⭐⭐ (高)
**预计时间**: 3-4小时

### 任务描述
实现批量处理多张场景图像的功能，提升处理效率。

### 子任务清单

#### 子任务7.1: 多文件选择
- [ ] 支持多选文件对话框
- [ ] 文件列表显示
- [ ] 文件管理（添加、删除）

#### 子任务7.2: 批处理逻辑
- [ ] 实现批量处理循环
- [ ] 进度追踪和显示
- [ ] 结果批量保存

#### 子任务7.3: 结果预览
- [ ] 添加结果列表视图
- [ ] 支持结果切换查看
- [ ] 缩略图显示

### AI提示词

```

作为批处理系统专家，请帮我为 DeepFocus 添加批量处理功能。

**任务目标**：
增强 GUI 支持多文件选择和批量处理，使用 BatchProcessWorker 线程类。

**具体要求**：

1. **在 MainWindow 添加批处理 UI**：

```python
# 在create_control_panel中添加

self.btn_batch_load = QPushButton("📁 批量加载")
self.btn_batch_load.clicked.connect(self.batch_load_scenes)

self.btn_batch_process = QPushButton("⚡ 批量处理")
self.btn_batch_process.clicked.connect(self.batch_process)
self.btn_batch_process.setEnabled(False)

# 文件列表
self.file_list = QListWidget()
self.file_list.setMaximumHeight(150)

def batch_load_scenes(self):
    """批量加载场景图像"""
    file_paths, _ = QFileDialog.getOpenFileNames(
        self, "批量选择场景图像", "Images/",
        "图像文件 (*.jpg *.jpeg *.png *.bmp)"
    )

    if file_paths:
        self.scene_paths = file_paths
        self.file_list.clear()
        for path in file_paths:
            filename = os.path.basename(path)
            self.file_list.addItem(filename)

        self.btn_batch_process.setEnabled(True)
        self.status_bar.showMessage(f"已加载 {len(file_paths)} 张图像")

def batch_process(self):
    """批量处理"""
    if not self.target_loaded:
        self.status_bar.showMessage("⚠️ 请先加载目标人脸")
        return

    self.btn_batch_process.setEnabled(False)

    # 创建批处理线程
    self.batch_worker = BatchProcessWorker(
        self.engine,
        self.scene_paths,
        upsample=2
    )

    self.batch_worker.update_signal.connect(self.on_batch_update)
    self.batch_worker.progress_signal.connect(self.on_batch_progress)
    self.batch_worker.finished_signal.connect(self.on_batch_finished)
    self.batch_worker.error_signal.connect(self.on_recognition_error)

    self.batch_worker.start()

def on_batch_update(self, index: int, filename: str, result_img: np.ndarray):
    """单张处理完成"""
    self.info_text.append(f"[{index+1}] {filename} 处理完成")

def on_batch_progress(self, current: int, total: int):
    """批处理进度"""
    self.status_bar.showMessage(f"🔄 批量处理中... ({current}/{total})")
    # 更新进度条
    if hasattr(self, 'progress_bar'):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(current / total * 100))

def on_batch_finished(self, results: list):
    """批处理完成"""
    self.status_bar.showMessage(f"✅ 批量处理完成！共处理 {len(results)} 张图像")
    self.info_text.append(f"\n[完成] 批量处理成功，共 {len(results)} 张图像")

    # 自动保存所有结果
    from core.image_utils import save_image
    for i, result in enumerate(results):
        filename = os.path.basename(result['path'])
        output_path = f"outputs/results/{filename}"
        save_image(result['image'], output_path)

    self.btn_batch_process.setEnabled(True)
    if hasattr(self, 'progress_bar'):
        self.progress_bar.setVisible(False)
```

2. **添加结果浏览功能**：

```python
# 添加结果列表和预览
self.result_list = QListWidget()
self.result_list.itemClicked.connect(self.on_result_selected)

def on_result_selected(self, item):
    """选择结果项进行预览"""
    filename = item.text()
    result_path = f"outputs/results/{filename}"
    from core.image_utils import safe_imread
    img = safe_imread(result_path)
    if img is not None:
        self.display_image(img)
```

**验收标准**：

- 支持多文件选择
- 批量处理正常工作
- 进度显示准确
- 结果自动保存
- 可以浏览历史结果

**注意事项**：

- 批处理时要显示清晰的进度
- 内存管理：不要同时加载所有大图到内存
- 错误处理：单张失败不影响其他图像

```

### 验收标准

- [ ] 多文件选择功能实现
- [ ] 批量处理逻辑正确
- [ ] 进度显示准确
- [ ] 结果自动保存
- [ ] 结果浏览功能正常
- [ ] 内存管理合理
- [ ] 错误处理完善

### 注意事项

⚠️ **关键注意点**：
1. **内存管理**：不要同时加载所有大图
2. **进度反馈**：清晰显示当前处理进度
3. **错误恢复**：单张失败继续处理其他
4. **结果组织**：合理命名保存的结果文件

---

## TASK008: 参数调节功能

**版本**: 2.0
**状态**: ⚪ 未开始
**优先级**: ⭐⭐⭐ (中)
**预计时间**: 2-3小时

### 任务描述
添加GUI控件允许用户调节检测参数，实时查看效果。

### 子任务清单

#### 子任务8.1: 添加参数控件
- [ ] 阈值滑块（tolerance）
- [ ] 上采样滑块（upsample）
- [ ] 检测器切换按钮（HOG/CNN）

#### 子任务8.2: 参数实时更新
- [ ] 参数改变时更新引擎配置
- [ ] 显示当前参数值
- [ ] 参数预设快捷按钮

#### 子任务8.3: 参数说明
- [ ] 添加工具提示
- [ ] 参数说明文档
- [ ] 推荐值标注

### AI提示词

```

作为 UI/UX 专家，请帮我为 DeepFocus 添加参数调节功能。

**任务目标**：
在 GUI 中添加滑块和按钮，允许用户调节检测参数并实时生效。

**具体要求**：

1. **在 control_panel 中添加参数组**：

```python
# 创建参数设置组
param_group = QGroupBox("参数设置")
param_layout = QVBoxLayout()

# 阈值滑块
tolerance_layout = QHBoxLayout()
tolerance_label = QLabel("匹配阈值:")
self.tolerance_slider = QSlider(Qt.Horizontal)
self.tolerance_slider.setMinimum(30)  # 0.30
self.tolerance_slider.setMaximum(80)  # 0.80
self.tolerance_slider.setValue(45)     # 0.45
self.tolerance_slider.setTickPosition(QSlider.TicksBelow)
self.tolerance_slider.setTickInterval(5)
self.tolerance_slider.valueChanged.connect(self.on_tolerance_changed)

self.tolerance_value_label = QLabel("0.45")
self.tolerance_value_label.setMinimumWidth(40)

tolerance_layout.addWidget(tolerance_label)
tolerance_layout.addWidget(self.tolerance_slider)
tolerance_layout.addWidget(self.tolerance_value_label)
param_layout.addLayout(tolerance_layout)

# 上采样滑块
upsample_layout = QHBoxLayout()
upsample_label = QLabel("上采样:")
self.upsample_slider = QSlider(Qt.Horizontal)
self.upsample_slider.setMinimum(0)
self.upsample_slider.setMaximum(2)
self.upsample_slider.setValue(1)
self.upsample_slider.setTickPosition(QSlider.TicksBelow)
self.upsample_slider.setTickInterval(1)
self.upsample_slider.valueChanged.connect(self.on_upsample_changed)

self.upsample_value_label = QLabel("1")
self.upsample_value_label.setMinimumWidth(40)

upsample_layout.addWidget(upsample_label)
upsample_layout.addWidget(self.upsample_slider)
upsample_layout.addWidget(self.upsample_value_label)
param_layout.addLayout(upsample_layout)

# 检测器模式切换
model_layout = QHBoxLayout()
model_label = QLabel("检测器:")
self.model_combo = QComboBox()
self.model_combo.addItems(["HOG (快速)", "CNN (精确)"])
self.model_combo.currentIndexChanged.connect(self.on_model_changed)
model_layout.addWidget(model_label)
model_layout.addWidget(self.model_combo)
param_layout.addLayout(model_layout)

# 参数预设按钮
preset_layout = QHBoxLayout()
preset_label = QLabel("预设:")
btn_preset_fast = QPushButton("快速")
btn_preset_balanced = QPushButton("平衡")
btn_preset_accurate = QPushButton("精确")

btn_preset_fast.clicked.connect(lambda: self.apply_preset('fast'))
btn_preset_balanced.clicked.connect(lambda: self.apply_preset('balanced'))
btn_preset_accurate.clicked.connect(lambda: self.apply_preset('accurate'))

preset_layout.addWidget(preset_label)
preset_layout.addWidget(btn_preset_fast)
preset_layout.addWidget(btn_preset_balanced)
preset_layout.addWidget(btn_preset_accurate)
param_layout.addLayout(preset_layout)

param_group.setLayout(param_layout)
layout.addWidget(param_group)

def on_tolerance_changed(self, value: int):
    """阈值改变"""
    tolerance = value / 100.0
    self.tolerance_value_label.setText(f"{tolerance:.2f}")
    self.engine.tolerance = tolerance
    self.info_text.append(f"[参数] 阈值已设置为 {tolerance:.2f}")

def on_upsample_changed(self, value: int):
    """上采样改变"""
    self.upsample_value_label.setText(str(value))
    self.current_upsample = value
    self.info_text.append(f"[参数] 上采样已设置为 {value}")

def on_model_changed(self, index: int):
    """检测器模式改变"""
    model = 'hog' if index == 0 else 'cnn'
    self.engine.model_method = model
    model_name = "HOG" if index == 0 else "CNN"
    self.info_text.append(f"[参数] 检测器已切换为 {model_name}")

def apply_preset(self, preset: str):
    """应用参数预设"""
    presets = {
        'fast': {
            'tolerance': 0.45,
            'upsample': 0,
            'model': 'hog'
        },
        'balanced': {
            'tolerance': 0.45,
            'upsample': 1,
            'model': 'hog'
        },
        'accurate': {
            'tolerance': 0.40,
            'upsample': 2,
            'model': 'hog'
        }
    }

    params = presets[preset]
    self.tolerance_slider.setValue(int(params['tolerance'] * 100))
    self.upsample_slider.setValue(params['upsample'])
    model_index = 0 if params['model'] == 'hog' else 1
    self.model_combo.setCurrentIndex(model_index)

    self.info_text.append(f"[预设] 已应用 {preset.upper()} 模式")
```

2. **添加工具提示**：

```python
self.tolerance_slider.setToolTip(
    "匹配阈值 (0.30-0.80)\n"
    "值越小越严格，越大越宽松\n"
    "推荐: 0.40-0.45 (亚洲人脸)"
)

self.upsample_slider.setToolTip(
    "上采样次数 (0-2)\n"
    "0: 不上采样，速度最快\n"
    "1: 标准模式\n"
    "2: 检测小人脸，适合教室场景"
)

self.model_combo.setToolTip(
    "检测器模式\n"
    "HOG: 速度快，适合CPU\n"
    "CNN: 精度高，需要GPU加速"
)
```

**验收标准**：

- 所有参数控件正常工作
- 参数改变实时生效
- 工具提示清晰有用
- 预设功能正常
- 界面布局合理

**注意事项**：

- 参数范围要合理限制
- 提供清晰的参数说明
- 预设值要经过测试验证
- CNN 模式提示需要 GPU

````

### 验收标准

- [ ] 阈值滑块正常工作
- [ ] 上采样滑块正常工作
- [ ] 检测器切换功能正常
- [ ] 参数实时更新生效
- [ ] 预设功能正常
- [ ] 工具提示清晰有用
- [ ] 界面布局合理美观

### 注意事项

⚠️ **关键注意点**：
1. **参数范围**：tolerance建议0.30-0.80
2. **用户提示**：清晰说明每个参数的作用
3. **预设验证**：预设值要经过实际测试
4. **GPU检测**：CNN模式提示是否有GPU

---

## TASK009-TASK012

由于篇幅限制，TASK009-TASK012（结果保存增强、界面美化、统计报告、2.0版本测试）的详细内容请在实际开发时参考TASK001-TASK008的格式补充。

---

# Version 3.0 - 高级优化版

**版本目标**：性能优化、配置持久化、完善文档和测试。

**核心功能**：
- ✅ 配置持久化（JSON）
- ✅ 性能优化（大图处理）
- ✅ 日志系统完善
- ✅ 单元测试补充
- ✅ API文档完善
- ✅ 用户手册编写

---

## TASK013-TASK018

TASK013: 配置持久化
TASK014: 性能优化
TASK015: 日志系统完善
TASK016: 单元测试补充
TASK017: 文档完善
TASK018: 3.0版本发布准备

（详细内容参考前述任务格式）

---

# 附录：技术参考

## 常用命令

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行应用
python main.py

# 运行测试
python -m pytest tests/ -v

# 代码格式化
black . --line-length 88

# 类型检查
mypy core/ gui/

# 生成文档
pdoc --html core gui -o docs/
````

## 关键技术要点

### 1. 中文路径处理

```python
# 读取
img_data = np.fromfile(path, dtype=np.uint8)
img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)

# 保存
_, img_encode = cv2.imencode('.jpg', img)
img_encode.tofile(path)
```

### 2. 色彩空间转换

```python
# OpenCV (BGR) → face_recognition (RGB)
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

# RGB → PyQt5 QImage
q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
```

### 3. 小人脸检测

```python
# 使用上采样
boxes = face_recognition.face_locations(
    image,
    number_of_times_to_upsample=2,  # 关键参数
    model='hog'
)
```

### 4. PyQt5 线程安全

```python
# 定义信号
update_signal = pyqtSignal(np.ndarray, str)

# 在线程中发射信号
self.update_signal.emit(result, info)

# 在主线程连接槽函数
worker.update_signal.connect(self.on_complete)
```

## 常见问题解决

### Q1: dlib 安装失败

```bash
# Windows: 下载预编译wheel
# https://github.com/z-mahmud22/Dlib_Windows_Python3.x
pip install dlib-19.22.99-cp39-cp39-win_amd64.whl
```

### Q2: 中文路径乱码

```python
# 使用np.fromfile + cv2.imdecode组合
```

### Q3: GUI 卡顿

```python
# 使用QThread处理耗时操作
# 不要在主线程直接调用处理函数
```

### Q4: 内存占用高

```python
# 大图先缩放再处理
if max(img.shape[:2]) > 1920:
    scale = 1920 / max(img.shape[:2])
    img = cv2.resize(img, None, fx=scale, fy=scale)
```

---

## 开发进度追踪

### 1.0 版本

- [ ] TASK001: 项目基础架构 (2 小时)
- [ ] TASK002: 核心引擎开发 (6 小时)
- [ ] TASK003: 预处理模块 (3 小时)
- [ ] TASK004: GUI 界面 (5 小时)
- [ ] TASK005: 多线程集成 (4 小时)
- [ ] TASK006: 结果优化 (3 小时)

**预计总时间**: 5-7 天

### 2.0 版本

- [ ] TASK007: 批量处理 (4 小时)
- [ ] TASK008: 参数调节 (3 小时)
- [ ] TASK009: 结果保存 (2 小时)
- [ ] TASK010: 界面美化 (3 小时)
- [ ] TASK011: 统计报告 (2 小时)
- [ ] TASK012: 测试验收 (2 小时)

**预计总时间**: 3-4 天

### 3.0 版本

- [ ] TASK013: 配置持久化 (2 小时)
- [ ] TASK014: 性能优化 (3 小时)
- [ ] TASK015: 日志系统 (2 小时)
- [ ] TASK016: 单元测试 (3 小时)
- [ ] TASK017: 文档完善 (2 小时)
- [ ] TASK018: 发布准备 (2 小时)

**预计总时间**: 2-3 天

---

<div align="center">

**📝 持续更新中...**

项目进度请查看 GitHub: https://github.com/xiaowenhao404/DeepFocus

</div>
