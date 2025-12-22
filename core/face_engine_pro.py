"""
DeepFocus 增强版人脸识别引擎 v2.1

支持多特征匹配（原图+翻转图），提高识别准确率
支持多目标照片增强、分阶段输出用于可视化
新增：GPU/CUDA检测、CNN参数优化、性能统计
"""

import face_recognition
import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Union
import logging
import time
import dlib

from core.preprocessing import apply_clahe
from core.matcher import compute_confidence, distance_to_similarity
from core.gpu_utils import (
    get_cuda_info, is_cuda_available,
    resize_for_processing, scale_face_locations,
    PerformanceTimer
)


class FaceEnginePro:
    """
    增强版人脸识别引擎 v2.1
    
    支持多特征匹配，自动生成多种形态特征，提高识别准确率
    特别适合处理侧脸、不同角度和光照的场景
    支持多张目标照片累加增强特征库
    
    v2.1 新增:
    - GPU/CUDA自动检测与利用
    - CNN模式参数优化（upsample自动调整）
    - 性能统计（处理耗时）
    """
    
    def __init__(self, model_method: str = 'hog', tolerance: float = 0.45):
        self.model_method = model_method
        self.tolerance = tolerance
        # 存储目标的多个特征向量（原图、翻转、旋转、亮度增强等）
        self.target_encodings: List[np.ndarray] = []
        # 存储每张目标照片的信息
        self.target_images: List[Dict] = []  # [{path, crop_image, encoding_count}]
        self.target_image_path = ""
        self.logger = logging.getLogger(__name__)
        
        # v2.1: GPU状态
        self._cuda_info = get_cuda_info()
        self.logger.info(f"引擎初始化: {self._cuda_info['gpu_info']}")
        
        # v2.1: 性能统计
        self._last_process_time: float = 0.0
        self._last_detection_time: float = 0.0
        self._last_encoding_time: float = 0.0
    
    @property
    def cuda_available(self) -> bool:
        """CUDA是否可用"""
        return self._cuda_info.get("cuda_available", False)
    
    @property
    def gpu_info(self) -> str:
        """GPU信息描述"""
        return self._cuda_info.get("gpu_info", "未知")
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        获取最近一次处理的性能统计
        
        Returns:
            {
                "total_time": 总处理时间(秒),
                "detection_time": 人脸检测时间(秒),
                "encoding_time": 特征提取时间(秒)
            }
        """
        return {
            "total_time": self._last_process_time,
            "detection_time": self._last_detection_time,
            "encoding_time": self._last_encoding_time
        }
    
    def _read_image(self, path: str) -> Optional[np.ndarray]:
        try:
            img_array = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            self.logger.error(f"读取图像失败 {path}: {e}")
            return None

    def _adjust_gamma(self, image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """Gamma校正：gamma < 1.0 提亮暗部，gamma > 1.0 压暗亮部"""
        if gamma <= 0:
            return image
        inv_gamma = 1.0 / gamma
        table = np.array(
            [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)],
            dtype="uint8",
        )
        return cv2.LUT(image, table)

    def _rotate_image(self, image: np.ndarray, angle: float) -> np.ndarray:
        """旋转图像，用于生成歪头等增强样本"""
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, M, (w, h))

    def _extract_encoding_safe(self, rgb_img: np.ndarray) -> Optional[np.ndarray]:
        """
        安全提取特征，如果检测不到脸则返回None
        使用HOG快速检测 + num_jitters增加鲁棒性
        """
        try:
            boxes = face_recognition.face_locations(rgb_img, model="hog")
            if not boxes:
                return None
            # 取最大的一张脸
            boxes.sort(key=lambda x: (x[2] - x[0]) * (x[1] - x[3]), reverse=True)
            encodings = face_recognition.face_encodings(
                rgb_img, [boxes[0]], num_jitters=5
            )
            if encodings:
                return encodings[0]
            return None
        except Exception as e:
            self.logger.warning(f"安全提取特征失败: {e}")
            return None
    
    def load_target_face(self, image_path: str) -> Tuple[bool, Union[str, np.ndarray]]:
        """
        加载目标人脸（清空已有特征库）
        
        如需追加而非替换，请使用 add_target_face()
        """
        # 清空已有特征
        self.clear_targets()
        
        img = self._read_image(image_path)
        if img is None:
            return False, "无法读取图片"
        
        # 先做CLAHE增强，提高整体质量
        img = apply_clahe(img, clip_limit=2.0, tile_size=8)
        rgb_base = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 策略1: 原图
        enc = self._extract_encoding_safe(rgb_base)
        if enc is not None:
            self.target_encodings.append(enc)

        # 策略2: 水平翻转 (模拟另一侧脸)
        rgb_flip = cv2.flip(rgb_base, 1)
        enc = self._extract_encoding_safe(rgb_flip)
        if enc is not None:
            self.target_encodings.append(enc)

        # 策略3: 旋转 (模拟歪头)
        for angle in (-10, 10):
            rgb_rot = self._rotate_image(rgb_base, angle)
            enc = self._extract_encoding_safe(rgb_rot)
            if enc is not None:
                self.target_encodings.append(enc)

        # 策略4: 亮度增强 (模拟过曝或欠曝)
        rgb_bright = self._adjust_gamma(rgb_base, 0.6)
        enc = self._extract_encoding_safe(rgb_bright)
        if enc is not None:
            self.target_encodings.append(enc)

        if not self.target_encodings:
            return False, "在目标图中未检测到人脸，请更换清晰的正脸照片。"

        self.target_image_path = image_path
        self.logger.info(f"目标加载成功，共 {len(self.target_encodings)} 个特征向量")
        
        # 返回裁剪图用于显示（使用原图的最大人脸框）
        boxes = face_recognition.face_locations(rgb_base, model="hog")
        crop = img
        if boxes:
            boxes.sort(key=lambda x: (x[2] - x[0]) * (x[1] - x[3]), reverse=True)
            top, right, bottom, left = boxes[0]
            margin = 20
            h, w, _ = img.shape
            crop = img[
                max(0, top - margin):min(h, bottom + margin),
                max(0, left - margin):min(w, right + margin),
            ]
        
        # 记录目标信息
        self.target_images.append({
            "path": image_path,
            "crop_image": crop,
            "encoding_count": len(self.target_encodings)
        })

        return True, crop
    
    def add_target_face(self, image_path: str) -> Tuple[bool, Union[str, np.ndarray]]:
        """
        追加目标照片到现有特征库（不清空已有特征）
        
        Args:
            image_path: 目标人脸图像路径
            
        Returns:
            (成功标志, 裁剪图像或错误信息)
        """
        img = self._read_image(image_path)
        if img is None:
            return False, "无法读取图片"
        
        # 先做CLAHE增强
        img = apply_clahe(img, clip_limit=2.0, tile_size=8)
        rgb_base = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 记录新增特征数量的起始位置
        start_count = len(self.target_encodings)

        # 策略1: 原图
        enc = self._extract_encoding_safe(rgb_base)
        if enc is not None:
            self.target_encodings.append(enc)

        # 策略2: 水平翻转 (模拟另一侧脸)
        rgb_flip = cv2.flip(rgb_base, 1)
        enc = self._extract_encoding_safe(rgb_flip)
        if enc is not None:
            self.target_encodings.append(enc)

        # 策略3: 旋转 (模拟歪头)
        for angle in (-10, 10):
            rgb_rot = self._rotate_image(rgb_base, angle)
            enc = self._extract_encoding_safe(rgb_rot)
            if enc is not None:
                self.target_encodings.append(enc)

        # 策略4: 亮度增强 (模拟过曝或欠曝)
        rgb_bright = self._adjust_gamma(rgb_base, 0.6)
        enc = self._extract_encoding_safe(rgb_bright)
        if enc is not None:
            self.target_encodings.append(enc)

        new_count = len(self.target_encodings) - start_count
        if new_count == 0:
            return False, "在目标图中未检测到人脸"

        # 返回裁剪图用于显示
        boxes = face_recognition.face_locations(rgb_base, model="hog")
        crop = img
        if boxes:
            boxes.sort(key=lambda x: (x[2] - x[0]) * (x[1] - x[3]), reverse=True)
            top, right, bottom, left = boxes[0]
            margin = 20
            h, w, _ = img.shape
            crop = img[
                max(0, top - margin):min(h, bottom + margin),
                max(0, left - margin):min(w, right + margin),
            ]
        
        # 记录目标信息
        self.target_images.append({
            "path": image_path,
            "crop_image": crop,
            "encoding_count": new_count
        })
        
        self.logger.info(f"追加目标成功，新增 {new_count} 个特征，总计 {len(self.target_encodings)} 个")
        return True, crop
    
    def clear_targets(self):
        """清空所有目标特征"""
        self.target_encodings = []
        self.target_images = []
        self.target_image_path = ""
        self.logger.info("已清空所有目标特征")
    
    def get_target_count(self) -> int:
        """返回目标照片数量"""
        return len(self.target_images)
    
    def get_target_encoding_count(self) -> int:
        """返回目标特征总数"""
        return len(self.target_encodings)
    
    def get_target_images(self) -> List[Dict]:
        """获取所有目标照片信息"""
        return self.target_images
    
    def process_scene(
        self,
        scene_path: str,
        tolerance: Optional[float] = None,
        upsample: int = 1,
        model: Optional[str] = None,
        use_clahe: bool = True,
        gamma: float = 1.0,
        best_only: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Tuple[Optional[np.ndarray], Dict]:
        """
        处理场景图像，搜索并标注目标人脸
        
        Args:
            scene_path: 场景图像路径
            tolerance: 匹配阈值
            upsample: 上采样次数 (CNN模式下自动优化为0)
            model: 检测模型 ('hog' 或 'cnn')
            use_clahe: 是否使用CLAHE增强 (CNN模式下自动减弱)
            gamma: Gamma校正值
            best_only: 是否只显示最佳匹配（隐藏其他人脸）
            progress_callback: 进度回调函数
            
        Returns:
            (标注后的图像, 统计信息字典)
            统计信息包含: total, matches, best_dist, process_time等
        """
        start_time = time.time()
        
        if not self.target_encodings:
            return None, {"error": "请先加载目标"}
        
        def update_progress(value: int):
            if progress_callback:
                progress_callback(value)
        
        # 使用参数或默认值
        tolerance = tolerance if tolerance is not None else self.tolerance
        model = model if model is not None else self.model_method
        
        update_progress(5)
        
        img = self._read_image(scene_path)
        if img is None:
            return None, {"error": "无法读取场景图"}
        
        update_progress(10)
        
        # v2.3: HOG/CNN 综合优化 - 根据图像尺寸自动调整参数
        img_h, img_w = img.shape[:2]
        max_dim = max(img_h, img_w)
        
        if model == 'cnn':
            # CNN: 根据图像尺寸自动调整 upsample
            if max_dim < 800:
                effective_upsample = 2  # 小图：上采样2次检测更小的人脸
            elif max_dim < 1500:
                effective_upsample = 1  # 中图：标准设置
            else:
                effective_upsample = 1  # 大图：保持1次，后续会缩放
            self.logger.debug(f"CNN自适应: 图像{img_w}x{img_h}, upsample={effective_upsample}")
        else:
            # HOG: 根据图像尺寸优化 upsample（HOG 对 upsample 非常敏感）
            if max_dim < 600:
                effective_upsample = min(upsample, 2)  # 小图：最多2次
            elif max_dim < 1200:
                effective_upsample = min(upsample, 1)  # 中图：最多1次
            else:
                effective_upsample = 1  # 大图：固定1次，依赖后续缩放
            if effective_upsample != upsample:
                self.logger.debug(f"HOG自适应: 图像{img_w}x{img_h}, upsample {upsample}->{effective_upsample}")
        
        # v2.3: 大图预缩放优化（HOG和CNN都适用）
        # 对超大图先缩放再检测，然后映射回原坐标
        scale_factor = 1.0
        process_for_detection = img
        # HOG 对大图非常慢，阈值设低一些
        max_size_threshold = 1500 if model == 'hog' else 2000
        target_size = 1200 if model == 'hog' else 2000
        if max_dim > max_size_threshold:
            # 缩放到目标尺寸
            scale_factor = target_size / max_dim
            new_w = int(img_w * scale_factor)
            new_h = int(img_h * scale_factor)
            process_for_detection = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            self.logger.info(f"大图优化: {img_w}x{img_h} -> {new_w}x{new_h} (scale={scale_factor:.2f})")
        
        # v2.1: 图像预处理优化
        # CNN对原始图像细节更敏感，减少过度预处理
        process_img = process_for_detection.copy()
        
        if abs(gamma - 1.0) > 0.01:
            self.logger.info(f"应用Gamma校正: {gamma}")
            process_img = self._adjust_gamma(process_img, gamma)
        
        # 图像增强：CLAHE
        if use_clahe:
            # CNN和HOG都使用相同的CLAHE参数，保证一致性
            self.logger.info("应用CLAHE增强...")
            process_img = apply_clahe(process_img, clip_limit=2.0, tile_size=8)
        
        update_progress(15)
        
        rgb_img = cv2.cvtColor(process_img, cv2.COLOR_BGR2RGB)
        
        # 检测人脸
        detection_start = time.time()
        self.logger.info(f"检测人脸中（model={model}, upsample={effective_upsample}）...")
        update_progress(20)
        
        try:
            boxes = face_recognition.face_locations(
                rgb_img,
                number_of_times_to_upsample=effective_upsample,
                model=model
            )
        except Exception as e:
            self.logger.warning(f"检测出错: {e}, 降级为 HOG")
            boxes = face_recognition.face_locations(
                rgb_img,
                number_of_times_to_upsample=upsample,
                model='hog'
            )
        
        self._last_detection_time = time.time() - detection_start
        
        self.logger.info(f"检测到 {len(boxes)} 个人脸 (耗时 {self._last_detection_time:.2f}s)")
        update_progress(40)
        
        # v2.2: 如果进行了缩放，将坐标映射回原始尺寸
        if scale_factor != 1.0 and boxes:
            # boxes 格式: (top, right, bottom, left)
            boxes = [
                (
                    int(top / scale_factor),
                    int(right / scale_factor),
                    int(bottom / scale_factor),
                    int(left / scale_factor)
                )
                for (top, right, bottom, left) in boxes
            ]
            self.logger.debug(f"坐标已映射回原始尺寸 (scale_factor={scale_factor:.2f})")
            # 需要在原图上重新提取特征
            process_img = img.copy()
            if abs(gamma - 1.0) > 0.01:
                process_img = self._adjust_gamma(process_img, gamma)
            if use_clahe:
                process_img = apply_clahe(process_img, clip_limit=2.0, tile_size=8)
            rgb_img = cv2.cvtColor(process_img, cv2.COLOR_BGR2RGB)
        
        if not boxes:
            self._last_process_time = time.time() - start_time
            return img, {
                "total": 0, "matches": 0, "best_dist": 1.0,
                "best_similarity": 0.0,  # 统一的相似度百分比
                "process_time": self._last_process_time,
                "detection_time": self._last_detection_time,
                "encoding_time": 0.0,
                "model_used": model,
                "cuda_used": self.cuda_available and model == 'cnn'
            }
        
        # 提取特征
        encoding_start = time.time()
        self.logger.info("提取所有人脸特征...")
        encodings = face_recognition.face_encodings(rgb_img, boxes)
        self._last_encoding_time = time.time() - encoding_start
        self.logger.info(f"特征提取完成 (耗时 {self._last_encoding_time:.2f}s)")
        update_progress(60)
        
        matches_found = 0
        min_global_dist = 1.0
        best_match_idx = -1
        results = []
        
        # 遍历场景中的每一张脸
        total_faces = len(boxes)
        for idx, (box, encoding) in enumerate(zip(boxes, encodings)):
            if total_faces > 0:
                match_progress = 60 + int(25 * (idx + 1) / total_faces)
                update_progress(match_progress)
            
            distances = face_recognition.face_distance(self.target_encodings, encoding)
            best_dist = np.min(distances)
            
            is_match = best_dist <= tolerance
            if is_match:
                matches_found += 1
                if best_dist < min_global_dist:
                    min_global_dist = best_dist
                    best_match_idx = idx
            
            results.append((box, is_match, best_dist))
        
        # 绘图（不显示文字标签，仅框和置信度）
        update_progress(85)
        for draw_idx, ((top, right, bottom, left), is_match, dist) in enumerate(results):
            if total_faces > 0:
                draw_progress = 85 + int(10 * (draw_idx + 1) / total_faces)
                update_progress(draw_progress)
            
            is_best_match = (draw_idx == best_match_idx)
            
            # best_only 模式下，只绘制最佳匹配
            if best_only and not is_best_match:
                continue
            
            if is_match:
                if is_best_match:
                    color = (0, 255, 0)  # 绿色
                    thickness = 3
                else:
                    color = (0, 255, 255)  # 黄色
                    thickness = 2
                # 使用统一的相似度转换（用于横向比较不同模型）
                similarity = distance_to_similarity(dist, 'euclidean')
            else:
                color = (0, 0, 255)  # 红色
                thickness = 1
                similarity = distance_to_similarity(dist, 'euclidean')
            
            # 绘制检测框
            cv2.rectangle(img, (left, top), (right, bottom), color, thickness)
            
            # 如果是匹配的人脸，在框上方显示相似度
            if is_match:
                similarity_text = f"{similarity:.1f}%"
                conf_size = cv2.getTextSize(
                    similarity_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )[0]
                
                text_x = left + (right - left - conf_size[0]) // 2
                text_y = max(top - 10, conf_size[1] + 5)
                
                # 绘制文本背景
                bg_color = tuple(int(c * 0.8) for c in color)
                cv2.rectangle(
                    img,
                    (text_x - 6, text_y - conf_size[1] - 6),
                    (text_x + conf_size[0] + 6, text_y + 6),
                    bg_color, -1
                )
                cv2.rectangle(
                    img,
                    (text_x - 6, text_y - conf_size[1] - 6),
                    (text_x + conf_size[0] + 6, text_y + 6),
                    color, 2
                )
                cv2.putText(
                    img, similarity_text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                )
        
        update_progress(100)
        
        self._last_process_time = time.time() - start_time
        self.logger.info(f"场景处理完成 (总耗时 {self._last_process_time:.2f}s)")
        
        # 计算统一的相似度百分比
        best_similarity = distance_to_similarity(min_global_dist, 'euclidean')
        
        return img, {
            "total": len(boxes),
            "matches": matches_found,
            "best_dist": min_global_dist,
            "best_similarity": best_similarity,  # 统一的相似度百分比
            "process_time": self._last_process_time,
            "detection_time": self._last_detection_time,
            "encoding_time": self._last_encoding_time,
            "model_used": model,
            "cuda_used": self.cuda_available and model == 'cnn'
        }
    
    def process_scene_with_stages(
        self,
        scene_path: str,
        tolerance: Optional[float] = None,
        upsample: int = 1,
        model: Optional[str] = None,
        use_clahe: bool = True,
        gamma: float = 1.0,
        best_only: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict]:
        """
        处理场景图像并返回各阶段图像（用于可视化）
        
        Returns:
            stages: {
                "original": 原图,
                "gamma": Gamma校正后,
                "clahe": CLAHE增强后,
                "detection": 绘制检测框后,
                "final": 最终结果
            }
            stats: 统计信息（含性能数据）
        """
        start_time = time.time()
        stages = {}
        
        if not self.target_encodings:
            return stages, {"error": "请先加载目标"}
        
        def update_progress(value: int):
            if progress_callback:
                progress_callback(value)
        
        tolerance = tolerance if tolerance is not None else self.tolerance
        model = model if model is not None else self.model_method
        
        update_progress(5)
        
        img = self._read_image(scene_path)
        if img is None:
            return stages, {"error": "无法读取场景图"}
        
        # v2.3: HOG/CNN 综合优化 - 根据图像尺寸自动调整参数
        img_h, img_w = img.shape[:2]
        max_dim = max(img_h, img_w)
        
        if model == 'cnn':
            if max_dim < 800:
                effective_upsample = 2
            elif max_dim < 1500:
                effective_upsample = 1
            else:
                effective_upsample = 1
        else:
            # HOG: 根据图像尺寸优化 upsample
            if max_dim < 600:
                effective_upsample = min(upsample, 2)
            elif max_dim < 1200:
                effective_upsample = min(upsample, 1)
            else:
                effective_upsample = 1
        
        # 阶段1: 原图
        stages["original"] = img.copy()
        update_progress(10)
        
        # 阶段2: Gamma校正
        process_img = img.copy()
        if abs(gamma - 1.0) > 0.01:
            process_img = self._adjust_gamma(process_img, gamma)
        stages["gamma"] = process_img.copy()
        update_progress(15)
        
        # 阶段3: CLAHE增强
        if use_clahe:
            process_img = apply_clahe(process_img, clip_limit=2.0, tile_size=8)
        stages["clahe"] = process_img.copy()
        update_progress(20)
        
        # v2.3: 大图预缩放优化（HOG和CNN都适用）
        scale_factor = 1.0
        detection_img = process_img
        max_size_threshold = 1500 if model == 'hog' else 2000
        target_size = 1200 if model == 'hog' else 2000
        if max_dim > max_size_threshold:
            scale_factor = target_size / max_dim
            new_w = int(img_w * scale_factor)
            new_h = int(img_h * scale_factor)
            detection_img = cv2.resize(process_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            self.logger.info(f"大图优化: {img_w}x{img_h} -> {new_w}x{new_h}")
        
        rgb_img = cv2.cvtColor(detection_img, cv2.COLOR_BGR2RGB)
        
        # 检测人脸
        detection_start = time.time()
        update_progress(25)
        try:
            boxes = face_recognition.face_locations(
                rgb_img, number_of_times_to_upsample=effective_upsample, model=model
            )
        except Exception as e:
            self.logger.warning(f"检测出错: {e}, 降级为 HOG")
            boxes = face_recognition.face_locations(
                rgb_img, number_of_times_to_upsample=upsample, model='hog'
            )
        
        # v2.2: 如果进行了缩放，将坐标映射回原始尺寸
        if scale_factor != 1.0 and boxes:
            boxes = [
                (
                    int(top / scale_factor),
                    int(right / scale_factor),
                    int(bottom / scale_factor),
                    int(left / scale_factor)
                )
                for (top, right, bottom, left) in boxes
            ]
            rgb_img = cv2.cvtColor(process_img, cv2.COLOR_BGR2RGB)
        
        self._last_detection_time = time.time() - detection_start
        update_progress(45)
        
        # 注意：detection 阶段的绘制移到匹配计算之后，以便统一 best_only 逻辑
        
        if not boxes:
            # 没有检测到人脸时，detection 阶段显示原图
            stages["detection"] = process_img.copy()
            stages["final"] = img.copy()
            self._last_process_time = time.time() - start_time
            return stages, {
                "total": 0, "matches": 0, "best_dist": 1.0,
                "best_similarity": 0.0,  # 统一的相似度百分比
                "process_time": self._last_process_time,
                "detection_time": self._last_detection_time,
                "model_used": model,
                "cuda_used": self.cuda_available and model == 'cnn'
            }
        
        # 提取特征
        encoding_start = time.time()
        encodings = face_recognition.face_encodings(rgb_img, boxes)
        self._last_encoding_time = time.time() - encoding_start
        update_progress(65)
        
        matches_found = 0
        min_global_dist = 1.0
        best_match_idx = -1
        results = []
        
        for idx, (box, encoding) in enumerate(zip(boxes, encodings)):
            if len(boxes) > 0:
                update_progress(65 + int(20 * (idx + 1) / len(boxes)))
            
            distances = face_recognition.face_distance(self.target_encodings, encoding)
            best_dist = np.min(distances)
            
            is_match = best_dist <= tolerance
            if is_match:
                matches_found += 1
                if best_dist < min_global_dist:
                    min_global_dist = best_dist
                    best_match_idx = idx
            
            results.append((box, is_match, best_dist))
        
        # 阶段4: 检测框（根据 best_only 参数统一显示逻辑）
        detection_img = process_img.copy()
        for draw_idx, ((top, right, bottom, left), is_match, dist) in enumerate(results):
            is_best_match = (draw_idx == best_match_idx)
            # best_only 模式下只显示最佳匹配
            if best_only and not is_best_match:
                continue
            # 检测阶段使用橙色框表示所有检测到的人脸
            cv2.rectangle(detection_img, (left, top), (right, bottom), (255, 128, 0), 2)
        stages["detection"] = detection_img
        
        # 阶段5: 最终结果（彩色框）
        final_img = img.copy()
        update_progress(88)
        
        for draw_idx, ((top, right, bottom, left), is_match, dist) in enumerate(results):
            is_best_match = (draw_idx == best_match_idx)
            
            if best_only and not is_best_match:
                continue
            
            if is_match:
                if is_best_match:
                    color = (0, 255, 0)
                    thickness = 3
                else:
                    color = (0, 255, 255)
                    thickness = 2
                # 使用统一的相似度转换
                similarity = distance_to_similarity(dist, 'euclidean')
            else:
                color = (0, 0, 255)
                thickness = 1
                similarity = distance_to_similarity(dist, 'euclidean')
            
            cv2.rectangle(final_img, (left, top), (right, bottom), color, thickness)
            
            if is_match:
                similarity_text = f"{similarity:.1f}%"
                conf_size = cv2.getTextSize(
                    similarity_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                )[0]
                text_x = left + (right - left - conf_size[0]) // 2
                text_y = max(top - 10, conf_size[1] + 5)
                
                bg_color = tuple(int(c * 0.8) for c in color)
                cv2.rectangle(
                    final_img,
                    (text_x - 6, text_y - conf_size[1] - 6),
                    (text_x + conf_size[0] + 6, text_y + 6),
                    bg_color, -1
                )
                cv2.rectangle(
                    final_img,
                    (text_x - 6, text_y - conf_size[1] - 6),
                    (text_x + conf_size[0] + 6, text_y + 6),
                    color, 2
                )
                cv2.putText(
                    final_img, similarity_text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                )
        
        stages["final"] = final_img
        update_progress(100)
        
        self._last_process_time = time.time() - start_time
        
        # 计算统一的相似度百分比
        best_similarity = distance_to_similarity(min_global_dist, 'euclidean')
        
        return stages, {
            "total": len(boxes),
            "matches": matches_found,
            "best_dist": min_global_dist,
            "best_similarity": best_similarity,  # 统一的相似度百分比
            "process_time": self._last_process_time,
            "detection_time": self._last_detection_time,
            "encoding_time": self._last_encoding_time,
            "model_used": model,
            "cuda_used": self.cuda_available and model == 'cnn'
        }

