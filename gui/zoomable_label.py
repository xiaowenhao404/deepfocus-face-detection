"""
可缩放图像标签组件

支持 Ctrl+鼠标滚轮缩放、拖拽平移、双击重置
"""

from PyQt5.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPixmap, QImage, QPainter, QWheelEvent, QMouseEvent
import numpy as np
import cv2


class ZoomableImageLabel(QWidget):
    """
    可缩放的图像显示组件
    
    支持：
    - Ctrl + 鼠标滚轮缩放
    - 鼠标拖拽平移
    - 双击重置缩放
    """
    
    image_clicked = pyqtSignal()  # 图像被点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scale_factor = 1.0
        self.min_scale = 0.25
        self.max_scale = 4.0
        self.original_pixmap = None
        self.dragging = False
        self.last_pos = QPoint()
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)  # 默认填充，加载图片后改为False
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #F2F2F7; border-radius: 8px; }")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setWordWrap(True)
        self.image_label.setStyleSheet("""
            background-color: #F2F2F7;
            color: #86868B;
            font-size: 13px;
            border-radius: 8px;
            padding: 20px;
        """)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # 设置事件过滤
        self.scroll_area.viewport().installEventFilter(self)
    
    def set_image(self, image):
        """
        设置显示的图像
        
        Args:
            image: numpy数组(BGR格式)、QPixmap或QImage
        """
        if image is None:
            self.original_pixmap = None
            self.image_label.clear()
            self.image_label.setText("未加载")
            self.scroll_area.setWidgetResizable(True)  # 无图时让标签填充
            self.image_label.setStyleSheet("""
                background-color: #F2F2F7;
                color: #86868B;
                font-size: 13px;
                border-radius: 8px;
                padding: 20px;
            """)
            return
        
        if isinstance(image, np.ndarray):
            # numpy数组转换为QPixmap
            if len(image.shape) == 3:
                h, w, ch = image.shape
                if ch == 3:
                    # BGR转RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    if not rgb_image.flags['C_CONTIGUOUS']:
                        rgb_image = np.ascontiguousarray(rgb_image)
                    bytes_per_line = ch * w
                    q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    self.original_pixmap = QPixmap.fromImage(q_image.copy())
                elif ch == 4:
                    # BGRA转RGBA
                    rgba_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                    if not rgba_image.flags['C_CONTIGUOUS']:
                        rgba_image = np.ascontiguousarray(rgba_image)
                    bytes_per_line = ch * w
                    q_image = QImage(rgba_image.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
                    self.original_pixmap = QPixmap.fromImage(q_image.copy())
            else:
                # 灰度图
                h, w = image.shape
                if not image.flags['C_CONTIGUOUS']:
                    image = np.ascontiguousarray(image)
                q_image = QImage(image.data, w, h, w, QImage.Format_Grayscale8)
                self.original_pixmap = QPixmap.fromImage(q_image.copy())
        elif isinstance(image, QImage):
            self.original_pixmap = QPixmap.fromImage(image)
        elif isinstance(image, QPixmap):
            self.original_pixmap = image
        else:
            return
        
        self.scale_factor = 1.0
        self._update_display()
    
    def set_placeholder_text(self, text: str):
        """设置占位文本"""
        if self.original_pixmap is None:
            self.scroll_area.setWidgetResizable(True)
            self.image_label.setStyleSheet("""
                background-color: #F2F2F7;
                color: #86868B;
                font-size: 13px;
                border-radius: 8px;
                padding: 20px;
            """)
            self.image_label.setText(text)
    
    def _update_display(self):
        """更新显示"""
        if self.original_pixmap is None:
            return
        
        # 有图片时关闭自动填充，允许手动控制尺寸
        self.scroll_area.setWidgetResizable(False)
        self.image_label.setStyleSheet("background-color: transparent;")
        
        # 计算缩放后的尺寸
        scaled_size = self.original_pixmap.size() * self.scale_factor
        scaled_pixmap = self.original_pixmap.scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
    
    def fit_to_view(self):
        """适应视图大小"""
        if self.original_pixmap is None:
            return
        
        view_size = self.scroll_area.viewport().size()
        img_size = self.original_pixmap.size()
        
        # 计算适应比例
        scale_x = view_size.width() / img_size.width()
        scale_y = view_size.height() / img_size.height()
        self.scale_factor = min(scale_x, scale_y, 1.0)
        
        self._update_display()
    
    def reset_zoom(self):
        """重置缩放"""
        self.scale_factor = 1.0
        self._update_display()
    
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
                return self._handle_double_click(event)
        return super().eventFilter(obj, event)
    
    def _handle_wheel(self, event: QWheelEvent) -> bool:
        """处理滚轮事件"""
        if event.modifiers() == Qt.ControlModifier and self.original_pixmap:
            # Ctrl+滚轮缩放
            delta = event.angleDelta().y()
            if delta > 0:
                new_scale = self.scale_factor * 1.1
            else:
                new_scale = self.scale_factor / 1.1
            
            # 限制缩放范围
            self.scale_factor = max(self.min_scale, min(self.max_scale, new_scale))
            self._update_display()
            return True
        return False
    
    def _handle_mouse_press(self, event: QMouseEvent) -> bool:
        """处理鼠标按下"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.scroll_area.viewport().setCursor(Qt.ClosedHandCursor)
            return True
        return False
    
    def _handle_mouse_move(self, event: QMouseEvent) -> bool:
        """处理鼠标移动"""
        if self.dragging:
            delta = event.pos() - self.last_pos
            self.last_pos = event.pos()
            
            # 移动滚动条
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
            self.image_clicked.emit()
            return True
        return False
    
    def _handle_double_click(self, event: QMouseEvent) -> bool:
        """处理双击"""
        if event.button() == Qt.LeftButton:
            self.fit_to_view()
            return True
        return False
    
    def get_current_pixmap(self) -> QPixmap:
        """获取当前显示的pixmap"""
        return self.original_pixmap
    
    def has_image(self) -> bool:
        """是否有图像"""
        return self.original_pixmap is not None

