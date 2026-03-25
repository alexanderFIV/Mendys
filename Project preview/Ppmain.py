import math
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from Ppcolorpallete import ColorSwatch, create_color_palette


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


class TextObject:
    def __init__(self, text="NEW TEXT", side="front", color="#000000"):
        self.text = text
        self.side = side # "front" or "back"
        self.pos = [0.0, 0.0]
        self.color = QtGui.QColor(color)
        self.font = QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold)
        self.screen_rect = QtCore.QRect()

class GLWidget(QOpenGLWidget):
    def __init__(self, card_type="CR80", parent=None):
        # Initialize the OpenGL widget and default rotation angles
        super().__init__(parent)
        self.rotation = [20, -30, 0] # Initial attractive angle
        self.camera_dist = 140.0 
        self.set_card_dimensions(card_type)
        self.quadric = None
        
        # Default card color
        self.card_color = QtGui.QColor("#ffffff")
        
        # Multi-text support
        self.text_objects = [TextObject("MENDY'S PREMIUM", "front", "#2c3e50")]
        self.dragging_obj = None

        # Surface/Material system
        self.card_material = "Matte" # Matte, Glossy, Metallic, Scratched, Grainy, Frosted
        self.textures = {} 
        self.custom_front_tex = None
        self.custom_back_tex = None

    def set_card_dimensions(self, card_type):
        # Precise industry specifications (in mm)
        dimensions = {
            "CR80": (85.60, 53.98, 0.76),   # Standard Credit Card size
            "CR79": (83.90, 52.10, 0.254),  # Adhesive-back card size
            "CR100": (98.50, 67.00, 0.76),  # "Military" or Oversized size
            "CR90": (92.00, 60.00, 0.76),   # Driver's License size (approx)
            "CR50": (43.66, 28.58, 0.76)    # Luggage tag / Key tag size
        }
        self.card_w, self.card_h, self.card_t = dimensions.get(card_type, (85.6, 53.98, 0.76))
        # Industry standard corner radius is roughly 3.18mm
        self.corner_radius = 3.18 
        self.update()

    def set_card_type(self, card_type):
        self.set_card_dimensions(card_type)

    def add_text_object(self, text="NEW TEXT", side="front", color="#000000"):
        obj = TextObject(text, side, color)
        self.text_objects.append(obj)
        self.update()
        return obj

    def set_card_color(self, hex_color):
        self.card_color = QtGui.QColor(hex_color)
        self.update()

    def set_card_material(self, material_name):
        self.card_material = material_name
        self.update()

    def set_custom_texture(self, image_path, side):
        self.makeCurrent() # Ensure context is active for texture gen
        img = QtGui.QImage(image_path)
        if img.isNull():
            return False
            
        tid = self._load_qimage_as_texture(img)
        if side in ["front", "both"]:
            if self.custom_front_tex: 
                glDeleteTextures(1, [int(self.custom_front_tex)])
            self.custom_front_tex = tid
        if side in ["back", "both"]:
            if self.custom_back_tex: 
                glDeleteTextures(1, [int(self.custom_back_tex)])
            self.custom_back_tex = tid
            
        self.update()
        return True

    def initializeGL(self):
        glClearColor(0.12, 0.12, 0.14, 1.0) 
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        
        # Enhanced Shading/Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glShadeModel(GL_SMOOTH)
        
        # Global Ambient light for "shades"
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        
        glLightfv(GL_LIGHT0, GL_POSITION, [100.0, 100.0, 200.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.7, 0.7, 0.7, 1.0])
        
        # Support for surface textures
        glEnable(GL_TEXTURE_2D)
        self._init_procedural_textures()
        glDisable(GL_TEXTURE_2D) # Start clean
        
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        self.quadric = gluNewQuadric()

    def _init_procedural_textures(self):
        # High quality noise for Frosted/Grainy
        for name in ["Grainy", "Frosted"]:
            img = QtGui.QImage(128, 128, QtGui.QImage.Format_ARGB32)
            alpha = 255 if name == "Grainy" else 150 # Frosted is semi-translucent
            for y in range(128):
                for x in range(128):
                    v = int(220 + 35 * (math.sin(x*0.5)*math.cos(y*0.5)))
                    img.setPixel(x, y, QtGui.qRgba(v, v, v, alpha))
            self.textures[name] = self._load_qimage_as_texture(img)

        # Scratched Pattern (Fine hairline scratches)
        scratched_img = QtGui.QImage(256, 256, QtGui.QImage.Format_ARGB32)
        scratched_img.fill(QtGui.QColor(255, 255, 255, 0))
        p = QtGui.QPainter(scratched_img)
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 60), 1))
        for i in range(120): # Increased scratch density
            x = (i * 37) % 256
            y = (i * 51) % 256
            p.drawLine(x, y, x + (i * 13 % 25), y + (i * 7 % 11))
        p.end()
        self.textures["Scratched"] = self._load_qimage_as_texture(scratched_img)

    def _load_qimage_as_texture(self, qimage):
        img = qimage.convertToFormat(QtGui.QImage.Format_RGBA8888).mirrored()
        tid = glGenTextures(1)
        if hasattr(tid, '__len__'):
            tid = tid[0]
            
        glBindTexture(GL_TEXTURE_2D, tid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # Directly pass the QImage bits
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width(), img.height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, img.constBits())
        return tid

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h if h != 0 else 1, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_dist)
        
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)

        self.draw_card()
        
    def paintEvent(self, event):
        # Override paintEvent to use QPainter on top of OpenGL
        self.makeCurrent()
        self.paintGL()
        
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        
        # Calculate projection matrices
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        hz = self.card_t / 2.0
        
        for obj in self.text_objects:
            lx, ly = obj.pos
            # Local Z depends on side
            lz = (hz + 0.1) if obj.side == "front" else (-hz - 0.1)
            
            # Check if current face is visible using dot product approach (normal vs viewer)
            is_face_visible = (modelview[2][2] > 0) if obj.side == "front" else (modelview[2][2] < 0)
            
            if is_face_visible:
                try:
                    # Project local points into screen space to build a 2D transform basis
                    s0 = gluProject(lx, ly, lz, modelview, projection, viewport)
                    
                    # Compute surface X-axis vector: project local X step and subtract origin
                    lx_step = 1.0 if obj.side == "front" else -1.0 # Reverse X on back for readability
                    sx = gluProject(lx + lx_step, ly, lz, modelview, projection, viewport)
                    
                    # Compute surface Y-axis vector: project local -Y to ensure upright text
                    sy = gluProject(lx, ly - 1.0, lz, modelview, projection, viewport)
                    
                    # Convert GL coordinates (bottom-up) to Screen coordinates (top-down)
                    s0y = viewport[3] - s0[1]
                    sxy = viewport[3] - sx[1]
                    syy = viewport[3] - sy[1]
                    
                    # Calculate basis vectors in screen space
                    vx = [sx[0] - s0[0], sxy - s0y]
                    vy = [sy[0] - s0[0], syy - s0y]
                    
                    if 0 <= s0[2] <= 1: # Only draw if in front of camera
                        painter.save()
                        # Map text local space to these 3D basis vectors using QTransform
                        transform = QtGui.QTransform(vx[0], vx[1], vy[0], vy[1], s0[0], s0y)
                        painter.setTransform(transform)
                        
                        painter.setFont(obj.font)
                        painter.setPen(obj.color)
                        
                        metrics = painter.fontMetrics()
                        rect = metrics.boundingRect(obj.text)
                        
                        painter.drawText(-rect.width() / 2, rect.height() / 4, obj.text)
                        
                        # Store screen area for mouse interaction
                        # We map the local rect back to screen coords
                        obj.screen_rect = transform.mapRect(QtCore.QRectF(
                            -rect.width()/2, -rect.height()/4, rect.width(), rect.height()
                        )).toRect()
                        
                        painter.restore()
                    else:
                        obj.screen_rect = QtCore.QRect()
                except:
                    obj.screen_rect = QtCore.QRect()
            else:
                obj.screen_rect = QtCore.QRect()
            
        painter.end()

    def draw_card(self):
        corner_radius = self.corner_radius
        card_w, card_h, card_t = self.card_w, self.card_h, self.card_t
        hx, hy, hz = card_w / 2.0, card_h / 2.0, card_t / 2.0
        steps_per_corner = 32

        top_pts = []
        # Generate arc points using trigonometry for rounded card corners
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

        # Apply Material Properties based on IRL specs
        if self.card_material == "Glossy":
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 128.0) # Maximum polish
        elif self.card_material == "Metallic":
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 100.0) 
        elif self.card_material == "Matte":
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 5.0) # Subdued
        else: # Scratched / Grainy / Frosted
            glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.4, 0.4, 0.4, 1.0])
            glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 20.0)

        # Handle Transparency for Frosted
        if self.card_material == "Frosted":
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_BLEND)

        # Bind texture if applicable (Prefer custom image over procedural pattern)
        def bind_face_texture(side):
            tex = self.custom_front_tex if side == "front" else self.custom_back_tex
            if tex:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, tex)
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                return True
            elif self.card_material in self.textures:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, self.textures[self.card_material])
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
                return True
            glDisable(GL_TEXTURE_2D)
            return False

        c = self.card_color
        # For Frosted, we use the alpha from the texture mostly, but can add it here too
        alpha = 0.8 if self.card_material == "Frosted" else 1.0
        glColor4f(c.redF(), c.greenF(), c.blueF(), alpha)
        
        # Front Face
        bind_face_texture("front")
        glBegin(GL_POLYGON)
        glNormal3f(0, 0, 1)
        for p in top_pts:
            glTexCoord2f(p[0]/card_w + 0.5, p[1]/card_h + 0.5)
            glVertex3f(*p)
        glEnd()

        # Back Face
        bind_face_texture("back")
        glBegin(GL_POLYGON)
        glNormal3f(0, 0, -1)
        for p in reversed(bottom_pts):
            glTexCoord2f(p[0]/card_w + 0.5, p[1]/card_h + 0.5)
            glVertex3f(*p)
        glEnd()

        # Side Edges (usually no texture or stretched texture)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUAD_STRIP)
        for i in range(len(top_pts) + 1):
            idx = i % len(top_pts)
            p_top = top_pts[idx]
            p_bot = bottom_pts[idx]
            norm = [p_top[0], p_top[1], 0]
            mag = math.sqrt(norm[0]**2 + norm[1]**2)
            if mag > 0:
                glNormal3f(norm[0]/mag, norm[1]/mag, 0)
            glVertex3f(*p_top)
            glVertex3f(*p_bot)
        glEnd()

    def mousePressEvent(self, event):
        pos = event.pos()
        self.dragging_obj = None
        # Check from top to bottom (reverse list) for matches
        for obj in reversed(self.text_objects):
            if obj.screen_rect.contains(pos):
                self.dragging_obj = obj
                break
        self.last_pos = pos

    def mouseReleaseEvent(self, event):
        self.dragging_obj = None

    def mouseMoveEvent(self, event):
        pos = event.pos()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        
        # Hover feedback
        hovering = False
        for obj in self.text_objects:
            if obj.screen_rect.contains(pos):
                hovering = True
                break
        
        if hovering:
            self.setCursor(QtCore.Qt.SizeAllCursor)
        else:
            self.unsetCursor()

        if self.dragging_obj:
            # Scale mouse delta (px) to local 3D surface units based on distance
            scale = self.camera_dist / 500.0
            # Reverse X movement on back face to match viewer perspective
            side_scale = 1.0 if self.dragging_obj.side == "front" else -1.0
            self.dragging_obj.pos[0] += dx * scale * side_scale
            self.dragging_obj.pos[1] -= dy * scale # Mouse-down is positive screen, negative local-Y
            
            # Constraints
            hw, hh = self.card_w / 2.0, self.card_h / 2.0
            self.dragging_obj.pos[0] = max(-hw, min(hw, self.dragging_obj.pos[0]))
            self.dragging_obj.pos[1] = max(-hh, min(hh, self.dragging_obj.pos[1]))
        else:
            self.rotation[1] += dx * 0.5
            self.rotation[0] += dy * 0.5
            
        self.last_pos = pos
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 8.0
        if delta == 0: return
        self.camera_dist -= delta * 0.2
        self.camera_dist = max(20.0, min(500.0, self.camera_dist))
        self.update()

