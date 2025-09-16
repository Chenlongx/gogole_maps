
# Maps_scraper.py 滚动卡顿修复集成指南

## 🔧 修复步骤

### 1. 备份原文件
```bash
cp Maps_scraper.py Maps_scraper.py.backup
```

### 2. 在GoogleMapsApp类的__init__方法中添加
```python
def __init__(self):
    # ... 现有代码 ...
    
    # 添加滚动性能优化组件
    self.scroll_throttler = ScrollThrottler(200)  # 200ms节流
    self.background_processor = BackgroundScrollProcessor()
    self.dom_cleaner = DOMCleaner(1000)  # 每处理1000个商家清理一次
    self.performance_monitor = ScrollPerformanceMonitor()
    
    print("🚀 [滚动优化] 性能优化组件已初始化")
```

### 3. 替换_scroll_and_wait方法
```python
def _scroll_and_wait(self, tab_index, current_count):
    """【性能优化版】滚动列表并等待新结果"""
    
    # 检查节流
    if not self.scroll_throttler.can_scroll(tab_index):
        print(f"🔄 (标签页 {tab_index+1}) 滚动被节流，稍后重试")
        QTimer.singleShot(300, lambda: self._scroll_and_wait(tab_index, current_count))
        return
    
    browser_view = self.tabs[tab_index]['view']
    
    # 记录滚动开始
    self.performance_monitor.record_scroll_start()
    
    # 异步执行滚动
    def scroll_callback(result):
        self.performance_monitor.record_scroll_end()
        self._handle_scroll_result(tab_index, current_count, result)
    
    self.background_processor.process_scroll_async(tab_index, browser_view, scroll_callback)
```

### 4. 添加DOM清理检查
```python
def after_extraction_and_move_on(self, tab_index):
    """【改造版】处理完一个商家后，继续处理下一个"""
    if not self.is_searching or tab_index >= len(self.tabs): 
        return
    
    tab_info = self.tabs[tab_index]
    if tab_info['state'] != 'running': 
        return

    tab_info['current_item_index'] = tab_info.get('current_item_index', 0) + 1
    
    # 检查是否需要DOM清理
    if self.dom_cleaner.should_cleanup():
        self.dom_cleaner.cleanup_dom(tab_info['view'])
    
    # 继续处理下一个商家
    QTimer.singleShot(100, lambda: self._process_next_item(tab_index))
```

### 5. 添加性能监控输出
```python
def finish_region_extraction(self, tab_index):
    """【改造版】一个地区任务完成后的核心回调"""
    # ... 现有代码 ...
    
    # 输出性能报告
    print(self.performance_monitor.get_performance_report())
    
    # ... 其余代码不变 ...
```

## 📊 预期效果

修复后应该观察到：
1. ✅ 滚动操作不再长时间阻塞UI
2. ✅ 内存使用更加稳定，不会持续增长
3. ✅ 滚动响应更加流畅
4. ✅ 程序不会在滚动到底部时卡死

## 🔍 监控指标

通过日志观察以下指标：
- 滚动节流日志："滚动被节流，稍后重试"
- DOM清理日志："清理了X个DOM元素"
- UI冻结警告："检测到UI冻结: X秒"
- 性能报告：平均滚动时间应<1秒

## 🚨 注意事项

1. 修改后请先在小数据集上测试
2. 观察内存使用情况，确保没有内存泄漏
3. 如果出现问题，可以还原备份文件
4. 可以根据实际情况调整节流时间和清理频率
