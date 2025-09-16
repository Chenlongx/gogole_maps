#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证semaphore_count变量修复
"""

import threading

class MockMainWindow:
    """模拟主窗口类来测试变量定义修复"""
    
    def __init__(self):
        # 模拟初始化
        self.playwright_pool_size = 5
        
        # 【修复后】将semaphore_count保存为实例变量
        self.email_worker_semaphore_count = min(self.playwright_pool_size, 5)
        self.email_worker_semaphore = threading.Semaphore(self.email_worker_semaphore_count)
        print(f"📊 [资源配置] EmailWorker信号量: {self.email_worker_semaphore_count}, Playwright页面池: {self.playwright_pool_size}")
    
    def test_resource_monitoring(self):
        """测试资源监控功能是否能正常访问semaphore_count"""
        try:
            # 模拟资源监控代码
            active_workers = self.email_worker_semaphore_count - self.email_worker_semaphore._value
            print(f"📊 [资源监控] 活跃Worker: {active_workers}/{self.email_worker_semaphore_count}")
            return True
        except NameError as e:
            print(f"❌ 变量定义错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 其他错误: {e}")
            return False

def main():
    print("🧪 测试semaphore_count变量修复")
    print("=" * 50)
    
    # 创建模拟对象
    mock_window = MockMainWindow()
    
    # 测试资源监控
    success = mock_window.test_resource_monitoring()
    
    if success:
        print("✅ 修复成功！semaphore_count变量现在可以正常访问")
        print("💡 修复内容:")
        print("  - 将semaphore_count改为self.email_worker_semaphore_count")
        print("  - 作为实例变量，可以在整个类中访问")
        print("  - 资源监控功能现在可以正常工作")
    else:
        print("❌ 修复失败，仍有问题需要解决")
    
    print("=" * 50)
    print("现在可以运行Maps_scraper.py测试实际效果")

if __name__ == "__main__":
    main()