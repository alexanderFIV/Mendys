from PySide6 import QtWidgets, QtCore
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *


class GLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rotation = [0, 0, 0]

    def initializeGL(self):
        glClearColor(0.5, 0.5, 0.5, 1.0)
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -100.0)
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)

        self.draw_cube()

    def draw_cube(self):
        vertices = [
            [42.8, 27, 0.38], [42.8, 27, -0.38], [42.8, -27, -0.38], [42.8, -27, 0.38],
            [-42.8, 27, 0.38], [-42.8, 27, -0.38], [-42.8, -27, -0.38], [-42.8, -27, 0.38]
        ]
        faces = [
            [0, 1, 2, 3], [3, 2, 6, 7], [7, 6, 5, 4],
            [4, 5, 1, 0], [5, 6, 2, 1], [7, 4, 0, 3]
        ]
        glBegin(GL_QUADS)
        for face in faces:
            glColor3f(1, 1, 1)  
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()

    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.pos().x() - self.last_pos.x()
        dy = event.pos().y() - self.last_pos.y()
        self.rotation[1] += dx * 0.5
        self.rotation[0] += dy * 0.5
        self.last_pos = event.pos()
        self.update()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Preview")
        self.setGeometry(100, 100, 800, 600)
        self.gl_widget = GLWidget()
        self.setCentralWidget(self.gl_widget)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()  
