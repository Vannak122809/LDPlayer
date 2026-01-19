import random
import threading
import time
from datetime import datetime

class DeviceTaskRunner(threading.Thread):
    def __init__(self, index, controller, settings, log_callback):
        super().__init__()
        self.index = index
        self.controller = controller
        self.settings = settings
        self.log_callback = log_callback # Optional: function to print logs
        self.running = True
        self.daemon = True

    def log(self, msg):
        print(f"[Device {self.index}] {msg}")

    def run(self):
        self.log("Task Runner started.")
        
        # 0. Launch App
        # Assuming Facebook package
        fb_pkg = "com.facebook.katana"
        # If user wants another app, logic would be here.
        
        self.log("Launching Facebook...")
        self.controller.adb_start_app(self.index, fb_pkg)
        time.sleep(10) # Wait for load
        
        try:
            # 1. Scroll Feed
            if self.settings.get("scroll_news"):
                min_m = int(self.settings.get("scroll_news_val1", 2))
                max_m = int(self.settings.get("scroll_news_val2", 3))
                duration = random.randint(min_m * 60, max_m * 60)
                
                self.log(f"Scrolling News Feed for ~{duration}s")
                end_time = time.time() + duration
                while time.time() < end_time and self.running:
                    # Swipe Up
                    x = random.randint(200, 500)
                    y_start = random.randint(800, 1000)
                    y_end = random.randint(200, 400)
                    self.controller.adb_swipe(self.index, x, y_start, x, y_end, random.randint(500, 1000))
                    time.sleep(random.uniform(2.0, 5.0))
            
            # 2. Add Friends
            if self.settings.get("add_friends") and self.running:
                count = int(self.settings.get("add_friends_val1", 1))
                self.log(f"Adding {count} friends (Simulated taps)")
                for _ in range(count):
                    if not self.running: break
                    # Dummy coordinate for "Add Friend" - highly dependent on UI
                    self.controller.adb_tap(self.index, 650, 300) 
                    time.sleep(2)

            # 3. Comments (Simulated)
            if self.settings.get("comments") and self.settings.get("comments_val2") and self.running:
                comment_text = self.settings.get("comments_val2")
                self.log(f"Posting comment: {comment_text}")
                # Click comment box (approx)
                self.controller.adb_tap(self.index, 300, 1100) 
                time.sleep(1)
                self.controller.adb_input_text(self.index, comment_text)
                time.sleep(1)
                # Send
                self.controller.adb_tap(self.index, 650, 1150)
                
            # 4. Wait / Loop Delay
            if self.settings.get("loop_delay"):
                min_s = int(self.settings.get("loop_delay_val1", 20))
                max_s = int(self.settings.get("loop_delay_val2", 25))
                wait = random.randint(min_s, max_s)
                self.log(f"Loop delay: {wait}s")
                time.sleep(wait)

            self.log("Tasks completed.")
            
            # Shutdown if requested
            if self.settings.get("shutdown"):
                 self.log("Shutting down instance settings enabled.")
                 self.controller.stop_instance(self.index)

        except Exception as e:
            self.log(f"Error in task: {e}")

class AutomationManager:
    def __init__(self, controller, update_timer_callback, log_callback=None):
        self.controller = controller
        self.update_timer_callback = update_timer_callback
        self.log_callback = log_callback
        self.running = False
        self.start_time = None
        self.thread = None
        
        # Configuration
        self.max_active = 1
        self.selected_instances = [] 
        self.delay_between_start = 40 
        self.wait_after_boot = 60 
        self.task_settings = {}
        
        self.active_workers = {} # index -> thread
        
    def start_automation(self, selected_instances, max_active, interval_delay=40, boot_delay=60, task_settings=None):
        if self.running:
            return
            
        self.selected_instances = list(selected_instances)
        self.max_active = int(max_active)
        self.delay_between_start = int(interval_delay)
        self.wait_after_boot = int(boot_delay)
        self.task_settings = task_settings or {}
        
        self.running = True
        self.start_time = datetime.now()
        self.active_workers = {}
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        
        # Start worker thread
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        
    def stop_automation(self):
        self.running = False
        self.start_time = None
        # Signal workers to stop
        for idx in self.active_workers:
            if self.active_workers[idx]:
                self.active_workers[idx].running = False
        
    def _timer_loop(self):
        while self.running and self.start_time:
            delta = datetime.now() - self.start_time
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            
            if self.update_timer_callback:
                self.update_timer_callback(time_str)
            time.sleep(1)
            
    def _worker_loop(self):
        queue = list(self.selected_instances)
        print(f"Queue: {queue}")
        print(f"Settings: {self.task_settings}")

        while self.running:
            # 1. Clean up dead workers
            stopped_indices = []
            for idx, worker in list(self.active_workers.items()):
                if not worker.is_alive():
                    # Worker finished
                    stopped_indices.append(idx)
                    # Check if instance is still running, maybe close it if not "shutdown" logic
            
            for idx in stopped_indices:
                del self.active_workers[idx]

            # 2. Check running count logic
            # Get REAL running count from controller for safety
            # But "Max Active" usually applies to how many WE control.
            
            current_count = len(self.active_workers)
            
            if current_count < self.max_active and queue:
                next_in_line = queue.pop(0)
                print(f"Launching instance {next_in_line}...")
                
                # Start LD
                self.controller.start_instance(next_in_line)
                
                # Wait Boot
                time.sleep(self.wait_after_boot)
                
                # Start Task Runner
                if self.running:
                    worker = DeviceTaskRunner(next_in_line, self.controller, self.task_settings, self.log_callback)
                    worker.start()
                    self.active_workers[next_in_line] = worker
                    
                    # Interval Delay
                    if queue: # Only wait if more to come
                        print(f"Waiting interval {self.delay_between_start}s...")
                        time.sleep(self.delay_between_start)
            
            time.sleep(1)
            
            if not queue and not self.active_workers:
                print("All tasks finished.")
                self.running = False
                break
        
        print("Automation loop ended.")
