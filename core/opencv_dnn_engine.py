"""
DeepFocus OpenCV DNN 引擎 v1.0

基于 OpenCV Zoo 的 YuNet + SFace 模型实现人脸检测与识别
- 检测器 YuNet: cv2.FaceDetectorYN - 轻量级 CNN 人脸检测
- 识别器 SFace: cv2.FaceRecognizerSF - 128 维特征向量 + 余弦相似度

这是 CPU 实现但效果很好的方案，特别适合侧脸、遮挡等复杂场景。
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Union
import logging
import time
import os
import shutil
import tempfile
import atexit


# ==================== 引擎可用性检测 ====================

_OPENCV_DNN_AVAILABLE = False
_OPENCV_DNN_ERROR = ""


def _check_opencv_dnn():
    """检查 OpenCV DNN 模块是否可用"""
    global _OPENCV_DNN_AVAILABLE, _OPENCV_DNN_ERROR
    try:
        # 检查 OpenCV 版本
        cv_version = cv2.__version__
        major, minor = map(int, cv_version.split('.')[:2])
        if major < 4 or (major == 4 and minor < 5):
            _OPENCV_DNN_ERROR = f"OpenCV 版本过低 ({cv_version})，需要 >= 4.5"
            return
        
        # 检查 FaceDetectorYN 是否存在
        if not hasattr(cv2, 'FaceDetectorYN'):
            _OPENCV_DNN_ERROR = "OpenCV 不支持 FaceDetectorYN（需要 opencv-python >= 4.5.4）"
            return
        
        # 检查 FaceRecognizerSF 是否存在
        if not hasattr(cv2, 'FaceRecognizerSF'):
            _OPENCV_DNN_ERROR = "OpenCV 不支持 FaceRecognizerSF（需要 opencv-python >= 4.5.4）"
            return
        
        _OPENCV_DNN_AVAILABLE = True
        
    except Exception as e:
        _OPENCV_DNN_ERROR = f"OpenCV DNN 检测失败: {e}"


_check_opencv_dnn()


def is_opencv_dnn_available() -> bool:
    """检查 OpenCV DNN 引擎是否可用"""
    return _OPENCV_DNN_AVAILABLE


def get_opencv_dnn_error() -> str:
    """获取 OpenCV DNN 不可用的原因"""
    return _OPENCV_DNN_ERROR


# ==================== 模型路径管理 ====================

def get_default_model_paths() -> Tuple[str, str]:
    """
    获取默认模型文件路径
    
    Returns:
        (det_model_path, rec_model_path)
    """
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    models_dir = os.path.join(project_root, "models")
    
    det_model_path = os.path.join(models_dir, "face_detection_yunet_2023mar.onnx")
    rec_model_path = os.path.join(models_dir, "face_recognition_sface_2021dec.onnx")
    
    return det_model_path, rec_model_path


def check_models_exist() -> Tuple[bool, str]:
    """
    检查模型文件是否存在
    
    Returns:
        (是否存在, 错误信息)
    """
    det_path, rec_path = get_default_model_paths()
    
    if not os.path.exists(det_path):
        return False, f"YuNet 模型文件不存在: {det_path}\n请运行 python models/download_models.py 下载模型"
    
    if not os.path.exists(rec_path):
        return False, f"SFace 模型文件不存在: {rec_path}\n请运行 python models/download_models.py 下载模型"
    
    return True, ""


# ==================== OpenCV DNN 引擎 ====================

class OpenCVDNNEngine:
    """
    基于 OpenCV DNN 的人脸识别引擎
    
    使用 YuNet 进行人脸检测，SFace 进行特征提取和匹配
    CPU 实现，效果优秀，特别适合侧脸、遮挡等复杂场景
    """
    
    def __init__(
        self,
        det_model_path: Optional[str] = None,
        rec_model_path: Optional[str] = None,
        score_threshold: float = 0.6,
        nms_threshold: float = 0.3,
        top_k: int = 5000
    ):
        """
        初始化 OpenCV DNN 引擎
        
        Args:
            det_model_path: YuNet 检测模型路径（None 则使用默认路径）
            rec_model_path: SFace 识别模型路径（None 则使用默认路径）
            score_threshold: 检测置信度阈值
            nms_threshold: 非极大值抑制阈值
            top_k: 最大检测数量
        """
        if not _OPENCV_DNN_AVAILABLE:
            raise ImportError(f"OpenCV DNN 不可用: {_OPENCV_DNN_ERROR}")
        
        self.logger = logging.getLogger(__name__)
        
        # 使用默认路径
        if det_model_path is None or rec_model_path is None:
            default_det, default_rec = get_default_model_paths()
            det_model_path = det_model_path or default_det
            rec_model_path = rec_model_path or default_rec
        
        self.det_model_path = det_model_path
        self.rec_model_path = rec_model_path
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        
        # 目标特征存储
        self.target_features: List[np.ndarray] = []
        self.target_images: List[Dict] = []
        
        # 性能统计
        self._last_detection_time: float = 0.0
        self._last_encoding_time: float = 0.0
        self._last_process_time: float = 0.0
        
        # 初始化模型
        self._init_models()
    
    def _init_models(self):
        """初始化检测和识别模型"""
        # 检查模型文件
        if not os.path.exists(self.det_model_path):
            raise FileNotFoundError(
                f"YuNet 模型文件不存在: {self.det_model_path}\n"
                "请运行 python models/download_models.py 下载模型"
            )
        
        if not os.path.exists(self.rec_model_path):
            raise FileNotFoundError(
                f"SFace 模型文件不存在: {self.rec_model_path}\n"
                "请运行 python models/download_models.py 下载模型"
            )
        
        # 处理中文路径问题：OpenCV DNN 不支持中文路径
        # 检测路径是否包含非 ASCII 字符
        self._temp_dir = None
        det_path = self.det_model_path
        rec_path = self.rec_model_path
        
        def has_non_ascii(s):
            return any(ord(c) > 127 for c in s)
        
        if has_non_ascii(det_path) or has_non_ascii(rec_path):
            self.logger.info("检测到中文路径，复制模型到临时目录...")
            # 创建临时目录
            self._temp_dir = tempfile.mkdtemp(prefix="deepfocus_models_")
            
            # 复制模型文件到临时目录
            temp_det_path = os.path.join(self._temp_dir, "yunet.onnx")
            temp_rec_path = os.path.join(self._temp_dir, "sface.onnx")
            
            shutil.copy2(self.det_model_path, temp_det_path)
            shutil.copy2(self.rec_model_path, temp_rec_path)
            
            det_path = temp_det_path
            rec_path = temp_rec_path
            
            self.logger.info(f"模型已复制到: {self._temp_dir}")
            
            # 注册清理函数
            atexit.register(self._cleanup_temp_dir)
        
        try:
            # 初始化 YuNet 人脸检测器
            self.detector = cv2.FaceDetectorYN.create(
                model=det_path,
                config="",
                input_size=(320, 320),
                score_threshold=self.score_threshold,
                nms_threshold=self.nms_threshold,
                top_k=self.top_k
            )
            
            # 初始化 SFace 人脸识别器
            self.recognizer = cv2.FaceRecognizerSF.create(
                model=rec_path,
                config=""
            )
            
            self.logger.info("OpenCV DNN 引擎初始化成功 (YuNet + SFace)")
            
        except Exception as e:
            self.logger.error(f"模型初始化失败: {e}")
            self._cleanup_temp_dir()
            raise
    
    def _cleanup_temp_dir(self):
        """清理临时目录"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                self.logger.info(f"已清理临时目录: {self._temp_dir}")
            except Exception as e:
                self.logger.warning(f"清理临时目录失败: {e}")
    
    def _read_image(self, path: str) -> Optional[np.ndarray]:
        """读取图像（支持中文路径）"""
        try:
            img_array = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            self.logger.error(f"读取图像失败 {path}: {e}")
            return None
    
    def _detect_faces(self, img: np.ndarray) -> np.ndarray:
        """
        检测图像中的人脸
        
        Args:
            img: BGR 格式图像
            
        Returns:
            faces: 人脸检测结果，每行包含 [x, y, w, h, ..关键点.., score]
        """
        h, w = img.shape[:2]
        
        # 设置输入尺寸为原图尺寸（YuNet 会自动缩放）
        self.detector.setInputSize((w, h))
        
        # 检测人脸
        _, faces = self.detector.detect(img)
        
        if faces is None:
            return np.array([])
        
        return faces
    
    def _extract_feature(self, img: np.ndarray, face: np.ndarray) -> Optional[np.ndarray]:
        """
        提取单个人脸的特征向量
        
        Args:
            img: 原始图像
            face: 人脸检测结果
            
        Returns:
            128 维特征向量，失败返回 None
        """
        try:
            # 对齐裁剪人脸
            aligned_face = self.recognizer.alignCrop(img, face)
            
            # 提取特征
            feature = self.recognizer.feature(aligned_face)
            
            return feature
            
        except Exception as e:
            self.logger.warning(f"特征提取失败: {e}")
            return None
    
    def _compute_similarity(self, feature1: np.ndarray, feature2: np.ndarray) -> float:
        """
        计算两个特征向量的余弦相似度
        
        Returns:
            相似度 (0~1，越大越相似)
        """
        score = self.recognizer.match(
            feature1, feature2,
            cv2.FaceRecognizerSF_FR_COSINE
        )
        return float(score)
    
    def _similarity_to_distance(self, similarity: float) -> float:
        """
        将相似度转换为距离（与 dlib 兼容的度量）
        
        dlib 使用欧氏距离，范围约 0~1
        SFace 使用余弦相似度，范围 -1~1
        
        转换公式：distance = (1 - similarity) / 2
        """
        return (1.0 - similarity) / 2.0
    
    def _cosine_to_percent(self, cosine_sim: float) -> float:
        """
        将余弦相似度直接转换为百分比（用于界面显示）
        
        余弦相似度范围 -1~1 映射到 0~100%
        - 1.0 -> 100%（完全相同）
        - 0.5 -> 75%（很可能是同一人）
        - 0.0 -> 50%（边界）
        - -1.0 -> 0%（完全不同）
        """
        return max(0.0, min(100.0, (cosine_sim + 1.0) / 2.0 * 100))
    
    def load_target_face(self, image_path: str) -> Tuple[bool, Union[str, np.ndarray]]:
        """
        加载目标人脸（清空已有特征）
        
        Args:
            image_path: 目标人脸图像路径
            
        Returns:
            (成功标志, 裁剪图像或错误信息)
        """
        self.clear_targets()
        return self.add_target_face(image_path)
    
    def add_target_face(self, image_path: str) -> Tuple[bool, Union[str, np.ndarray]]:
        """
        添加目标人脸到特征库
        
        Args:
            image_path: 目标人脸图像路径
            
        Returns:
            (成功标志, 裁剪图像或错误信息)
        """
        img = self._read_image(image_path)
        if img is None:
            return False, "无法读取图片"
        
        # 检测人脸
        faces = self._detect_faces(img)
        
        if len(faces) == 0:
            return False, "未检测到人脸"
        
        # 选择最大的人脸
        faces = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
        main_face = faces[0]
        
        # 提取特征
        feature = self._extract_feature(img, main_face)
        if feature is None:
            return False, "无法提取人脸特征"
        
        self.target_features.append(feature)
        
        # 裁剪人脸区域用于显示
        x, y, w, h = main_face[:4].astype(int)
        margin = 20
        img_h, img_w = img.shape[:2]
        crop = img[
            max(0, y - margin):min(img_h, y + h + margin),
            max(0, x - margin):min(img_w, x + w + margin)
        ]
        
        # 记录目标信息
        self.target_images.append({
            "path": image_path,
            "crop_image": crop,
            "feature": feature
        })
        
        self.logger.info(f"目标加载成功: {image_path}")
        return True, crop
    
    def clear_targets(self):
        """清空所有目标"""
        self.target_features = []
        self.target_images = []
        self.logger.info("已清空所有目标特征")
    
    def get_target_count(self) -> int:
        """返回目标数量"""
        return len(self.target_images)
    
    def get_target_encoding_count(self) -> int:
        """返回目标特征总数（与其他引擎接口兼容）"""
        return len(self.target_features)
    
    def process_scene(
        self,
        scene_path: str,
        tolerance: float = 0.45,
        best_only: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Tuple[Optional[np.ndarray], Dict]:
        """
        处理场景图像，检测并匹配目标人脸
        
        Args:
            scene_path: 场景图像路径
            tolerance: 匹配阈值（距离阈值，越小越严格）
            best_only: 是否只显示最佳匹配
            progress_callback: 进度回调函数
            
        Returns:
            (标注后的图像, 统计信息字典)
        """
        start_time = time.time()
        
        if not self.target_features:
            return None, {"error": "请先加载目标"}
        
        def update_progress(value: int):
            if progress_callback:
                progress_callback(value)
        
        update_progress(5)
        
        img = self._read_image(scene_path)
        if img is None:
            return None, {"error": "无法读取场景图"}
        
        result_img = img.copy()
        update_progress(15)
        
        # 人脸检测
        detection_start = time.time()
        faces = self._detect_faces(img)
        self._last_detection_time = time.time() - detection_start
        
        self.logger.info(f"检测到 {len(faces)} 个人脸 (耗时 {self._last_detection_time:.2f}s)")
        update_progress(40)
        
        if len(faces) == 0:
            self._last_process_time = time.time() - start_time
            return result_img, {
                "total": 0,
                "matches": 0,
                "best_dist": 1.0,
                "process_time": self._last_process_time,
                "detection_time": self._last_detection_time,
                "encoding_time": 0.0,
                "model_used": "yunet+sface",
                "cuda_used": False
            }
        
        # 特征提取和匹配
        encoding_start = time.time()
        matches_found = 0
        min_global_dist = 1.0
        max_global_sim = -1.0  # 跟踪最高余弦相似度
        best_match_idx = -1
        results = []
        
        for idx, face in enumerate(faces):
            if len(faces) > 0:
                progress = 40 + int(35 * (idx + 1) / len(faces))
                update_progress(progress)
            
            # 提取特征
            feature = self._extract_feature(img, face)
            if feature is None:
                results.append((face[:4], False, 1.0, -1.0))
                continue
            
            # 计算与所有目标的相似度
            best_sim = -1.0
            for target_feat in self.target_features:
                sim = self._compute_similarity(feature, target_feat)
                if sim > best_sim:
                    best_sim = sim
            
            # 转换为距离（用于阈值判断）
            dist = self._similarity_to_distance(best_sim)
            is_match = dist <= tolerance
            
            if is_match:
                matches_found += 1
                if dist < min_global_dist:
                    min_global_dist = dist
                    max_global_sim = best_sim
                    best_match_idx = idx
            
            # 保存余弦相似度用于显示 (face[:4], is_match, dist, best_sim)
            results.append((face[:4], is_match, dist, best_sim))
        
        self._last_encoding_time = time.time() - encoding_start
        update_progress(80)
        
        # 绘制结果
        for draw_idx, (bbox, is_match, dist, cosine_sim) in enumerate(results):
            is_best_match = (draw_idx == best_match_idx)
            
            if best_only and not is_best_match:
                continue
            
            x, y, w, h = bbox.astype(int)
            
            if is_match:
                if is_best_match:
                    color = (0, 255, 0)  # 绿色 - BGR
                    thickness = 3
                else:
                    color = (0, 255, 255)  # 黄色 - BGR
                    thickness = 2
                # 使用余弦相似度转换为百分比（更直观）
                similarity = self._cosine_to_percent(cosine_sim)
            else:
                color = (0, 0, 255)  # 红色 - BGR
                thickness = 1
                similarity = self._cosine_to_percent(cosine_sim)
            
            # 绘制检测框
            cv2.rectangle(result_img, (x, y), (x + w, y + h), color, thickness)
            
            # 显示相似度
            if is_match:
                sim_text = f"{similarity:.1f}%"
                text_size = cv2.getTextSize(sim_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                text_x = x + (w - text_size[0]) // 2
                text_y = max(y - 10, text_size[1] + 5)
                
                # 背景
                bg_color = tuple(int(c * 0.8) for c in color)
                cv2.rectangle(
                    result_img,
                    (text_x - 6, text_y - text_size[1] - 6),
                    (text_x + text_size[0] + 6, text_y + 6),
                    bg_color, -1
                )
                cv2.rectangle(
                    result_img,
                    (text_x - 6, text_y - text_size[1] - 6),
                    (text_x + text_size[0] + 6, text_y + 6),
                    color, 2
                )
                cv2.putText(
                    result_img, sim_text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                )
        
        update_progress(100)
        
        self._last_process_time = time.time() - start_time
        self.logger.info(f"场景处理完成 (总耗时 {self._last_process_time:.2f}s)")
        
        # 计算最佳相似度百分比（用于界面显示）
        best_similarity_percent = self._cosine_to_percent(max_global_sim) if max_global_sim > -1 else 0.0
        
        return result_img, {
            "total": len(faces),
            "matches": matches_found,
            "best_dist": min_global_dist,
            "best_similarity": best_similarity_percent,  # 余弦相似度百分比（用于横向比较）
            "best_cosine": max_global_sim,  # 原始余弦相似度
            "process_time": self._last_process_time,
            "detection_time": self._last_detection_time,
            "encoding_time": self._last_encoding_time,
            "model_used": "yunet+sface",
            "cuda_used": False
        }
    
    def get_performance_stats(self) -> Dict[str, float]:
        """获取性能统计"""
        return {
            "total_time": self._last_process_time,
            "detection_time": self._last_detection_time,
            "encoding_time": self._last_encoding_time
        }

