from PySide6 import QtWidgets, QtCore, QtGui

class ColorSwatch(QtWidgets.QPushButton):
    colorSelected = QtCore.Signal(str)
    
    def __init__(self, color_hex, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setFixedSize(24, 24)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #ddd; border-radius: 12px;")
        self.clicked.connect(lambda: self.colorSelected.emit(self.color_hex))

def create_color_palette(colors, callback, custom_callback=None, gradient_style=None):
    """
    Creates a QHBoxLayout containing ColorSwatches and an optional custom color button.
    """
    layout = QtWidgets.QHBoxLayout()
    layout.setSpacing(5)
    
    for color in colors:
        swatch = ColorSwatch(color)
        swatch.colorSelected.connect(callback)
        layout.addWidget(swatch)
        
    if custom_callback:
        custom_btn = QtWidgets.QPushButton("+")
        custom_btn.setFixedSize(24, 24)
        custom_btn.setCursor(QtCore.Qt.PointingHandCursor)
        if gradient_style:
            custom_btn.setStyleSheet(f"background: {gradient_style}; color: white; border-radius: 12px; font-weight: bold;")
        else:
            custom_btn.setStyleSheet("background-color: #3f3f46; color: white; border-radius: 12px; font-weight: bold;")
        custom_btn.clicked.connect(custom_callback)
        layout.addWidget(custom_btn)
        
    return layout
