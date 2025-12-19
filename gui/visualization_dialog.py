"""
处理过程可视化弹窗

展示人脸识别各阶段的图像处理结果
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import numpy as np
import cv2


class ImageStageWidget(QFrame):
    """单个阶段图像显示组件"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.original_pixmap = None
        self._init_ui()
    
    def _init_ui(self):
        self.setObjectName("ImageStageWidget")
        self.setStyleSheet("""
            QFrame#ImageStageWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 标题
        self.title_label = QLabel(self.title)
        self.title_label.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #1D1D1F;
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # 图像
        self.image_label = QLabel()
        self.image_label.setMinimumSize(200, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #F5F5F7;
            border-radius: 4px;
        """)
        self.image_label.setScaledContents(False)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label, 1)
    
    def set_image(self, image: np.ndarray):
        """设置图像"""
        if image is None:
            self.image_label.setText("无图像")
            return
        
        # BGR转RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image
        
        if not rgb_image.flags['C_CONTIGUOUS']:
            rgb_image = np.ascontiguousarray(rgb_image)
        
        h, w = rgb_image.shape[:2]
        if len(rgb_image.shape) == 3:
            ch = rgb_image.shape[2]
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        else:
            q_image = QImage(rgb_image.data, w, h, w, QImage.Format_Grayscale8)
        
        pixmap = QPixmap.fromImage(q_image.copy())
        self.original_pixmap = pixmap
        
        # 缩放适应标签大小
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """调整大小时重新缩放图像"""
        super().resizeEvent(event)
        if self.original_pixmap:
            scaled_pixmap = self.original_pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)


class VisualizationDialog(QDialog):
    """
    处理过程可视化弹窗
    
    展示人脸识别各阶段的图像处理结果：
    - 原始图像
    - Gamma校正后
    - CLAHE增强后
    - 人脸检测框
    - 最终结果
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stages = {}
        self.stats = {}
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("处理过程可视化")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F7;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("处理过程可视化")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1D1D1F;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 统计信息
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("""
            font-size: 14px;
            color: #86868B;
            padding: 10px;
            background-color: #FFFFFF;
            border-radius: 8px;
        """)
        self.stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.stats_label)
        
        # 滚动区域包裹网格
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setSpacing(15)
        
        # 创建5个阶段的显示组件（2行3列布局，最后一格空着或放说明）
        stage_configs = [
            ("original", "1. 原始图像", 0, 0),
            ("gamma", "2. Gamma校正", 0, 1),
            ("clahe", "3. CLAHE增强", 0, 2),
            ("detection", "4. 人脸检测", 1, 0),
            ("final", "5. 最终结果", 1, 1),
        ]
        
        self.stage_widgets = {}
        for key, title, row, col in stage_configs:
            widget = ImageStageWidget(title)
            self.stage_widgets[key] = widget
            grid_layout.addWidget(widget, row, col)
        
        # 图例说明（放在最后一个格子）
        legend_widget = self._create_legend_widget()
        grid_layout.addWidget(legend_widget, 1, 2)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area, 1)
        
        # 关闭按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedSize(120, 36)
        close_btn.setStyleSheet("""
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
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _create_legend_widget(self) -> QFrame:
        """创建图例说明组件"""
        widget = QFrame()
        widget.setObjectName("LegendWidget")
        widget.setStyleSheet("""
            QFrame#LegendWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("图例说明")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1D1D1F;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 图例项
        legends = [
            ("#00C853", "最佳匹配"),
            ("#FFD600", "其他匹配"),
            ("#FF3D00", "未能匹配"),
        ]
        
        for color, text in legends:
            row = QHBoxLayout()
            row.setSpacing(10)
            
            dot = QLabel()
            dot.setFixedSize(16, 16)
            dot.setStyleSheet(f"""
                background-color: {color};
                border-radius: 8px;
            """)
            
            label = QLabel(text)
            label.setStyleSheet("font-size: 13px; color: #333333;")
            
            row.addWidget(dot)
            row.addWidget(label)
            row.addStretch()
            
            layout.addLayout(row)
        
        layout.addStretch()
        
        # 处理流程说明
        flow_label = QLabel("处理流程：\n原图 → Gamma校正 → CLAHE增强 → 人脸检测 → 特征匹配 → 结果标注")
        flow_label.setStyleSheet("font-size: 11px; color: #86868B;")
        flow_label.setWordWrap(True)
        layout.addWidget(flow_label)
        
        return widget
    
    def set_stages(self, stages: dict, stats: dict):
        """
        设置各阶段图像
        
        Args:
            stages: 包含各阶段图像的字典
            stats: 统计信息
        """
        self.stages = stages
        self.stats = stats
        
        # 更新统计信息
        total = stats.get("total", 0)
        matches = stats.get("matches", 0)
        best_dist = stats.get("best_dist", 1.0)
        
        self.stats_label.setText(
            f"检测人数: {total}  |  匹配人数: {matches}  |  最佳距离: {best_dist:.3f}"
        )
        
        # 更新各阶段图像
        for key, widget in self.stage_widgets.items():
            if key in stages:
                widget.set_image(stages[key])
            else:
                widget.set_image(None)
    
    @staticmethod
    def show_stages(stages: dict, stats: dict, parent=None):
        """静态方法：显示可视化弹窗"""
        dialog = VisualizationDialog(parent)
        dialog.set_stages(stages, stats)
        dialog.exec_()

