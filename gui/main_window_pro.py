"""
DeepFocus Pro v3.0 最终版主窗口模块

整合FaceEnginePro、macOS风格界面、可缩放图像、批量处理、可视化等功能
v3.0最终版：GPU状态显示、性能统计、CNN参数优化、YuNet引擎、模型对比
"""

import sys
import os
import cv2
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QGroupBox, QSlider,
    QProgressBar, QMessageBox, QCheckBox, QFrame, QRadioButton,
    QButtonGroup, QStatusBar, QSizePolicy, QSpacerItem, QToolTip,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QFile, QTextStream
from PyQt5.QtGui import QImage, QPixmap, QColor
import logging

# ==================== 安全导入 dlib 相关模块 ====================
# dlib 可能因为 CUDA 问题而无法导入

_DLIB_AVAILABLE = False
_DLIB_ERROR = ""
FaceEnginePro = None
get_cuda_info = None

try:
    from core.face_engine_pro import FaceEnginePro, get_cuda_info
    _DLIB_AVAILABLE = True
except RuntimeError as e:
    if "CUDA" in str(e) or "cuda" in str(e):
        _DLIB_ERROR = f"dlib CUDA 错误: {e}"
        logging.warning(_DLIB_ERROR)
    else:
        raise
except ImportError as e:
    _DLIB_ERROR = f"dlib 导入失败: {e}"
    logging.warning(_DLIB_ERROR)

def is_dlib_available() -> bool:
    return _DLIB_AVAILABLE

def get_dlib_error() -> str:
    return _DLIB_ERROR

# 如果 dlib 不可用，提供一个模拟的 get_cuda_info
if get_cuda_info is None:
    def get_cuda_info():
        return {"cuda_available": False, "gpu_info": "dlib 不可用"}

# ==================== 其他导入 ====================
from core.opencv_dnn_engine import (
    OpenCVDNNEngine, 
    is_opencv_dnn_available, 
    get_opencv_dnn_error,
    check_models_exist
)
from gui.zoomable_label import ZoomableImageLabel
from gui.image_drop_label import ImageDropLabel
from gui.visualization_dialog import VisualizationDialog
from gui.report_generator import ReportGenerator, is_report_available
from gui.compare_dialog import CompareDialog


class RecognitionWorker(QThread):
    """单图识别工作线程"""
    result_ready = pyqtSignal(object, dict, str)  # img, stats, path
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self, engine, scene_path: str, params: dict, engine_type: str = "dlib"):
        super().__init__()
        self.engine = engine
        self.scene_path = scene_path
        self.params = params
        self.engine_type = engine_type

    def run(self):
        try:
            def progress_callback(value):
                self.progress_updated.emit(value)
            
            # 根据引擎类型调用不同的处理方法
            if self.engine_type == "opencv_dnn":
                # OpenCV DNN引擎 (YuNet+SFace)
                result_img, stats = self.engine.process_scene(
                    self.scene_path,
                    tolerance=self.params['tolerance'],
                    best_only=self.params.get('best_only', False),
                    progress_callback=progress_callback
                )
            else:
                # dlib引擎 (HOG/CNN)
                result_img, stats = self.engine.process_scene(
                    self.scene_path,
                    tolerance=self.params['tolerance'],
                    upsample=self.params['upsample'],
                    model=self.params['model'],
                    use_clahe=self.params['use_clahe'],
                    gamma=self.params['gamma'],
                    best_only=self.params.get('best_only', False),
                    progress_callback=progress_callback
                )
            
            if result_img is None:
                error_msg = stats.get('error', '未知错误')
                self.error_occurred.emit(error_msg)
            else:
                self.result_ready.emit(result_img, stats, self.scene_path)
        except Exception as e:
            self.error_occurred.emit(str(e))


class BatchWorker(QThread):
    """批量识别工作线程"""
    single_result_ready = pyqtSignal(object, dict, str, int, int)  # img, stats, path, current, total
    all_finished = pyqtSignal(list, float)  # list of (img, stats, path), total_time
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)  # 总体进度 0-100

    def __init__(self, engine, scene_paths: List[str], params: dict, engine_type: str = "dlib"):
        super().__init__()
        self.engine = engine
        self.scene_paths = scene_paths
        self.params = params
        self.engine_type = engine_type

    def run(self):
        import time
        batch_start_time = time.time()  # 记录批量处理开始时间
        results = []
        total = len(self.scene_paths)
        
        for idx, path in enumerate(self.scene_paths):
            try:
                # 单图进度：在总进度的一个区间内
                base_progress = int((idx / total) * 100)
                segment = int(100 / total)
                
                def progress_callback(value):
                    overall = base_progress + int(value * segment / 100)
                    self.progress_updated.emit(min(overall, 100))
                
                # 根据引擎类型调用不同的处理方法
                if self.engine_type == "opencv_dnn":
                    result_img, stats = self.engine.process_scene(
                        path,
                        tolerance=self.params['tolerance'],
                        best_only=self.params.get('best_only', False),
                        progress_callback=progress_callback
                    )
                else:
                    result_img, stats = self.engine.process_scene(
                        path,
                        tolerance=self.params['tolerance'],
                        upsample=self.params['upsample'],
                        model=self.params['model'],
                        use_clahe=self.params['use_clahe'],
                        gamma=self.params['gamma'],
                        best_only=self.params.get('best_only', False),
                        progress_callback=progress_callback
                    )
                
                if result_img is not None:
                    results.append((result_img, stats, path))
                    self.single_result_ready.emit(result_img, stats, path, idx + 1, total)
                
            except Exception as e:
                self.error_occurred.emit(f"处理 {os.path.basename(path)} 时出错: {e}")
        
        self.progress_updated.emit(100)
        total_time = time.time() - batch_start_time  # 计算总耗时
        self.all_finished.emit(results, total_time)


