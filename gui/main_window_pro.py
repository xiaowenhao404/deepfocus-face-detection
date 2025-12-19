"""
DeepFocus Pro v2.0 增强版主窗口模块

整合FaceEnginePro、macOS风格界面、可缩放图像、批量处理、可视化等功能
"""

import sys
import os
import cv2
import numpy as np
from typing import List, Optional, Dict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QGroupBox, QSlider,
    QProgressBar, QMessageBox, QCheckBox, QFrame, QRadioButton,
    QButtonGroup, QStatusBar, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QFile, QTextStream
from PyQt5.QtGui import QImage, QPixmap
import logging

from core.face_engine_pro import FaceEnginePro
from gui.zoomable_label import ZoomableImageLabel
from gui.visualization_dialog import VisualizationDialog


class RecognitionWorker(QThread):
    """单图识别工作线程"""
    result_ready = pyqtSignal(object, dict, str)  # img, stats, path
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
    all_finished = pyqtSignal(list)  # list of (img, stats, path)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)  # 总体进度 0-100

    def __init__(self, engine: FaceEnginePro, scene_paths: List[str], params: dict):
        super().__init__()
        self.engine = engine
        self.scene_paths = scene_paths
        self.params = params

    def run(self):
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
        self.all_finished.emit(results)


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
            
            stages, stats = self.engine.process_scene_with_stages(
                self.scene_path,
                tolerance=self.params['tolerance'],
                upsample=self.params['upsample'],
                model=self.params['model'],
                use_clahe=self.params['use_clahe'],
                gamma=self.params['gamma'],
                best_only=self.params.get('best_only', False),
                progress_callback=progress_callback
            )
            self.result_ready.emit(stages, stats)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindowPro(QMainWindow):
    """DeepFocus Pro v2.0 增强版主窗口"""
    
    def __init__(self):
        super().__init__()
        self.engine = FaceEnginePro()
        self.logger = logging.getLogger(__name__)
        
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
        
        # 工作线程
        self.worker = None
        
        self.init_ui()
        self.load_stylesheet()
        
        self.logger.info("DeepFocus Pro v2.0 主窗口初始化完成")

    def load_stylesheet(self):
        """加载 macOS 风格样式表"""
        stylesheet_path = "gui/macos.qss"
        if os.path.exists(stylesheet_path):
            file = QFile(stylesheet_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                stream.setCodec("UTF-8")
                self.setStyleSheet(stream.readAll())
                self.logger.info("样式表加载成功")
        else:
            self.logger.warning(f"样式表文件不存在: {stylesheet_path}")

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepFocus Pro v2.0 - 智能人脸定位系统")
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
        sidebar.setFixedWidth(320)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(15)

        # 1. 标题
        title_label = QLabel("DeepFocus Pro")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #1D1D1F;")
        layout.addWidget(title_label)
        
        version_label = QLabel("v2.0")
        version_label.setStyleSheet("font-size: 12px; color: #86868B; margin-top: -10px;")
        layout.addWidget(version_label)
        
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
        self.radio_hog = QRadioButton("HOG (快)")
        self.radio_cnn = QRadioButton("CNN (准)")
        self.radio_hog.setChecked(True)
        model_bg = QButtonGroup(self)
        model_bg.addButton(self.radio_hog)
        model_bg.addButton(self.radio_cnn)
        model_layout.addWidget(self.radio_hog)
        model_layout.addWidget(self.radio_cnn)
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
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # 主显示区（可缩放）
        self.scene_display = ZoomableImageLabel()
        self.scene_display.setMinimumSize(700, 450)
        self.scene_display.set_placeholder_text("预览区域\n\nCtrl+滚轮缩放，拖拽平移，双击适应窗口")
        layout.addWidget(self.scene_display, 1)
        
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
        
        save_layout.addWidget(self.btn_save_current)
        save_layout.addWidget(self.btn_save_all)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        return content

    def _create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        layout = QHBoxLayout()
        
        # 加载场景按钮
        self.btn_load_scene = QPushButton("加载场景")
        self.btn_load_scene.setFixedSize(100, 36)
        self.btn_load_scene.clicked.connect(self.load_scene)
        self.btn_load_scene.setEnabled(False)
        
        # 识别场景按钮
        self.btn_recognize = QPushButton("识别场景")
        self.btn_recognize.setObjectName("PrimaryButton")
        self.btn_recognize.setFixedSize(100, 36)
        self.btn_recognize.clicked.connect(self.recognize_scene)
        self.btn_recognize.setEnabled(False)
        
        # 批量导入识别按钮
        self.btn_batch = QPushButton("批量导入识别")
        self.btn_batch.setFixedSize(130, 36)
        self.btn_batch.clicked.connect(self.batch_process)
        self.btn_batch.setEnabled(False)
        
        # 状态标签
        self.status_label = QLabel("请先加载目标人脸")
        self.status_label.setStyleSheet("color: #86868B; font-size: 13px;")
        
        layout.addWidget(self.btn_load_scene)
        layout.addWidget(self.btn_recognize)
        layout.addWidget(self.btn_batch)
        layout.addSpacing(15)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        return layout

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
        
        self.lbl_best_dist = QLabel("距离: -")
        self.lbl_best_dist.setStyleSheet("font-size: 14px; font-weight: 600; color: #007AFF;")
        
        data_layout.addWidget(self.lbl_total)
        data_layout.addWidget(self.lbl_matches)
        data_layout.addWidget(self.lbl_best_dist)
        
        layout.addWidget(data_frame)
        
        return layout

    # ==================== 目标操作 ====================
    
    def load_target_image(self):
        """加载目标人脸（替换模式）"""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择目标人脸（可多选）", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        if not paths:
            return
        
        # 清空现有目标
        self.engine.clear_targets()
        self.target_images = []
        self.current_target_index = 0
        
        success_count = 0
        for path in paths:
            self.logger.info(f"加载目标人脸: {path}")
            success, res = self.engine.add_target_face(path)
            if success:
                self.target_images.append(res)
                success_count += 1
            else:
                self.logger.warning(f"目标加载失败: {path} - {res}")
        
        if success_count > 0:
            self._update_target_display()
            self._enable_scene_buttons(True)
            self.btn_add_target.setEnabled(True)
            self.btn_clear_target.setEnabled(True)
            self.status_label.setText(f"已加载 {success_count} 张目标照片")
            self.status_bar.showMessage(f"目标加载成功: {success_count} 张照片, {self.engine.get_target_encoding_count()} 个特征")
        else:
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
        
        if success_count > 0:
            self._update_target_display()
            self.status_bar.showMessage(f"已追加 {success_count} 张照片, 总计 {self.engine.get_target_encoding_count()} 个特征")

    def clear_targets(self):
        """清空所有目标"""
        self.engine.clear_targets()
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

    # ==================== 场景操作 ====================
    
    def _enable_scene_buttons(self, enabled: bool):
        """启用/禁用场景相关按钮"""
        self.btn_load_scene.setEnabled(enabled)
        self.btn_batch.setEnabled(enabled)
        self.btn_visualize.setEnabled(enabled and self.current_scene_path is not None)

    def load_scene(self):
        """加载场景图像（不识别）"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择场景图像", "",
            "Images (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        if not path:
            return
        
        self.current_scene_path = path
        self.scene_paths = [path]
        self.scene_results = []
        self.current_scene_index = 0
        
        # 显示原始图像
        img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is not None:
            self.scene_display.set_image(img)
            self.scene_display.fit_to_view()
            self.btn_recognize.setEnabled(True)
            self.btn_visualize.setEnabled(True)
            self.status_label.setText(f"已加载: {os.path.basename(path)}")
            self._update_scene_nav()

    def recognize_scene(self):
        """识别当前场景"""
        if not self.current_scene_path:
            return
        
        params = self._get_params()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        
        self.worker = RecognitionWorker(self.engine, self.current_scene_path, params)
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
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        self.status_label.setText(f"正在批量处理 {len(paths)} 张图像...")
        
        self.worker = BatchWorker(self.engine, paths, params)
        self.worker.single_result_ready.connect(self._on_batch_single_result)
        self.worker.all_finished.connect(self._on_batch_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.start()

    def show_visualization(self):
        """显示处理过程可视化"""
        if not self.current_scene_path:
            return
        
        params = self._get_params()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self._set_processing_state(True)
        self.status_label.setText("正在生成可视化...")
        
        self.worker = VisualizationWorker(self.engine, self.current_scene_path, params)
        self.worker.result_ready.connect(self._on_visualization_ready)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.start()

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
            
            self.scene_display.set_image(img)
            self.scene_display.fit_to_view()
            self._update_stats_display(stats)
            self._update_scene_nav()
            self.btn_visualize.setEnabled(True)

    def _get_params(self) -> dict:
        """获取当前参数"""
        return {
            "tolerance": self.slider_tol.value() / 100.0,
            "upsample": 2 if self.radio_hog.isChecked() else 1,
            "model": "cnn" if self.radio_cnn.isChecked() else "hog",
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
        self.btn_save_current.setEnabled(not processing and self.current_result_image is not None)
        self.btn_save_all.setEnabled(not processing and len(self.scene_results) > 0)

    def _update_stats_display(self, stats: dict):
        """更新统计数据显示"""
        total = stats.get("total", 0)
        matches = stats.get("matches", 0)
        best_dist = stats.get("best_dist", 1.0)
        
        self.lbl_total.setText(f"检测: {total}")
        self.lbl_matches.setText(f"匹配: {matches}")
        self.lbl_best_dist.setText(f"距离: {best_dist:.3f}")

    # ==================== 回调处理 ====================
    
    def _on_progress(self, value: int):
        """进度更新"""
        self.progress_bar.setValue(value)

    def _on_single_result(self, img: np.ndarray, stats: dict, path: str):
        """单图识别完成"""
        self.progress_bar.setValue(100)
        self._set_processing_state(False)
        
        self.current_result_image = img
        self.current_stats = stats
        self.scene_results = [(img, stats, path)]
        self.current_scene_index = 0
        
        self.scene_display.set_image(img)
        self.scene_display.fit_to_view()
        self._update_stats_display(stats)
        self._update_scene_nav()
        
        self.btn_save_current.setEnabled(True)
        self.btn_visualize.setEnabled(True)
        
        self.status_label.setText(f"识别完成: {stats['total']}人, 匹配{stats['matches']}人")
        self.status_bar.showMessage(f"识别完成 - {os.path.basename(path)}")

    def _on_batch_single_result(self, img: np.ndarray, stats: dict, path: str, current: int, total: int):
        """批量处理中单张完成"""
        self.status_label.setText(f"正在处理 {current}/{total} 张...")

    def _on_batch_finished(self, results: list):
        """批量处理全部完成"""
        self.progress_bar.setValue(100)
        self._set_processing_state(False)
        
        self.scene_results = results
        if results:
            self.current_scene_index = 0
            self._display_scene_result(0)
            self.btn_save_all.setEnabled(True)
        
        self.status_label.setText(f"批量处理完成: 共 {len(results)} 张")
        self.status_bar.showMessage(f"批量处理完成: {len(results)} 张图像")

    def _on_visualization_ready(self, stages: dict, stats: dict):
        """可视化处理完成"""
        self.progress_bar.setValue(100)
        self._set_processing_state(False)
        
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
        
        self.status_label.setText("可视化完成")

    def _on_error(self, msg: str):
        """错误处理"""
        self.progress_bar.setVisible(False)
        self._set_processing_state(False)
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
