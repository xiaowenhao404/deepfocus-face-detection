"""
DeepFocus 核心人脸识别引擎

实现人脸检测、特征提取和特征匹配功能
基于face_recognition库（dlib + ResNet）
"""

import face_recognition
import cv2
import numpy as np
from typing import Tuple, Optional, List
import logging

from core.matcher import compute_confidence


class FaceEngine:
    """
    人脸识别引擎核心类
    
    提供人脸检测、特征提取和匹配功能。
    基于深度学习的ResNet-34网络提取128维人脸特征向量。
    
    Attributes:
        model_method: 检测模型方法 ('hog' 或 'cnn')
        tolerance: 匹配容忍度阈值
        target_encoding: 目标人脸的特征向量
    """
    
    def __init__(self, model_method: str = 'hog', tolerance: float = 0.45):
        """
        初始化人脸识别引擎
        
        Args:
            model_method: 检测方法
                - 'hog': HOG特征 + 线性SVM，速度快，适合CPU
                - 'cnn': 卷积神经网络，精度高，需要GPU加速
            tolerance: 匹配容忍度，范围0.0-1.0
                - 值越小越严格，越大越宽松
                - 针对亚洲人脸，推荐0.40-0.45
                - 默认0.45
        """
        self.model_method = model_method
        self.tolerance = tolerance
        self.target_encoding = None
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"FaceEngine初始化: model={model_method}, tolerance={tolerance}")
    
    def load_target_face(self, image_path: str) -> bool:
        """
        加载并编码目标人脸
        
        从图像文件中检测人脸，提取特征向量并保存。
        如果图像中有多个人脸，自动选择面积最大的人脸作为目标。
        
        Args:
            image_path: 目标人脸图像文件路径（支持中文路径）
            
        Returns:
            bool: 成功返回True，失败返回False
            
        Raises:
            无异常抛出，所有错误通过返回False表示
            
        Examples:
            >>> engine = FaceEngine()
            >>> success = engine.load_target_face("Images/目标脸.jpg")
            >>> if success:
            ...     print("目标人脸加载成功")
        """
        try:
            # 1. 读取图像（支持中文路径）
            # 使用np.fromfile读取二进制数据，避免cv2.imread对中文路径的限制
            self.logger.info(f"正在加载目标人脸: {image_path}")
            img_data = np.fromfile(image_path, dtype=np.uint8)
            img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
            
            if img is None:
                self.logger.error(f"无法读取图像文件: {image_path}")
                return False
            
            self.logger.info(f"图像读取成功，尺寸: {img.shape}")
            
            # 2. BGR转RGB（OpenCV使用BGR，face_recognition需要RGB）
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 3. 检测人脸位置
            # 返回格式: [(top, right, bottom, left), ...]
            self.logger.info(f"使用{self.model_method}模型检测人脸...")
            boxes = face_recognition.face_locations(rgb_img, model=self.model_method)
            
            if not boxes:
                self.logger.warning(f"未在图像中检测到人脸: {image_path}")
                return False
            
            self.logger.info(f"检测到 {len(boxes)} 个人脸")
            
            # 4. 选择最大人脸（按面积排序）
            # 计算面积: (bottom - top) * (right - left)
            boxes.sort(key=lambda x: (x[2] - x[0]) * (x[1] - x[3]), reverse=True)
            target_box = boxes[0]
            
            top, right, bottom, left = target_box
            face_area = (bottom - top) * (right - left)
            self.logger.info(f"选择最大人脸: 位置({left},{top},{right},{bottom}), 面积={face_area}px²")
            
            # 5. 提取人脸特征向量（128维）
            # 使用ResNet-34网络提取深度特征
            self.logger.info("提取人脸特征向量...")
            encodings = face_recognition.face_encodings(rgb_img, [target_box])
            
            if not encodings:
                self.logger.error("特征提取失败")
                return False
            
            # 6. 保存目标特征向量
            self.target_encoding = encodings[0]
            self.logger.info(f"目标人脸特征提取成功，特征维度: {len(self.target_encoding)}")
            
            return True
            
        except FileNotFoundError:
            self.logger.error(f"文件不存在: {image_path}")
            return False
        except Exception as e:
            self.logger.exception(f"加载目标人脸时发生错误: {e}")
            return False
    
    def process_scene(self, scene_path: str, upsample: int = 1) -> Tuple[np.ndarray, str]:
        """
        处理场景图像，搜索并标注目标人脸
        
        在场景图中检测所有人脸，与目标人脸进行特征匹配，
        并在原图上绘制检测框和标签。
        
        Args:
            scene_path: 场景图像文件路径（支持中文路径）
            upsample: 上采样次数，用于检测小人脸
                - 0: 不上采样，速度最快
                - 1: 标准模式（默认）
                - 2: 检测小人脸，适合教室等远距离场景
                
        Returns:
            Tuple[np.ndarray, str]: (标注后的图像, 结果信息字符串)
            
        Raises:
            ValueError: 如果未加载目标人脸或无法读取场景图像
            
        Examples:
            >>> engine = FaceEngine()
            >>> engine.load_target_face("Images/目标脸.jpg")
            >>> result_img, info = engine.process_scene("Images/Image-1.jpg", upsample=2)
            >>> print(info)
            检测到人脸: 15 个 | 匹配目标: 1 个 | 最佳匹配距离: 0.385
        """
        # 0. 检查是否已加载目标人脸
        if self.target_encoding is None:
            raise ValueError("请先使用load_target_face()加载目标人脸！")
        
        try:
            # 1. 读取场景图像（支持中文路径）
            self.logger.info(f"正在处理场景图: {scene_path}")
            img_data = np.fromfile(scene_path, dtype=np.uint8)
            scene_img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
            
            if scene_img is None:
                raise ValueError(f"无法读取场景图像: {scene_path}")
            
            self.logger.info(f"场景图读取成功，尺寸: {scene_img.shape}")
            
            # 2. BGR转RGB
            rgb_scene = cv2.cvtColor(scene_img, cv2.COLOR_BGR2RGB)
            
            # 3. 检测场景中所有人脸
            # 使用upsample参数提高小人脸的检测率
            self.logger.info(f"检测人脸中（upsample={upsample}）...")
            scene_boxes = face_recognition.face_locations(
                rgb_scene,
                number_of_times_to_upsample=upsample,
                model=self.model_method
            )
            
            self.logger.info(f"场景中检测到 {len(scene_boxes)} 个人脸")
            
            # 4. 批量提取所有人脸的特征向量
            self.logger.info("提取所有人脸特征...")
            scene_encodings = face_recognition.face_encodings(rgb_scene, scene_boxes)
            
            # 统计变量
            match_count = 0
            min_distance = 1.0
            best_match_box = None
            
            # 5. 遍历每个人脸，进行特征匹配
            for idx, ((top, right, bottom, left), face_encoding) in enumerate(
                zip(scene_boxes, scene_encodings)
            ):
                # 计算与目标人脸的欧氏距离
                distance = face_recognition.face_distance(
                    [self.target_encoding],
                    face_encoding
                )[0]
                
                # 判断是否匹配（距离小于阈值）
                is_match = distance <= self.tolerance
                
                if is_match:
                    match_count += 1
                    self.logger.info(f"人脸#{idx+1} 匹配成功! 距离: {distance:.3f}")
                    
                    # 记录最佳匹配
                    if distance < min_distance:
                        min_distance = distance
                        best_match_box = (top, right, bottom, left)
                    
                    # 匹配的人脸：绿色粗框
                    color = (0, 255, 0)  # BGR格式：绿色
                    thickness = 3
                    
                    # 计算置信度
                    confidence = compute_confidence(distance, self.tolerance)
                    label = f"Target {confidence:.1f}%"
                else:
                    # 非匹配人脸：红色细框
                    color = (0, 0, 255)  # BGR格式：红色
                    thickness = 1
                    label = "Unknown"
                
                # 6. 绘制检测框
                cv2.rectangle(
                    scene_img,
                    (left, top),
                    (right, bottom),
                    color,
                    thickness
                )
                
                # 7. 绘制标签背景（填充矩形）
                label_size = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.6,
                    1
                )[0]
                
                cv2.rectangle(
                    scene_img,
                    (left, bottom - label_size[1] - 10),
                    (right, bottom),
                    color,
                    cv2.FILLED
                )
                
                # 8. 绘制标签文字（白色）
                cv2.putText(
                    scene_img,
                    label,
                    (left + 6, bottom - 6),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.6,
                    (255, 255, 255),  # BGR格式：白色
                    1
                )
            
            # 9. 生成结果统计信息
            result_info = (
                f"检测到人脸: {len(scene_boxes)} 个 | "
                f"匹配目标: {match_count} 个 | "
                f"最佳匹配距离: {min_distance:.3f}"
            )
            
            self.logger.info(f"处理完成 - {result_info}")
            
            return scene_img, result_info
            
        except Exception as e:
            self.logger.exception(f"处理场景图时发生错误: {e}")
            raise
    
    def get_target_info(self) -> Optional[dict]:
        """
        获取目标人脸信息
        
        Returns:
            Optional[dict]: 目标人脸信息字典，包含特征维度等
                           如果未加载目标，返回None
        """
        if self.target_encoding is None:
            return None
        
        return {
            'feature_dim': len(self.target_encoding),
            'model_method': self.model_method,
            'tolerance': self.tolerance,
            'loaded': True
        }
    
    def reset_target(self):
        """
        重置目标人脸
        
        清除当前加载的目标人脸特征，允许加载新的目标。
        """
        self.target_encoding = None
        self.logger.info("目标人脸已重置")


# 模块级便捷函数
def create_engine(model_method: str = 'hog', tolerance: float = 0.45) -> FaceEngine:
    """
    创建人脸识别引擎实例（工厂函数）
    
    Args:
        model_method: 检测模型 ('hog' 或 'cnn')
        tolerance: 匹配阈值
        
    Returns:
        FaceEngine: 人脸识别引擎实例
    """
    return FaceEngine(model_method=model_method, tolerance=tolerance)

