"""
FaceEngine 核心引擎单元测试

测试人脸检测、特征提取和匹配功能
"""

import unittest
import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.face_engine import FaceEngine, create_engine
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"警告: 依赖库未安装 - {e}")
    print("请运行: pip install -r requirements.txt")


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "依赖库未安装")
class TestFaceEngine(unittest.TestCase):
    """FaceEngine 测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 测试图像路径
        cls.target_image = "Images/目标脸.jpg"
        cls.scene_image = "Images/Image-1.jpg"
        
        # 检查测试图像是否存在
        cls.images_exist = (
            os.path.exists(cls.target_image) and
            os.path.exists(cls.scene_image)
        )
    
    def test_01_engine_initialization(self):
        """测试引擎初始化"""
        # 测试默认参数
        engine = FaceEngine()
        self.assertEqual(engine.model_method, 'hog')
        self.assertEqual(engine.tolerance, 0.45)
        self.assertIsNone(engine.target_encoding)
        
        # 测试自定义参数
        engine2 = FaceEngine(model_method='cnn', tolerance=0.50)
        self.assertEqual(engine2.model_method, 'cnn')
        self.assertEqual(engine2.tolerance, 0.50)
    
    def test_02_factory_function(self):
        """测试工厂函数"""
        engine = create_engine(model_method='hog', tolerance=0.40)
        self.assertIsInstance(engine, FaceEngine)
        self.assertEqual(engine.tolerance, 0.40)
    
    @unittest.skipIf(not os.path.exists("Images/目标脸.jpg"), "测试图像不存在")
    def test_03_load_target_face_success(self):
        """测试加载目标人脸（成功情况）"""
        engine = FaceEngine()
        success = engine.load_target_face(self.target_image)
        
        self.assertTrue(success, "目标人脸应该加载成功")
        self.assertIsNotNone(engine.target_encoding, "特征向量应该被提取")
        self.assertEqual(len(engine.target_encoding), 128, "特征向量应该是128维")
    
    def test_04_load_target_face_invalid_path(self):
        """测试加载不存在的图像文件"""
        engine = FaceEngine()
        success = engine.load_target_face("nonexistent_file.jpg")
        
        self.assertFalse(success, "不存在的文件应该返回False")
        self.assertIsNone(engine.target_encoding, "特征向量应该为None")
    
    @unittest.skipIf(
        not (os.path.exists("Images/目标脸.jpg") and os.path.exists("Images/Image-1.jpg")),
        "测试图像不存在"
    )
    def test_05_process_scene_success(self):
        """测试处理场景图像（成功情况）"""
        engine = FaceEngine()
        
        # 先加载目标人脸
        engine.load_target_face(self.target_image)
        
        # 处理场景图
        result_img, info = engine.process_scene(self.scene_image, upsample=1)
        
        # 验证返回值
        self.assertIsNotNone(result_img, "应该返回图像")
        self.assertIsInstance(info, str, "应该返回字符串信息")
        self.assertIn("检测到人脸", info, "信息应该包含检测统计")
        
        # 验证图像尺寸
        self.assertEqual(len(result_img.shape), 3, "应该返回彩色图像")
    
    def test_06_process_scene_without_target(self):
        """测试未加载目标时处理场景"""
        engine = FaceEngine()
        
        # 未加载目标人脸就处理场景
        with self.assertRaises(ValueError) as context:
            engine.process_scene(self.scene_image)
        
        self.assertIn("加载目标人脸", str(context.exception))
    
    @unittest.skipIf(not os.path.exists("Images/目标脸.jpg"), "测试图像不存在")
    def test_07_get_target_info(self):
        """测试获取目标信息"""
        engine = FaceEngine()
        
        # 未加载时
        info = engine.get_target_info()
        self.assertIsNone(info, "未加载时应返回None")
        
        # 加载后
        engine.load_target_face(self.target_image)
        info = engine.get_target_info()
        
        self.assertIsNotNone(info, "加载后应返回信息")
        self.assertEqual(info['feature_dim'], 128)
        self.assertTrue(info['loaded'])
    
    @unittest.skipIf(not os.path.exists("Images/目标脸.jpg"), "测试图像不存在")
    def test_08_reset_target(self):
        """测试重置目标"""
        engine = FaceEngine()
        
        # 加载目标
        engine.load_target_face(self.target_image)
        self.assertIsNotNone(engine.target_encoding)
        
        # 重置
        engine.reset_target()
        self.assertIsNone(engine.target_encoding, "重置后特征应为None")
    
    @unittest.skipIf(
        not (os.path.exists("Images/目标脸.jpg") and os.path.exists("Images/Image-1.jpg")),
        "测试图像不存在"
    )
    def test_09_upsample_parameter(self):
        """测试上采样参数"""
        engine = FaceEngine()
        engine.load_target_face(self.target_image)
        
        # 测试不同的上采样值
        for upsample in [0, 1, 2]:
            result_img, info = engine.process_scene(self.scene_image, upsample=upsample)
            self.assertIsNotNone(result_img, f"upsample={upsample}应该成功")
            print(f"Upsample={upsample}: {info}")


class TestFaceEngineIntegration(unittest.TestCase):
    """FaceEngine 集成测试"""
    
    @unittest.skipIf(not DEPENDENCIES_AVAILABLE, "依赖库未安装")
    @unittest.skipIf(
        not (os.path.exists("Images/目标脸.jpg") and os.path.exists("Images/Image-1.jpg")),
        "测试图像不存在"
    )
    def test_complete_workflow(self):
        """测试完整工作流程"""
        print("\n=== 完整工作流程测试 ===")
        
        # 1. 创建引擎
        print("1. 创建人脸识别引擎...")
        engine = create_engine(model_method='hog', tolerance=0.45)
        
        # 2. 加载目标人脸
        print("2. 加载目标人脸...")
        success = engine.load_target_face("Images/目标脸.jpg")
        self.assertTrue(success, "目标加载失败")
        print("   ✓ 目标人脸加载成功")
        
        # 3. 获取目标信息
        info = engine.get_target_info()
        print(f"   目标信息: {info}")
        
        # 4. 处理场景图
        print("3. 处理场景图像...")
        result_img, result_info = engine.process_scene(
            "Images/Image-1.jpg",
            upsample=2
        )
        print(f"   结果: {result_info}")
        print("   ✓ 场景处理完成")
        
        # 5. 验证结果
        self.assertIsNotNone(result_img)
        self.assertIn("检测到人脸", result_info)
        
        print("\n=== 测试通过 ===\n")


def run_tests():
    """运行测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestFaceEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestFaceEngineIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # 运行测试
    success = run_tests()
    
    # 退出码
    sys.exit(0 if success else 1)

