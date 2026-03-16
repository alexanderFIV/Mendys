import math
from PySide6 import QtWidgets, QtCore
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        # Initialize the OpenGL widget and default rotation angles
        super().__init__(parent)
        self.rotation = [0, 0, 0]
        self.camera_dist = 100.0  # camera distance (bird-eye zoom)
        self.corner_radius = 3.0  # mm, requested rounded corner radius
        self.quadric = None

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
        gluPerspective(45, w / h if h != 0 else 1, 0.1, 100.0)
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
        # Draw a CR80 PVC card (85.6x53.98 mm, 0.76 mm thick) with 3 mm rounded corners
        corner_radius = 3.0
        card_w, card_h, card_t = 85.6, 53.98, 0.76
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
        self.camera_dist = max(20.0, min(300.0, self.camera_dist))
        self.update()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        # Main window containing the GL widget
        super().__init__()
        self.setWindowTitle("3D Preview")
        self.setGeometry(100, 100, 800, 600)
        self.gl_widget = GLWidget()
        self.setCentralWidget(self.gl_widget)

if __name__ == "__main__":
    # Standard Qt application bootstrap
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()  