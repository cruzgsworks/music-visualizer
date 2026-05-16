#!/usr/bin/env python3
"""
Quick diagnostic script to test the visualizer GUI button functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os

def test_button():
    """Simple test to verify button clicks work"""
    print("Button clicked successfully!")
    messagebox.showinfo("Test", "Button is working!")

def main():
    root = tk.Tk()
    root.title("Button Test")
    root.geometry("400x200")
    
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Click the button below to test:", font=('Arial', 12)).pack(pady=10)
    
    btn = ttk.Button(frame, text="▶ Click Me", command=test_button, width=20)
    btn.pack(pady=10)
    
    status_label = ttk.Label(frame, text="Button state: Enabled", foreground='green')
    status_label.pack(pady=5)
    
    def toggle_button():
        current_state = btn['state']
        if current_state == 'disabled':
            btn.config(state=tk.NORMAL)
            status_label.config(text="Button state: Enabled", foreground='green')
        else:
            btn.config(state=tk.DISABLED)
            status_label.config(text="Button state: Disabled", foreground='red')
    
    ttk.Button(frame, text="Toggle Button State", command=toggle_button).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    main()
