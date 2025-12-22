"""
处理过程可视化弹窗

展示人脸识别各阶段的图像处理结果
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent
import numpy as np
import cv2


class ZoomableStageWidget(QFrame):
    """可缩放的阶段图像显示组件"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.original_pixmap = None
        self.scale_factor = 1.0
        self.base_scale = 1.0  # 适应窗口的基础缩放
        self.user_zoom = 1.0   # 用户缩放倍数（1.0表示未缩放）
        self.min_zoom = 0.5    # 最小缩放倍数
        self.max_zoom = 4.0    # 最大缩放倍数
        self.dragging = False
        self.last_pos = QPoint()
        self._init_ui()
    
    def _init_ui(self):
        self.setObjectName("ZoomableStageWidget")
        self.setStyleSheet("""
            QFrame#ZoomableStageWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
            }
        """)
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(250, 200)
        
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
        self.title_label.setFixedHeight(20)
        
        # 滚动区域（支持缩放后的平移）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #F5F5F7; 
                border-radius: 4px;
            }
        """)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: transparent;")
        self.image_label.setText("无图像")
        
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.viewport().installEventFilter(self)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.scroll_area, 1)
    
    def set_image(self, image: np.ndarray):
        """设置图像"""
        if image is None:
            self.original_pixmap = None
            self.image_label.clear()
            self.image_label.setText("无图像")
            self.scroll_area.setWidgetResizable(True)
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
        
        self.original_pixmap = QPixmap.fromImage(q_image.copy())
        self.user_zoom = 1.0  # 重置用户缩放
        self._fit_to_view()
    
    def _fit_to_view(self):
        """适应视图大小"""
        if self.original_pixmap is None:
            return
        
        self.scroll_area.setWidgetResizable(False)
        view_size = self.scroll_area.viewport().size()
        img_size = self.original_pixmap.size()
        
        if img_size.width() > 0 and img_size.height() > 0:
            scale_x = view_size.width() / img_size.width()
            scale_y = view_size.height() / img_size.height()
            # 计算基础缩放（让图片适应窗口）
            self.base_scale = min(scale_x, scale_y, 1.0)
            # 最终缩放 = 基础缩放 * 用户缩放
            self.scale_factor = self.base_scale * self.user_zoom
        
        self._update_display()
    
    def _update_display(self):
        """更新显示"""
        if self.original_pixmap is None:
            return
        
        scaled_size = self.original_pixmap.size() * self.scale_factor
        scaled_pixmap = self.original_pixmap.scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        if obj == self.scroll_area.viewport():
            if event.type() == event.Wheel:
                return self._handle_wheel(event)
            elif event.type() == event.MouseButtonPress:
                return self._handle_mouse_press(event)
            elif event.type() == event.MouseMove:
                return self._handle_mouse_move(event)
            elif event.type() == event.MouseButtonRelease:
                return self._handle_mouse_release(event)
            elif event.type() == event.MouseButtonDblClick:
                # 双击重置缩放
                self.user_zoom = 1.0
                self._fit_to_view()
                return True
        return super().eventFilter(obj, event)
    
    def _handle_wheel(self, event: QWheelEvent) -> bool:
        """处理滚轮事件 - Ctrl+滚轮缩放"""
        if event.modifiers() == Qt.ControlModifier and self.original_pixmap:
            delta = event.angleDelta().y()
            # 使用更平滑的缩放步进
            zoom_step = 1.1
            if delta > 0:
                new_zoom = self.user_zoom * zoom_step
            else:
                new_zoom = self.user_zoom / zoom_step
            
            # 限制用户缩放范围
            self.user_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
            # 更新最终缩放因子
            self.scale_factor = self.base_scale * self.user_zoom
            self._update_display()
            return True
        return False
    
    def _handle_mouse_press(self, event: QMouseEvent) -> bool:
        """处理鼠标按下 - 开始拖拽"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.scroll_area.viewport().setCursor(Qt.ClosedHandCursor)
            return True
        return False
    
    def _handle_mouse_move(self, event: QMouseEvent) -> bool:
        """处理鼠标移动 - 拖拽平移"""
        if self.dragging:
            delta = event.pos() - self.last_pos
            self.last_pos = event.pos()
            
            h_bar = self.scroll_area.horizontalScrollBar()
            v_bar = self.scroll_area.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            return True
        return False
    
    def _handle_mouse_release(self, event: QMouseEvent) -> bool:
        """处理鼠标释放"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.scroll_area.viewport().setCursor(Qt.ArrowCursor)
            return True
        return False
    
    def resizeEvent(self, event):
        """调整大小时重新适应"""
        super().resizeEvent(event)
        if self.original_pixmap:
            # 窗口调整时重新计算基础缩放
            self._fit_to_view()
    
    def showEvent(self, event):
        """显示时更新图像"""
        super().showEvent(event)
        QTimer.singleShot(50, self._fit_to_view)


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
        # 添加最大化/最小化按钮，移除帮助按钮
        self.setWindowFlags(
            self.windowFlags() 
            & ~Qt.WindowContextHelpButtonHint 
            | Qt.WindowMaximizeButtonHint 
            | Qt.WindowMinimizeButtonHint
        )
        
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
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
        
        # 网格布局（不用滚动区域，直接让图像随窗口缩放）
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(15)
        
        # 设置列伸展因子，让各列均匀分配空间
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(2, 1)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 1)
        
        # 创建5个阶段的显示组件（2行3列布局，最后一格放说明）
        stage_configs = [
            ("original", "1. 原始图像", 0, 0),
            ("gamma", "2. Gamma校正", 0, 1),
            ("clahe", "3. CLAHE增强", 0, 2),
            ("detection", "4. 人脸检测", 1, 0),
            ("final", "5. 最终结果", 1, 1),
        ]
        
        self.stage_widgets = {}
        for key, title, row, col in stage_configs:
            widget = ZoomableStageWidget(title)
            self.stage_widgets[key] = widget
            grid_layout.addWidget(widget, row, col)
        
        # 图例说明（放在最后一个格子）
        legend_widget = self._create_legend_widget()
        grid_layout.addWidget(legend_widget, 1, 2)
        
        layout.addWidget(grid_widget, 1)
        
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
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        widget.setMinimumSize(250, 200)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        # 标题（保存引用用于动态调整）
        self.legend_title = QLabel("图例说明")
        self.legend_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #1D1D1F;")
        self.legend_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.legend_title)
        
        layout.addSpacing(10)
        
        # 图例项
        legends = [
            ("#00C853", "最佳匹配"),
            ("#FFD600", "其他匹配"),
            ("#FF3D00", "未能匹配"),
        ]
        
        self.legend_labels = []
        self.legend_dots = []
        for color, text in legends:
            row = QHBoxLayout()
            row.setSpacing(12)
            
            dot = QLabel()
            dot.setFixedSize(18, 18)
            dot.setStyleSheet(f"""
                background-color: {color};
                border-radius: 9px;
            """)
            self.legend_dots.append(dot)
            
            label = QLabel(text)
            label.setStyleSheet("font-size: 14px; color: #333333;")
            self.legend_labels.append(label)
            
            row.addWidget(dot)
            row.addWidget(label)
            row.addStretch()
            
            layout.addLayout(row)
        
        layout.addStretch()
        
        # 处理流程说明
        self.flow_label = QLabel("处理流程：\n原图 → Gamma校正 → CLAHE增强\n→ 人脸检测 → 特征匹配 → 结果标注")
        self.flow_label.setStyleSheet("font-size: 12px; color: #86868B;")
        self.flow_label.setWordWrap(True)
        layout.addWidget(self.flow_label)
        
        return widget
    
    def _update_legend_font_size(self):
        """根据窗口大小更新图例文字大小"""
        # 获取窗口宽度，计算基础字号
        width = self.width()
        base_size = max(11, min(16, int(width / 80)))
        
        # 更新标题
        if hasattr(self, 'legend_title'):
            self.legend_title.setStyleSheet(f"font-weight: bold; font-size: {base_size + 2}px; color: #1D1D1F;")
        
        # 更新图例标签
        if hasattr(self, 'legend_labels'):
            for label in self.legend_labels:
                label.setStyleSheet(f"font-size: {base_size + 1}px; color: #333333;")
        
        # 更新流程说明
        if hasattr(self, 'flow_label'):
            self.flow_label.setStyleSheet(f"font-size: {base_size}px; color: #86868B;")
        
        # 更新圆点大小
        if hasattr(self, 'legend_dots'):
            dot_size = max(14, min(22, base_size + 4))
            colors = ["#00C853", "#FFD600", "#FF3D00"]
            for i, dot in enumerate(self.legend_dots):
                dot.setFixedSize(dot_size, dot_size)
                dot.setStyleSheet(f"""
                    background-color: {colors[i]};
                    border-radius: {dot_size // 2}px;
                """)
    
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
    
    def showEvent(self, event):
        """显示时更新所有图像和字体"""
        super().showEvent(event)
        # 延迟更新所有图像和字体，确保布局完成
        QTimer.singleShot(100, self._refresh_all_images)
        QTimer.singleShot(100, self._update_legend_font_size)
    
    def resizeEvent(self, event):
        """窗口大小改变时更新所有图像和字体"""
        super().resizeEvent(event)
        self._refresh_all_images()
        self._update_legend_font_size()
    
    def _refresh_all_images(self):
        """刷新所有阶段图像"""
        for widget in self.stage_widgets.values():
            if widget.original_pixmap:
                widget._fit_to_view()
    
    @staticmethod
    def show_stages(stages: dict, stats: dict, parent=None):
        """静态方法：显示可视化弹窗"""
        dialog = VisualizationDialog(parent)
        dialog.set_stages(stages, stats)
        dialog.exec_()
