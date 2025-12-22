"""
增强型图像显示组件

支持：
- 拖拽上传图片
- 长按对比原图/结果图
- Ctrl+滚轮缩放
- 拖拽平移
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QScrollArea, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QMimeData
from PyQt5.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent, QDragEnterEvent, QDropEvent


class ImageDropLabel(QWidget):
    """
    增强型图像显示组件
    
    支持：
    - 拖拽文件上传
    - 长按切换原图/结果对比
    - Ctrl+滚轮缩放
    - 鼠标拖拽平移
    - 双击适应视图
    """
    
    image_clicked = pyqtSignal()  # 图像被点击信号
    file_dropped = pyqtSignal(str)  # 文件拖入信号
    
    def __init__(self, parent=None, placeholder_text: str = ""):
        super().__init__(parent)
        
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0
        
        # 图像存储
        self.original_pixmap = None  # 原始图像 (处理前/预处理后)
        self.result_pixmap = None    # 结果图像 (带标注)
        self.current_pixmap = None   # 当前显示的图像
        self.is_showing_result = True  # 当前显示的是结果还是原图
        
        # 拖拽状态
        self.dragging = False
        self.last_pos = QPoint()
        
        # 长按状态
        self._is_pressing = False
        
        self._placeholder_text = placeholder_text or "👋\n拖拽图片到这里\n或点击加载"
        
        self._init_ui()
        self.setAcceptDrops(True)
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #FAFAFA; 
                border-radius: 12px; 
            }
        """)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setWordWrap(True)
        self._set_placeholder_style()
        self.image_label.setText(self._placeholder_text)
        
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        # 设置事件过滤
        self.scroll_area.viewport().installEventFilter(self)
    
    def _set_placeholder_style(self):
        """设置占位符样式"""
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #FAFAFA;
                color: #86868B;
                font-size: 15px;
                border-radius: 12px;
                padding: 30px;
                border: 2px dashed #D1D1D6;
            }
        """)
    
    def _set_image_style(self):
        """设置图像显示样式"""
        self.image_label.setStyleSheet("background-color: transparent;")
    
    # ==================== 拖拽功能 ====================
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # 高亮边框
            self.scroll_area.setStyleSheet("""
                QScrollArea { 
                    border: 2px solid #007AFF; 
                    background-color: #F0F8FF; 
                    border-radius: 12px; 
                }
            """)
    
    def dragLeaveEvent(self, event):
        """拖出事件"""
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #FAFAFA; 
                border-radius: 12px; 
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        self.scroll_area.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background-color: #FAFAFA; 
                border-radius: 12px; 
            }
        """)
        
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            # 检查是否为图像文件
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                self.file_dropped.emit(file_path)
    
    # ==================== 图像设置 ====================
    
    def set_image(self, image, is_result: bool = True):
        """
        设置显示的图像
        
        Args:
            image: numpy数组(BGR格式)、QPixmap或QImage
            is_result: True设置为结果图，False设置为原图
        """
        pixmap = self._convert_to_pixmap(image)
        
        if is_result:
            self.result_pixmap = pixmap
            self.is_showing_result = True
        else:
            self.original_pixmap = pixmap
        
        self.current_pixmap = pixmap
        self._update_display()
    
    def set_comparison_images(self, original, result):
        """
        设置对比图像（原图和结果图）
        
        长按显示原图，松开显示结果
        """
        self.original_pixmap = self._convert_to_pixmap(original)
        self.result_pixmap = self._convert_to_pixmap(result)
        self.current_pixmap = self.result_pixmap
        self.is_showing_result = True
        self._update_display()
    
    def _convert_to_pixmap(self, image) -> QPixmap:
        """将各种格式转换为QPixmap"""
        if image is None:
            return None
        
        if isinstance(image, np.ndarray):
            if len(image.shape) == 3:
                h, w, ch = image.shape
                if ch == 3:
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    if not rgb_image.flags['C_CONTIGUOUS']:
                        rgb_image = np.ascontiguousarray(rgb_image)
                    bytes_per_line = ch * w
                    q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    return QPixmap.fromImage(q_image.copy())
                elif ch == 4:
                    rgba_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
                    if not rgba_image.flags['C_CONTIGUOUS']:
                        rgba_image = np.ascontiguousarray(rgba_image)
                    bytes_per_line = ch * w
                    q_image = QImage(rgba_image.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
                    return QPixmap.fromImage(q_image.copy())
            else:
                h, w = image.shape
                if not image.flags['C_CONTIGUOUS']:
                    image = np.ascontiguousarray(image)
                q_image = QImage(image.data, w, h, w, QImage.Format_Grayscale8)
                return QPixmap.fromImage(q_image.copy())
        elif isinstance(image, QImage):
            return QPixmap.fromImage(image)
        elif isinstance(image, QPixmap):
            return image
        
        return None
    
    def set_placeholder_text(self, text: str):
        """设置占位文本"""
        self._placeholder_text = text
        if self.current_pixmap is None:
            self.scroll_area.setWidgetResizable(True)
            self._set_placeholder_style()
            self.image_label.setText(text)
    
    def _update_display(self):
        """更新显示"""
        if self.current_pixmap is None:
            self.set_placeholder_text(self._placeholder_text)
            return
        
        self.scroll_area.setWidgetResizable(False)
        self._set_image_style()
        
        # 计算缩放后的尺寸
        scaled_size = self.current_pixmap.size() * self.scale_factor
        scaled_pixmap = self.current_pixmap.scaled(
            scaled_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
    
    def fit_to_view(self):
        """适应视图大小"""
        if self.current_pixmap is None:
            return
        
        view_size = self.scroll_area.viewport().size()
        img_size = self.current_pixmap.size()
        
        scale_x = view_size.width() / img_size.width()
        scale_y = view_size.height() / img_size.height()
        self.scale_factor = min(scale_x, scale_y, 1.0)
        
        self._update_display()
    
    def reset_zoom(self):
        """重置缩放"""
        self.scale_factor = 1.0
        self._update_display()
    
    # ==================== 事件处理 ====================
    
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
        if event.modifiers() == Qt.ControlModifier and self.current_pixmap:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            new_scale = self.scale_factor * factor
            
            self.scale_factor = max(self.min_scale, min(self.max_scale, new_scale))
            self._update_display()
            return True
        return False
    
    def _handle_mouse_press(self, event: QMouseEvent) -> bool:
        """处理鼠标按下"""
        if event.button() == Qt.LeftButton:
            self._is_pressing = True
            
            # 长按对比功能：如果有对比图，按下时切换到原图
            if self.original_pixmap and self.result_pixmap and self.is_showing_result:
                self.current_pixmap = self.original_pixmap
                self._update_display()
            
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
            
            h_bar = self.scroll_area.horizontalScrollBar()
            v_bar = self.scroll_area.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            return True
        return False
    
    def _handle_mouse_release(self, event: QMouseEvent) -> bool:
        """处理鼠标释放"""
        if event.button() == Qt.LeftButton:
            was_pressing = self._is_pressing
            self._is_pressing = False
            self.dragging = False
            self.scroll_area.viewport().setCursor(Qt.ArrowCursor)
            
            # 长按对比功能：松开时切回结果图
            if self.original_pixmap and self.result_pixmap and not self.is_showing_result:
                self.current_pixmap = self.result_pixmap
                self.is_showing_result = True
                self._update_display()
            elif was_pressing:
                # 恢复显示结果
                if self.result_pixmap:
                    self.current_pixmap = self.result_pixmap
                    self.is_showing_result = True
                    self._update_display()
            
            self.image_clicked.emit()
            return True
        return False
    
    def _handle_double_click(self, event: QMouseEvent) -> bool:
        """处理双击"""
        if event.button() == Qt.LeftButton:
            self.fit_to_view()
            return True
        return False
    
    # ==================== 辅助方法 ====================
    
    def get_current_pixmap(self) -> QPixmap:
        """获取当前显示的pixmap"""
        return self.current_pixmap
    
    def has_image(self) -> bool:
        """是否有图像"""
        return self.current_pixmap is not None
    
    def has_comparison(self) -> bool:
        """是否有对比图"""
        return self.original_pixmap is not None and self.result_pixmap is not None
    
    def clear(self):
        """清空图像"""
        self.original_pixmap = None
        self.result_pixmap = None
        self.current_pixmap = None
        self.scale_factor = 1.0
        self.set_placeholder_text(self._placeholder_text)

