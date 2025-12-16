"""
DeepFocus 主窗口模块

实现PyQt5图形用户界面，提供人脸识别与定位的可视化操作
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QStatusBar,
    QTextEdit, QGroupBox, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
import numpy as np
import logging
import os

from core.face_engine import FaceEngine
from core.image_utils import safe_imread, save_image


class MainWindow(QMainWindow):
    """
    DeepFocus 主窗口类
    
    提供图形用户界面，整合人脸识别引擎和图像处理功能。
    
    Attributes:
        engine: 人脸识别引擎实例
        current_image: 当前显示的图像
        current_scene_path: 当前场景图像路径
        target_loaded: 目标人脸是否已加载
    """
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化引擎
        self.engine = FaceEngine()
        
        # 状态变量
        self.current_image = None
        self.current_scene_path = None
        self.target_loaded = False
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 初始化UI
        self.init_ui()
        
        self.logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        # 窗口基本设置
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
        
        # 使用分隔器实现可调整大小的布局
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
        self.status_bar.showMessage("就绪 - 请加载目标人脸开始识别")
    
    def create_image_panel(self) -> QWidget:
        """
        创建图像显示面板
        
        Returns:
            QWidget: 图像显示面板部件
        """
        panel = QWidget()
        layout = QVBoxLayout()
        
        # 标题标签
        title = QLabel("图像显示区域")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 图像显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f7;
                border: 2px solid #d1d1d6;
                border-radius: 8px;
            }
        """)
        self.image_label.setText("请加载目标人脸和场景图像")
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setScaledContents(False)
        
        layout.addWidget(self.image_label)
        panel.setLayout(layout)
        
        return panel
    
    def create_control_panel(self) -> QWidget:
        """
        创建控制面板
        
        包含操作按钮、信息显示等控件。
        
        Returns:
            QWidget: 控制面板部件
        """
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
        
        # 加载目标人脸按钮
        self.btn_load_target = QPushButton("1. 加载目标人脸")
        self.btn_load_target.clicked.connect(self.load_target)
        self.btn_load_target.setMinimumHeight(45)
        self.btn_load_target.setToolTip("选择包含目标人物的照片")
        
        # 加载场景图像按钮
        self.btn_load_scene = QPushButton("2. 加载场景图像")
        self.btn_load_scene.clicked.connect(self.load_scene)
        self.btn_load_scene.setMinimumHeight(45)
        self.btn_load_scene.setToolTip("选择需要搜索目标的场景图片")
        
        # 开始识别按钮
        self.btn_process = QPushButton("3. 开始识别")
        self.btn_process.clicked.connect(self.process_image)
        self.btn_process.setMinimumHeight(45)
        self.btn_process.setEnabled(False)
        self.btn_process.setToolTip("在场景图中搜索目标人脸")
        
        # 保存结果按钮
        self.btn_save = QPushButton("4. 保存结果")
        self.btn_save.clicked.connect(self.save_result)
        self.btn_save.setMinimumHeight(45)
        self.btn_save.setEnabled(False)
        self.btn_save.setToolTip("保存识别结果图像")
        
        btn_layout.addWidget(self.btn_load_target)
        btn_layout.addWidget(self.btn_load_scene)
        btn_layout.addWidget(self.btn_process)
        btn_layout.addWidget(self.btn_save)
        btn_group.setLayout(btn_layout)
        layout.addWidget(btn_group)
        
        # 结果信息显示区域
        info_group = QGroupBox("识别信息")
        info_layout = QVBoxLayout()
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(250)
        self.info_text.setText("等待操作...\n\n使用步骤：\n1. 加载目标人脸图像\n2. 加载场景图像\n3. 点击开始识别\n4. 保存识别结果")
        
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 添加弹性空间
        layout.addStretch()
        panel.setLayout(layout)
        
        return panel
    
    def load_target(self):
        """
        加载目标人脸
        
        打开文件对话框，选择目标人脸图像，
        使用FaceEngine加载并提取特征。
        """
        self.logger.info("用户点击：加载目标人脸")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择目标人脸图像",
            "Images/",
            "图像文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        
        if not file_path:
            self.logger.info("用户取消选择")
            return
        
        self.logger.info(f"选择的目标图像: {file_path}")
        self.status_bar.showMessage("正在加载目标人脸...")
        
        # 使用引擎加载目标人脸
        success = self.engine.load_target_face(file_path)
        
        if success:
            self.target_loaded = True
            self.status_bar.showMessage(f"[成功] 目标人脸加载成功")
            self.info_text.append(f"\n[成功] 目标人脸已加载")
            self.info_text.append(f"路径: {os.path.basename(file_path)}")
            
            # 获取目标信息
            target_info = self.engine.get_target_info()
            self.info_text.append(f"特征维度: {target_info['feature_dim']}")
            self.info_text.append(f"检测模型: {target_info['model_method'].upper()}")
            
            # 启用处理按钮
            self.btn_process.setEnabled(True)
            
            self.logger.info("目标人脸加载成功")
        else:
            self.target_loaded = False
            self.status_bar.showMessage("[失败] 未检测到人脸")
            self.info_text.append(f"\n[失败] 未在图像中检测到人脸")
            self.info_text.append("请确保图像包含清晰可见的人脸")
            
            self.logger.warning("目标人脸加载失败")
            
            # 显示错误对话框
            QMessageBox.warning(
                self,
                "加载失败",
                "未在选择的图像中检测到人脸！\n\n请确保：\n1. 图像包含清晰的人脸\n2. 人脸未被过度遮挡\n3. 图像质量良好"
            )
    
    def load_scene(self):
        """
        加载场景图像
        
        打开文件对话框，选择场景图像并显示。
        """
        self.logger.info("用户点击：加载场景图像")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择场景图像",
            "Images/",
            "图像文件 (*.jpg *.jpeg *.png *.bmp);;所有文件 (*.*)"
        )
        
        if not file_path:
            self.logger.info("用户取消选择")
            return
        
        self.logger.info(f"选择的场景图像: {file_path}")
        self.status_bar.showMessage("正在加载场景图像...")
        
        # 读取图像
        self.current_image = safe_imread(file_path)
        self.current_scene_path = file_path
        
        if self.current_image is not None:
            # 显示图像
            self.display_image(self.current_image)
            
            # 更新状态
            self.status_bar.showMessage(f"[成功] 场景图像已加载")
            self.info_text.append(f"\n[信息] 场景图像已加载")
            self.info_text.append(f"路径: {os.path.basename(file_path)}")
            self.info_text.append(f"尺寸: {self.current_image.shape[1]}x{self.current_image.shape[0]}")
            
            self.logger.info(f"场景图像加载成功: {self.current_image.shape}")
        else:
            self.status_bar.showMessage("[失败] 无法读取图像")
            self.info_text.append(f"\n[失败] 无法读取图像文件")
            
            self.logger.error("场景图像加载失败")
            
            QMessageBox.critical(
                self,
                "加载失败",
                f"无法读取图像文件！\n\n文件路径: {file_path}"
            )
    
    def process_image(self):
        """
        处理图像（简化版本，TASK005将实现多线程版本）
        
        在场景图中搜索目标人脸并标注结果。
        """
        self.logger.info("用户点击：开始识别")
        
        # 检查前置条件
        if not self.target_loaded:
            self.status_bar.showMessage("[警告] 请先加载目标人脸")
            QMessageBox.warning(self, "提示", "请先加载目标人脸！")
            return
        
        if self.current_scene_path is None:
            self.status_bar.showMessage("[警告] 请先加载场景图像")
            QMessageBox.warning(self, "提示", "请先加载场景图像！")
            return
        
        # 禁用按钮防止重复点击
        self.btn_process.setEnabled(False)
        self.status_bar.showMessage("正在识别中，请稍候...")
        self.info_text.append("\n[开始] 识别处理中...")
        
        try:
            # 执行识别（注意：这里会阻塞UI，TASK005将改为多线程）
            self.logger.info("开始处理场景图...")
            result_img, info = self.engine.process_scene(
                self.current_scene_path,
                upsample=2  # 教室场景使用upsample=2
            )
            
            # 更新显示
            self.current_image = result_img
            self.display_image(result_img)
            
            # 更新信息
            self.info_text.append(f"[结果] {info}")
            self.status_bar.showMessage("[成功] 识别完成")
            
            # 启用保存按钮
            self.btn_save.setEnabled(True)
            
            self.logger.info(f"识别完成: {info}")
            
        except Exception as e:
            self.info_text.append(f"\n[错误] 识别失败: {str(e)}")
            self.status_bar.showMessage(f"[错误] 识别失败")
            
            self.logger.exception(f"识别过程发生错误: {e}")
            
            QMessageBox.critical(
                self,
                "识别失败",
                f"识别过程发生错误！\n\n错误信息: {str(e)}"
            )
        
        finally:
            # 恢复按钮状态
            self.btn_process.setEnabled(True)
    
    def save_result(self):
        """
        保存识别结果
        
        打开保存对话框，将标注后的图像保存到文件。
        """
        self.logger.info("用户点击：保存结果")
        
        if self.current_image is None:
            self.status_bar.showMessage("[警告] 没有可保存的结果")
            QMessageBox.warning(self, "提示", "没有可保存的结果！\n\n请先完成识别。")
            return
        
        # 打开保存对话框
        default_name = "result.jpg"
        if self.current_scene_path:
            # 根据原文件名生成默认保存名
            base_name = os.path.splitext(os.path.basename(self.current_scene_path))[0]
            default_name = f"{base_name}_result.jpg"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存识别结果",
            f"outputs/results/{default_name}",
            "JPEG图像 (*.jpg);;PNG图像 (*.png);;所有文件 (*.*)"
        )
        
        if not file_path:
            self.logger.info("用户取消保存")
            return
        
        self.logger.info(f"保存路径: {file_path}")
        self.status_bar.showMessage("正在保存...")
        
        # 保存图像
        success = save_image(self.current_image, file_path, quality=95)
        
        if success:
            self.status_bar.showMessage(f"[成功] 结果已保存")
            self.info_text.append(f"\n[保存] 结果已保存到: {os.path.basename(file_path)}")
            
            self.logger.info(f"结果保存成功: {file_path}")
            
            QMessageBox.information(
                self,
                "保存成功",
                f"识别结果已成功保存！\n\n保存位置:\n{file_path}"
            )
        else:
            self.status_bar.showMessage("[失败] 保存失败")
            self.info_text.append(f"\n[错误] 保存失败")
            
            self.logger.error("结果保存失败")
            
            QMessageBox.critical(
                self,
                "保存失败",
                "保存图像时发生错误！\n\n请检查文件路径和磁盘空间。"
            )
    
    def display_image(self, cv_img: np.ndarray):
        """
        在界面上显示图像
        
        将OpenCV图像（BGR格式）转换为Qt图像并显示。
        
        Args:
            cv_img: OpenCV图像数组（BGR格式）
        """
        try:
            # BGR转RGB（Qt需要RGB格式）
            rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            
            # 转换为QImage
            q_img = QImage(
                rgb_img.data,
                w,
                h,
                bytes_per_line,
                QImage.Format_RGB888
            )
            
            # 转换为QPixmap并缩放
            pixmap = QPixmap.fromImage(q_img)
            
            # 缩放到标签大小，保持宽高比
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # 显示图像
            self.image_label.setPixmap(scaled_pixmap)
            
            self.logger.debug(f"图像显示成功: {w}x{h}")
            
        except Exception as e:
            self.logger.exception(f"显示图像时发生错误: {e}")
            self.status_bar.showMessage("[错误] 图像显示失败")
    
    def closeEvent(self, event):
        """
        窗口关闭事件处理
        
        在关闭窗口前进行清理工作。
        
        Args:
            event: 关闭事件
        """
        reply = QMessageBox.question(
            self,
            '确认退出',
            '确定要退出DeepFocus吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logger.info("用户关闭应用")
            event.accept()
        else:
            event.ignore()
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>DeepFocus</h2>
        <p><b>人脸识别与定位系统</b></p>
        <p>版本: 1.0.0</p>
        <p>基于深度学习的智能人脸识别应用</p>
        <br>
        <p>技术栈：</p>
        <ul>
            <li>Python 3.9+</li>
            <li>PyQt5 - 图形界面</li>
            <li>face_recognition - 人脸识别</li>
            <li>OpenCV - 图像处理</li>
        </ul>
        <br>
        <p>GitHub: <a href='https://github.com/xiaowenhao404/DeepFocus'>
        https://github.com/xiaowenhao404/DeepFocus</a></p>
        """
        
        QMessageBox.about(self, "关于 DeepFocus", about_text)

