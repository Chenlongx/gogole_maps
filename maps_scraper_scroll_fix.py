#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maps_scraper.py 滚动卡顿修复补丁
专门解决Qt浏览器左侧商家滑动到底部时主程序卡顿的问题

使用说明：
1. 将此文件中的代码替换Maps_scraper.py中对应的方法
2. 在GoogleMapsApp.__init__()中添加初始化代码
3. 重新运行程序测试滚动性能
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

# =====================================================================
# 滚动性能优化组件
# =====================================================================

class ScrollThrottler:
    """滚动节流器 - 限制滚动频率，避免过度频繁的滚动操作"""
    
    def __init__(self, throttle_ms=200):
        self.throttle_ms = throttle_ms
        self.last_scroll_times = {}
        self.adaptive_throttle = {}  # 自适应节流时间
    
    def can_scroll(self, tab_index):
        """检查是否允许滚动"""
        current_time = time.time() * 1000
        
        # 获取当前标签页的节流时间（可能是自适应调整过的）
        current_throttle = self.adaptive_throttle.get(tab_index, self.throttle_ms)
        last_time = self.last_scroll_times.get(tab_index, 0)
        
        if current_time - last_time >= current_throttle:
            self.last_scroll_times[tab_index] = current_time
            return True
        return False
    
    def increase_throttle(self, tab_index, factor=2.0):
        """增加节流时间（当检测到卡顿时）"""
        current = self.adaptive_throttle.get(tab_index, self.throttle_ms)
        new_throttle = min(current * factor, 1000)  # 最大1秒
        self.adaptive_throttle[tab_index] = new_throttle
        print(f"🔧 (标签页 {tab_index+1}) 增加滚动节流至{new_throttle}ms")
    
    def decrease_throttle(self, tab_index, factor=0.8):
        """减少节流时间（当性能恢复时）"""
        current = self.adaptive_throttle.get(tab_index, self.throttle_ms)
        new_throttle = max(current * factor, self.throttle_ms)
        self.adaptive_throttle[tab_index] = new_throttle
        if new_throttle <= self.throttle_ms:
            print(f"✅ (标签页 {tab_index+1}) 滚动节流已恢复正常")

