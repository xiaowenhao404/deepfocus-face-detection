"""
图像预处理模块单元测试

测试CLAHE增强、色彩空间转换等功能
"""

import unittest
import os
import sys
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.preprocessing import (
        apply_clahe,
        histogram_equalization,
        gamma_correction,
        denoise_image,
        enhance_image_quality
    )
    from core.image_utils import (
        safe_imread,
        save_image,
        resize_image,
        convert_color_space,
        crop_image,
        get_image_info,
        validate_image,
        is_supported_format
    )
    import cv2
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"警告: 依赖库未安装 - {e}")


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "依赖库未安装")
class TestCLAHE(unittest.TestCase):
    """CLAHE增强测试"""
    
    def test_clahe_on_color_image(self):
        """测试彩色图CLAHE增强"""
        # 创建测试图像
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        enhanced = apply_clahe(img, clip_limit=2.0, tile_size=8)
        
        # 验证输出
        self.assertEqual(enhanced.shape, img.shape)
        self.assertEqual(enhanced.dtype, img.dtype)
    
    def test_clahe_on_gray_image(self):
        """测试灰度图CLAHE增强"""
        img = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        enhanced = apply_clahe(img)
        
        self.assertEqual(enhanced.shape, img.shape)
        self.assertEqual(enhanced.dtype, img.dtype)
    
    def test_clahe_with_different_params(self):
        """测试不同参数的CLAHE"""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 测试不同clip_limit
        for clip_limit in [1.0, 2.0, 4.0]:
            enhanced = apply_clahe(img, clip_limit=clip_limit)
            self.assertEqual(enhanced.shape, img.shape)
        
        # 测试不同tile_size
        for tile_size in [4, 8, 16]:
            enhanced = apply_clahe(img, tile_size=tile_size)
            self.assertEqual(enhanced.shape, img.shape)
    
    @unittest.skipIf(not os.path.exists("Images/目标脸.jpg"), "测试图像不存在")
    def test_clahe_on_real_image(self):
        """测试真实图像的CLAHE增强"""
        img = safe_imread("Images/目标脸.jpg")
        self.assertIsNotNone(img)
        
        enhanced = apply_clahe(img)
        self.assertEqual(enhanced.shape, img.shape)


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "依赖库未安装")
class TestImageUtils(unittest.TestCase):
    """图像工具函数测试"""
    
    @unittest.skipIf(not os.path.exists("Images/目标脸.jpg"), "测试图像不存在")
    def test_safe_imread_chinese_path(self):
        """测试中文路径读取"""
        img = safe_imread("Images/目标脸.jpg")
        
        self.assertIsNotNone(img, "应该成功读取图像")
        self.assertEqual(len(img.shape), 3, "应该是彩色图像")
        self.assertEqual(img.shape[2], 3, "应该有3个通道")
    
    def test_safe_imread_invalid_path(self):
        """测试无效路径"""
        img = safe_imread("nonexistent_file.jpg")
        self.assertIsNone(img, "不存在的文件应返回None")
    
    def test_resize_image_large(self):
        """测试缩小大图"""
        # 创建一个大图
        img = np.zeros((2000, 3000, 3), dtype=np.uint8)
        
        resized, scale = resize_image(img, max_dimension=1920)
        
        # 验证缩放结果
        self.assertLessEqual(max(resized.shape[:2]), 1920)
        self.assertLess(scale, 1.0, "应该是缩小")
        
        # 验证宽高比保持
        original_ratio = img.shape[1] / img.shape[0]
        resized_ratio = resized.shape[1] / resized.shape[0]
        self.assertAlmostEqual(original_ratio, resized_ratio, places=2)
    
    def test_resize_image_small(self):
        """测试小图不缩放"""
        img = np.zeros((800, 600, 3), dtype=np.uint8)
        
        resized, scale = resize_image(img, max_dimension=1920)
        
        # 小图应该不缩放
        self.assertEqual(scale, 1.0)
        self.assertTrue(np.array_equal(img, resized))
    
    def test_convert_color_space(self):
        """测试色彩空间转换"""
        bgr_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # BGR转RGB
        rgb_img = convert_color_space(bgr_img, 'RGB')
        self.assertEqual(rgb_img.shape, bgr_img.shape)
        
        # BGR转灰度
        gray_img = convert_color_space(bgr_img, 'GRAY')
        self.assertEqual(len(gray_img.shape), 2)
        
        # BGR转HSV
        hsv_img = convert_color_space(bgr_img, 'HSV')
        self.assertEqual(hsv_img.shape, bgr_img.shape)
        
        # BGR转LAB
        lab_img = convert_color_space(bgr_img, 'LAB')
        self.assertEqual(lab_img.shape, bgr_img.shape)
    
    def test_convert_color_space_invalid(self):
        """测试不支持的色彩空间"""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        with self.assertRaises(ValueError):
            convert_color_space(img, 'INVALID')
    
    def test_crop_image(self):
        """测试图像裁剪"""
        img = np.ones((200, 300, 3), dtype=np.uint8) * 128
        
        # 裁剪中心区域
        cropped = crop_image(img, 50, 50, 100, 100)
        
        self.assertEqual(cropped.shape, (100, 100, 3))
    
    def test_crop_image_boundary(self):
        """测试裁剪边界情况"""
        img = np.ones((100, 100, 3), dtype=np.uint8)
        
        # 超出边界的裁剪
        cropped = crop_image(img, 80, 80, 50, 50)
        
        # 应该自动限制在有效范围
        self.assertLessEqual(cropped.shape[0], 20)
        self.assertLessEqual(cropped.shape[1], 20)
    
    def test_get_image_info(self):
        """测试获取图像信息"""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        info = get_image_info(img)
        
        self.assertEqual(info['shape'], (480, 640, 3))
        self.assertEqual(info['channels'], 3)
        self.assertEqual(info['size'], 480 * 640 * 3)
    
    def test_validate_image(self):
        """测试图像验证"""
        # 有效图像
        valid_img = np.zeros((100, 100, 3), dtype=np.uint8)
        self.assertTrue(validate_image(valid_img))
        
        # 无效图像
        self.assertFalse(validate_image(None))
        self.assertFalse(validate_image([1, 2, 3]))
        self.assertFalse(validate_image(np.array([])))
    
    def test_is_supported_format(self):
        """测试格式支持检查"""
        self.assertTrue(is_supported_format("image.jpg"))
        self.assertTrue(is_supported_format("image.png"))
        self.assertTrue(is_supported_format("image.bmp"))
        self.assertFalse(is_supported_format("image.txt"))


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "依赖库未安装")
class TestOtherPreprocessing(unittest.TestCase):
    """其他预处理功能测试"""
    
    def test_histogram_equalization(self):
        """测试全局直方图均衡化"""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        equalized = histogram_equalization(img)
        
        self.assertEqual(equalized.shape, img.shape)
    
    def test_gamma_correction(self):
        """测试伽马校正"""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 增亮
        bright = gamma_correction(img, gamma=0.5)
        self.assertEqual(bright.shape, img.shape)
        
        # 变暗
        dark = gamma_correction(img, gamma=2.0)
        self.assertEqual(dark.shape, img.shape)
    
    def test_denoise_image(self):
        """测试图像去噪"""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 双边滤波
        denoised = denoise_image(img, method='bilateral', strength=5)
        self.assertEqual(denoised.shape, img.shape)
        
        # 高斯滤波
        denoised = denoise_image(img, method='gaussian', strength=3)
        self.assertEqual(denoised.shape, img.shape)
        
        # 中值滤波
        denoised = denoise_image(img, method='median', strength=3)
        self.assertEqual(denoised.shape, img.shape)
    
    def test_enhance_image_quality(self):
        """测试综合图像增强"""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 只CLAHE
        enhanced1 = enhance_image_quality(img, apply_clahe_flag=True, denoise_flag=False)
        self.assertEqual(enhanced1.shape, img.shape)
        
        # CLAHE + 去噪
        enhanced2 = enhance_image_quality(img, apply_clahe_flag=True, denoise_flag=True)
        self.assertEqual(enhanced2.shape, img.shape)


