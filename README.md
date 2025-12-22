# DeepFocus Pro v3.0 - 智能人脸定位系统（最终版）

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)
![Version](https://img.shields.io/badge/version-3.0-orange.svg)

**基于深度学习的智能人脸识别与定位系统**

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [技术架构](#技术架构)

</div>

---

## 📋 项目简介

DeepFocus Pro 是一个面向数字图像处理课程设计的人脸识别与定位应用，能够从复杂场景（如教室环境）中精确识别并定位目标人脸。系统采用多种深度学习技术，提供准确可靠的人脸识别能力。

### 应用场景

- 📸 **教室场景识别**：从多人教室照片中定位特定学生
- 🎯 **目标人脸搜索**：在大图中快速检索目标人物
- 📊 **批量图像处理**：一次性处理多张场景图像
- 📄 **识别报告导出**：生成美观的HTML识别报告

### 项目特点

- ✅ **多引擎支持**：HOG快速检测、CNN高精度检测、YuNet轻量级检测
- ✅ **GPU加速**：CNN模式支持CUDA加速
- ✅ **现代界面**：macOS风格的PyQt5图形界面
- ✅ **可视化处理**：查看完整的图像处理过程
- ✅ **模型对比**：同时对比多个模型的识别效果
- ✅ **HTML报告**：导出美观的识别结果报告

---

## 功能特性

### 三大识别引擎

| 引擎 | 检测器 | 识别器 | 特点 | 适用场景 |
|------|--------|--------|------|----------|
| **HOG** | HOG+SVM | dlib 128D | 速度快，CPU友好 | 正脸、近距离 |
| **CNN** | MMOD CNN | dlib 128D | 精度高，支持GPU | 侧脸、遮挡 |
| **YuNet** | YuNet | SFace | 轻量高效，侧脸好 | 复杂场景、小脸 |

### 核心功能

1. **图像预处理**
   - CLAHE自适应直方图均衡化
   - Gamma校正调节亮度
   - 智能中文路径支持

2. **人脸检测与识别**
   - 多人脸同时检测
   - 128维深度特征提取
   - 可调阈值匹配

3. **结果展示**
   - 边框标注（绿色匹配/红色未匹配）
   - 相似度百分比显示
   - 按住对比原图功能

4. **批量处理**
   - 多图批量导入识别
   - 一键重新识别
   - 总耗时统计

5. **报告导出**
   - HTML格式识别报告
   - 图表可视化统计
   - 完整参数记录

---

## 目录结构

```
DeepFocus/
├── main_pro.py              # 🚀 程序入口
├── config.py                # ⚙️ 配置文件
├── requirements.txt         # 📦 依赖清单
├── README.md                # 📖 说明文档
│
├── core/                    # 🧠 核心算法
│   ├── face_engine_pro.py   # HOG/CNN人脸引擎
│   ├── opencv_dnn_engine.py # YuNet/SFace引擎
│   ├── preprocessing.py     # 图像预处理
│   ├── matcher.py           # 特征匹配
│   └── gpu_utils.py         # GPU工具
│
├── gui/                     # 🖥️ 图形界面
│   ├── main_window_pro.py   # 主窗口
│   ├── visualization_dialog.py # 可视化对话框
│   ├── compare_dialog.py    # 模型对比对话框
│   ├── report_generator.py  # HTML报告生成
│   ├── zoomable_label.py    # 缩放图像组件
│   ├── image_drop_label.py  # 拖放图像组件
│   ├── modern.qss           # 现代风格样式
│   └── macos.qss            # macOS风格样式
│
├── models/                  # 🤖 模型文件
│   ├── face_detection_yunet_2023mar.onnx
│   ├── face_recognition_sface_2021dec.onnx
│   ├── download_models.py   # 模型下载脚本
│   └── README.md
│
├── Images/                  # 📸 测试图像
├── outputs/                 # 💾 输出结果
│   ├── results/             # 识别结果图像
│   └── logs/                # 运行日志
│
└── utils/                   # 🛠️ 工具模块
```

---

## 快速开始

### 环境要求

- **Python**: 3.9+
- **操作系统**: Windows 10/11、macOS、Linux
- **内存**: 8GB+
- **GPU**（可选）: NVIDIA显卡（CUDA支持）

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/xiaowenhao404/DeepFocus.git
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
pip install -r requirements.txt
```

> **注意**: Windows上安装dlib可能需要Visual Studio Build Tools，或使用预编译wheel

#### 4. 下载模型（YuNet引擎需要）

```bash
python models/download_models.py
```

#### 5. 运行程序

```bash
python main_pro.py
```

---

## 使用指南

### 基本流程

1. **加载目标人脸** → 点击"选择目标"或"添加目标"
2. **选择检测模型** → HOG（快速）/ CNN（精确）/ YuNet（轻量）
3. **调整参数** → 阈值、上采样、CLAHE、Gamma
4. **加载场景** → 单张或批量导入
5. **开始识别** → 点击"识别场景"或"一键识别"
6. **查看结果** → 按住图片对比原图，翻页查看多张结果
7. **导出报告** → 生成HTML格式识别报告

### 参数说明

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| 阈值 | 0.30~0.70 | 0.45 | 越小越严格 |
| 上采样 | 0~2 | 1 | 越大检测小脸越好，但更慢 |
| CLAHE | 开/关 | 开 | 增强对比度 |
| Gamma | 0.5~1.5 | 1.0 | <1变暗，>1变亮 |
| 仅显示最佳 | 开/关 | 关 | 只标注最佳匹配 |

### 模型选择建议

| 场景 | 推荐模型 | 阈值 | 上采样 |
|------|----------|------|--------|
| 近距离正脸 | HOG | 0.45 | 1 |
| 远距离多人 | HOG | 0.40 | 2 |
| 侧脸/遮挡 | CNN | 0.50 | 1 |
| 轻量快速 | YuNet | 0.40 | - |

---

## 技术架构

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                      用户界面层                          │
│              PyQt5 主窗口 + macOS风格                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    控制器层                              │
│           多线程管理 + 信号槽机制                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                     引擎层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ HOG Engine  │  │ CNN Engine  │  │YuNet Engine │     │
│  │ (dlib)      │  │ (dlib+CUDA) │  │(OpenCV DNN) │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 核心技术

| 技术 | 用途 | 说明 |
|------|------|------|
| dlib | HOG/CNN检测 | 基于深度学习的人脸检测 |
| face_recognition | 特征编码 | 128维人脸特征向量 |
| OpenCV DNN | YuNet/SFace | ONNX模型推理 |
| PyQt5 | GUI框架 | 跨平台图形界面 |
| jinja2 | 报告生成 | HTML模板渲染 |

### 相似度计算

- **HOG/CNN**: 欧氏距离 → 相似度百分比
- **YuNet**: 余弦相似度 → 相似度百分比

统一显示为0-100%相似度，便于横向比较。

---

## 常见问题

### Q1: 安装dlib失败？
**A**: Windows用户可下载预编译wheel：
```bash
# 从 https://github.com/z-mahmud22/Dlib_Windows_Python3.x 下载
pip install dlib-19.22.99-cp39-cp39-win_amd64.whl
```

### Q2: YuNet模型找不到？
**A**: 运行模型下载脚本：
```bash
python models/download_models.py
```

### Q3: 检测不到小人脸？
**A**: 增加上采样次数到2，或使用YuNet引擎。

### Q4: 识别速度慢？
**A**: 
- 使用HOG代替CNN
- 减少上采样次数
- 使用YuNet（最快）

### Q5: 误识率高？
**A**: 降低阈值（如0.40），使用更清晰的目标照片。

---

## 许可证

本项目采用 MIT 许可证。

---

## 致谢

- [face_recognition](https://github.com/ageitgey/face_recognition)
- [dlib](http://dlib.net/)
- [OpenCV](https://opencv.org/)

---

<div align="center">

**DeepFocus Pro v3.0 最终版**

Made with ❤️ for Digital Image Processing Course

</div>
