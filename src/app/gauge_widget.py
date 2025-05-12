from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PyQt6.QtCore import Qt, QRectF, QPointF, QRect


class CircularGauge(QWidget):
    def __init__(self, parent=None, min_value=0, max_value=100, title=""):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.value = 0
        self.title = title
        self.setMinimumSize(150, 150)
        
        # Updated colors with a softer pastel palette
        self.bg_color = QColor(40, 40, 40, 80)
        self.track_color = QColor(60, 60, 60)
        
        # Pastel color scheme - softer and more pleasing to the eye
        self.progress_start_color = QColor(197, 249, 215)  # Soft sky blue
        self.progress_mid_color = QColor(247, 212, 134)    # Mint green
        self.progress_end_color = QColor(242, 122, 125)    # Peach/gold
        
        self.text_color = QColor(255, 255, 255)
        
        # Get system palette for better theme integration
        self.update_colors_from_palette()
    
    def update_colors_from_palette(self):
        """Update colors based on application palette for better theme integration"""
        palette = self.palette()
        bg = palette.color(palette.ColorRole.Window)
        fg = palette.color(palette.ColorRole.WindowText)
        
        # Check if we're in dark mode
        is_dark = bg.lightness() < 128
        
        if is_dark:
            # Dark theme
            self.bg_color = QColor(40, 40, 40, 80)
            self.track_color = QColor(60, 60, 60)
            self.text_color = QColor(220, 220, 220)
        else:
            # Light theme
            self.bg_color = QColor(230, 230, 230, 80)
            self.track_color = QColor(180, 180, 180)
            self.text_color = QColor(30, 30, 30)
    
    def set_value(self, value):
        """Set current value and repaint"""
        try:
            # Ensure value is a number
            numeric_value = float(value)
            self.value = max(self.min_value, min(self.max_value, numeric_value))
            self.update()
        except (ValueError, TypeError):
            print(f"Invalid value for gauge: {value}")
    
    def set_max_value(self, max_value):
        """Update the maximum value for the gauge"""
        try:
            self.max_value = float(max_value)
            self.update()
        except (ValueError, TypeError):
            print(f"Invalid max value for gauge: {max_value}")
    
    def draw_arc_with_gradient(self, painter, rect, start_angle, span_angle, pen_width):
        """Draw an arc with a color gradient"""
        # Convert to integers for drawArc
        start_angle_int = int(start_angle)
        span_angle_int = int(span_angle)
        
        # Save the current painter state
        painter.save()
        
        # Create a pixmap to paint our gradient arc on
        pixmap_size = max(rect.width(), rect.height()) + pen_width
        pixmap = self.create_gradient_arc_pixmap(pixmap_size, pen_width, span_angle_int)
        
        # Create a QPainter for the pixmap
        pixmap_painter = QPainter(pixmap)
        pixmap_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set clipPath to only show the desired arc portion
        pixmap_painter.end()
        
        # Draw the pixmap centered on our rect
        painter.drawPixmap(
            int(rect.x() - pen_width/2),
            int(rect.y() - pen_width/2),
            pixmap
        )
        
        # Restore painter state
        painter.restore()
    
    def create_gradient_arc_pixmap(self, size, pen_width, span_angle):
        """Create a pixmap with a gradient arc"""
        pixmap = self.grab(QRect(0, 0, int(size), int(size)))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(pixmap.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Create the gradient
        gradient = QLinearGradient(0, 0, pixmap.width(), 0)
        gradient.setColorAt(0.0, self.progress_start_color)  # Blue at start
        gradient.setColorAt(0.4, self.progress_mid_color)    # Green in middle  
        gradient.setColorAt(1.0, self.progress_end_color)    # Red at end
        
        center = pixmap.rect().center()
        
        # Create the gradient pen
        pen = QPen()
        pen.setWidth(pen_width)
        pen.setBrush(gradient)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw a full circle (we'll clip it later)
        radius = (pixmap.width() - pen_width) / 2
        painter.drawArc(
            QRectF(
                center.x() - radius, 
                center.y() - radius,
                radius * 2, 
                radius * 2
            ),
            210 * 16,  # Start angle (left side)
            -240 * 16  # Span angle (clockwise)
        )
        
        painter.end()
        return pixmap
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate sizes
        rect = event.rect()
        center_x = rect.center().x()
        center_y = rect.center().y()
        size = min(rect.width(), rect.height())
        
        # Adjusted to keep gauge arcs within the widget bounds
        outer_radius = (size / 2) * 0.9
        inner_radius = outer_radius * 0.75
        
        # Create a QRectF for the ellipse
        ellipse_rect = QRectF(
            center_x - outer_radius,
            center_y - outer_radius,
            outer_radius * 2,
            outer_radius * 2
        )
        
        # Draw the transparent background circle
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawEllipse(ellipse_rect)
        
        # Arc parameters for left-to-right gauge
        start_angle = 210 * 16  # Start from left side (210 degrees)
        span_angle = -240 * 16  # Negative for clockwise direction
        
        # Calculate progress
        progress = 0
        if self.max_value > self.min_value:
            progress = (self.value - self.min_value) / (self.max_value - self.min_value)
        
        # Create the arc track - converting float to int for pen width
        pen_width = int(outer_radius - inner_radius)
        track_pen = QPen(self.track_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        
        # Calculate the rectangle for the arc
        pen_half_width = pen_width / 2
        track_rect = QRectF(
            center_x - outer_radius + pen_half_width,
            center_y - outer_radius + pen_half_width,
            2 * (outer_radius - pen_half_width),
            2 * (outer_radius - pen_half_width)
        )
        painter.drawArc(track_rect, int(start_angle), int(span_angle))
        
        # Create a clip path that only shows the progress portion
        if progress > 0:
            # Calculate the angle for the current progress
            progress_angle = int(span_angle * progress)
            
            # Create gradient directly on the painter
            gradient = QLinearGradient(
                QPointF(center_x - outer_radius, center_y),  # Left edge of the gauge
                QPointF(center_x + outer_radius, center_y)   # Right edge of the gauge
            )
            
            # Set gradient colors
            gradient.setColorAt(0.0, self.progress_start_color)  # Soft blue at start
            gradient.setColorAt(0.5, self.progress_mid_color)    # Mint green in middle
            gradient.setColorAt(1.0, self.progress_end_color)    # Peach at end
            
            # Create a gradient pen for the progress
            progress_pen = QPen()
            progress_pen.setWidth(pen_width)
            progress_pen.setBrush(gradient)
            progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(progress_pen)
            
            # Draw the progress arc with the gradient pen
            painter.drawArc(track_rect, int(start_angle), progress_angle)
        
        # Draw center text for value
        painter.setPen(self.text_color)
        text_font = QFont("Arial", int(outer_radius / 4))
        text_font.setBold(True)
        painter.setFont(text_font)
        
        # Value text
        value_text = f"{int(self.value)}"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, value_text)
        
        # Units/label text (smaller, below value)
        label_font = QFont("Arial", int(outer_radius / 8))
        painter.setFont(label_font)
        unit_text_rect = QRectF(
            center_x - outer_radius,
            center_y + (outer_radius / 9),
            2 * outer_radius,
            outer_radius / 4
        )
        painter.drawText(unit_text_rect, Qt.AlignmentFlag.AlignCenter, self.title)