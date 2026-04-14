import math
import random
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from Ppcolorpalette import ColorSwatch, create_color_palette


class StartMenuDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("3D Preview - Start Menu")
        self.setModal(True)
        self.resize(300, 320)
        self.setStyleSheet("""
            QDialog { background-color: #09090b; color: #f4f4f5; }
            QLabel { color: #f4f4f5; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-top: 10px; }
            QRadioButton { color: #fafafa; font-size: 12px; padding: 5px; }
            QComboBox { background-color: #18181b; color: #fafafa; border: 1px solid #27272a; padding: 6px; border-radius: 4px; }
            QPushButton { background-color: #27272a; color: white; border: 1px solid #3f3f46; padding: 10px; border-radius: 6px; font-weight: 600; }
            QPushButton:hover { background-color: #3f3f46; }
        """)

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

        self.emboss_label = QtWidgets.QLabel("Embossing Quality:")
        layout.addWidget(self.emboss_label)

        self.emboss_combo = QtWidgets.QComboBox()
        self.emboss_combo.addItems(["Normal", "Realistic", "Super Realistic"])
        self.emboss_combo.setCurrentText("Realistic")
        layout.addWidget(self.emboss_combo)

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

    def get_selected_emboss_quality(self):
        return self.emboss_combo.currentText()


class TextObject:
    def __init__(self, text="NEW TEXT", side="front", color="#000000"):
        self.text = self.validate_text(text)
        self.side = side # "front" or "back"
        self.pos = [0.0, 0.0]
        self.color = QtGui.QColor(color)
        self.font = QtGui.QFont("Segoe UI", 12, QtGui.QFont.Bold)
        self.screen_rect = QtCore.QRect()
        # New properties for embossing and constraints
        self.style = "Standard" # "Standard", "Embossed"
        self.is_physical = False # If true, raised on front, into card on back
        self.border_enabled = False
        self.width_3d = 10.0 # Approximate width in local units
        self.height_3d = 5.0 # Approximate height in local units
        self.tex_3d = None # For Super Realistic 3D extrusion

    def validate_text(self, text):
        # Only allow Latin text and common punctuation
        return "".join([c for c in text if c.isascii()])

    def show_emboss_effect(self):
        return self.is_physical or self.style == "Embossed"
    
    def get_hit_rect(self):
        # Return a tight hit box in local mm
        hw = self.width_3d / 2
        hh = self.height_3d / 2
        return QtCore.QRectF(-hw, -hh, self.width_3d, self.height_3d)

class GraphicObject:
    def __init__(self, image, side="front", obj_type="custom"):
        self.image = image
        self.pos = [0, 0] # mm
        self.side = side
        self.obj_type = obj_type
        # Default sizes in mm
        if obj_type == "qr": self.size_mm = [20, 20]
        elif obj_type == "barcode": self.size_mm = [35, 15]
        else: self.size_mm = [25, 25] # Default for custom
        
        self.width_3d = self.size_mm[0]
        self.height_3d = self.size_mm[1]

