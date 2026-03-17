import math
from PySide6 import QtWidgets, QtCore
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


class StartMenuDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D Preview - Start Menu")
        self.setModal(True)
        self.resize(300, 250)

        layout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel("Select window mode:")
        layout.addWidget(self.label)

        self.windowed_radio = QtWidgets.QRadioButton("Windowed")
        self.windowed_radio.setChecked(True)
        layout.addWidget(self.windowed_radio)

        self.fullscreen_radio = QtWidgets.QRadioButton("Fullscreen")
        layout.addWidget(self.fullscreen_radio)

        self.borderless_radio = QtWidgets.QRadioButton("Borderless Window")
        layout.addWidget(self.borderless_radio)

        self.card_label = QtWidgets.QLabel("Select card type:")
        layout.addWidget(self.card_label)

        self.card_combo = QtWidgets.QComboBox()
        self.card_combo.addItems(["CR80", "CR79", "CR100", "CR90", "CR50"])
        self.card_combo.setCurrentText("CR80")
        layout.addWidget(self.card_combo)

        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start")
        self.start_button.clicked.connect(self.accept)
        button_layout.addWidget(self.start_button)

        self.exit_button = QtWidgets.QPushButton("Exit")
        self.exit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.exit_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_selected_mode(self):
        if self.fullscreen_radio.isChecked():
            return "fullscreen"
        elif self.borderless_radio.isChecked():
            return "borderless"
        else:
            return "windowed"

    def get_selected_card_type(self):
        return self.card_combo.currentText()