class TextObjectWidget(QtWidgets.QWidget):
    def __init__(self, text_obj, gl_widget, parent=None):
        super().__init__(parent)
        self.text_obj = text_obj
        self.gl_widget = gl_widget
        
        self.setStyleSheet("""
            QWidget { background-color: #27272a; border-radius: 6px; padding: 5px; }
            QLineEdit { background-color: #18181b; border: 1px solid #3f3f46; color: #e0e0e0; font-size: 11px; }
            QPushButton { background-color: #3f3f46; border: none; color: white; padding: 3px; border-radius: 3px; font-size: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #52525b; }
            QComboBox { background-color: #18181b; border: 1px solid #3f3f46; color: #e0e0e0; font-size: 10px; }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Row 1: Text Input
        self.edit = QtWidgets.QLineEdit(text_obj.text)
        self.edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.edit)
        
        # Row 2: Controls
        ctrl_layout = QtWidgets.QHBoxLayout()
        
        self.side_combo = QtWidgets.QComboBox()
        self.side_combo.addItems(["front", "back"])
        self.side_combo.setCurrentText(text_obj.side)
        self.side_combo.currentTextChanged.connect(self.on_side_changed)
        ctrl_layout.addWidget(self.side_combo)
        
        self.color_btn = QtWidgets.QPushButton("Color")
        self.color_btn.clicked.connect(self.on_color_requested)
        ctrl_layout.addWidget(self.color_btn)
        
        self.font_btn = QtWidgets.QPushButton("Font")
        self.font_btn.clicked.connect(self.on_font_requested)
        ctrl_layout.addWidget(self.font_btn)
        
        self.del_btn = QtWidgets.QPushButton("X")
        self.del_btn.setFixedWidth(20)
        self.del_btn.setStyleSheet("background-color: #7f1d1d;")
        self.del_btn.clicked.connect(self.on_delete)
        ctrl_layout.addWidget(self.del_btn)
        
        layout.addLayout(ctrl_layout)

    def on_text_changed(self, text):
        self.text_obj.text = text
        self.gl_widget.update()

    def on_side_changed(self, side):
        self.text_obj.side = side
        self.gl_widget.update()

    def on_color_requested(self):
        color = QtWidgets.QColorDialog.getColor(initial=self.text_obj.color, parent=self)
        if color.isValid():
            self.text_obj.color = color
            self.gl_widget.update()

    def on_font_requested(self):
        font, ok = QtWidgets.QFontDialog.getFont(self.text_obj.font, self)
        if ok:
            self.text_obj.font = font
            self.gl_widget.update()

    def on_delete(self):
        self.gl_widget.text_objects.remove(self.text_obj)
        self.gl_widget.update()
        self.setParent(None)
        self.deleteLater()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, mode="windowed", card_type="CR80"):
        super().__init__()
        self.setWindowTitle("Mendy's 3D Card Preview")
        self.setGeometry(100, 100, 1100, 700)

        # Apply dark theme stylesheet to the whole window
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e21; }
            QLabel { color: #e0e0e0; font-size: 13px; font-weight: bold; margin-top: 10px; }
            QComboBox { 
                background-color: #2d2d30; color: #e0e0e0; border: 1px solid #3f3f46; 
                padding: 5px; border-radius: 4px; 
            }
            QLineEdit { 
                background-color: #2d2d30; color: #e0e0e0; border: 1px solid #3f3f46; 
                padding: 5px; border-radius: 4px; 
            }
            QPushButton#ActionBtn {
                background-color: #3f3f46; color: white; border: none; padding: 8px; 
                border-radius: 4px; font-weight: bold;
            }
            QPushButton#ActionBtn:hover { background-color: #52525b; }
        """)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # GL Widget - Init early so we can reference it
        self.gl_widget = GLWidget(card_type)

        # Sidebar
        self.sidebar = QtWidgets.QWidget()
        self.sidebar.setFixedWidth(280) # Slightly wider for multiple objects
        self.sidebar.setStyleSheet("background-color: #18181b; border-right: 1px solid #27272a;")
        sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(10)

        title = QtWidgets.QLabel("CARD CONFIGURATION")
        title.setStyleSheet("font-size: 16px; color: #ffffff; margin-bottom: 5px;")
        sidebar_layout.addWidget(title)

        # Card Type Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Standard Dimensions"))
        self.card_combo = QtWidgets.QComboBox()
        self.card_combo.addItems(["CR80", "CR79", "CR100", "CR90", "CR50"])
        self.card_combo.setCurrentText(card_type)
        self.card_combo.currentTextChanged.connect(self.on_card_type_changed)
        sidebar_layout.addWidget(self.card_combo)

        # Surface Type Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Surface Finish / Material"))
        self.material_combo = QtWidgets.QComboBox()
        self.material_combo.addItems(["Matte", "Glossy", "Metallic", "Scratched", "Grainy", "Frosted"])
        self.material_combo.currentTextChanged.connect(self.on_material_changed)
        sidebar_layout.addWidget(self.material_combo)

        # Card Color Palette
        sidebar_layout.addWidget(QtWidgets.QLabel("Card Surface Color"))
        
        # 7 Basic colors for card surface
        card_colors = ["#ffffff", "#2c3e50", "#d4af37", "#2980b9", "#c0392b", "#27ae60", "#8e44ad"]
        
        # Build palette using helper from ColorPalette.py
        card_palette_layout = create_color_palette(
            colors=card_colors, 
            callback=self.on_card_color_changed, 
            custom_callback=self.on_custom_card_color_requested,
            gradient_style="qlineargradient(stop:0 red, stop:1 blue)"
        )
        sidebar_layout.addLayout(card_palette_layout)

        # Custom Image Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Surface Image (Custom)"))
        self.import_btn = QtWidgets.QPushButton("Import Image...")
        self.import_btn.setObjectName("ActionBtn")
        self.import_btn.clicked.connect(self.on_import_image_clicked)
        sidebar_layout.addWidget(self.import_btn)

        # Multiple Text Objects Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Custom Text Layers"))
        
        add_text_layout = QtWidgets.QHBoxLayout()
        self.add_text_btn = QtWidgets.QPushButton("+ Add New Text Layer")
        self.add_text_btn.setObjectName("ActionBtn")
        self.add_text_btn.clicked.connect(self.on_add_text_clicked)
        add_text_layout.addWidget(self.add_text_btn)
        sidebar_layout.addLayout(add_text_layout)

        # Scroll area for text objects
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.text_list_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.text_list_layout.setContentsMargins(0, 0, 0, 0)
        self.text_list_layout.setSpacing(8)
        self.text_list_layout.addStretch()
        self.scroll.setWidget(self.scroll_content)
        sidebar_layout.addWidget(self.scroll)

        # Initialize existing text objects in UI
        for obj in self.gl_widget.text_objects:
            self.add_text_widget(obj)

        sidebar_layout.addStretch()

        # Help / Exit
        exit_btn = QtWidgets.QPushButton("Exit Application (ESC)")
        exit_btn.setObjectName("ActionBtn")
        exit_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(exit_btn)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.gl_widget)

        if mode == "fullscreen":
            self.showFullScreen()
        elif mode == "borderless":
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            self.show()
        else:
            self.show()

    def on_card_type_changed(self, new_type):
        self.gl_widget.set_card_type(new_type)

    def on_material_changed(self, new_mat):
        self.gl_widget.set_card_material(new_mat)

    def on_card_color_changed(self, color_hex):
        self.gl_widget.set_card_color(color_hex)

    def on_import_image_clicked(self):
        # 1. Open File Dialog
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Card Surface Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        
        if not file_path:
            return

        # 2. Ask user which side(s) to apply to
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Target Side")
        msg.setText("Where would you like to apply this image?")
        btn_front = msg.addButton("Front Side", QtWidgets.QMessageBox.ActionRole)
        btn_back = msg.addButton("Back Side", QtWidgets.QMessageBox.ActionRole)
        btn_both = msg.addButton("Both Sides", QtWidgets.QMessageBox.ActionRole)
        msg.addButton(QtWidgets.QMessageBox.Cancel)
        
        msg.exec()
        
        clicked_btn = msg.clickedButton()
        side = None
        if clicked_btn == btn_front: side = "front"
        elif clicked_btn == btn_back: side = "back"
        elif clicked_btn == btn_both: side = "both"
        
        if side:
            self.gl_widget.set_custom_texture(file_path, side)

    def on_custom_card_color_requested(self):
        # Open standard color dialog with current color as initial
        color = QtWidgets.QColorDialog.getColor(
            initial=self.gl_widget.card_color, 
            parent=self, 
            title="Select Card Color"
        )
        if color.isValid():
            self.on_card_color_changed(color.name())

    def on_add_text_clicked(self):
        # Create a new text object in GLWidget and a corresponding widget in sidebar
        new_obj = self.gl_widget.add_text_object("NEW TEXT", "front")
        self.add_text_widget(new_obj)

    def add_text_widget(self, text_obj):
        widget = TextObjectWidget(text_obj, self.gl_widget)
        # Insert before the stretch at the bottom
        self.text_list_layout.insertWidget(self.text_list_layout.count() - 1, widget)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    print("Starting App...")
    app = QtWidgets.QApplication([])
    dialog = StartMenuDialog()
    if dialog.exec() == QtWidgets.QDialog.Accepted:
        mode = dialog.get_selected_mode()
        card_type = dialog.get_selected_card_type()
        window = MainWindow(mode, card_type)
        app.exec()
    else:
        app.quit()
