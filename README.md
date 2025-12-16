# DeepFocus - 人脸识别与定位系统

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-development-orange.svg)

**基于深度学习的智能人脸识别与定位系统**

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [开发文档](#开发文档)

</div>

---

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [开发文档](#开发文档)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 项目简介

DeepFocus 是一个面向数字图像处理课程设计的人脸识别与定位应用，旨在从复杂场景（如教室环境）中精确识别并定位目标人脸。系统采用深度学习技术，能够克服光照变化、姿态变化、表情变化等挑战，提供准确可靠的人脸识别能力。

### 应用场景

- 📸 **教室场景识别**：从多人教室照片中定位特定学生
- 🎯 **目标人脸搜索**：在大图中快速检索目标人物
- 🔍 **人脸特征分析**：提取和比对人脸深度特征
- 📊 **批量图像处理**：一次性处理多张场景图像

### 项目特点

- ✅ **工业级精度**：基于ResNet-34的深度特征提取，LFW基准测试精度达99.38%
- ✅ **鲁棒性强**：有效应对光照、姿态、表情、遮挡等复杂情况
- ✅ **用户友好**：现代简洁的PyQt5图形界面，操作流畅
- ✅ **高性能**：多线程架构，支持大图处理不卡顿
- ✅ **可配置**：灵活的参数调节，支持HOG/CNN检测器切换

---

## 功能特性

### 核心功能

#### 1. 图像预处理与增强
- 🖼️ **自适应增强**：CLAHE限制对比度自适应直方图均衡化
- 🌈 **色彩空间转换**：智能处理RGB/BGR/灰度图像
- 📂 **中文路径支持**：完美处理包含中文的文件路径
- 🔧 **图像归一化**：自动调整图像尺寸和质量

#### 2. 目标人脸定位与提取
- 🎯 **精准检测**：自动定位目标图像中的人脸区域
- 🧹 **背景去除**：排除背景干扰，提取纯净人脸特征
- 📐 **人脸对齐**：基于关键点的人脸对齐技术
- 📊 **特征编码**：生成128维深度特征向量

#### 3. 场景全图人脸搜索
- 🔎 **多人脸检测**：在复杂场景中检测所有人脸
- 🎲 **特征匹配**：基于欧氏距离的特征相似度计算
- 📍 **精确定位**：标注目标人脸位置和置信度
- 🏷️ **结果可视化**：绘制边框和标签，直观展示识别结果

#### 4. 批量处理能力
- 📦 **批量识别**：支持一次性处理多张场景图像
- 💾 **结果保存**：自动保存识别结果图像和数据
- 📈 **统计报告**：生成识别统计信息和准确率报告

#### 5. 智能参数调节
- 🎚️ **检测器切换**：HOG（快速）/ CNN（精确）模式
- 📏 **阈值调整**：自定义特征匹配容忍度
- 🔍 **上采样控制**：调节小人脸检测灵敏度
- ⚙️ **配置保存**：参数持久化存储

---

## 技术架构

### 核心技术栈

| 技术领域 | 使用技术 | 版本要求 | 用途说明 |
|---------|---------|---------|---------|
| **编程语言** | Python | 3.9+ | 主开发语言 |
| **人脸识别** | face_recognition | latest | 基于dlib的人脸识别库 |
| **图像处理** | OpenCV | 4.5+ | 图像读取、处理、可视化 |
| **深度学习** | dlib | 19.22+ | HOG/CNN检测器、特征编码 |
| **GUI框架** | PyQt5 | 5.15+ | 图形用户界面 |
| **数值计算** | NumPy | 1.21+ | 数组操作和矩阵运算 |
| **版本控制** | Git/GitHub | - | 代码版本管理 |

### 系统架构设计

DeepFocus采用经典的MVC（Model-View-Controller）分层架构，保证代码的可维护性与扩展性。

```
┌─────────────────────────────────────────────────────────┐
│                      用户界面层 (View)                     │
│              PyQt5 主窗口 + 自定义控件                      │
└────────────────────┬────────────────────────────────────┘
                     │ 事件触发 / UI更新
┌────────────────────▼────────────────────────────────────┐
│                    控制器层 (Controller)                   │
│           业务调度 + 多线程管理 + 信号槽机制                 │
└────────────────────┬────────────────────────────────────┘
                     │ 调用核心算法
┌────────────────────▼────────────────────────────────────┐
│                     模型层 (Model)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 图像预处理   │  │ 人脸检测     │  │ 特征匹配     │     │
│  │ CLAHE增强   │→ │ HOG/CNN     │→ │ 欧氏距离     │     │
│  │ 色彩转换     │  │ 特征编码     │  │ 阈值判定     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 数据流程图

```
输入目标人脸图像 ──┐
                 │
                 ├──> [图像预处理] ──> [人脸检测] ──> [特征提取] ──> 目标特征向量
                 │
输入场景图像 ─────┤
                 │
                 └──> [图像预处理] ──> [多人脸检测] ──> [批量特征提取]
                                                              │
                                                              ▼
                                                      [特征匹配比对]
                                                              │
                                                              ▼
                                                      [结果可视化输出]
```

### 核心算法说明

#### 1. CLAHE自适应直方图均衡化
```
原理：将图像分块处理，每块独立均衡化，防止噪声放大
公式：β = (M/N) × (1 + α)
作用：增强局部对比度，改善暗部和过曝区域
```

#### 2. HOG人脸检测器
```
流程：梯度计算 → Cell统计 → Block归一化 → SVM分类
特点：对光照鲁棒，速度快，适合CPU
适用：常规场景，实时性要求高
```

#### 3. CNN深度检测器
```
架构：MMOD (Max-Margin Object Detection)
特点：精度极高，可检测侧脸和遮挡
适用：复杂场景，有GPU加速
```

#### 4. 深度度量学习
```
网络：ResNet-34残差网络
训练：三元组损失 (Triplet Loss)
输出：128维人脸特征向量
匹配：欧氏距离 < 阈值 → 同一人
```

---

## 目录结构

```
DeepFocus/
│
├── main.py                          # 🚀 应用程序入口文件
│                                    #    - 初始化应用
│                                    #    - 启动主窗口
│                                    #    - 异常捕获和日志记录
│
├── config.py                        # ⚙️ 全局配置文件
│                                    #    - 默认参数设置
│                                    #    - 路径配置
│                                    #    - 检测器模式配置
│
├── requirements.txt                 # 📦 Python依赖列表
│                                    #    - 所有第三方库及版本
│                                    #    - pip安装依赖清单
│
├── .gitignore                       # 🚫 Git忽略文件配置
│                                    #    - Python缓存文件
│                                    #    - 输出结果文件
│                                    #    - IDE配置文件
│
├── README.md                        # 📖 项目说明文档（本文件）
├── DEV_PLAN.md                      # 📋 开发计划文档
│
├── core/                            # 🧠 核心算法模块
│   ├── __init__.py                  #    模块初始化文件
│   │
│   ├── image_utils.py               # 🖼️ 图像工具函数
│   │                                #    - 图像读取（支持中文路径）
│   │                                #    - 图像缩放和裁剪
│   │                                #    - 格式转换（BGR/RGB/Gray）
│   │                                #    - 图像保存
│   │
│   ├── preprocessing.py             # 🎨 图像预处理模块
│   │                                #    - CLAHE自适应直方图均衡化
│   │                                #    - 图像增强和去噪
│   │                                #    - 色彩空间处理
│   │                                #    - 归一化操作
│   │
│   ├── face_engine.py               # 👤 人脸检测与编码引擎
│   │                                #    - FaceEngine类（核心引擎）
│   │                                #    - load_target_face() 加载目标人脸
│   │                                #    - detect_faces() 检测人脸位置
│   │                                #    - encode_faces() 提取特征向量
│   │                                #    - process_scene() 场景图处理
│   │
│   └── matcher.py                   # 🎯 特征匹配算法
│                                    #    - 欧氏距离计算
│                                    #    - 相似度评分
│                                    #    - 阈值判定逻辑
│                                    #    - 批量匹配优化
│
├── gui/                             # 🖥️ 图形界面模块
│   ├── __init__.py                  #    模块初始化文件
│   │
│   ├── main_window.py               # 🪟 主窗口界面类
│   │                                #    - MainWindow类（主窗口）
│   │                                #    - UI布局设计
│   │                                #    - 事件处理逻辑
│   │                                #    - 菜单和工具栏
│   │
│   ├── widgets.py                   # 🧩 自定义控件
│   │                                #    - ImageLabel（自适应图像显示）
│   │                                #    - ParamSlider（参数滑块）
│   │                                #    - ResultPanel（结果面板）
│   │                                #    - LogViewer（日志查看器）
│   │
│   ├── styles.qss                   # 🎨 QSS样式表
│   │                                #    - 现代简洁风格
│   │                                #    - 颜色主题定义
│   │                                #    - 控件美化样式
│   │
│   └── worker_threads.py            # 🧵 后台工作线程
│                                    #    - RecognitionWorker（识别线程）
│                                    #    - BatchProcessWorker（批处理线程）
│                                    #    - QThread信号槽管理
│                                    #    - 进度反馈机制
│
├── utils/                           # 🛠️ 工具模块
│   ├── __init__.py                  #    模块初始化文件
│   │
│   ├── logger.py                    # 📝 日志工具
│   │                                #    - 日志配置和初始化
│   │                                #    - 多级别日志输出
│   │                                #    - 文件和控制台双输出
│   │
│   └── file_handler.py              # 📁 文件操作工具
│                                    #    - 文件路径处理
│                                    #    - 批量文件读取
│                                    #    - 结果导出功能
│
├── tests/                           # 🧪 测试模块
│   ├── __init__.py                  #    测试模块初始化
│   │
│   ├── test_face_engine.py          # 🧪 人脸引擎单元测试
│   │                                #    - 人脸检测测试
│   │                                #    - 特征编码测试
│   │                                #    - 匹配准确率测试
│   │
│   └── test_preprocessing.py        # 🧪 预处理模块测试
│                                    #    - CLAHE效果测试
│                                    #    - 中文路径测试
│                                    #    - 格式转换测试
│
├── Images/                          # 📸 测试图像资源
│   ├── 目标脸.jpg                    #    目标人脸照片
│   ├── Image-1.jpg                  #    场景测试图1
│   ├── Image-2.jpg                  #    场景测试图2
│   ├── Image-3.jpg                  #    场景测试图3
│   ├── Image-4.jpg                  #    场景测试图4
│   ├── Image-5.jpg                  #    场景测试图5
│   ├── Image-6.jpg                  #    场景测试图6
│   ├── Image-7.jpg                  #    场景测试图7
│   ├── Image-8.jpg                  #    场景测试图8
│   └── 结果示例.jpg                  #    识别结果示例
│
├── outputs/                         # 💾 输出结果目录
│   ├── results/                     #    识别结果图像保存
│   │   ├── Image-1_result.jpg       #    标注后的结果图
│   │   └── ...
│   │
│   └── logs/                        #    运行日志文件
│       ├── app.log                  #    应用日志
│       └── error.log                #    错误日志
│
├── docs/                            # 📚 项目文档
│   ├── API.md                       #    API接口文档
│   ├── TUTORIAL.md                  #    使用教程
│   └── ALGORITHM.md                 #    算法原理说明
│
└── Reference/                       # 📖 参考资料
    └── 技术实现深度思路.md            #    技术实现参考文档
```

### 关键文件说明

#### 📂 core/ - 核心算法模块

**face_engine.py** - 人脸识别引擎核心
```python
class FaceEngine:
    """人脸检测与识别核心引擎"""
    
    def __init__(self, model_method='hog', tolerance=0.45):
        """初始化引擎，配置检测模式和匹配阈值"""
        
    def load_target_face(self, image_path: str) -> bool:
        """加载目标人脸并提取特征"""
        
    def process_scene(self, scene_path: str, upsample: int = 1):
        """处理场景图，返回识别结果"""
```

**preprocessing.py** - 图像预处理
```python
def apply_clahe(image: np.ndarray) -> np.ndarray:
    """应用CLAHE增强"""
    
def safe_imread(file_path: str) -> np.ndarray:
    """安全读取图像（支持中文路径）"""
```

#### 📂 gui/ - 界面模块

**main_window.py** - 主窗口
```python
class MainWindow(QMainWindow):
    """应用主窗口类"""
    
    def __init__(self):
        """初始化界面和引擎"""
        
    def load_target(self):
        """加载目标人脸"""
        
    def process_image(self):
        """处理场景图像"""
```

**worker_threads.py** - 多线程
```python
class RecognitionWorker(QThread):
    """识别任务工作线程"""
    
    update_signal = pyqtSignal(np.ndarray, str)
    
    def run(self):
        """在后台执行识别任务"""
```

---

## 快速开始

### 环境要求

- **操作系统**：Windows 10/11、macOS 10.15+、Ubuntu 18.04+
- **Python版本**：Python 3.9 或更高版本
- **内存**：建议 8GB 以上
- **硬盘空间**：至少 2GB 可用空间
- **显卡**（可选）：支持CUDA的NVIDIA显卡可加速CNN检测

### 安装步骤

#### 1. 克隆项目

```bash
# 使用HTTPS
git clone https://github.com/xiaowenhao404/DeepFocus.git

# 或使用SSH
git clone git@github.com:xiaowenhao404/DeepFocus.git

# 进入项目目录
cd DeepFocus
```

#### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. 安装依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 注意：dlib在Windows上安装可能需要预编译wheel
# 可以从 https://github.com/z-mahmud22/Dlib_Windows_Python3.x 下载
```

#### 4. 运行应用

```bash
# 启动图形界面
python main.py
```

### 快速测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_face_engine.py -v
```

---

## 使用指南

### 基本操作流程

#### 1️⃣ 加载目标人脸

1. 点击 **"加载目标人脸"** 按钮
2. 在文件选择对话框中选择目标人物的照片
3. 系统自动检测人脸并提取特征
4. 状态栏显示 "目标加载成功" 提示

**提示**：目标图片中人脸应清晰可见，建议使用正面照片

#### 2️⃣ 选择场景图像

1. 点击 **"加载场景图像"** 按钮
2. 选择需要搜索的场景图片（支持单张或批量）
3. 系统开始在后台处理（不会卡顿界面）

#### 3️⃣ 调整识别参数（可选）

**检测器模式**：
- **HOG模式**：速度快，适合CPU，适用于常规场景
- **CNN模式**：精度高，需要GPU，适用于复杂场景

**匹配阈值（Tolerance）**：
- 范围：0.30 ~ 0.80
- 默认：0.45（推荐用于亚洲人脸）
- 越小越严格，越大越宽松

**上采样次数**：
- 0：不上采样，速度最快
- 1：标准模式（默认）
- 2：检测小人脸，适合教室场景

#### 4️⃣ 查看识别结果

- 图像显示区域显示标注后的结果
- 绿色边框：匹配到的目标人脸
- 红色边框：检测到的其他人脸
- 边框标签显示匹配距离或"Unknown"

#### 5️⃣ 保存结果

1. 点击 **"保存结果"** 按钮
2. 结果图像自动保存到 `outputs/results/` 目录
3. 同时生成识别报告（JSON格式）

### 批量处理模式

```python
# 在代码中使用批量处理
from core.face_engine import FaceEngine

engine = FaceEngine()
engine.load_target_face("Images/目标脸.jpg")

scene_images = [
    "Images/Image-1.jpg",
    "Images/Image-2.jpg",
    # ... 更多场景图
]

for scene_path in scene_images:
    result_img, info = engine.process_scene(scene_path, upsample=2)
    # 处理结果...
```

### 参数优化建议

#### 针对不同场景的参数组合

| 场景类型 | 检测器 | 阈值 | 上采样 | 说明 |
|---------|-------|------|-------|------|
| 近距离清晰照片 | HOG | 0.45 | 1 | 标准配置 |
| 教室多人远景 | HOG | 0.40 | 2 | 提高召回率 |
| 复杂光照/侧脸 | CNN | 0.50 | 1 | 提高鲁棒性 |
| 低分辨率图像 | CNN | 0.55 | 2 | 放宽匹配条件 |
| 追求速度 | HOG | 0.45 | 0 | 最快模式 |

---

## 开发文档

### 模块接口说明

#### FaceEngine 核心接口

```python
class FaceEngine:
    """人脸识别引擎核心类"""
    
    def __init__(self, model_method: str = 'hog', tolerance: float = 0.45):
        """
        初始化人脸引擎
        
        参数:
            model_method: 检测模式 'hog' 或 'cnn'
            tolerance: 匹配阈值，默认0.45
        """
        
    def load_target_face(self, image_path: str) -> bool:
        """
        加载并编码目标人脸
        
        参数:
            image_path: 目标图片路径
            
        返回:
            bool: 成功返回True，失败返回False
        """
        
    def process_scene(self, scene_path: str, upsample: int = 1) -> Tuple[np.ndarray, str]:
        """
        处理场景图像，搜索目标人脸
        
        参数:
            scene_path: 场景图片路径
            upsample: 上采样次数（0-2）
            
        返回:
            tuple: (标注后的图像, 结果信息字符串)
        """
```

#### 图像预处理接口

```python
def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    """
    应用CLAHE自适应直方图均衡化
    
    参数:
        image: 输入图像（BGR或灰度）
        clip_limit: 对比度限制阈值
        tile_size: 分块大小
        
    返回:
        增强后的图像
    """

def safe_imread(file_path: str) -> Optional[np.ndarray]:
    """
    安全读取图像（支持中文路径）
    
    参数:
        file_path: 文件路径
        
    返回:
        图像数组，失败返回None
    """
```

### 扩展开发指南

#### 添加新的检测算法

1. 在 `core/face_engine.py` 中添加新的检测方法
2. 实现统一的接口：`detect_faces(image) -> List[Tuple]`
3. 在配置文件中注册新算法
4. 更新GUI的检测器选择下拉框

#### 添加自定义特征匹配

1. 在 `core/matcher.py` 中实现新的匹配算法
2. 继承 `BaseMatcher` 基类
3. 实现 `compare(feat1, feat2) -> float` 方法

#### 自定义界面主题

编辑 `gui/styles.qss` 文件：

```css
/* 主窗口背景 */
QMainWindow {
    background-color: #f5f5f5;
}

/* 按钮样式 */
QPushButton {
    background-color: #007aff;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
}

QPushButton:hover {
    background-color: #0051d5;
}
```

### 性能优化建议

#### 1. 图像预缩放

对于超大图像（>4000px），先缩小再处理：

```python
# 缩小到合适的尺寸
max_dimension = 1920
if max(image.shape[:2]) > max_dimension:
    scale = max_dimension / max(image.shape[:2])
    image = cv2.resize(image, None, fx=scale, fy=scale)
```

#### 2. 批量处理优化

使用多进程并行处理：

```python
from multiprocessing import Pool

def process_batch(scene_paths: List[str]):
    with Pool(processes=4) as pool:
        results = pool.map(engine.process_scene, scene_paths)
    return results
```

#### 3. GPU加速

安装GPU版本的dlib：

```bash
# 需要CUDA和cuDNN
pip install dlib-cuda
```

---

## 常见问题

### Q1: 安装dlib失败怎么办？

**A**: Windows用户可以下载预编译的wheel文件：
```bash
# 从以下地址下载对应Python版本的whl文件
# https://github.com/z-mahmud22/Dlib_Windows_Python3.x
pip install dlib-19.22.99-cp39-cp39-win_amd64.whl
```

### Q2: 为什么检测不到小人脸？

**A**: 增加上采样次数：
- 将 `number_of_times_to_upsample` 参数设置为 2
- 或者在GUI中调整"上采样"滑块

### Q3: 如何处理中文路径？

**A**: 使用项目提供的 `safe_imread` 函数：
```python
from core.image_utils import safe_imread
image = safe_imread("包含中文的路径/图片.jpg")
```

### Q4: 识别速度太慢怎么办？

**A**: 优化建议：
1. 使用HOG模式代替CNN
2. 减少上采样次数
3. 预先缩小大图
4. 使用GPU加速（如果有NVIDIA显卡）

### Q5: 误识率太高怎么办？

**A**: 调整匹配阈值：
- 降低tolerance值（例如从0.45降到0.40）
- 使用更清晰的目标人脸照片
- 确保目标照片是正面照

### Q6: 如何提高识别准确率？

**A**: 
1. 使用高质量的目标人脸照片
2. 针对亚洲人脸调整阈值（0.40-0.45）
3. 对场景图像进行CLAHE预处理
4. 使用CNN检测器（如果有GPU）

---

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 贡献流程

1. **Fork** 本仓库到你的GitHub账号
2. **Clone** 你的Fork到本地
3. 创建新分支：`git checkout -b feature/your-feature`
4. 提交更改：`git commit -m "Add your feature"`
5. 推送分支：`git push origin feature/your-feature`
6. 创建 **Pull Request**

### 代码规范

- 遵循 **PEP 8** 编码规范
- 使用 **Type Hints** 类型注解
- 编写清晰的 **docstring** 文档
- 添加必要的 **单元测试**
- 提交前运行 `black` 格式化代码

### 提交信息规范

```
类型: 简短描述

详细说明（可选）

关联Issue: #123
```

类型包括：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链更新

---

## 开发计划

详细的开发计划请查看 [DEV_PLAN.md](DEV_PLAN.md)

### 版本路线图

- **v1.0** (MVP) - 核心识别功能 + 基础界面
- **v2.0** (增强) - 批量处理 + 参数调节 + 结果保存
- **v3.0** (优化) - 性能优化 + 配置持久化 + 完善文档

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

```
MIT License

Copyright (c) 2025 DeepFocus Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 致谢

- 感谢 [face_recognition](https://github.com/ageitgey/face_recognition) 提供的优秀人脸识别库
- 感谢 [dlib](http://dlib.net/) 提供的深度学习模型
- 感谢所有贡献者和使用者的支持

---

## 联系方式

- **项目主页**: https://github.com/xiaowenhao404/DeepFocus
- **问题反馈**: https://github.com/xiaowenhao404/DeepFocus/issues
- **技术讨论**: https://github.com/xiaowenhao404/DeepFocus/discussions

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个Star！⭐**

Made with ❤️ for Digital Image Processing Course

</div>

