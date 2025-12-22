"""
模型对比窗口

同时使用多个模型进行识别，展示各自的效果图进行对比
支持 Ctrl+滚轮缩放、拖拽平移
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QProgressBar, QFrame, QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import cv2
from typing import List, Dict, Optional, Tuple
import logging

from gui.visualization_dialog import ZoomableStageWidget


class ModelCompareWorker(QThread):
    """单个模型的处理线程"""
    result_ready = pyqtSignal(str, object, dict)  # model_name, img, stats
    error_occurred = pyqtSignal(str, str)  # model_name, error_msg
    progress_updated = pyqtSignal(str, int)  # model_name, progress (0-100)
    
    def __init__(
        self,
        model_name: str,
        engine,
        engine_type: str,
        scene_path: str,
        params: dict
    ):
        super().__init__()
        self.model_name = model_name
        self.engine = engine
        self.engine_type = engine_type
        self.scene_path = scene_path
        self.params = params
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        try:
            def progress_callback(value):
                self.progress_updated.emit(self.model_name, value)
            
            # 根据引擎类型调用不同的处理方法
            if self.engine_type == "opencv_dnn":
                result_img, stats = self.engine.process_scene(
                    self.scene_path,
                    tolerance=self.params['tolerance'],
                    best_only=self.params.get('best_only', False),
                    progress_callback=progress_callback
                )
            else:
                # dlib 引擎 (HOG/CNN)
                result_img, stats = self.engine.process_scene(
                    self.scene_path,
                    tolerance=self.params['tolerance'],
                    upsample=self.params.get('upsample', 1),
                    model=self.params.get('model', 'hog'),
                    use_clahe=self.params.get('use_clahe', True),
                    gamma=self.params.get('gamma', 1.0),
                    best_only=self.params.get('best_only', False),
                    progress_callback=progress_callback
                )
            
            if result_img is None:
                error_msg = stats.get('error', '未知错误')
                self.error_occurred.emit(self.model_name, error_msg)
            else:
                self.result_ready.emit(self.model_name, result_img, stats)
                
        except Exception as e:
            self.logger.error(f"{self.model_name} 处理出错: {e}")
            self.error_occurred.emit(self.model_name, str(e))


class CompareDialog(QDialog):
    """
    模型对比窗口
    
    同时运行多个模型并展示各自的识别结果，
    方便用户比较不同模型的效果
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 模型信息
        self.models: List[Dict] = []
        self.workers: List[ModelCompareWorker] = []
        self.results: Dict[str, Tuple[np.ndarray, dict]] = {}
        self.progress_values: Dict[str, int] = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("模型效果对比")
        # 添加最大化/最小化按钮，移除帮助按钮
        self.setWindowFlags(
            self.windowFlags() 
            & ~Qt.WindowContextHelpButtonHint 
            | Qt.WindowMaximizeButtonHint 
            | Qt.WindowMinimizeButtonHint
        )
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F7;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("模型效果对比")
        title_label.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #1D1D1F;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 进度条区域
        progress_frame = QFrame()
        progress_frame.setObjectName("ProgressFrame")
        progress_frame.setStyleSheet("""
            QFrame#ProgressFrame {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setSpacing(8)
        
        self.progress_label = QLabel("准备中...")
        self.progress_label.setStyleSheet("font-size: 14px; color: #86868B;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E5E5E5;
                border-radius: 4px;
                text-align: center;
                height: 24px;
                font-size: 12px;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        
        # 结果网格区域
        self.grid_widget = QFrame()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(15)
        layout.addWidget(self.grid_widget, 1)
        
        # 存储各模型的显示组件
        self.model_widgets: Dict[str, ZoomableStageWidget] = {}
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_close = QPushButton("关闭")
        self.btn_close.setFixedSize(120, 36)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0062CC;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def setup_models(self, models: List[Dict]):
        """
        设置要对比的模型
        
        Args:
            models: 模型列表，每个元素是 {
                "name": 显示名称,
                "engine": 引擎实例,
                "engine_type": 引擎类型 ("dlib", "opencv_dnn"),
                "params": 参数字典
            }
        """
        self.models = models
        self.results = {}
        self.progress_values = {m["name"]: 0 for m in models}
        
        # 清除旧的组件
        for widget in self.model_widgets.values():
            widget.deleteLater()
        self.model_widgets = {}
        
        # 计算网格布局
        n = len(models)
        if n <= 2:
            rows, cols = 1, n
        elif n <= 4:
            rows, cols = 2, 2
        else:
            rows, cols = 2, 3
        
        # 设置列伸展因子
        for i in range(cols):
            self.grid_layout.setColumnStretch(i, 1)
        for i in range(rows):
            self.grid_layout.setRowStretch(i, 1)
        
        # 创建各模型的显示组件
        for idx, model_info in enumerate(models):
            name = model_info["name"]
            row = idx // cols
            col = idx % cols
            
            widget = ZoomableStageWidget(name)
            widget.set_image(None)
            self.model_widgets[name] = widget
            self.grid_layout.addWidget(widget, row, col)
        
        self.progress_label.setText(f"正在对比 {n} 个模型...")
    
    def start_comparison(self, scene_path: str):
        """
        开始对比处理
        
        Args:
            scene_path: 场景图像路径
        """
        if not self.models:
            QMessageBox.warning(self, "错误", "没有设置要对比的模型")
            return
        
        self.results = {}
        self.progress_values = {m["name"]: 0 for m in self.models}
        self.workers = []
        
        # 为每个模型创建工作线程
        for model_info in self.models:
            worker = ModelCompareWorker(
                model_name=model_info["name"],
                engine=model_info["engine"],
                engine_type=model_info["engine_type"],
                scene_path=scene_path,
                params=model_info["params"]
            )
            worker.result_ready.connect(self._on_result_ready)
            worker.error_occurred.connect(self._on_error)
            worker.progress_updated.connect(self._on_progress)
            self.workers.append(worker)
        
        # 启动所有线程
        for worker in self.workers:
            worker.start()
        
        self._update_overall_progress()
    
    def _on_result_ready(self, model_name: str, img: np.ndarray, stats: dict):
        """单个模型处理完成"""
        self.results[model_name] = (img, stats)
        self.progress_values[model_name] = 100
        
        # 更新显示
        if model_name in self.model_widgets:
            widget = self.model_widgets[model_name]
            widget.set_image(img)
            
            # 更新标题显示统计信息
            total = stats.get("total", 0)
            matches = stats.get("matches", 0)
            best_sim = stats.get("best_similarity", 0.0)
            time_used = stats.get("process_time", 0)
            widget.title_label.setText(
                f"{model_name} | 检测:{total} 匹配:{matches} 相似度:{best_sim:.1f}% 耗时:{time_used:.2f}s"
            )
        
        self._update_overall_progress()
        self._check_completion()
    
    def _on_error(self, model_name: str, error_msg: str):
        """单个模型处理出错"""
        self.progress_values[model_name] = 100
        
        if model_name in self.model_widgets:
            widget = self.model_widgets[model_name]
            widget.title_label.setText(f"{model_name} | 错误")
            widget.image_label.setText(f"处理失败:\n{error_msg}")
        
        self.logger.error(f"{model_name} 处理失败: {error_msg}")
        self._update_overall_progress()
        self._check_completion()
    
    def _on_progress(self, model_name: str, progress: int):
        """单个模型进度更新"""
        self.progress_values[model_name] = progress
        self._update_overall_progress()
    
    def _update_overall_progress(self):
        """更新整体进度"""
        if not self.progress_values:
            return
        
        # 计算平均进度
        total_progress = sum(self.progress_values.values())
        overall = int(total_progress / len(self.progress_values))
        self.progress_bar.setValue(overall)
        
        # 更新状态文本
        completed = sum(1 for v in self.progress_values.values() if v >= 100)
        total = len(self.progress_values)
        self.progress_label.setText(f"已完成 {completed}/{total} 个模型")
    
    def _check_completion(self):
        """检查是否所有模型都处理完成"""
        all_done = all(v >= 100 for v in self.progress_values.values())
        if all_done:
            self.progress_label.setText("全部完成!")
            self.progress_bar.setValue(100)
            
            # 延迟刷新所有图像
            QTimer.singleShot(100, self._refresh_all_images)
    
    def _refresh_all_images(self):
        """刷新所有图像显示"""
        for widget in self.model_widgets.values():
            if widget.original_pixmap:
                widget._fit_to_view()
    
    def closeEvent(self, event):
        """关闭时停止所有工作线程"""
        for worker in self.workers:
            if worker.isRunning():
                worker.terminate()
                worker.wait(1000)
        super().closeEvent(event)
    
    def showEvent(self, event):
        """显示时刷新图像"""
        super().showEvent(event)
        QTimer.singleShot(100, self._refresh_all_images)
    
    def resizeEvent(self, event):
        """调整大小时刷新图像"""
        super().resizeEvent(event)
        self._refresh_all_images()
    
    @staticmethod
    def run_comparison(
        models: List[Dict],
        scene_path: str,
        parent=None
    ) -> Optional['CompareDialog']:
        """
        静态方法：运行模型对比
        
        Args:
            models: 模型列表
            scene_path: 场景图像路径
            parent: 父窗口
            
        Returns:
            CompareDialog 实例
        """
        dialog = CompareDialog(parent)
        dialog.setup_models(models)
        dialog.show()
        dialog.start_comparison(scene_path)
        return dialog

