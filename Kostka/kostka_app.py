import tkinter as tk  
import random
def roll_dice():
    result = random.randint(1, 6)
    label.config(text=f"Result: {result}")
root = tk.Tk()
root.title("Dice Roller")
root.geometry("250x200")
# Simple, high-contrast dark theme for the test app
root.configure(bg="#18181b")
label = tk.Label(root, text="Roll the dice!", font=("Arial", 16, "bold"), 
                 bg="#18181b", fg="#fafafa", pady=30)
label.pack()
button = tk.Button(root, text="ROLL DICE", command=roll_dice, 
                   font=("Arial", 12, "bold"), bg="#3b82f6", fg="white", 
                   padx=20, pady=10, border=0)
button.pack()
root.mainloop()