@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "依赖库未安装")
class TestImageIO(unittest.TestCase):
    """图像读写测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_output_dir = "outputs/test_temp"
        os.makedirs(self.test_output_dir, exist_ok=True)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
    
    def test_save_and_load_image(self):
        """测试图像保存和读取"""
        # 创建测试图像
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 保存
        save_path = os.path.join(self.test_output_dir, "test.jpg")
        success = save_image(img, save_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(save_path))
        
        # 读取
        loaded_img = safe_imread(save_path)
        self.assertIsNotNone(loaded_img)
        self.assertEqual(loaded_img.shape, img.shape)
    
    def test_save_image_with_chinese_path(self):
        """测试中文路径保存"""
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        # 中文路径
        save_path = os.path.join(self.test_output_dir, "测试图像.jpg")
        success = save_image(img, save_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(save_path))
    
    def test_save_image_different_formats(self):
        """测试不同格式保存"""
        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        # JPEG
        jpg_path = os.path.join(self.test_output_dir, "test.jpg")
        self.assertTrue(save_image(img, jpg_path, quality=90))
        
        # PNG
        png_path = os.path.join(self.test_output_dir, "test.png")
        self.assertTrue(save_image(img, png_path))


def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestCLAHE))
    suite.addTests(loader.loadTestsFromTestCase(TestImageUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestOtherPreprocessing))
    suite.addTests(loader.loadTestsFromTestCase(TestImageIO))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