class AsyncScrollManager(QObject):
    """异步滚动管理器 - 在后台线程处理滚动逻辑"""
    
    scroll_completed = pyqtSignal(int, dict)  # tab_index, result
    
    def __init__(self):
        super().__init__()
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="AsyncScroll")
        self.active_tasks = {}
        self.js_execution_cache = {}  # JavaScript执行结果缓存
    
    def async_scroll_and_check(self, tab_index, browser_view, current_count, timeout=25):
        """异步执行滚动和结果检查"""
        
        if tab_index in self.active_tasks:
            print(f"⚠️ (标签页 {tab_index+1}) 上一个滚动任务还在进行中，跳过")
            return
        
        # 提交到后台线程执行
        future = self.executor.submit(
            self._background_scroll_task, 
            tab_index, browser_view, current_count, timeout
        )
        
        self.active_tasks[tab_index] = {
            'future': future,
            'start_time': time.time()
        }
        
        # 监控任务完成
        self._monitor_task_completion(tab_index)
    
    def _background_scroll_task(self, tab_index, browser_view, current_count, timeout):
        """在后台线程中执行的滚动任务"""
        try:
            print(f"🔄 (标签页 {tab_index+1}) 开始后台滚动任务，当前商家数: {current_count}")
            
            # 1. 执行滚动JavaScript
            scroll_success = self._execute_scroll_js_sync(browser_view)
            if not scroll_success:
                return {'success': False, 'error': '滚动JavaScript执行失败'}
            
            # 2. 等待新结果，使用智能轮询
            start_time = time.time()
            check_interval = 0.5  # 开始时每500ms检查一次
            max_interval = 2.0    # 最大间隔2秒
            
            while time.time() - start_time < timeout:
                # 检查新的商家数量
                new_count = self._get_merchant_count_sync(browser_view)
                
                if new_count > current_count:
                    elapsed = time.time() - start_time
                    print(f"✅ (标签页 {tab_index+1}) 发现新商家: {new_count} (用时{elapsed:.1f}s)")
                    return {
                        'success': True,
                        'new_count': new_count,
                        'old_count': current_count,
                        'wait_time': elapsed
                    }
                
                # 动态调整检查间隔
                elapsed = time.time() - start_time
                if elapsed > 10:  # 10秒后降低检查频率
                    check_interval = min(check_interval * 1.2, max_interval)
                
                time.sleep(check_interval)
            
            # 超时处理
            print(f"⏰ (标签页 {tab_index+1}) 滚动等待超时({timeout}s)，可能已到达底部")
            return {
                'success': True,
                'new_count': current_count,
                'old_count': current_count,
                'timeout': True,
                'wait_time': timeout
            }
            
        except Exception as e:
            print(f"❌ (标签页 {tab_index+1}) 后台滚动任务异常: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_scroll_js_sync(self, browser_view):
        """同步执行滚动JavaScript（在后台线程中调用）"""
        js_scroll = """
        (function() {
            const feed = document.querySelector('div[role="feed"]');
            if (!feed) return false;
            
            const oldScrollTop = feed.scrollTop;
            const scrollHeight = feed.scrollHeight;
            
            // 平滑滚动到底部
            feed.scrollTo({
                top: scrollHeight,
                behavior: 'smooth'
            });
            
            // 等待滚动完成
            return new Promise(resolve => {
                setTimeout(() => {
                    resolve(feed.scrollTop > oldScrollTop);
                }, 300);
            });
        })();
        """
        
        result_container = {'result': None, 'completed': False, 'error': None}
        
        def js_callback(result):
            result_container['result'] = result
            result_container['completed'] = True
        
        def execute_js():
            try:
                browser_view.page().runJavaScript(js_scroll, js_callback)
            except Exception as e:
                result_container['error'] = str(e)
                result_container['completed'] = True
        
        # 在主线程中执行JavaScript
        QTimer.singleShot(0, execute_js)
        
        # 等待执行完成
        timeout = 5
        start_time = time.time()
        while not result_container['completed'] and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        if result_container['error']:
            print(f"❌ JavaScript执行错误: {result_container['error']}")
            return False
        
        return bool(result_container.get('result', False))
    
    def _get_merchant_count_sync(self, browser_view):
        """同步获取商家数量（在后台线程中调用）"""
        js_count = "document.querySelectorAll('a.hfpxzc').length;"
        
        result_container = {'result': 0, 'completed': False}
        
        def js_callback(result):
            result_container['result'] = result or 0
            result_container['completed'] = True
        
        def execute_js():
            browser_view.page().runJavaScript(js_count, js_callback)
        
        QTimer.singleShot(0, execute_js)
        
        # 等待执行完成
        timeout = 3
        start_time = time.time()
        while not result_container['completed'] and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        return result_container.get('result', 0)
    
    def _monitor_task_completion(self, tab_index):
        """监控任务完成状态"""
        if tab_index not in self.active_tasks:
            return
        
        task_info = self.active_tasks[tab_index]
        future = task_info['future']
        
        if future.done():
            try:
                result = future.result()
                self.scroll_completed.emit(tab_index, result)
            except Exception as e:
                error_result = {'success': False, 'error': str(e)}
                self.scroll_completed.emit(tab_index, error_result)
            finally:
                del self.active_tasks[tab_index]
        else:
            # 继续监控
            QTimer.singleShot(200, lambda: self._monitor_task_completion(tab_index))
    
    def cancel_task(self, tab_index):
        """取消指定标签页的滚动任务"""
        if tab_index in self.active_tasks:
            self.active_tasks[tab_index]['future'].cancel()
            del self.active_tasks[tab_index]
            print(f"🚫 (标签页 {tab_index+1}) 滚动任务已取消")
    
    def cleanup(self):
        """清理资源"""
        for tab_index in list(self.active_tasks.keys()):
            self.cancel_task(tab_index)
        self.executor.shutdown(wait=True)

class DOMMemoryManager:
    """DOM内存管理器 - 智能清理不必要的DOM元素"""
    
    def __init__(self, cleanup_threshold=500, keep_elements=100):
        self.cleanup_threshold = cleanup_threshold
        self.keep_elements = keep_elements
        self.processed_count = {}  # 每个标签页的处理计数
        self.last_cleanup = {}     # 上次清理时间
    
    def should_cleanup(self, tab_index):
        """检查是否需要清理DOM"""
        count = self.processed_count.get(tab_index, 0)
        self.processed_count[tab_index] = count + 1
        
        # 基于处理数量和时间间隔的双重检查
        if count % self.cleanup_threshold == 0 and count > 0:
            current_time = time.time()
            last_time = self.last_cleanup.get(tab_index, 0)
            
            # 至少间隔30秒才清理一次
            if current_time - last_time > 30:
                self.last_cleanup[tab_index] = current_time
                return True
        
        return False
    
    def cleanup_dom_elements(self, browser_view, tab_index):
        """清理DOM元素"""
        cleanup_js = f"""
        (function() {{
            const merchants = document.querySelectorAll('.Nv2PK');
            let cleaned = 0;
            
            // 只保留最后{self.keep_elements}个商家元素
            if (merchants.length > {self.keep_elements}) {{
                const toRemove = merchants.length - {self.keep_elements};
                
                for (let i = 0; i < toRemove; i++) {{
                    if (merchants[i] && merchants[i].parentNode) {{
                        merchants[i].parentNode.removeChild(merchants[i]);
                        cleaned++;
                    }}
                }}
            }}
            
            // 清理其他可能的内存泄漏
            const images = document.querySelectorAll('img[src*="streetview"], img[src*="maps"]');
            images.forEach(img => {{
                if (img.closest('.Nv2PK:nth-child(n+{self.keep_elements + 1})')) {{
                    img.src = '';  // 清空图片源
                }}
            }});
            
            // 强制垃圾回收（如果支持）
            if (window.gc) {{
                window.gc();
            }}
            
            return {{
                cleaned: cleaned,
                remaining: document.querySelectorAll('.Nv2PK').length,
                total_links: document.querySelectorAll('a.hfpxzc').length
            }};
        }})();
        """
        
        def cleanup_callback(result):
            if result:
                print(f"🧹 (标签页 {tab_index+1}) DOM清理完成: "
                      f"移除{result.get('cleaned', 0)}个元素, "
                      f"保留{result.get('remaining', 0)}个商家, "
                      f"总链接{result.get('total_links', 0)}个")
        
        browser_view.page().runJavaScript(cleanup_js, cleanup_callback)

class ScrollPerformanceMonitor(QObject):
    """滚动性能监控器"""
    
    performance_alert = pyqtSignal(str, float)  # alert_type, value
    
    def __init__(self):
        super().__init__()
        self.metrics = {
            'scroll_count': 0,
            'total_scroll_time': 0,
            'max_scroll_time': 0,
            'ui_freeze_count': 0,
            'last_ui_check': time.time()
        }
        
        # 创建监控定时器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._check_ui_responsiveness)
        self.monitor_timer.start(2000)  # 每2秒检查一次
    
    def record_scroll_start(self, tab_index):
        """记录滚动开始"""
        self.scroll_start_time = time.time()
        self.current_tab = tab_index
    
    def record_scroll_end(self, tab_index, success=True):
        """记录滚动结束"""
        if hasattr(self, 'scroll_start_time'):
            duration = time.time() - self.scroll_start_time
            
            self.metrics['scroll_count'] += 1
            self.metrics['total_scroll_time'] += duration
            self.metrics['max_scroll_time'] = max(self.metrics['max_scroll_time'], duration)
            
            if duration > 3.0:  # 超过3秒视为性能问题
                self.metrics['ui_freeze_count'] += 1
                print(f"⚠️ (标签页 {tab_index+1}) 滚动耗时过长: {duration:.1f}秒")
                self.performance_alert.emit('slow_scroll', duration)
    
    def _check_ui_responsiveness(self):
        """检查UI响应性"""
        current_time = time.time()
        time_diff = current_time - self.metrics['last_ui_check']
        
        if time_diff > 5.0:  # 超过5秒未检查，可能UI卡住了
            print(f"⚠️ [UI监控] 检测到可能的UI卡顿: {time_diff:.1f}秒")
            self.performance_alert.emit('ui_freeze', time_diff)
        
        self.metrics['last_ui_check'] = current_time
    
    def get_performance_summary(self):
        """获取性能摘要"""
        if self.metrics['scroll_count'] > 0:
            avg_time = self.metrics['total_scroll_time'] / self.metrics['scroll_count']
            return f"""
📊 滚动性能摘要:
- 总滚动次数: {self.metrics['scroll_count']}
- 平均滚动时间: {avg_time:.2f}秒
- 最长滚动时间: {self.metrics['max_scroll_time']:.2f}秒
- UI冻结次数: {self.metrics['ui_freeze_count']}
- 性能评级: {'优秀' if avg_time < 1 else '良好' if avg_time < 2 else '需要优化'}
            """
        return "📊 暂无滚动性能数据"

# =====================================================================
# 修复后的核心方法 - 替换Maps_scraper.py中的对应方法
# =====================================================================

def init_scroll_optimization(self):
    """
    在GoogleMapsApp.__init__()方法中调用此函数进行初始化
    """
    # 创建滚动优化组件
    self.scroll_throttler = ScrollThrottler(200)  # 200ms节流
    self.async_scroll_manager = AsyncScrollManager()
    self.dom_memory_manager = DOMMemoryManager(500, 100)  # 每500个商家清理一次，保留100个
    self.scroll_performance_monitor = ScrollPerformanceMonitor()
    
    # 连接信号
    self.async_scroll_manager.scroll_completed.connect(self._handle_async_scroll_result)
    self.scroll_performance_monitor.performance_alert.connect(self._handle_performance_alert)
    
    print("🚀 [滚动优化] 滚动性能优化系统已初始化")
    print(f"   - 滚动节流: 200ms")
    print(f"   - DOM清理: 每500个商家清理一次，保留最新100个")
    print(f"   - 性能监控: 每2秒检查一次UI响应性")

def _scroll_and_wait_optimized(self, tab_index, current_count):
    """
    【性能优化版】替换原来的_scroll_and_wait方法
    """
    if not self.is_searching or tab_index >= len(self.tabs):
        return
        
    tab_info = self.tabs[tab_index]
    if tab_info['state'] != 'running':
        return
    
    # 1. 滚动节流检查
    if not self.scroll_throttler.can_scroll(tab_index):
        print(f"🔄 (标签页 {tab_index+1}) 滚动被节流，300ms后重试")
        QTimer.singleShot(300, lambda: self._scroll_and_wait_optimized(tab_index, current_count))
        return
    
    # 2. 记录滚动开始
    self.scroll_performance_monitor.record_scroll_start(tab_index)
    
    # 3. 使用异步滚动管理器
    browser_view = tab_info['view']
    print(f"🔄 (标签页 {tab_index+1}) 开始异步滚动，当前商家数: {current_count}")
    
    self.async_scroll_manager.async_scroll_and_check(
        tab_index, browser_view, current_count, timeout=25
    )

def _handle_async_scroll_result(self, tab_index, result):
    """
    处理异步滚动结果的回调方法
    """
    if not self.is_searching or tab_index >= len(self.tabs):
        return
        
    tab_info = self.tabs[tab_index]
    if tab_info['state'] != 'running':
        return
    
    # 记录滚动结束
    self.scroll_performance_monitor.record_scroll_end(tab_index, result.get('success', False))
    
    if result.get('success'):
        new_count = result.get('new_count', 0)
        old_count = result.get('old_count', 0)
        wait_time = result.get('wait_time', 0)
        
        print(f"✅ (标签页 {tab_index+1}) 异步滚动完成: "
              f"{old_count} -> {new_count} 商家, 用时{wait_time:.1f}s")
        
        # 检查是否到达底部
        if result.get('timeout') or new_count <= old_count:
            print(f"🛑 (标签页 {tab_index+1}) 滚动到底部，当前地区抓取完成")
            self.finish_region_extraction(tab_index)
        else:
            # 有新结果，继续处理
            tab_info['last_merchant_count'] = new_count
            
            # 检查DOM清理
            if self.dom_memory_manager.should_cleanup(tab_index):
                self.dom_memory_manager.cleanup_dom_elements(tab_info['view'], tab_index)
            
            # 继续滚动和提取循环
            QTimer.singleShot(200, lambda: self._scroll_and_extract_loop(tab_index, old_count))
    else:
        error = result.get('error', '未知错误')
        print(f"❌ (标签页 {tab_index+1}) 异步滚动失败: {error}")
        
        # 失败时也要继续，避免程序卡死
        QTimer.singleShot(2000, lambda: self.finish_region_extraction(tab_index))

def _handle_performance_alert(self, alert_type, value):
    """
    处理性能警报
    """
    if alert_type == 'slow_scroll':
        print(f"⚠️ [性能警报] 检测到慢滚动: {value:.1f}秒")
        # 增加所有标签页的滚动节流时间
        for i in range(len(self.tabs)):
            self.scroll_throttler.increase_throttle(i, 1.5)
    
    elif alert_type == 'ui_freeze':
        print(f"⚠️ [性能警报] 检测到UI冻结: {value:.1f}秒")
        # 强制清理所有标签页的DOM
        for i, tab_info in enumerate(self.tabs):
            if tab_info.get('view'):
                self.dom_memory_manager.cleanup_dom_elements(tab_info['view'], i)

def after_extraction_and_move_on_optimized(self, tab_index):
    """
    【性能优化版】替换原来的after_extraction_and_move_on方法
    """
    if not self.is_searching or tab_index >= len(self.tabs): 
        return
    
    tab_info = self.tabs[tab_index]
    if tab_info['state'] != 'running': 
        return

    tab_info['current_item_index'] = tab_info.get('current_item_index', 0) + 1
    
    # 检查DOM清理
    if self.dom_memory_manager.should_cleanup(tab_index):
        self.dom_memory_manager.cleanup_dom_elements(tab_info['view'], tab_index)
    
    # 非阻塞地继续处理下一个商家
    QTimer.singleShot(50, lambda: self._process_next_item(tab_index))

def cleanup_scroll_optimization(self):
    """
    程序结束时清理滚动优化资源
    在程序退出时调用
    """
    if hasattr(self, 'async_scroll_manager'):
        self.async_scroll_manager.cleanup()
    
    if hasattr(self, 'scroll_performance_monitor'):
        print(self.scroll_performance_monitor.get_performance_summary())
    
    print("🧹 [滚动优化] 资源清理完成")

# =====================================================================
# 集成说明
# =====================================================================

INTEGRATION_INSTRUCTIONS = """
# Maps_scraper.py 滚动优化集成说明

## 1. 在GoogleMapsApp.__init__()方法末尾添加:
```python
# 初始化滚动性能优化
self.init_scroll_optimization = lambda: init_scroll_optimization(self)
self.init_scroll_optimization()
```

## 2. 替换以下方法:
- 将 _scroll_and_wait 替换为 _scroll_and_wait_optimized
- 将 after_extraction_and_move_on 替换为 after_extraction_and_move_on_optimized
- 添加 _handle_async_scroll_result 方法
- 添加 _handle_performance_alert 方法

## 3. 在程序退出时添加清理:
```python
def closeEvent(self, event):
    # ... 现有代码 ...
    self.cleanup_scroll_optimization()
    event.accept()
```

## 4. 预期效果:
- ✅ 滚动操作不再阻塞主UI线程
- ✅ 智能节流避免过度频繁滚动
- ✅ 自动清理DOM元素，控制内存使用
- ✅ 实时性能监控，及时发现问题
- ✅ 异步处理提升整体响应性

## 5. 监控日志:
关注以下日志输出来确认修复效果:
- "🔄 滚动被节流，300ms后重试" - 节流正常工作
- "🧹 DOM清理完成" - 内存管理正常
- "⚠️ 检测到慢滚动" - 性能监控正常
- "📊 滚动性能摘要" - 最终性能报告
"""

if __name__ == "__main__":
    print("Maps_scraper.py 滚动卡顿修复补丁")
    print("=" * 50)
    print(INTEGRATION_INSTRUCTIONS)