class GLWidget(QOpenGLWidget):
    def __init__(self, card_type="CR80", emboss_quality="Realistic", parent=None):
        # Initialize the OpenGL widget and default rotation angles
        super().__init__(parent)
        self.rotation = [20, -30, 0] # Initial attractive angle
        self.camera_dist = 140.0 
        self.set_card_dimensions(card_type)
        self.emboss_quality = emboss_quality
        self.quadric = None
        
        # Default card color
        self.card_color = QtGui.QColor("#ffffff")
        
        # Multi-text support
        self.text_objects = [TextObject("MENDY'S PREMIUM", "front", "#2c3e50")]
        self.selected_obj = None
        self.is_dragging = False

        # Surface/Material system
        self.card_material = "Matte" # Matte, Glossy, Metallic, Scratched, Grainy, Frosted
        self.textures = {} 
        self.custom_front_img = None
        self.custom_back_img = None

    def set_card_dimensions(self, card_type):
        dimensions = {
            "CR80": (85.60, 53.98, 0.76),   # Standard Credit Card size
            "CR79": (83.90, 52.10, 0.254),  # Adhesive-back card size
            "CR100": (98.50, 67.00, 0.76),  # "Military" or Oversized size
            "CR90": (92.00, 60.00, 0.76),   # Driver's License size (approx)
            "CR50": (43.66, 28.58, 0.76)   # Luggage tag / Key tag size
        }
        self.card_w, self.card_h, self.card_t = dimensions.get(card_type, (85.6, 53.98, 0.76))
        # Chip support
        self.chip_type = "None" # "None", "Gold 6-Pad", "Gold 8-Pad", "Silver 6-Pad", "Silver 8-Pad"
        # ISO 7816-2 Standard Position:
        # Left edge starts at 10.25mm. Top edge starts at 19.23mm.
        # Center GL coords for 13x12mm module:
        self.chip_pos = [-27.74, 3.10] 
        
        # Magstripe support
        self.magstripe_type = "None" # "None", "HiCo (Black)", "LoCo (Brown)"
        
        # Momentum / Inertia System for Pro feel
        self.rot_velocity = [0.0, 0.0]
        self.inertia_timer = QtCore.QTimer()
        self.inertia_timer.timeout.connect(self.apply_inertia)
        self.inertia_timer.setInterval(16) # ~60fps smooth momentum
        
        # Animation System for View Presets
        self.anim_timer = QtCore.QTimer()
        self.anim_timer.timeout.connect(self.update_animation)
        self.anim_timer.setInterval(16)
        self.target_rotation = [0.0, 0.0]
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.corner_radius = 3.18 
        
        self.text_objects = []
        self.graphic_objects = []
        self.selected_obj = None
        self.is_dragging = False
        
        self._refresh_textures = True
        self.update()

    def update_face_textures(self):
        # Fusing all design elements into 1024x640 textures for each side
        # This makes text part of the actual material (reacts to GL light)
        self.makeCurrent()
        TW, TH = 1024, 640
        
        for side in ["front", "back"]:
            img = QtGui.QImage(TW, TH, QtGui.QImage.Format_ARGB32)
            img.fill(self.card_color)
            
            p = QtGui.QPainter(img)
            p.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
            
            # 1. Background Image (Custom Import)
            bg_img = self.custom_front_img if side == "front" else self.custom_back_img
            if bg_img:
                # Scale background image to fit the 1024x640 texture
                scaled_bg = bg_img.scaled(TW, TH, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
                # Center-crop or just draw it
                p.drawImage(0, 0, scaled_bg)
            
            # 2. Render Chip (Only on front)
            if side == "front" and self.chip_type != "None":
                self._draw_chip(p, TW, TH)
            
            # 3. Render Magstripe (Only on back)
            if side == "back" and self.magstripe_type != "None":
                self._draw_magstripe(p, TW, TH)

            # 4. Render Text into texture
            # Map local mm coord [-hw, hw] to texture pixel [0, TW]
            hw, hh = self.card_w / 2.0, self.card_h / 2.0
            def mm_to_px(lx, ly):
                px = ((lx + hw) / self.card_w) * TW
                py = (1.0 - (ly + hh) / self.card_h) * TH
                return px, py

            for obj in self.text_objects:
                if not obj.is_physical and obj.side != side:
                    continue
                
                lx, ly = obj.pos
                px, py = mm_to_px(lx, ly)
                
                # Setup font for 1024px width
                # 12pt is roughly 1/8th of an inch. We'll scale font by (TW / card_w)
                scale_f = TW / self.card_w
                font = QtGui.QFont(obj.font)
                font.setPointSizeF(obj.font.pointSizeF() * scale_f * 0.35) # Adjusted for real feel
                p.setFont(font)
                
                metrics = p.fontMetrics()
                rect = metrics.boundingRect(obj.text)
                tx, ty = px - rect.width()/2, py + rect.height()/4

                # Realistic Effects (Shading/Highlights baked into texture)
                if obj.show_emboss_effect():
                    # Check quality levels
                    if self.emboss_quality == "Normal":
                        p.setPen(QtGui.QColor(0, 0, 0, 100))
                        p.drawText(tx + 1, ty + 1, obj.text)
                    elif self.emboss_quality == "Realistic":
                        if side == "front":
                            p.setPen(QtGui.QColor(255, 255, 255, 180))
                            p.drawText(tx - 1.5, ty - 1.5, obj.text)
                            p.setPen(QtGui.QColor(0, 0, 0, 160))
                            p.drawText(tx + 1.5, ty + 1.5, obj.text)
                        else: # Indented for physical back
                            p.setPen(QtGui.QColor(0, 0, 0, 140))
                            p.drawText(tx - 1, ty - 1, obj.text)
                            p.setPen(QtGui.QColor(255, 255, 255, 110))
                            p.drawText(tx + 1, ty + 1, obj.text)
                    elif self.emboss_quality == "Super Realistic":
                        # For super realistic, we add a subtle glow/shadow even on the face
                        # BUT the main effect is 3D geometry in draw_card
                        pass
                
                if obj.border_enabled:
                    path = QtGui.QPainterPath()
                    path.addText(tx, ty, font, obj.text)
                    p.strokePath(path, QtGui.QPen(QtGui.QColor(0,0,0, 180), 4))

                final_color = QtGui.QColor(obj.color)
                if obj.is_physical and side == "back":
                    final_color = final_color.darker(130)
                
                p.setPen(final_color)
                # For Super Realistic 3D, we also generate a dedicated texture of JUST the text
                if self.emboss_quality == "Super Realistic" and obj.show_emboss_effect() and side == "front":
                    t_img = QtGui.QImage(512, 128, QtGui.QImage.Format_ARGB32)
                    t_img.fill(QtCore.Qt.transparent)
                    tp = QtGui.QPainter(t_img)
                    tp.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
                    t_font = QtGui.QFont(font)
                    t_font.setPointSizeF(obj.font.pointSizeF() * (512 / self.card_w) * 0.35)
                    tp.setFont(t_font)
                    tm = tp.fontMetrics()
                    tr = tm.boundingRect(obj.text)
                    # For Super Realistic extrusion, we use a WHITE mask texture
                    # We will apply the color logic in paintGL
                    tp.setPen(QtCore.Qt.white)
                    tp.drawText(256 - tr.width()/2, 64 + tr.height()/4, obj.text)
                    tp.end()
                    if obj.tex_3d: glDeleteTextures(1, [int(obj.tex_3d)])
                    obj.tex_3d = self._load_qimage_as_texture(t_img)
                    obj.tex_w_ratio = tr.width() / 512
                    obj.tex_h_ratio = tr.height() / 128

                p.drawText(tx, ty, obj.text)
                
                # Store hit box for selection
                obj.width_3d = rect.width() / scale_f
                obj.height_3d = rect.height() / scale_f

                # Selection Highlight (only on active editing side)
                if obj == self.selected_obj:
                    p.setPen(QtGui.QPen(QtGui.QColor(59, 130, 246, 200), 4, QtCore.Qt.DashLine))
                    p.drawRect(tx - 4, ty - rect.height() + 4, rect.width() + 8, rect.height() + 4)

            # 5. Render Graphics (QR, Barcode, Custom Images)
            for obj in self.graphic_objects:
                if obj.side != side: continue
                
                # Convert mm to px
                gw, gh = obj.size_mm[0] * scale_x, obj.size_mm[1] * scale_y
                gx = (obj.pos[0] + self.card_w/2) * scale_x - gw/2
                gy = (self.card_h/2 - obj.pos[1]) * scale_y - gh/2
                
                p.drawImage(QtCore.QRectF(gx, gy, gw, gh), obj.image)
                
                # Highlight if selected
                if obj == self.selected_obj:
                    p.setPen(QtGui.QPen(QtGui.QColor(59, 130, 246, 200), 4, QtCore.Qt.DashLine))
                    p.drawRect(gx - 4, gy - 4, gw + 8, gh + 8)

            p.end()
            
            tid = self._load_qimage_as_texture(img)
            if side == "front":
                if hasattr(self, 'fused_front_tex') and self.fused_front_tex: glDeleteTextures(1, [int(self.fused_front_tex)])
                self.fused_front_tex = tid
            else:
                if hasattr(self, 'fused_back_tex') and self.fused_back_tex: glDeleteTextures(1, [int(self.fused_back_tex)])
                self.fused_back_tex = tid
        
        self._refresh_textures = False

    def _draw_chip(self, p, TW, TH):
        # Position mapping
        hw, hh = self.card_w / 2.0, self.card_h / 2.0
        scale_x = TW / self.card_w
        scale_y = TH / self.card_h

        # CONTACT CHIPS (Visible Pad)
        if "(Contact" in self.chip_type:
            # Common module size (encompassing ISO-7816-2 pads)
            cw_mm, ch_mm = 13.0, 12.0
            cw, ch = cw_mm * scale_x, ch_mm * scale_y
            lx, ly = self.chip_pos
            
            # Map GL center to texture pixels
            px = ((lx - cw_mm/2 + hw) / self.card_w) * TW
            py = (1.0 - (ly + ch_mm/2 + hh) / self.card_h) * TH
            
            is_gold = "Gold" in self.chip_type
            base_color = QtGui.QColor("#e2bd4d") if is_gold else QtGui.QColor("#d1d5db")
            border_color = base_color.darker(140)
            gap_color = base_color.darker(250)
            
            # 1. Main Metallic Pad
            p.setPen(QtGui.QPen(border_color, 1))
            p.setBrush(base_color)
            p.drawRoundedRect(px, py, cw, ch, 3, 3)
            
            # 2. Internal Segments (ISO 7816-2 Pitches: 7.62mm Horiz, 2.54mm Vert)
            p.setBrush(QtCore.Qt.NoBrush)
            p.setPen(QtGui.QPen(gap_color, 1.2))
            
            # Vertical split (Between C1-C4 and C5-C8)
            # Standard center split is 7.62mm wide region
            vx = px + (7.62/2 / cw_mm) * cw
            # However, for 13mm module, we just split it roughly center or offset
            p.drawLine(px + cw*0.5, py + 2, px + cw*0.5, py + ch - 2)
            
            # Horizontal splits (Row gaps are 2.54mm)
            for i in range(1, 4 if "8-Pad" in self.chip_type else 3):
                # Calculate relative Y based on 2.54mm pitch
                # ISO pads start ~19.23 and end ~28.55.
                y_off = (i * 2.54 / ch_mm) * ch
                p.drawLine(px + 2, py + y_off, px + cw - 2, py + y_off)

            # Center "Isolation Area" (Typical for modern microchips)
            if "8-Pad" in self.chip_type:
                p.drawRoundedRect(px + cw*0.3, py + ch*0.25, cw*0.4, ch*0.5, 2, 2)
            else:
                p.drawRoundedRect(px + cw*0.35, py + ch*0.35, cw*0.3, ch*0.3, 1, 1)

            # 3. Metallic Lustre
            grad = QtGui.QLinearGradient(px, py, px + cw, py + ch)
            grad.setColorAt(0, QtGui.QColor(255, 255, 255, 120))
            grad.setColorAt(0.4, QtCore.Qt.transparent)
            grad.setColorAt(1, QtGui.QColor(0, 0, 0, 60))
            p.setBrush(grad); p.setPen(QtCore.Qt.NoPen); p.drawRoundedRect(px, py, cw, ch, 3, 3)
        
        # CONTACTLESS CHIPS (Internal Antenna - Subtle X-Ray Look)
        else:
            self._draw_contactless_antenna(p, TW, TH, scale_x, scale_y)

    def _draw_contactless_antenna(self, p, TW, TH, sx, sy):
        # Subtle internal antenna visualization
        p.setBrush(QtCore.Qt.NoBrush)
        color = QtGui.QColor(0, 0, 0, 15) # Very faint shadow of antenna
        p.setPen(QtGui.QPen(color, 2))
        
        if "[LF]" in self.chip_type:
            # Round coil (125kHz)
            # Centered roughly on the left half
            cx, cy = 0.25 * TW, 0.5 * TH
            for r in range(5):
                p.drawEllipse(QtCore.QPointF(cx, cy), 12*sx + r*2, 12*sy + r*2)
        elif "[HF]" in self.chip_type or "[NFC]" in self.chip_type:
            # Rectangular perimeter coil (13.56MHz)
            for i in range(4):
                off = i * 4
                p.drawRoundedRect(0.1*TW + off, 0.1*TH + off, 0.8*TW - 2*off, 0.8*TH - 2*off, 5, 5)
        elif "[UHF]" in self.chip_type:
            # Long dipole antenna center
            p.drawRoundedRect(0.1*TW, 0.45*TH, 0.8*TW, 0.1*TH, 2, 2)
            p.drawRoundedRect(0.35*TW, 0.3*TH, 0.3*TW, 0.4*TH, 2, 2)

    def set_chip_type(self, chip_type):
        self.chip_type = chip_type
        self._refresh_textures = True
        self.update()

    def _draw_magstripe(self, p, TW, TH):
        # Professional Magstripe Rendering (ISO 7811)
        # Width: 12.7 mm (Standard 3-track)
        # Margin from top: 5.54 mm (Wait research said 2.92mm to top edge of stripe)
        # Typical height is 12.7mm.
        sw_mm = self.card_w
        sh_mm = 12.7
        top_margin_mm = 2.92
        
        scale_x = TW / self.card_w
        scale_y = TH / self.card_h
        
        sw, sh = sw_mm * scale_x, sh_mm * scale_y
        px = 0
        # py is from top of texture. 
        # Texture Y 0 is TOP, card Y 0 is CENTER.
        py = (top_margin_mm / self.card_h) * TH
        
        is_hico = "HiCo" in self.magstripe_type
        base_color = QtGui.QColor("#111111") if is_hico else QtGui.QColor("#402d20")
        shine_color = QtGui.QColor(255, 255, 255, 35)
        
        # 1. Base Stripe
        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(base_color)
        p.drawRect(px, py, sw, sh)
        
        # 2. Metallic "Shiny" Effect
        # A series of thin diagonal gradients to simulate light catching magnetic particles
        grad = QtGui.QLinearGradient(px, py, px + sw, py + sh)
        grad.setColorAt(0, QtCore.Qt.transparent)
        grad.setColorAt(0.2, shine_color)
        grad.setColorAt(0.25, QtCore.Qt.transparent)
        grad.setColorAt(0.5, shine_color)
        grad.setColorAt(0.55, QtCore.Qt.transparent)
        grad.setColorAt(0.8, shine_color)
        grad.setColorAt(1, QtCore.Qt.transparent)
        
        p.setBrush(grad)
        p.drawRect(px, py, sw, sh)
        
        # 3. Microtexture (Subtle noise/grain for magnetic particles)
        noise_brush = QtGui.QBrush(QtCore.Qt.Dense7Pattern)
        p.setBrush(noise_brush)
        p.setOpacity(0.1)
        p.drawRect(px, py, sw, sh)
        p.setOpacity(1.0)

    def set_magstripe_type(self, mtype):
        self.magstripe_type = mtype
        self._refresh_textures = True
        self.update()

    def add_text_object(self, text="NEW TEXT", side="front", color="#000000"):
        obj = TextObject(text, side, color)
        self.text_objects.append(obj)
        self.selected_obj = obj
        self._refresh_textures = True
        self.update()
        return obj

    def add_graphic_object(self, image, side="front", obj_type="custom"):
        obj = GraphicObject(image, side, obj_type)
        self.graphic_objects.append(obj)
        self.selected_obj = obj
        self._refresh_textures = True
        self.update()

    def set_card_color(self, hex_color):
        self.card_color = QtGui.QColor(hex_color)
        self._refresh_textures = True
        self.update()

    def set_card_material(self, material_name):
        self.card_material = material_name
        self.update()

    def set_custom_texture(self, image_path, side):
        img = QtGui.QImage(image_path)
        if img.isNull():
            return False
        
        if side == "front":
            self.custom_front_img = img
        elif side == "back":
            self.custom_back_img = img
        elif side == "both":
            self.custom_front_img = img
            self.custom_back_img = img
            
        self._refresh_textures = True
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
        if self._refresh_textures:
            self.update_face_textures()
            
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.camera_dist)
        
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)

        # Update matrices for picking retrieval if needed (actually better to do in mousePress)
        self.draw_card()
        
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

        # Bind texture if applicable (Prefer fused design texture)
        def bind_face_texture(side):
            tex = getattr(self, f'fused_{side}_tex', None)
            if tex:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, tex)
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

        # Super Realistic 3D Extrusion/Indentation Pass
        if self.emboss_quality == "Super Realistic":
            for obj in self.text_objects:
                if not obj.show_emboss_effect() or not obj.tex_3d:
                    continue
                
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, obj.tex_3d)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                
                tw = 51.2 * obj.tex_w_ratio
                th = 12.8 * obj.tex_h_ratio
                lx, ly = obj.pos
                
                # FRONT: Raised (Extrusion)
                if obj.side == "front" or obj.is_physical:
                    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
                    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 100.0)
                    layers = 20
                    thickness = 1.0 
                    for i in range(layers):
                        z_off = hz + 0.05 + (i / layers) * thickness
                        
                        if i == layers - 1:
                            # TOP FACE: Use the object's actual color
                            c = obj.color
                            glColor4f(c.redF(), c.greenF(), c.blueF(), 1.0)
                        else:
                            # SIDES: Use White/Gray for the material side look
                            brightness = 0.95 + (i / layers) * 0.05
                            glColor4f(brightness, brightness, brightness, 1.0)
                        
                        glBegin(GL_QUADS)
                        glNormal3f(0, 0, 1)
                        glTexCoord2f(0.5 - obj.tex_w_ratio/2, 0.5 - obj.tex_h_ratio/2); glVertex3f(lx - tw/2, ly - th/2, z_off)
                        glTexCoord2f(0.5 + obj.tex_w_ratio/2, 0.5 - obj.tex_h_ratio/2); glVertex3f(lx + tw/2, ly - th/2, z_off)
                        glTexCoord2f(0.5 + obj.tex_w_ratio/2, 0.5 + obj.tex_h_ratio/2); glVertex3f(lx + tw/2, ly + th/2, z_off)
                        glTexCoord2f(0.5 - obj.tex_w_ratio/2, 0.5 + obj.tex_h_ratio/2); glVertex3f(lx - tw/2, ly + th/2, z_off)
                        glEnd()

                # BACK: Indented (Recessed) - the physical 'sink in' on the other side
                if (obj.side == "front" and obj.is_physical) or (obj.side == "back"):
                    # On the back, it goes INTO the card
                    layers = 12
                    thickness = -0.5 # Goes inward from back surface
                    card_c = self.card_color
                    for i in range(layers):
                        z_off = -hz - 0.01 + (i / layers) * thickness
                        # Slightly darken the card color to simulate the shadow inside the indentation
                        darkness = 0.5 + (i / layers) * 0.3
                        glColor4f(card_c.redF() * darkness, card_c.greenF() * darkness, card_c.blueF() * darkness, 1.0)
                        
                        glBegin(GL_QUADS)
                        glNormal3f(0, 0, -1)
                        # MIRRORED Texture coordinates for the back side
                        # Swap Left and Right to show the back of the punched letters correctly
                        glTexCoord2f(0.5 + obj.tex_w_ratio/2, 0.5 - obj.tex_h_ratio/2); glVertex3f(lx - tw/2, ly - th/2, z_off)
                        glTexCoord2f(0.5 - obj.tex_w_ratio/2, 0.5 - obj.tex_h_ratio/2); glVertex3f(lx + tw/2, ly - th/2, z_off)
                        glTexCoord2f(0.5 - obj.tex_w_ratio/2, 0.5 + obj.tex_h_ratio/2); glVertex3f(lx + tw/2, ly + th/2, z_off)
                        glTexCoord2f(0.5 + obj.tex_w_ratio/2, 0.5 + obj.tex_h_ratio/2); glVertex3f(lx - tw/2, ly + th/2, z_off)
                        glEnd()
                
                glDisable(GL_BLEND)

    def update(self):
        self._refresh_textures = True
        super().update()

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            if self.selected_obj:
                # Remove from appropriate list
                if self.selected_obj in self.text_objects:
                    self.text_objects.remove(self.selected_obj)
                elif self.selected_obj in self.graphic_objects:
                    self.graphic_objects.remove(self.selected_obj)
                
                self.selected_obj = None
                self._refresh_textures = True
                self.update()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.last_pos = event.pos()
        self.makeCurrent()
        
        # Stop any ongoing inertia when user touches the card
        self.inertia_timer.stop()
        self.rot_velocity = [0.0, 0.0]
        
        if event.button() == QtCore.Qt.LeftButton:
            new_selection = self.pick_object(event.pos())
            if new_selection != self.selected_obj:
                self.selected_obj = new_selection
                self._refresh_textures = True # Re-bake to update highlight
                self.update()
            
            if self.selected_obj:
                self.is_dragging = True
                # Bring selected object to front of interaction list (draw last)
                self.text_objects.remove(self.selected_obj)
                self.text_objects.append(self.selected_obj)
        
        elif event.button() == QtCore.Qt.RightButton:
            pass

    def pick_object(self, pos):
        # 1. Determine which side is facing the camera
        # Calculated from rotation: normal [0,0,1] transformed
        rx = math.radians(self.rotation[0])
        ry = math.radians(self.rotation[1])
        # The dot product of the front normal shadowed on camera Z is basically:
        nz = math.cos(ry) * math.cos(rx)
        camera_side = "front" if nz > 0 else "back"
        
        # 2. Get GL matrices for projection
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        best_obj = None
        min_dist = float('inf')
        
        # Check both Texts and Graphics
        all_objs = self.text_objects + self.graphic_objects
        
        for obj in reversed(all_objs):
            # Only consider objects on the visible side (or physical)
            is_phys = hasattr(obj, 'is_physical') and obj.is_physical
            if obj.side != camera_side and not is_phys:
                continue
            
            # Project local 3D pos to screen
            lx, ly = obj.pos
            lz = (self.card_t/2 + 0.1) if camera_side == "front" else -(self.card_t/2 + 0.1)
            
            try:
                sx, sy, sz = gluProject(lx, ly, lz, modelview, projection, viewport)
                sy = viewport[3] - sy
                
                dx = pos.x() - sx
                dy = pos.y() - sy
                
                # Use cached 3D dimension
                hit_w = obj.width_3d * (viewport[2] / self.camera_dist / 1.5)
                hit_h = obj.height_3d * (viewport[3] / self.camera_dist / 1.5)
                
                if abs(dx) < hit_w/2 and abs(dy) < hit_h/2:
                    return obj
            except: continue
        return None

    def mouseReleaseEvent(self, event):
        if self.is_dragging:
            self.is_dragging = False
            # Re-bake final position
            self._refresh_textures = True
            self.update()
        else:
            # Start the inertia timer for momentum
            # Only if the movement was fast enough to matter
            if abs(self.rot_velocity[0]) > 0.1 or abs(self.rot_velocity[1]) > 0.1:
                self.inertia_timer.start()

    def animate_to_view(self, rx, ry):
        # Stop all existing movement
        self.inertia_timer.stop()
        self.rot_velocity = [0.0, 0.0]
        self.target_rotation = [rx, ry]
        self.anim_timer.start()

    def update_animation(self):
        # Smooth interpolation (lerp) toward target rotation
        lerp = 0.15
        
        dx = self.target_rotation[0] - self.rotation[0]
        dy = self.target_rotation[1] - self.rotation[1]
        
        self.rotation[0] += dx * lerp
        self.rotation[1] += dy * lerp
        
        # Check if close enough to stop
        if abs(dx) < 0.1 and abs(dy) < 0.1:
            self.rotation[0] = self.target_rotation[0]
            self.rotation[1] = self.target_rotation[1]
            self.anim_timer.stop()
            
        self.update()

    def apply_inertia(self):
        # Professional friction decay (0.95 factor per frame)
        friction = 0.96
        self.rot_velocity[0] *= friction
        self.rot_velocity[1] *= friction
        
        # Apply current velocity to rotation
        self.rotation[1] += self.rot_velocity[0]
        self.rotation[0] += self.rot_velocity[1]
        
        # Threshold to stop the timer when movement is imperceptible
        if abs(self.rot_velocity[0]) < 0.01 and abs(self.rot_velocity[1]) < 0.01:
            self.inertia_timer.stop()
            self.rot_velocity = [0.0, 0.0]
            
        self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        
        # Rotation (Right Mouse or no selection) - Much smoother sensitivity (0.15)
        if (event.buttons() & QtCore.Qt.RightButton) or (not self.is_dragging):
            # Calculate velocity for inertia
            vx = dx * 0.12
            vy = dy * 0.12
            self.rotation[1] += vx
            self.rotation[0] += vy
            # Store smoothed velocity
            self.rot_velocity = [vx, vy]
            self.update()

        # Dragging (Left Mouse on selected object)
        if (event.buttons() & QtCore.Qt.LeftButton) and self.selected_obj and self.is_dragging:
            # Scale mouse movement to local mm based on depth
            scale = self.camera_dist * 0.002
            
            # Adjust movement direction based on side
            # When looking at the back, X is reversed
            rx = math.radians(self.rotation[0])
            ry = math.radians(self.rotation[1])
            nz = math.cos(ry) * math.cos(rx)
            ss = 1.0 if nz > 0 else -1.0
            
            self.selected_obj.pos[0] += dx * scale * ss
            self.selected_obj.pos[1] -= dy * scale
            
            # Bounds checking
            hw, hh = self.card_w/2.0, self.card_h/2.0
            self.selected_obj.pos[0] = max(-hw+5, min(hw-5, self.selected_obj.pos[0]))
            self.selected_obj.pos[1] = max(-hh+5, min(hh-5, self.selected_obj.pos[1]))
            
            # Request re-bake only if not too laggy
            self.update()

        self.last_pos = pos
        self.update()

    def wheelEvent(self, event):
        delta = event.angleDelta().y() / 8.0
        if delta == 0: return
        self.camera_dist -= delta * 0.2
        self.camera_dist = max(20.0, min(500.0, self.camera_dist))
        super().update()

