"""
DeepFocus 后台工作线程模块

实现QThread多线程，防止GUI在处理时卡顿
"""

from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import logging
from typing import List

from core.face_engine import FaceEngine


class RecognitionWorker(QThread):
    """
    人脸识别工作线程
    
    在后台线程执行人脸识别任务，避免阻塞GUI主线程。
    通过信号槽机制将结果传回主线程更新UI。
    
    Signals:
        update_signal: 识别完成信号，传递(结果图像, 信息文本)
        progress_signal: 进度更新信号，传递进度百分比(0-100)
        error_signal: 错误信号，传递错误消息字符串
    """
    
    # 定义信号（必须在类定义时声明）
    update_signal = pyqtSignal(np.ndarray, str)  # (结果图像, 信息文本)
    progress_signal = pyqtSignal(int)  # 进度百分比
    error_signal = pyqtSignal(str)  # 错误消息
    
    def __init__(self, engine: FaceEngine, scene_path: str, upsample: int = 1):
        """
        初始化识别工作线程
        
        Args:
            engine: 人脸识别引擎实例
            scene_path: 场景图像路径
            upsample: 上采样次数（0-2）
        """
        super().__init__()
        self.engine = engine
        self.scene_path = scene_path
        self.upsample = upsample
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """
        在后台线程执行识别任务
        
        这个方法会在调用start()后自动在新线程中运行。
        不要直接调用此方法，使用start()启动线程。
        """
        try:
            self.logger.info(f"识别线程开始: {self.scene_path}")
            
            # 发送开始进度
            self.progress_signal.emit(10)
            
            # 执行识别（耗时操作）
            self.logger.debug("正在处理场景图...")
            result_img, info = self.engine.process_scene(
                self.scene_path,
                upsample=self.upsample
            )
            
            # 发送完成进度
            self.progress_signal.emit(100)
            
            # 发送识别结果
            self.update_signal.emit(result_img, info)
            
            self.logger.info(f"识别线程完成: {info}")
            
        except Exception as e:
            # 捕获异常并通过信号传递
            error_msg = f"识别失败: {str(e)}"
            self.logger.exception(error_msg)
            self.error_signal.emit(error_msg)


class BatchProcessWorker(QThread):
    """
    批量处理工作线程
    
    批量处理多张场景图像，依次执行识别任务。
    适用于需要处理多张图片的场景。
    
    Signals:
        update_signal: 单张完成信号，传递(索引, 文件名, 结果图像)
        progress_signal: 进度信号，传递(当前数, 总数)
        finished_signal: 全部完成信号，传递结果列表
        error_signal: 错误信号，传递错误消息
    """
    
    # 定义信号
    update_signal = pyqtSignal(int, str, np.ndarray)  # (索引, 文件名, 结果图像)
    progress_signal = pyqtSignal(int, int)  # (当前, 总数)
    finished_signal = pyqtSignal(list)  # 所有结果
    error_signal = pyqtSignal(str)  # 错误消息
    
    def __init__(
        self,
        engine: FaceEngine,
        scene_paths: List[str],
        upsample: int = 1
    ):
        """
        初始化批处理工作线程
        
        Args:
            engine: 人脸识别引擎实例
            scene_paths: 场景图像路径列表
            upsample: 上采样次数（0-2）
        """
        super().__init__()
        self.engine = engine
        self.scene_paths = scene_paths
        self.upsample = upsample
        self.logger = logging.getLogger(__name__)
        
        # 停止标志
        self._stop_flag = False
    
    def run(self):
        """
        在后台线程批量处理多个场景图
        
        依次处理每张图像，发送进度和结果信号。
        如果某张图像处理失败，记录错误但继续处理其他图像。
        """
        results = []
        total = len(self.scene_paths)
        
        self.logger.info(f"批处理线程开始，共{total}张图像")
        
        try:
            for i, scene_path in enumerate(self.scene_paths):
                # 检查停止标志
                if self._stop_flag:
                    self.logger.info("批处理被用户停止")
                    break
                
                try:
                    self.logger.debug(f"处理第{i+1}/{total}张: {scene_path}")
                    
                    # 处理单张图像
                    result_img, info = self.engine.process_scene(
                        scene_path,
                        upsample=self.upsample
                    )
                    
                    # 保存结果
                    result_data = {
                        'index': i,
                        'path': scene_path,
                        'image': result_img,
                        'info': info,
                        'success': True
                    }
                    results.append(result_data)
                    
                    # 发送单张完成信号
                    import os
                    filename = os.path.basename(scene_path)
                    self.update_signal.emit(i, filename, result_img)
                    
                    # 发送进度信号
                    self.progress_signal.emit(i + 1, total)
                    
                    self.logger.debug(f"第{i+1}张处理完成")
                    
                except Exception as e:
                    # 单张失败不影响其他图像
                    error_msg = f"处理失败: {scene_path} - {str(e)}"
                    self.logger.error(error_msg)
                    
                    # 记录失败结果
                    results.append({
                        'index': i,
                        'path': scene_path,
                        'image': None,
                        'info': error_msg,
                        'success': False
                    })
                    
                    # 继续下一张
                    continue
            
            # 发送全部完成信号
            self.finished_signal.emit(results)
            
            success_count = sum(1 for r in results if r.get('success', False))
            self.logger.info(f"批处理完成: 成功{success_count}/{total}张")
            
        except Exception as e:
            # 整体错误
            error_msg = f"批处理失败: {str(e)}"
            self.logger.exception(error_msg)
            self.error_signal.emit(error_msg)
    
    def stop(self):
        """
        停止批处理
        
        设置停止标志，线程将在处理完当前图像后停止。
        """
        self.logger.info("请求停止批处理")
        self._stop_flag = True


class ProgressWorker(QThread):
    """
    通用进度工作线程
    
    用于执行任意耗时操作并报告进度。
    
    Signals:
        progress_signal: 进度信号(0-100)
        finished_signal: 完成信号
        error_signal: 错误信号
    """
    
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)
    
    def __init__(self, task_func, *args, **kwargs):
        """
        初始化进度工作线程
        
        Args:
            task_func: 要执行的任务函数
            *args: 任务函数的位置参数
            **kwargs: 任务函数的关键字参数
        """
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """执行任务"""
        try:
            self.logger.debug("进度线程开始")
            self.progress_signal.emit(0)
            
            # 执行任务
            result = self.task_func(*self.args, **self.kwargs)
            
            self.progress_signal.emit(100)
            self.finished_signal.emit(result)
            
            self.logger.debug("进度线程完成")
            
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            self.logger.exception(error_msg)
            self.error_signal.emit(error_msg)


# 工具函数
def create_recognition_worker(
    engine: FaceEngine,
    scene_path: str,
    upsample: int = 2
) -> RecognitionWorker:
    """
    创建识别工作线程（工厂函数）
    
    Args:
        engine: 人脸识别引擎
        scene_path: 场景图像路径
        upsample: 上采样次数
        
    Returns:
        RecognitionWorker: 识别工作线程实例
    """
    return RecognitionWorker(engine, scene_path, upsample)


def create_batch_worker(
    engine: FaceEngine,
    scene_paths: List[str],
    upsample: int = 2
) -> BatchProcessWorker:
    """
    创建批处理工作线程（工厂函数）
    
    Args:
        engine: 人脸识别引擎
        scene_paths: 场景图像路径列表
        upsample: 上采样次数
        
    Returns:
        BatchProcessWorker: 批处理工作线程实例
    """
    return BatchProcessWorker(engine, scene_paths, upsample)

