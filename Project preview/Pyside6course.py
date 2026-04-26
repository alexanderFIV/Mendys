from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
import sys

# 1. Create the application object. 
# sys.argv allows the app to process command line arguments.
app = QApplication(sys.argv)

# 2. Create the main window
window = QMainWindow()
window.setWindowTitle("Hello there")
window.resize(300, 100)

# 3. Create a widget (a button in this case)
button = QPushButton("Exit")

def button_clicked():
    """
    Slot: This function runs when the 'clicked' signal is emitted by the button.
    It replaces the central widget with a label.
    """
    qlabel = QLabel("I am alive")
    window.setCentralWidget(qlabel)


# 4. Set the initial central widget of the window
window.setCentralWidget(button)

# 5. Connect the 'clicked' signal of the button to our slot function
button.clicked.connect(button_clicked)

# 6. Show the window and start the event loop
window.show()
app.exec()