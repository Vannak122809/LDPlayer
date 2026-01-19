from ui import LDManagerApp
import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    # Check for admin rights
    if is_admin():
        try:
            app = LDManagerApp()
            app.mainloop()
        except Exception as e:
            import traceback
            traceback.print_exc()
            input("Error occurred. Press Enter to close...")
    else:
        # Re-run the program with admin rights
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                f'"{__file__}"', 
                None, 
                1
            )
        except Exception as e:
            print(f"Failed to elevate: {e}")
            input("Press Enter to exit...")