class TextObjectWidget(QtWidgets.QWidget):
    def __init__(self, text_obj, gl_widget, parent=None):
        super().__init__(parent)
        self.text_obj = text_obj
        self.gl_widget = gl_widget
        
        self.setStyleSheet("""
            QWidget { background-color: #09090b; border: 1px solid #27272a; border-radius: 8px; }
            QLineEdit { background-color: #18181b; border: 1px solid #27272a; color: #fafafa; font-size: 11px; padding: 4px; }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            QPushButton { background-color: #27272a; border: 1px solid #27272a; color: white; padding: 5px; border-radius: 4px; font-size: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #3f3f46; border-color: #52525b; }
            QComboBox { background-color: #18181b; border: 1px solid #27272a; color: #fafafa; font-size: 10px; padding: 3px; }
            QComboBox:hover { background-color: #27272a; }
        """)
        
        layout = QtWidgets.QVBoxLayout(self) 
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # Row 1: Text Input + Delete
        top_row = QtWidgets.QHBoxLayout()
        self.edit = QtWidgets.QLineEdit(text_obj.text)
        self.edit.textChanged.connect(self.on_text_changed)
        top_row.addWidget(self.edit)
        
        self.del_btn = QtWidgets.QPushButton("×")
        self.del_btn.setFixedSize(20, 20)
        self.del_btn.setStyleSheet("background-color: #7f1d1d; font-size: 14px; padding: 0;")
        self.del_btn.clicked.connect(self.on_delete)
        top_row.addWidget(self.del_btn)
        layout.addLayout(top_row)
        
        # Row 2: Basic Controls (Compact)
        ctrl_layout = QtWidgets.QHBoxLayout()
        ctrl_layout.setSpacing(4)
        
        self.side_combo = QtWidgets.QComboBox()
        self.side_combo.addItems(["Front", "Back"])
        self.side_combo.setCurrentText(text_obj.side.capitalize())
        self.side_combo.currentTextChanged.connect(self.on_side_changed)
        self.side_combo.setFixedWidth(60)
        if text_obj.is_physical:
            self.side_combo.setEnabled(False)
            self.side_combo.setToolTip("Physical embossing appears on both sides")
            self.side_combo.hide()
        ctrl_layout.addWidget(self.side_combo)
        
        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItems(["Std", "Emboss"])
        self.style_combo.setCurrentText("Std" if text_obj.style == "Standard" else "Emboss")
        self.style_combo.currentTextChanged.connect(self.on_style_changed)
        self.style_combo.setFixedWidth(65)
        ctrl_layout.addWidget(self.style_combo)
        
        self.border_check = QtWidgets.QCheckBox("Bdr")
        self.border_check.setStyleSheet("color: white; font-size: 10px;")
        self.border_check.setChecked(text_obj.border_enabled)
        self.border_check.stateChanged.connect(self.on_border_changed)
        ctrl_layout.addWidget(self.border_check)
        
        self.color_btn = QtWidgets.QPushButton("Col")
        self.color_btn.clicked.connect(self.on_color_requested)
        self.color_btn.setFixedWidth(32)
        ctrl_layout.addWidget(self.color_btn)
        
        self.font_btn = QtWidgets.QPushButton("Fnt")
        self.font_btn.clicked.connect(self.on_font_requested)
        self.font_btn.setFixedWidth(32)
        ctrl_layout.addWidget(self.font_btn)
        
        layout.addLayout(ctrl_layout)

    def on_text_changed(self, text):
        clean_text = self.text_obj.validate_text(text)
        if clean_text != text:
            self.edit.setText(clean_text)
        self.text_obj.text = clean_text
        self.gl_widget.update()

    def on_side_changed(self, side_text):
        self.text_obj.side = side_text.lower()
        self.gl_widget.update()

    def on_style_changed(self, style_text):
        self.text_obj.style = "Standard" if style_text == "Std" else "Embossed"
        self.gl_widget.update()

    def on_border_changed(self, state):
        self.text_obj.border_enabled = (state == QtCore.Qt.Checked)
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
    def __init__(self, mode="windowed", card_type="CR80", emboss_quality="Realistic"):
        super().__init__()
        self.setWindowTitle("Mendy's 3D Card Preview")
        self.setGeometry(100, 100, 1100, 700)

        # Apply premium dark theme stylesheet to the whole window
        self.setStyleSheet("""
            QMainWindow { background-color: #09090b; }
            QLabel { 
                color: #f4f4f5; 
                font-size: 11px; 
                text-transform: uppercase; 
                letter-spacing: 0.5px; 
                font-weight: 800; 
                margin-top: 15px; 
                margin-bottom: 2px;
            }
            QComboBox { 
                background-color: #18181b; color: #fafafa; border: 1px solid #27272a; 
                padding: 8px; border-radius: 6px; font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #18181b;
                color: #fafafa;
                selection-background-color: #3b82f6;
                selection-color: white;
                border: 1px solid #3f3f46;
                outline: 0px;
                padding: 4px;
            }
            QComboBox:hover { border: 1px solid #3f3f46; background-color: #27272a; }
            QComboBox::drop-down { border: none; }
            
            QLineEdit { 
                background-color: #18181b; color: #fafafa; border: 1px solid #27272a; 
                padding: 8px; border-radius: 6px; 
            }
            QLineEdit:focus { border: 1px solid #3b82f6; }
            
            QPushButton#ActionBtn {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3f3f46, stop:1 #27272a); 
                color: #ffffff; border: 1px solid #52525b; 
                padding: 10px; border-radius: 6px; font-weight: 700; font-size: 11px;
                text-transform: uppercase;
            }
            QPushButton#ActionBtn:hover { 
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #52525b, stop:1 #3f3f46); 
                border-color: #3b82f6; 
            }
            QPushButton#ActionBtn:pressed { background-color: #18181b; }
            
            QPushButton#EmbossBtn {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ca8a04, stop:1 #854d0e); 
                color: #ffffff; border: 1px solid #eab308; 
                padding: 10px; border-radius: 6px; font-weight: 800; font-size: 11px;
                text-transform: uppercase;
            }
            QPushButton#EmbossBtn:hover { 
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eab308, stop:1 #ca8a04); 
                border-color: #fef08a; 
            }
            
            QPushButton#ImportBtn {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #059669, stop:1 #065f46); 
                color: #ffffff; border: 1px solid #10b981; 
                padding: 10px; border-radius: 6px; font-weight: 800; font-size: 11px;
                text-transform: uppercase;
            }
            QPushButton#ImportBtn:hover { 
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669); 
                border-color: #6ee7b7; 
            }
        """)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # GL Widget - Init early so we can reference it
        self.gl_widget = GLWidget(card_type, emboss_quality)

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
        self.import_btn.setObjectName("ImportBtn")
        self.import_btn.clicked.connect(self.on_import_image_clicked)
        sidebar_layout.addWidget(self.import_btn)

        # Multiple Text Objects Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Custom Text Layers"))
        
        self.add_text_btn = QtWidgets.QPushButton("+ Add New Text Layer")
        self.add_text_btn.setObjectName("ActionBtn")
        self.add_text_btn.clicked.connect(self.on_add_text_clicked)
        sidebar_layout.addWidget(self.add_text_btn)

        # Chip Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Integrated Circuit (Chip)"))
        self.chip_combo = QtWidgets.QComboBox()
        
        # Build a robust model for the chips with disabled headers
        chip_list = [
            "None",
            "-- CONTACT CHIPS --",
            "SLE4442 (Contact Gold)",
            "SLE5542 (Contact Gold)",
            "Atmel/FM4442 (Contact Gold)",
            "Standard ISO (Contact Gold)",
            "Standard ISO (Contact Silver)",
            "-- LF 125 kHz --",
            "[LF] EM4102",
            "[LF] TK4100",
            "-- HF 13.56 MHz --",
            "[HF] MIFARE Classic 1k",
            "[HF] MIFARE Classic 4k",
            "[HF] MIFARE DESFire EV1/2",
            "[HF] MIFARE Ultralight/C",
            "[HF] ICODE SLIX",
            "-- NFC TECHNOLOGY --",
            "[NFC] NTAG 213",
            "[NFC] NTAG 215",
            "[NFC] NTAG 216",
            "-- UHF 900 MHz --",
            "[UHF] Alien H3"
        ]
        
        model = QtGui.QStandardItemModel()
        for text in chip_list:
            item = QtGui.QStandardItem(text)
            if text.startswith("--"):
                item.setSelectable(False)
                item.setEnabled(False)
                item.setForeground(QtGui.QColor("#71717a")) # Muted color for headers
            model.appendRow(item)
            
        self.chip_combo.setModel(model)
        self.chip_combo.currentTextChanged.connect(self.on_chip_type_changed)
        sidebar_layout.addWidget(self.chip_combo)

        # Magstripe Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Magnetic Stripe"))
        self.mag_combo = QtWidgets.QComboBox()
        self.mag_combo.addItems(["None", "HiCo (Black)", "LoCo (Brown)"])
        self.mag_combo.currentTextChanged.connect(self.on_magstripe_type_changed)
        sidebar_layout.addWidget(self.mag_combo)
        
        # Graphics Section
        sidebar_layout.addWidget(QtWidgets.QLabel("Custom Graphics / Codes"))
        codes_layout = QtWidgets.QHBoxLayout()
        
        self.add_qr_btn = QtWidgets.QPushButton("+ Import QR")
        self.add_qr_btn.setObjectName("ActionBtn")
        self.add_qr_btn.clicked.connect(self.on_add_qr_clicked)
        
        self.add_bar_btn = QtWidgets.QPushButton("+ Import Barcode")
        self.add_bar_btn.setObjectName("ActionBtn")
        self.add_bar_btn.clicked.connect(self.on_add_barcode_clicked)
        
        codes_layout.addWidget(self.add_qr_btn)
        codes_layout.addWidget(self.add_bar_btn)
        sidebar_layout.addLayout(codes_layout)

        self.add_emboss_btn = QtWidgets.QPushButton("+ Add Embossed Layer")
        self.add_emboss_btn.setObjectName("EmbossBtn")
        self.add_emboss_btn.clicked.connect(self.on_add_emboss_clicked)
        sidebar_layout.addWidget(self.add_emboss_btn)

        # Scroll area for text objects
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
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
        
        # GL View Container to handle overlays
        view_container = QtWidgets.QWidget()
        view_layout = QtWidgets.QGridLayout(view_container)
        view_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add GL widget to fill the whole area
        view_layout.addWidget(self.gl_widget, 0, 0)
        
        # Add the Navigation ViewCube (AutoCAD Style) to Top-Right
        self.hud = ViewCubeHUD(self.gl_widget)
        view_layout.addWidget(self.hud, 0, 0, QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)
        
        main_layout.addWidget(view_container)

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

    def on_chip_type_changed(self, new_chip):
        self.gl_widget.set_chip_type(new_chip)

    def on_magstripe_type_changed(self, new_mag):
        self.gl_widget.set_magstripe_type(new_mag)

    def on_add_qr_clicked(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import QR or Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            img = QtGui.QImage(file_path)
            if not img.isNull():
                self.gl_widget.add_graphic_object(img, obj_type="qr")

    def on_add_barcode_clicked(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Barcode", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            img = QtGui.QImage(file_path)
            if not img.isNull():
                self.gl_widget.add_graphic_object(img, obj_type="barcode")

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

    def on_add_emboss_clicked(self):
        # Create a new physical embossing object (Silver by default)
        new_obj = self.gl_widget.add_text_object("EMBOSSED", "front", "#c0c0c0")
        new_obj.is_physical = True
        self.add_text_widget(new_obj)

    def add_text_widget(self, text_obj):
        widget = TextObjectWidget(text_obj, self.gl_widget)
        # Insert before the stretch at the bottom
        self.text_list_layout.insertWidget(self.text_list_layout.count() - 1, widget)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        elif event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            # Exit movement and editation
            self.gl_widget.selected_obj = None
            self.gl_widget.is_dragging = False
            # De-focus any sidebar widgets
            self.setFocus() 
            self.gl_widget.update()
        else:
            super().keyPressEvent(event)

class ViewCubeHUD(QtWidgets.QWidget):
    def __init__(self, gl_widget, parent=None):
        super().__init__(parent)
        self.gl_widget = gl_widget
        self.setFixedSize(130, 160)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Side Switcher (Tabs front/back)
        side_layout = QtWidgets.QHBoxLayout()
        self.btn_f = QtWidgets.QPushButton("FRONT")
        self.btn_b = QtWidgets.QPushButton("BACK")
        for b in [self.btn_f, self.btn_b]:
            b.setCheckable(True)
            b.setFixedSize(55, 20)
            b.setStyleSheet("font-size: 8px; font-weight: bold; background: #18181b; color: #a1a1aa; border: 1px solid #27272a;")
            side_layout.addWidget(b)
        
        self.btn_f.setChecked(True)
        self.btn_f.clicked.connect(lambda: self.switch_side("front"))
        self.btn_b.clicked.connect(lambda: self.switch_side("back"))
        main_layout.addLayout(side_layout)
        
        # The "Cube" Grid (3x3)
        # Arrangement:
        # [TL] [T] [TR]
        # [L ] [F] [R ]
        # [BL] [B] [BR]
        cube_container = QtWidgets.QWidget()
        cube_container.setStyleSheet("background: rgba(24, 24, 27, 180); border-radius: 8px; border: 1px solid rgba(161,161,170,30);")
        grid = QtWidgets.QGridLayout(cube_container)
        grid.setContentsMargins(5, 5, 5, 5)
        grid.setSpacing(2)
        
        # Views [rx, ry]
        self.views = {
            "TL": [35, 35],  "T": [35, 0],  "TR": [35, -35],
            "L": [0, 35],    "C": [0, 0],   "R": [0, -35],
            "BL": [-35, 35], "B": [-35, 0], "BR": [-35, -35]
        }
        
        self.btns = {}
        for key, coords in self.views.items():
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(30, 30)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            
            # Specialty styling for Center (Face) vs Corners vs Edges
            color = "#3b82f6" if key == "C" else "#3f3f46"
            btn.setStyleSheet(f"background: {color}; border-radius: 2px;")
            if key == "C": btn.setText("FACE")
            
            btn.clicked.connect(lambda checked, c=coords: self.go_to(c))
            grid.addWidget(btn, list(self.views.keys()).index(key)//3, list(self.views.keys()).index(key)%3)
            self.btns[key] = btn
            
        main_layout.addWidget(cube_container)
        
        lbl = QtWidgets.QLabel("VIEW NAVIGATION")
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setStyleSheet("color: #71717a; font-size: 7px; letter-spacing: 1px; margin-top: 2px;")
        main_layout.addWidget(lbl)

    def switch_side(self, side):
        self.btn_f.setChecked(side == "front")
        self.btn_b.setChecked(side == "back")
        ry = 0 if side == "front" else 180
        self.gl_widget.animate_to_view(self.gl_widget.rotation[0], ry)

    def go_to(self, coords):
        # Apply current side (front/back) to the selection
        ry_offset = 0 if self.btn_f.isChecked() else 180
        self.gl_widget.animate_to_view(coords[0], coords[1] + ry_offset)

if __name__ == "__main__":
    print("Starting App...")
    app = QtWidgets.QApplication([])
    dialog = StartMenuDialog()
    if dialog.exec() == QtWidgets.QDialog.Accepted:
        mode = dialog.get_selected_mode()
        card_type = dialog.get_selected_card_type()
        emboss_quality = dialog.get_selected_emboss_quality()
        window = MainWindow(mode, card_type, emboss_quality)
        app.exec()
    else:
        app.quit()