class VisualizationWorker(QThread):
    """可视化处理工作线程"""
    result_ready = pyqtSignal(dict, dict)  # stages, stats
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self, engine: FaceEnginePro, scene_path: str, params: dict):
        super().__init__()
        self.engine = engine
        self.scene_path = scene_path
        self.params = params

    def run(self):
        try:
            def progress_callback(value):
                self.progress_updated.emit(value)
            
            # 可视化时始终显示所有匹配（best_only=False）
            stages, stats = self.engine.process_scene_with_stages(
                self.scene_path,
                tolerance=self.params['tolerance'],
                upsample=self.params['upsample'],
                model=self.params['model'],
                use_clahe=self.params['use_clahe'],
                gamma=self.params['gamma'],
                best_only=False,  # 可视化时显示所有匹配
                progress_callback=progress_callback
            )
            self.result_ready.emit(stages, stats)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindowPro(QMainWindow):
    """DeepFocus Pro v3.0 最终版主窗口"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 检查 dlib 是否可用
        self._dlib_available = is_dlib_available()
        if self._dlib_available:
            self.engine = FaceEnginePro()
        else:
            self.engine = None
            self.logger.warning(f"dlib 引擎不可用: {get_dlib_error()}")
        
        # v2.1: 获取GPU状态
        self._cuda_info = get_cuda_info()
        
        # v2.2: OpenCV DNN 引擎 (YuNet+SFace)
        self._opencv_dnn_available = is_opencv_dnn_available()
        self._opencv_dnn_engine = None  # 懒加载
        if not self._opencv_dnn_available:
            self.logger.warning(f"OpenCV DNN 不可用: {get_opencv_dnn_error()}")
        
        # 目标相关
        self.target_images: List[np.ndarray] = []  # 目标裁剪图列表
        self.current_target_index = 0
        
        # 场景相关
        self.scene_paths: List[str] = []  # 场景路径列表
        self.scene_results: List[tuple] = []  # [(img, stats, path), ...]
        self.current_scene_index = 0
        self.current_scene_path: Optional[str] = None
        self.current_result_image: Optional[np.ndarray] = None
        self.current_stats: Optional[Dict] = None
        self._original_scene_img: Optional[np.ndarray] = None  # 用于长按对比
        
        # 可视化缓存：避免每次查看处理过程都重新计算
        # 格式: {"path": str, "params_hash": str, "stages": dict, "stats": dict}
        self._visualization_cache: Optional[Dict] = None
        
        # 批量处理总耗时
        self._batch_total_time: float = 0.0
        
        # 工作线程
        self.worker = None
        
        # v2.1: 报告生成器
        self._report_generator = ReportGenerator()
        self._report_available = is_report_available()
        
        self.init_ui()
        self.load_stylesheet()
        
        # v2.1: 显示GPU状态
        gpu_status = "GPU可用" if self._cuda_info.get("cuda_available") else "CPU模式"
        self.logger.info(f"DeepFocus Pro v3.0 主窗口初始化完成 ({gpu_status})")

    def load_stylesheet(self):
        """加载现代化样式表"""
        # 优先使用 modern.qss，如果不存在则使用 macos.qss
        stylesheet_paths = ["gui/modern.qss", "gui/macos.qss"]
        
        for stylesheet_path in stylesheet_paths:
            if os.path.exists(stylesheet_path):
                try:
                    with open(stylesheet_path, "r", encoding="utf-8") as f:
                        self.setStyleSheet(f.read())
                        self.logger.info(f"样式表加载成功: {stylesheet_path}")
                        return
                except Exception as e:
                    self.logger.warning(f"样式表加载失败: {e}")
        
        self.logger.warning("未找到任何样式表文件")

    def init_ui(self):
        """初始化用户界面"""
        # v2.1: 标题显示GPU状态
        gpu_tag = "GPU" if self._cuda_info.get("cuda_available") else "CPU"
        self.setWindowTitle(f"DeepFocus Pro v3.0 - 智能人脸定位系统（最终版） [{gpu_tag}]")
        self.resize(1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 左侧边栏 ===
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # === 右侧内容区 ===
        content_area = self._create_content_area()
        main_layout.addWidget(content_area)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请先加载目标人脸")

    def _create_sidebar(self) -> QFrame:
        """创建左侧边栏"""
        sidebar = QFrame()
        sidebar.setObjectName("SideBar")
        sidebar.setFixedWidth(340)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(5, 0)
        sidebar.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(25, 30, 25, 30)
        layout.setSpacing(18)

        # 1. 标题
        title_label = QLabel("DeepFocus Pro")
        title_label.setObjectName("TitleLabel")
        title_label.setStyleSheet("font-size: 24px; font-weight: 800; color: #1D1D1F; letter-spacing: -0.5px;")
        layout.addWidget(title_label)
        
        version_label = QLabel("v3.0 最终版")
        version_label.setObjectName("VersionLabel")
        version_label.setStyleSheet("font-size: 12px; color: #86868B; margin-top: -8px; font-weight: 500;")
        layout.addWidget(version_label)
        
        # v2.1: GPU状态指示器
        gpu_available = self._cuda_info.get("cuda_available", False)
        gpu_color = "#00C853" if gpu_available else "#FF9800"
        gpu_text = "GPU加速" if gpu_available else "CPU模式"
        gpu_tooltip = self._cuda_info.get("gpu_info", "未知")
        
        self.gpu_status_label = QLabel(f"● {gpu_text}")
        self.gpu_status_label.setStyleSheet(f"font-size: 11px; color: {gpu_color}; font-weight: 500;")
        self.gpu_status_label.setToolTip(gpu_tooltip)
        layout.addWidget(self.gpu_status_label)
        
        # 2. 目标设定卡片
        target_group = self._create_target_group()
        layout.addWidget(target_group)

        # 3. 算法参数卡片
        param_group = self._create_param_group()
        layout.addWidget(param_group)
        
        # 4. 查看处理过程按钮
        self.btn_visualize = QPushButton("查看处理过程")
        self.btn_visualize.setEnabled(False)
        self.btn_visualize.clicked.connect(self.show_visualization)
        layout.addWidget(self.btn_visualize)

        layout.addStretch()
        
        return sidebar

    def _create_target_group(self) -> QGroupBox:
        """创建目标设定卡片"""
        group = QGroupBox("目标设定 (Target)")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 目标预览区（使用可缩放组件）
        self.target_preview = ZoomableImageLabel()
        self.target_preview.setFixedSize(260, 200)
        self.target_preview.set_placeholder_text("未加载目标")
        layout.addWidget(self.target_preview, alignment=Qt.AlignCenter)
        
        # 目标翻页导航
        nav_layout = QHBoxLayout()
        nav_btn_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
        """
        
        self.btn_target_prev = QPushButton("<")
        self.btn_target_prev.setFixedSize(36, 28)
        self.btn_target_prev.setStyleSheet(nav_btn_style)
        self.btn_target_prev.clicked.connect(self.prev_target)
        self.btn_target_prev.setEnabled(False)
        
        self.lbl_target_nav = QLabel("0/0")
        self.lbl_target_nav.setAlignment(Qt.AlignCenter)
        self.lbl_target_nav.setMinimumWidth(40)
        self.lbl_target_nav.setStyleSheet("color: #86868B; font-size: 13px;")
        
        self.btn_target_next = QPushButton(">")
        self.btn_target_next.setFixedSize(36, 28)
        self.btn_target_next.setStyleSheet(nav_btn_style)
        self.btn_target_next.clicked.connect(self.next_target)
        self.btn_target_next.setEnabled(False)
        
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_target_prev)
        nav_layout.addWidget(self.lbl_target_nav)
        nav_layout.addWidget(self.btn_target_next)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)
        
        # 按钮行
        # 按钮样式（紧凑型）
        compact_btn_style = """
            QPushButton {
                padding: 6px 8px;
                font-size: 12px;
            }
        """
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)
        
        self.btn_load_target = QPushButton("选择目标")
        self.btn_load_target.setStyleSheet(compact_btn_style)
        self.btn_load_target.clicked.connect(self.load_target_image)
        
        self.btn_add_target = QPushButton("添加更多")
        self.btn_add_target.setStyleSheet(compact_btn_style)
        self.btn_add_target.clicked.connect(self.add_target_image)
        self.btn_add_target.setEnabled(False)
        
        self.btn_clear_target = QPushButton("清空")
        self.btn_clear_target.setStyleSheet(compact_btn_style)
        self.btn_clear_target.setFixedWidth(50)
        self.btn_clear_target.clicked.connect(self.clear_targets)
        self.btn_clear_target.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load_target, 1)  # 伸展
        btn_layout.addWidget(self.btn_add_target, 1)   # 伸展
        btn_layout.addWidget(self.btn_clear_target, 0) # 固定
        layout.addLayout(btn_layout)
        
        # 特征信息
        self.lbl_target_info = QLabel("特征数: 0")
        self.lbl_target_info.setStyleSheet("color: #86868B; font-size: 12px;")
        self.lbl_target_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_target_info)
        
        group.setLayout(layout)
        return group

    def _create_param_group(self) -> QGroupBox:
        """创建算法参数卡片"""
        group = QGroupBox("算法参数 (Config)")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # 模型选择
        model_layout = QHBoxLayout()
        self.radio_hog = QRadioButton("HOG")
        if self._dlib_available:
            self.radio_hog.setToolTip("HOG模型：速度快，适合正脸检测\n使用CPU计算")
        else:
            self.radio_hog.setEnabled(False)
            self.radio_hog.setToolTip(f"dlib不可用\n{get_dlib_error()}")
        
        # v2.1: CNN模式显示GPU状态
        gpu_available = self._cuda_info.get("cuda_available", False)
        cnn_label = "CNN"
        cnn_tooltip = "CNN模型：精度高，适合多角度检测\n"
        cnn_tooltip += "当前使用GPU加速" if gpu_available else "当前使用CPU"
        
        self.radio_cnn = QRadioButton(cnn_label)
        if self._dlib_available:
            self.radio_cnn.setToolTip(cnn_tooltip)
        else:
            self.radio_cnn.setEnabled(False)
            self.radio_cnn.setToolTip(f"dlib不可用\n{get_dlib_error()}")
        
        # v2.2: OpenCV DNN选项 (YuNet+SFace)
        self.radio_yunet = QRadioButton("YuNet")
        if self._opencv_dnn_available:
            models_exist, models_error = check_models_exist()
            if models_exist:
                self.radio_yunet.setToolTip("OpenCV DNN引擎：高精度 CPU实现\nYuNet检测 + SFace识别\n效果优秀，无需GPU")
            else:
                self.radio_yunet.setEnabled(False)
                self.radio_yunet.setToolTip(f"模型文件缺失\n{models_error}")
        else:
            self.radio_yunet.setEnabled(False)
            error_msg = get_opencv_dnn_error()
            self.radio_yunet.setToolTip(f"OpenCV DNN不可用\n{error_msg}")
        
        # 默认选择：优先 HOG，如果 dlib 不可用则选择 YuNet
        if self._dlib_available:
            self.radio_hog.setChecked(True)
        elif self._opencv_dnn_available and self.radio_yunet.isEnabled():
            self.radio_yunet.setChecked(True)
        else:
            # 所有模型都不可用时，仍选择 HOG（虽然禁用）
            self.radio_hog.setChecked(True)
        
        model_bg = QButtonGroup(self)
        model_bg.addButton(self.radio_hog)
        model_bg.addButton(self.radio_cnn)
        model_bg.addButton(self.radio_yunet)
        model_layout.addWidget(self.radio_hog)
        model_layout.addWidget(self.radio_cnn)
        model_layout.addWidget(self.radio_yunet)
        layout.addLayout(model_layout)

        # 阈值滑块
        self.lbl_tol = QLabel("判定阈值: 0.45")
        self.slider_tol = QSlider(Qt.Horizontal)
        self.slider_tol.setRange(30, 60)
        self.slider_tol.setValue(45)
        self.slider_tol.valueChanged.connect(
            lambda v: self.lbl_tol.setText(f"判定阈值: {v/100:.2f}")
        )
        layout.addWidget(self.lbl_tol)
        layout.addWidget(self.slider_tol)
        
        # Gamma 滑块
        self.lbl_gamma = QLabel("场景提亮 (Gamma): 1.0")
        self.slider_gamma = QSlider(Qt.Horizontal)
        self.slider_gamma.setRange(30, 150)
        self.slider_gamma.setValue(100)
        self.slider_gamma.valueChanged.connect(
            lambda v: self.lbl_gamma.setText(f"场景提亮 (Gamma): {v/100:.1f}")
        )
        self.slider_gamma.setToolTip("向左拖动整体提亮，向右拖动整体变暗")
        layout.addWidget(self.lbl_gamma)
        layout.addWidget(self.slider_gamma)
        
        # 功能开关
        self.chk_clahe = QCheckBox("启用 CLAHE 增强")
        self.chk_clahe.setChecked(True)
        layout.addWidget(self.chk_clahe)
        
        self.chk_best_only = QCheckBox("仅显示最佳匹配")
        self.chk_best_only.setChecked(False)
        self.chk_best_only.setToolTip("勾选后只显示匹配最好的一个人脸（绿框）")
        layout.addWidget(self.chk_best_only)
        
        group.setLayout(layout)
        return group

    def _create_content_area(self) -> QWidget:
        """创建右侧内容区"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        # 进度条（美化版）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)
        
        # 主显示区（支持拖拽和长按对比）
        self.scene_display = ImageDropLabel(
            placeholder_text="👋 拖拽图片到这里\n或点击「加载场景」按钮\n\n💡 Ctrl+滚轮缩放 | 拖拽平移 | 双击适应\n🔍 识别后按住可对比原图"
        )
        self.scene_display.setMinimumSize(700, 450)
        self.scene_display.file_dropped.connect(self._handle_file_drop)
        layout.addWidget(self.scene_display, 1)
        
        # 长按对比提示
        hint_label = QLabel("💡 提示：识别完成后，按住图片可查看原图对比")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("color: #86868B; font-size: 12px; padding: 5px;")
        layout.addWidget(hint_label)
        
        # 场景翻页导航
        scene_nav = self._create_scene_nav()
        layout.addLayout(scene_nav)
        
        # 图例和数据面板
        info_panel = self._create_info_panel()
        layout.addLayout(info_panel)
        
        # 底部保存按钮
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.btn_save_current = QPushButton("保存当前")
        self.btn_save_current.setEnabled(False)
        self.btn_save_current.clicked.connect(self.save_current_result)
        
        self.btn_save_all = QPushButton("保存全部")
        self.btn_save_all.setEnabled(False)
        self.btn_save_all.clicked.connect(self.save_all_results)
        
        # v2.1: 导出报告按钮
        self.btn_export_report = QPushButton("导出报告")
        self.btn_export_report.setEnabled(False)
        self.btn_export_report.clicked.connect(self.export_html_report)
        if not self._report_available:
            self.btn_export_report.setToolTip("需要安装jinja2: pip install jinja2")
        else:
            self.btn_export_report.setToolTip("导出HTML格式的识别报告")
        
        save_layout.addWidget(self.btn_save_current)
        save_layout.addWidget(self.btn_save_all)
        save_layout.addWidget(self.btn_export_report)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        return content

    def _create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        layout = QHBoxLayout()
        
        # 加载场景按钮
        self.btn_load_scene = QPushButton("加载场景")
        self.btn_load_scene.setFixedSize(100, 40)
        self.btn_load_scene.clicked.connect(self.load_scene)
        self.btn_load_scene.setEnabled(False)
        
        # 识别场景按钮
        self.btn_recognize = QPushButton("识别场景")
        self.btn_recognize.setObjectName("PrimaryButton")
        self.btn_recognize.setFixedSize(100, 40)
        self.btn_recognize.clicked.connect(self.recognize_scene)
        self.btn_recognize.setEnabled(False)
        
        # 批量导入识别按钮
        self.btn_batch = QPushButton("批量导入")
        self.btn_batch.setFixedSize(100, 40)
        self.btn_batch.clicked.connect(self.batch_process)
        self.btn_batch.setEnabled(False)
        
        # v2.2: 对比模型按钮
        self.btn_compare = QPushButton("对比模型")
        self.btn_compare.setFixedSize(100, 40)
        self.btn_compare.clicked.connect(self.compare_models)
        self.btn_compare.setEnabled(False)
        self.btn_compare.setToolTip("同时用多个模型识别并对比效果")
        
        # v2.3: 一键识别按钮（重新识别所有已导入的场景）
        self.btn_recognize_all = QPushButton("一键识别")
        self.btn_recognize_all.setFixedSize(100, 40)
        self.btn_recognize_all.clicked.connect(self.recognize_all_scenes)
        self.btn_recognize_all.setEnabled(False)
        self.btn_recognize_all.setToolTip("重新识别所有已导入的场景图像\n（批量导入多张后才可用）")
        
        layout.addWidget(self.btn_load_scene)
        layout.addWidget(self.btn_recognize)
        layout.addWidget(self.btn_batch)
        layout.addWidget(self.btn_recognize_all)
        layout.addWidget(self.btn_compare)
        layout.addStretch()
        
        # 状态药丸 (Status Pill)
        self.status_pill = QLabel("🟢 准备就绪")
        self.status_pill.setObjectName("StatusPill")
        self.status_pill.setAlignment(Qt.AlignCenter)
        self.status_pill.setFixedHeight(36)
        self.status_pill.setMinimumWidth(200)
        layout.addWidget(self.status_pill)
        
        layout.addStretch()
        
        return layout
    
    def _update_status_pill(self, text: str, state: str = "normal"):
        """
        更新状态药丸
        
        Args:
            text: 显示文本
            state: 状态 ("normal", "success", "error", "busy")
        """
        self.status_pill.setText(text)
        
        base_style = """
            QLabel#StatusPill {
                background-color: #FFFFFF;
                border-radius: 18px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 14px;
                border: 1px solid #E5E5EA;
        """
        
        if state == "error":
            self.status_pill.setStyleSheet(base_style + """
                border-color: #FF3B30;
                color: #FF3B30;
                background: #FFF5F5;
            }""")
        elif state == "success":
            self.status_pill.setStyleSheet(base_style + """
                border-color: #34C759;
                color: #34C759;
                background: #F0FFF4;
            }""")
        elif state == "busy":
            self.status_pill.setStyleSheet(base_style + """
                border-color: #007AFF;
                color: #007AFF;
                background: #F0F8FF;
            }""")
        else:
            self.status_pill.setStyleSheet(base_style + """
                color: #1D1D1F;
            }""")

    def _create_scene_nav(self) -> QHBoxLayout:
        """创建场景翻页导航"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        scene_nav_btn_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }
        """
        
        self.btn_scene_prev = QPushButton("<")
        self.btn_scene_prev.setFixedSize(36, 28)
        self.btn_scene_prev.setStyleSheet(scene_nav_btn_style)
        self.btn_scene_prev.clicked.connect(self.prev_scene)
        self.btn_scene_prev.setEnabled(False)
        
        self.lbl_scene_nav = QLabel("0/0")
        self.lbl_scene_nav.setAlignment(Qt.AlignCenter)
        self.lbl_scene_nav.setMinimumWidth(60)
        self.lbl_scene_nav.setStyleSheet("color: #1D1D1F; font-size: 14px; font-weight: 500;")
        
        self.btn_scene_next = QPushButton(">")
        self.btn_scene_next.setFixedSize(36, 28)
        self.btn_scene_next.setStyleSheet(scene_nav_btn_style)
        self.btn_scene_next.clicked.connect(self.next_scene)
        self.btn_scene_next.setEnabled(False)
        
        layout.addWidget(self.btn_scene_prev)
        layout.addWidget(self.lbl_scene_nav)
        layout.addWidget(self.btn_scene_next)
        
        layout.addStretch()
        
        return layout

    def _create_info_panel(self) -> QHBoxLayout:
        """创建信息面板（图例+数据）"""
        layout = QHBoxLayout()
        
        # 图例
        legend_frame = QFrame()
        legend_frame.setObjectName("LegendFrame")
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(15, 8, 15, 8)
        legend_layout.setSpacing(20)
        
        legends = [
            ("#00C853", "最佳匹配"),
            ("#FFD600", "其他匹配"),
            ("#FF3D00", "未能匹配"),
        ]
        
        for color, text in legends:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(6)
            
            dot = QLabel()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            
            label = QLabel(text)
            label.setStyleSheet("font-size: 12px; color: #333333;")
            
            item_layout.addWidget(dot)
            item_layout.addWidget(label)
            legend_layout.addLayout(item_layout)
        
        layout.addWidget(legend_frame)
        layout.addStretch()
        
        # 数据面板
        data_frame = QFrame()
        data_frame.setObjectName("DataPanel")
        data_layout = QHBoxLayout(data_frame)
        data_layout.setContentsMargins(15, 8, 15, 8)
        data_layout.setSpacing(25)
        
        self.lbl_total = QLabel("检测: -")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: 600; color: #1D1D1F;")
        
        self.lbl_matches = QLabel("匹配: -")
        self.lbl_matches.setStyleSheet("font-size: 14px; font-weight: 600; color: #00C853;")
        
        self.lbl_best_sim = QLabel("相似度: -")
        self.lbl_best_sim.setStyleSheet("font-size: 14px; font-weight: 600; color: #007AFF;")
        
        # v2.1: 耗时显示
        self.lbl_time = QLabel("耗时: -")
        self.lbl_time.setStyleSheet("font-size: 14px; font-weight: 600; color: #9C27B0;")
        self.lbl_time.setToolTip("处理总耗时")
        
        data_layout.addWidget(self.lbl_total)
        data_layout.addWidget(self.lbl_matches)
        data_layout.addWidget(self.lbl_best_sim)
        data_layout.addWidget(self.lbl_time)
        
        layout.addWidget(data_frame)
        
        return layout

    # ==================== 引擎管理 ====================
    
    def _get_opencv_dnn_engine(self):
        """懒加载 OpenCV DNN 引擎 (YuNet+SFace)"""
        if self._opencv_dnn_engine is None and self._opencv_dnn_available:
            try:
                # 检查模型文件
                models_exist, models_error = check_models_exist()
                if not models_exist:
                    QMessageBox.warning(
                        self,
                        "模型文件缺失",
                        f"{models_error}\n\n请运行: python models/download_models.py"
                    )
                    if self._dlib_available:
                        self.radio_hog.setChecked(True)
                    return None
                
                self._opencv_dnn_engine = OpenCVDNNEngine()
                self.logger.info("OpenCV DNN 引擎加载成功 (YuNet+SFace)")
            except Exception as e:
                self.logger.error(f"OpenCV DNN 引擎加载失败: {e}")
                if self._dlib_available:
                    QMessageBox.warning(
                        self,
                        "OpenCV DNN 加载失败",
                        f"无法加载OpenCV DNN引擎:\n{e}\n\n将自动切换到HOG模式。"
                    )
                    self.radio_hog.setChecked(True)
                else:
                    QMessageBox.critical(
                        self,
                        "引擎加载失败",
                        f"无法加载OpenCV DNN引擎:\n{e}\n\ndlib 也不可用。请检查环境配置。"
                    )
                return None
        return self._opencv_dnn_engine
    
    def _get_current_engine(self):
        """获取当前选择的引擎"""
        if self.radio_yunet.isChecked() and self._opencv_dnn_available:
            engine = self._get_opencv_dnn_engine()
            if engine is not None:
                return engine, "opencv_dnn"
            # 如果OpenCV DNN加载失败，radio已经被切换到HOG，使用dlib引擎
        return self.engine, "dlib"
    
    # ==================== 目标操作 ====================
    
    def load_target_image(self):
        """加载目标人脸（替换模式）"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择目标人脸（可多选）", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        if not paths:
            return
        
        # 清空现有目标（所有引擎都清空）
        self.engine.clear_targets()
        if self._opencv_dnn_engine:
            self._opencv_dnn_engine.clear_targets()
        self.target_images = []
        self.current_target_index = 0
        
        success_count = 0
        for path in paths:
            self.logger.info(f"加载目标人脸: {path}")
            # 加载到dlib引擎
            success, res = self.engine.add_target_face(path)
            if success:
                self.target_images.append(res)
                success_count += 1
                # 同时加载到OpenCV DNN引擎（如果可用）
                if self._opencv_dnn_available:
                    opencv_dnn_engine = self._get_opencv_dnn_engine()
                    if opencv_dnn_engine:
                        opencv_dnn_engine.add_target_face(path)
            else:
                self.logger.warning(f"目标加载失败: {path} - {res}")
        
        if success_count > 0:
            self._update_target_display()
            self._enable_scene_buttons(True)
            self.btn_add_target.setEnabled(True)
            self.btn_clear_target.setEnabled(True)
            feature_count = self.engine.get_target_encoding_count() if self.engine else 0
            self._update_status_pill(f"🎯 已加载 {success_count} 张目标", "success")
            self.status_bar.showMessage(f"目标加载成功: {success_count} 张照片, {feature_count} 个特征")
        else:
            self._update_status_pill("❌ 未检测到人脸", "error")
            QMessageBox.warning(self, "错误", "未能从所选图片中检测到人脸")

    def add_target_image(self):
        """追加目标照片"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "添加更多目标照片", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        if not paths:
            return
        
        success_count = 0
        for path in paths:
            success, res = self.engine.add_target_face(path)
            if success:
                self.target_images.append(res)
                success_count += 1
                # 同时加载到OpenCV DNN引擎
                if self._opencv_dnn_engine:
                    self._opencv_dnn_engine.add_target_face(path)
        
        if success_count > 0:
            self._update_target_display()
            self.status_bar.showMessage(f"已追加 {success_count} 张照片, 总计 {self.engine.get_target_encoding_count()} 个特征")

    def clear_targets(self):
        """清空所有目标"""
        self.engine.clear_targets()
        if self._opencv_dnn_engine:
            self._opencv_dnn_engine.clear_targets()
        self.target_images = []
        self.current_target_index = 0
        
        self.target_preview.set_image(None)
        self.target_preview.set_placeholder_text("未加载目标")
        self._update_target_nav()
        self.lbl_target_info.setText("特征数: 0")
        
        self.btn_add_target.setEnabled(False)
        self.btn_clear_target.setEnabled(False)
        self._enable_scene_buttons(False)
        
        self.status_bar.showMessage("已清空所有目标")

    def prev_target(self):
        """上一张目标"""
        if self.current_target_index > 0:
            self.current_target_index -= 1
            self._update_target_display()

    def next_target(self):
        """下一张目标"""
        if self.current_target_index < len(self.target_images) - 1:
            self.current_target_index += 1
            self._update_target_display()

    def _update_target_display(self):
        """更新目标显示"""
        if self.target_images:
            img = self.target_images[self.current_target_index]
            self.target_preview.set_image(img)
            self.target_preview.fit_to_view()
        self._update_target_nav()
        self.lbl_target_info.setText(f"特征数: {self.engine.get_target_encoding_count()}")

    def _update_target_nav(self):
        """更新目标导航"""
        total = len(self.target_images)
        current = self.current_target_index + 1 if total > 0 else 0
        self.lbl_target_nav.setText(f"{current}/{total}")
        self.btn_target_prev.setEnabled(self.current_target_index > 0)
        self.btn_target_next.setEnabled(self.current_target_index < total - 1)

    # ==================== 拖拽处理 ====================
    
    def _handle_file_drop(self, file_path: str):
        """处理拖入的文件"""
        self.logger.info(f"拖入文件: {file_path}")
        
        # 如果没有加载目标，则作为目标加载
        target_count = 0
        if self._dlib_available and self.engine:
            target_count = self.engine.get_target_encoding_count()
        elif self._opencv_dnn_engine:
            target_count = self._opencv_dnn_engine.get_target_count()
        
        if target_count == 0:
            # 没有目标，询问用户
            reply = QMessageBox.question(
                self, "选择操作",
                f"检测到尚未加载目标人脸。\n\n将 {os.path.basename(file_path)} 作为：",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            reply.button(QMessageBox.Yes).setText("目标人脸")
            reply.button(QMessageBox.No).setText("场景图像")
            
            # 简化处理：默认作为场景
            self._load_scene_from_path(file_path)
        else:
            # 已有目标，作为场景加载并自动识别
            self._load_scene_from_path(file_path)
            self.recognize_scene()
    
    def _load_scene_from_path(self, path: str):
        """从路径加载场景"""
        self.current_scene_path = path
        self.scene_paths = [path]
        self.scene_results = []
        self.current_scene_index = 0
        
        # 清除可视化缓存
        self._visualization_cache = None
        
        # 显示原始图像
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            self.scene_display.set_image(img, is_result=False)
            self.scene_display.fit_to_view()
            self.btn_recognize.setEnabled(True)
            self.btn_visualize.setEnabled(True)
            self.btn_compare.setEnabled(True)
            self._update_status_pill(f"📂 已加载: {os.path.basename(path)}", "normal")
            self._update_scene_nav()
    
    # ==================== 场景操作 ====================
    
    def _enable_scene_buttons(self, enabled: bool):
        """启用/禁用场景相关按钮"""
        self.btn_load_scene.setEnabled(enabled)
        self.btn_batch.setEnabled(enabled)
        self.btn_compare.setEnabled(enabled and self.current_scene_path is not None)
        self.btn_visualize.setEnabled(enabled and self.current_scene_path is not None)

    def load_scene(self):
        """加载场景图像（不识别）"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择场景图像", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        if not path:
            return
        
        self._load_scene_from_path(path)

    def recognize_scene(self):
        """识别当前场景"""
        if not self.current_scene_path:
            return
        
        params = self._get_params()
        engine, engine_type = self._get_current_engine()
        
        # 检查引擎是否有目标
        if engine_type == "opencv_dnn":
            if engine.get_target_count() == 0:
                QMessageBox.warning(self, "提示", "请先加载目标人脸")
                return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        
        # 保存原图用于对比
        orig_img = cv2.imdecode(np.fromfile(self.current_scene_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if orig_img is not None:
            self._original_scene_img = orig_img
        
        model_name = params['model'].upper()
        self._update_status_pill(f"⏳ 识别中... ({model_name})", "busy")
        
        self.worker = RecognitionWorker(engine, self.current_scene_path, params, engine_type)
        self.worker.result_ready.connect(self._on_single_result)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.start()

    def batch_process(self):
        """批量导入并识别场景"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择多个场景图像", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        if not paths:
            return
        
        self.scene_paths = paths
        self.scene_results = []
        self.current_scene_index = 0
        
        params = self._get_params()
        engine, engine_type = self._get_current_engine()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        self._update_status_pill(f"⏳ 批量处理 {len(paths)} 张...", "busy")
        
        self.worker = BatchWorker(engine, paths, params, engine_type)
        self.worker.single_result_ready.connect(self._on_batch_single_result)
        self.worker.all_finished.connect(self._on_batch_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.start()

    def recognize_all_scenes(self):
        """一键识别：重新识别所有已导入的场景"""
        if not self.scene_paths or len(self.scene_paths) < 2:
            QMessageBox.warning(self, "提示", "请先批量导入多张场景图像")
            return
        
        # 检查是否有目标
        target_count = 0
        if self._dlib_available and self.engine:
            target_count = self.engine.get_target_encoding_count()
        elif self._opencv_dnn_engine:
            target_count = self._opencv_dnn_engine.get_target_count()
        
        if target_count == 0:
            QMessageBox.warning(self, "提示", "请先加载目标人脸")
            return
        
        # 使用已有的场景路径列表重新识别
        self.scene_results = []
        self.current_scene_index = 0
        
        params = self._get_params()
        engine, engine_type = self._get_current_engine()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        self._update_status_pill(f"⏳ 一键识别 {len(self.scene_paths)} 张...", "busy")
        
        self.worker = BatchWorker(engine, self.scene_paths, params, engine_type)
        self.worker.single_result_ready.connect(self._on_batch_single_result)
        self.worker.all_finished.connect(self._on_batch_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.start()

    def _get_params_hash(self, params: dict) -> str:
        """获取参数的哈希值，用于缓存判断"""
        import hashlib
        params_str = f"{params.get('tolerance')}-{params.get('upsample')}-{params.get('model')}-{params.get('use_clahe')}-{params.get('gamma')}-{params.get('best_only')}"
        return hashlib.md5(params_str.encode()).hexdigest()[:8]
    
    def show_visualization(self):
        """显示处理过程可视化"""
        if not self.current_scene_path:
            return
        
        # 检查 dlib 引擎是否可用（可视化需要 dlib 引擎）
        if not self._dlib_available or self.engine is None:
            QMessageBox.warning(
                self, "提示",
                "可视化功能需要 dlib 引擎，但 dlib 不可用。\n"
                "请安装 dlib 或使用其他功能。"
            )
            return
        
        params = self._get_params()
        
        # 如果选择了 YuNet，可视化时使用 HOG 模型（因为可视化只支持 dlib 引擎）
        if params['model'] == 'yunet':
            params['model'] = 'hog'
            params['upsample'] = 2
            self.logger.info("可视化模式：YuNet 切换为 HOG（可视化仅支持 dlib 引擎）")
        
        params_hash = self._get_params_hash(params)
        
        # 检查缓存是否有效
        if (self._visualization_cache and 
            self._visualization_cache.get("path") == self.current_scene_path and
            self._visualization_cache.get("params_hash") == params_hash):
            # 直接使用缓存
            self.logger.info("使用缓存的可视化结果")
            stages = self._visualization_cache["stages"]
            stats = self._visualization_cache["stats"]
            VisualizationDialog.show_stages(stages, stats, self)
            return
        
        # 没有缓存，需要重新生成
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        self._update_status_pill("🔬 生成可视化...", "busy")
        
        self.worker = VisualizationWorker(self.engine, self.current_scene_path, params)
        self.worker.result_ready.connect(self._on_visualization_ready)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.start()
    
    def compare_models(self):
        """对比多个模型的识别效果"""
        if not self.current_scene_path:
            QMessageBox.warning(self, "提示", "请先加载场景图像")
            return
        
        # 检查是否有目标
        if self.engine.get_target_encoding_count() == 0:
            QMessageBox.warning(self, "提示", "请先加载目标人脸")
            return
        
        # 获取当前参数
        params = self._get_params()
        
        # 构建可用模型列表
        models = []
        
        # 1. HOG 模型
        hog_params = params.copy()
        hog_params['model'] = 'hog'
        hog_params['upsample'] = 2
        models.append({
            "name": "HOG (dlib)",
            "engine": self.engine,
            "engine_type": "dlib",
            "params": hog_params
        })
        
        # 2. CNN 模型
        cnn_params = params.copy()
        cnn_params['model'] = 'cnn'
        cnn_params['upsample'] = 1
        models.append({
            "name": "CNN (dlib)",
            "engine": self.engine,
            "engine_type": "dlib",
            "params": cnn_params
        })
        
        # 3. YuNet+SFace 模型（如果可用）
        if self._opencv_dnn_available:
            opencv_engine = self._get_opencv_dnn_engine()
            if opencv_engine and opencv_engine.get_target_count() > 0:
                models.append({
                    "name": "YuNet+SFace (OpenCV)",
                    "engine": opencv_engine,
                    "engine_type": "opencv_dnn",
                    "params": params
                })
        
        if len(models) < 2:
            QMessageBox.information(
                self, "提示",
                f"当前只有 {len(models)} 个可用模型，至少需要 2 个模型才能对比。\n\n"
                "请检查：\n"
                "- OpenCV DNN 需要下载模型文件 (python models/download_models.py)"
            )
            return
        
        # 显示对比窗口
        self._update_status_pill(f"⚖️ 对比 {len(models)} 个模型...", "busy")
        CompareDialog.run_comparison(models, self.current_scene_path, self)
        self._update_status_pill("⚖️ 对比完成", "success")

    def prev_scene(self):
        """上一张场景结果"""
        if self.current_scene_index > 0:
            self.current_scene_index -= 1
            self._display_scene_result(self.current_scene_index)

    def next_scene(self):
        """下一张场景结果"""
        if self.current_scene_index < len(self.scene_results) - 1:
            self.current_scene_index += 1
            self._display_scene_result(self.current_scene_index)

    def _update_scene_nav(self):
        """更新场景导航"""
        total = len(self.scene_results) if self.scene_results else (1 if self.current_scene_path else 0)
        current = self.current_scene_index + 1 if total > 0 else 0
        self.lbl_scene_nav.setText(f"{current}/{total}")
        self.btn_scene_prev.setEnabled(self.current_scene_index > 0)
        self.btn_scene_next.setEnabled(self.current_scene_index < len(self.scene_results) - 1)

    def _display_scene_result(self, index: int):
        """显示指定索引的场景结果"""
        if 0 <= index < len(self.scene_results):
            img, stats, path = self.scene_results[index]
            self.current_result_image = img
            self.current_stats = stats
            self.current_scene_path = path
            
            # 尝试加载原图用于对比
            orig_img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if orig_img is not None:
                self.scene_display.set_comparison_images(orig_img, img)
            else:
                self.scene_display.set_image(img, is_result=True)
            self.scene_display.fit_to_view()
            self._update_stats_display(stats)
            self._update_scene_nav()
            self.btn_visualize.setEnabled(True)

    def _get_params(self) -> dict:
        """获取当前参数"""
        # 确定模型类型
        if self.radio_yunet.isChecked():
            model = "yunet"
            upsample = 1  # OpenCV DNN不使用此参数
        elif self.radio_cnn.isChecked():
            model = "cnn"
            upsample = 1
        else:
            model = "hog"
            upsample = 2
        
        return {
            "tolerance": self.slider_tol.value() / 100.0,
            "upsample": upsample,
            "model": model,
            "use_clahe": self.chk_clahe.isChecked(),
            "gamma": self.slider_gamma.value() / 100.0,
            "best_only": self.chk_best_only.isChecked(),
        }

    def _set_processing_state(self, processing: bool):
        """设置处理状态"""
        self.btn_load_scene.setEnabled(not processing)
        self.btn_recognize.setEnabled(not processing)
        self.btn_batch.setEnabled(not processing)
        self.btn_visualize.setEnabled(not processing)
        self.btn_compare.setEnabled(not processing)
        # 一键识别按钮：只有在有多张场景时才启用
        self.btn_recognize_all.setEnabled(not processing and len(self.scene_paths) > 1)
        self.btn_save_current.setEnabled(not processing and self.current_result_image is not None)
        self.btn_save_all.setEnabled(not processing and len(self.scene_results) > 0)
        self.btn_export_report.setEnabled(not processing and len(self.scene_results) > 0 and self._report_available)

    def _update_stats_display(self, stats: dict):
        """更新统计数据显示"""
        total = stats.get("total", 0)
        matches = stats.get("matches", 0)
        best_similarity = stats.get("best_similarity", 0.0)
        process_time = stats.get("process_time", 0.0)
        
        self.lbl_total.setText(f"检测: {total}")
        self.lbl_matches.setText(f"匹配: {matches}")
        self.lbl_best_sim.setText(f"相似度: {best_similarity:.1f}%")
        
        # v2.1: 显示耗时
        if process_time > 0:
            self.lbl_time.setText(f"耗时: {process_time:.2f}s")
            # 构建详细的性能提示
            detection_time = stats.get("detection_time", 0.0)
            encoding_time = stats.get("encoding_time", 0.0)
            model_used = stats.get("model_used", "unknown")
            cuda_used = stats.get("cuda_used", False)
            device = "GPU" if cuda_used else "CPU"
            tooltip = f"模型: {model_used.upper()} ({device})\n检测: {detection_time:.2f}s\n编码: {encoding_time:.2f}s"
            self.lbl_time.setToolTip(tooltip)
        else:
            self.lbl_time.setText("耗时: -")

    # ==================== 回调处理 ====================
    
    def _on_progress(self, value: int):
        """进度更新"""
        self.progress_bar.setValue(value)

    def _on_single_result(self, img: np.ndarray, stats: dict, path: str):
        """单图识别完成"""
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        # 先更新数据，再更新按钮状态
        self.current_result_image = img
        self.current_stats = stats
        self.scene_results = [(img, stats, path)]
        self.scene_paths = [path]  # 确保单张场景时路径列表只有一个
        self.current_scene_index = 0
        
        self._set_processing_state(False)
        
        # 设置对比图像（原图和结果图）
        if hasattr(self, '_original_scene_img') and self._original_scene_img is not None:
            self.scene_display.set_comparison_images(self._original_scene_img, img)
        else:
            self.scene_display.set_image(img, is_result=True)
        self.scene_display.fit_to_view()
        self._update_stats_display(stats)
        self._update_scene_nav()
        
        self.btn_save_current.setEnabled(True)
        self.btn_visualize.setEnabled(True)
        
        # 更新状态药丸
        matches = stats.get('matches', 0)
        total = stats.get('total', 0)
        if matches > 0:
            self._update_status_pill(f"✅ 完成: 发现 {total} 人, 匹配 {matches} 人", "success")
        else:
            self._update_status_pill(f"⚠️ 完成: 发现 {total} 人, 无匹配", "normal")
        
        self.status_bar.showMessage(f"识别完成 - {os.path.basename(path)}")

    def _on_batch_single_result(self, img: np.ndarray, stats: dict, path: str, current: int, total: int):
        """批量处理中单张完成"""
        self._update_status_pill(f"⏳ 处理中 {current}/{total} 张...", "busy")

    def _on_batch_finished(self, results: list, total_time: float):
        """批量处理全部完成"""
        self.progress_bar.setValue(100)
        self.progress_bar.setVisible(False)
        
        # 先更新数据
        self.scene_results = results
        self._batch_total_time = total_time  # 保存批量总耗时
        
        # 再更新按钮状态（此时 scene_results 和 scene_paths 已经是最新的）
        self._set_processing_state(False)
        
        if results:
            self.current_scene_index = 0
            self._display_scene_result(0)
            self.btn_save_all.setEnabled(True)
            # 启用一键识别按钮（只有多张场景时才有意义）
            if len(self.scene_paths) > 1:
                self.btn_recognize_all.setEnabled(True)
            # 启用导出报告按钮
            if self._report_available:
                self.btn_export_report.setEnabled(True)
        
        total_matches = sum(r[1].get('matches', 0) for r in results)
        self._update_status_pill(f"✅ 批量完成: {len(results)} 张, 匹配 {total_matches} 人", "success")
        self.status_bar.showMessage(f"批量处理完成: {len(results)} 张图像, 总耗时: {total_time:.2f}s")
        
        # 更新耗时显示为总耗时
        self.lbl_time.setText(f"总耗时: {total_time:.2f}s")
        self.lbl_time.setToolTip(f"批量处理总耗时\n共 {len(results)} 张图像")

    def _on_visualization_ready(self, stages: dict, stats: dict):
        """可视化处理完成"""
        self.progress_bar.setValue(100)
        self._set_processing_state(False)
        
        # 保存到缓存
        params = self._get_params()
        self._visualization_cache = {
            "path": self.current_scene_path,
            "params_hash": self._get_params_hash(params),
            "stages": stages,
            "stats": stats
        }
        self.logger.info("可视化结果已缓存")
        
        # 同时更新主显示
        if "final" in stages:
            self.current_result_image = stages["final"]
            self.current_stats = stats
            self.scene_display.set_image(stages["final"])
            self.scene_display.fit_to_view()
            self._update_stats_display(stats)
            self.btn_save_current.setEnabled(True)
        
        # 显示可视化弹窗
        VisualizationDialog.show_stages(stages, stats, self)
        
        self._update_status_pill("🔬 可视化完成", "success")

    def _on_error(self, msg: str):
        """错误处理"""
        self.progress_bar.setVisible(False)
        self._set_processing_state(False)
        self._update_status_pill(f"❌ 出错", "error")
        self.status_bar.showMessage(f"错误: {msg}")
        QMessageBox.critical(self, "错误", msg)
        self.logger.error(f"处理错误: {msg}")

    # ==================== 保存功能 ====================
    
    def save_current_result(self):
        """保存当前结果"""
        if self.current_result_image is None:
            return
        
        default_name = "result.jpg"
        if self.current_scene_path:
            base = os.path.splitext(os.path.basename(self.current_scene_path))[0]
            default_name = f"{base}_result.jpg"
        
        path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", default_name,
            "JPEG (*.jpg);;PNG (*.png);;所有文件 (*.*)"
        )
        if not path:
            return
        
        # 使用imencode处理中文路径
        ext = os.path.splitext(path)[1].lower()
        if ext == '.png':
            _, buf = cv2.imencode('.png', self.current_result_image)
        else:
            _, buf = cv2.imencode('.jpg', self.current_result_image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        buf.tofile(path)
        self.status_bar.showMessage(f"已保存: {path}")

    def save_all_results(self):
        """保存所有结果"""
        if not self.scene_results:
            return
        
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if not folder:
            return
        
        saved = 0
        for img, stats, path in self.scene_results:
            base = os.path.splitext(os.path.basename(path))[0]
            save_path = os.path.join(folder, f"{base}_result.jpg")
            
            _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
            buf.tofile(save_path)
            saved += 1
        
        self.status_bar.showMessage(f"已保存 {saved} 张结果到 {folder}")
        QMessageBox.information(self, "保存完成", f"已保存 {saved} 张结果图像")
    
    def export_html_report(self):
        """导出HTML识别报告"""
        if not self.scene_results:
            QMessageBox.warning(self, "提示", "没有可导出的识别结果")
            return
        
        if not self._report_available:
            QMessageBox.warning(self, "功能不可用", "需要安装jinja2库\n\n安装命令: pip install jinja2")
            return
        
        # 选择保存路径
        default_name = f"DeepFocus_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出报告", default_name,
            "HTML文件 (*.html);;所有文件 (*.*)"
        )
        if not path:
            return
        
        try:
            # 准备报告数据
            self._report_generator.clear()
            
            # 设置目标信息
            self._report_generator.set_targets(
                self.target_images,
                self.engine.get_target_encoding_count()
            )
            
            # 添加所有场景结果
            for img, stats, scene_path in self.scene_results:
                self._report_generator.add_scene_result(img, stats, scene_path)
            
            # 设置参数
            params = self._get_params()
            if self.scene_results:
                # 使用最后一次处理的实际参数
                last_stats = self.scene_results[-1][1]
                params["cuda_used"] = last_stats.get("cuda_used", False)
            self._report_generator.set_params(params)
            
            # 生成报告
            if self._report_generator.generate(path):
                self.status_bar.showMessage(f"报告已导出: {path}")
                QMessageBox.information(self, "导出成功", f"HTML报告已生成\n\n{path}")
            else:
                QMessageBox.warning(self, "导出失败", "报告生成失败，请查看日志")
                
        except Exception as e:
            self.logger.error(f"导出报告失败: {e}")
            QMessageBox.critical(self, "错误", f"导出报告失败: {e}")
