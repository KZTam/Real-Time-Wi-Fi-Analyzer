"""
Connected Axis Item for PyQtGraph.
Ensures seamless corner alignment between X and Y axes, prevents
boundary tick label clipping ('0' and maximum values), eliminates gaps on
window resize/maximize, and prevents tick label overlap at the origin.
"""

from PyQt5.QtCore import QRectF
import pyqtgraph as pg


class ConnectedAxisItem(pg.AxisItem):
    """
    Subclass of pg.AxisItem providing:
    1. Expanded bounding rectangle so '0' and boundary tick labels are never clipped.
    2. Picture cache invalidation on geometry change or resize.
    3. Micro-offset for origin tick label ('0') to prevent visual overlap between
       left-axis '0' and bottom-axis '0'.
    """

    def boundingRect(self) -> QRectF:
        rect = super().boundingRect()
        if self.orientation == 'bottom':
            return rect.adjusted(-40.0, 0.0, 40.0, 0.0)
        elif self.orientation == 'left':
            return rect.adjusted(0.0, -20.0, 0.0, 20.0)
        return rect

    def setGeometry(self, rect):
        self.picture = None
        super().setGeometry(rect)
        self.picture = None

    def resizeEvent(self, ev=None):
        self.picture = None
        super().resizeEvent(ev)
        self.picture = None

    def generateDrawSpecs(self, p):
        specs = super().generateDrawSpecs(p)
        if specs is None:
            return None
        axisSpec, tickSpecs, textSpecs = specs
        new_textSpecs = []
        for rect, flags, text in textSpecs:
            # Prevent overlap between the left axis '0' and bottom axis '0'
            if text == '0':
                if self.orientation == 'left':
                    rect = QRectF(rect.x(), rect.y() - 3.0, rect.width(), rect.height())
                elif self.orientation == 'bottom':
                    rect = QRectF(rect.x() + 4.0, rect.y(), rect.width(), rect.height())
            new_textSpecs.append((rect, flags, text))
        return axisSpec, tickSpecs, new_textSpecs