class GLWidget(QOpenGLWidget):
    def __init__(self, card_type="CR80", parent=None):
        # Initialize the OpenGL widget and default rotation angles
        super().__init__(parent)
        self.rotation = [0, 0, 0]
        self.camera_dist = 100.0  # camera distance (bird-eye zoom)
        self.set_card_dimensions(card_type)
        self.quadric = None

    def set_card_dimensions(self, card_type):
        # Set dimensions based on card type (in mm)
        dimensions = {
            "CR80": (85.6, 53.98, 0.76),
            "CR79": (79.0, 50.0, 0.76),
            "CR100": (100.0, 62.0, 0.76),
            "CR90": (90.0, 55.0, 0.76),
            "CR50": (50.0, 30.0, 0.76)
        }
        self.card_w, self.card_h, self.card_t = dimensions.get(card_type, (85.6, 53.98, 0.76))
        self.corner_radius = 3.0  # mm, rounded corner radius (assuming same for all)

    def set_card_type(self, card_type):
        # Change the card type and update dimensions
        self.set_card_dimensions(card_type)
        self.update()  # Redraw the scene

    def initializeGL(self):
        # Called once when GL context is ready; set clear color and depth buffer
        glClearColor(0.5, 0.5, 0.5, 1.0)
        glEnable(GL_DEPTH_TEST)
        self.quadric = gluNewQuadric()

    def resizeGL(self, w, h):
        # Called when widget resizes; update viewport and projection matrix
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h != 0 else 1, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        # Called on each frame; clear buffers, apply camera transforms, draw CR80 card
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_dist)
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)

        self.draw_card()

    def draw_card(self):
        # Draw a PVC card with specified dimensions and 3 mm rounded corners
        corner_radius = self.corner_radius
        card_w, card_h, card_t = self.card_w, self.card_h, self.card_t
        hx, hy, hz = card_w / 2.0, card_h / 2.0, card_t / 2.0
        steps_per_corner = 16

        top_pts = []
        # top-right arc 0..90
        cx, cy = hx - corner_radius, hy - corner_radius
        for i in range(steps_per_corner + 1):
            a = math.radians(0 + (90 / steps_per_corner) * i)
            top_pts.append((cx + corner_radius * math.cos(a), cy + corner_radius * math.sin(a), hz))
        # top-left arc 90..180
        cx, cy = -hx + corner_radius, hy - corner_radius
        for i in range(steps_per_corner + 1):
            a = math.radians(90 + (90 / steps_per_corner) * i)
            top_pts.append((cx + corner_radius * math.cos(a), cy + corner_radius * math.sin(a), hz))
        # bottom-left arc 180..270
        cx, cy = -hx + corner_radius, -hy + corner_radius
        for i in range(steps_per_corner + 1):
            a = math.radians(180 + (90 / steps_per_corner) * i)
            top_pts.append((cx + corner_radius * math.cos(a), cy + corner_radius * math.sin(a), hz))
        # bottom-right arc 270..360
        cx, cy = hx - corner_radius, -hy + corner_radius
        for i in range(steps_per_corner + 1):
            a = math.radians(270 + (90 / steps_per_corner) * i)
            top_pts.append((cx + corner_radius * math.cos(a), cy + corner_radius * math.sin(a), hz))

        bottom_pts = [(x, y, -hz) for x, y, z in top_pts]

        glColor3f(0.95, 0.95, 1.0)
        glBegin(GL_POLYGON)
        for p in top_pts:
            glVertex3f(*p)
        glEnd()

        glBegin(GL_POLYGON)
        for p in reversed(bottom_pts):
            glVertex3f(*p)
        glEnd()

        glBegin(GL_QUADS)
        for i in range(len(top_pts)):
            t1 = top_pts[i]
            t2 = top_pts[(i + 1) % len(top_pts)]
            b2 = bottom_pts[(i + 1) % len(bottom_pts)]
            b1 = bottom_pts[i]
            glVertex3f(*t1)
            glVertex3f(*t2)
            glVertex3f(*b2)
            glVertex3f(*b1)
        glEnd()

    def mousePressEvent(self, event):
        # Record mouse position when click begins, for drag rotation
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        # Update rotation based on drag distance and refresh view
        dx = event.pos().x() - self.last_pos.x()
        dy = event.pos().y() - self.last_pos.y()
        self.rotation[1] += dx * 0.5
        self.rotation[0] += dy * 0.5
        self.last_pos = event.pos()
        self.update()

    def wheelEvent(self, event):
        # Zoom control by mouse wheel
        delta = event.angleDelta().y() / 8.0  # degrees
        if delta == 0:
            return
        # Adjust by sensitivity (smaller increments)
        self.camera_dist -= delta * 0.1
        self.camera_dist = max(20.0, min(500.0, self.camera_dist))
        self.update()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, mode="windowed", card_type="CR80"):
        # Main window containing the GL widget
        super().__init__()
        self.setWindowTitle("3D Preview")
        self.setGeometry(100, 100, 1000, 600)  # Wider for sidebar

        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Create sidebar
        self.sidebar = QtWidgets.QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #ccc;")
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)

        # Card type selector in sidebar
        card_label = QtWidgets.QLabel("Card Type:")
        sidebar_layout.addWidget(card_label)

        self.card_combo = QtWidgets.QComboBox()
        self.card_combo.addItems(["CR80", "CR79", "CR100", "CR90", "CR50"])
        self.card_combo.setCurrentText(card_type)
        self.card_combo.currentTextChanged.connect(self.on_card_type_changed)
        sidebar_layout.addWidget(self.card_combo)

        # Add stretch to push items to top
        sidebar_layout.addStretch()

        # Add sidebar to main layout
        main_layout.addWidget(self.sidebar)

        # Create GL widget
        self.gl_widget = GLWidget(card_type)
        main_layout.addWidget(self.gl_widget)

        # Set window mode
        if mode == "fullscreen":
            self.showFullScreen()
        elif mode == "borderless":
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            self.show()
        else:
            self.show()

    def on_card_type_changed(self, new_type):
        # Update the card type in GL widget
        self.gl_widget.set_card_type(new_type)

    def keyPressEvent(self, event):
        # Handle ESC key to close the program
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    # Standard Qt application bootstrap
    app = QtWidgets.QApplication([])
    dialog = StartMenuDialog()
    if dialog.exec() == QtWidgets.QDialog.Accepted:
        mode = dialog.get_selected_mode()
        card_type = dialog.get_selected_card_type()
        window = MainWindow(mode, card_type)
        app.exec()
    else:
        app.quit()  