import ast
import sys
from datetime import datetime

import numpy as np
import pyqtgraph.opengl as gl
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QDockWidget, QDoubleSpinBox, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QPlainTextEdit, QSpinBox,
    QVBoxLayout, QWidget,
)

FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "sqrt": np.sqrt,
    "exp": np.exp,
    "log": np.log,
    "abs": np.abs,
}
VARIABLES = {"x", "y", "z", "t", "pi"}
ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)


def compile_formula(source: str):
    tree = ast.parse(source, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise ValueError(f"Nicht erlaubter Ausdruck: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in VARIABLES | FUNCTIONS.keys():
            raise ValueError(f"Unbekannter Name: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise ValueError("Erlaubt sind nur die eingebauten Mathefunktionen.")
            if node.keywords:
                raise ValueError("Benannte Funktionsargumente sind nicht erlaubt.")
    return compile(tree, "<NC_Engine-Formel>", "eval")


class NCWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NC_Engine — 3D Formel-Prototyp")
        self.resize(1200, 760)
        self.t = 0.0
        self.zoom = 1.0
        self.views = []
        self.compiled = compile_formula("x**2 + y**2 + z**2 - (1 + 0.2*sin(t))")

        root = QWidget()
        layout = QHBoxLayout(root)
        self.setCentralWidget(root)

        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=7)
        self.view.setBackgroundColor((20, 24, 32))
        self.views.append(self.view)
        layout.addWidget(self.view, 3)

        controls = QVBoxLayout()
        layout.addLayout(controls, 2)

        controls.addWidget(QLabel("Implizite Fläche: F(x,y,z,t) = 0"))
        self.editor = QPlainTextEdit()
        self.editor.setPlainText("x**2 + y**2 + z**2 - (1 + 0.2*sin(t))")
        self.editor.setPlaceholderText("Beispiel: x**2 + y**2 + z**2 - 1")
        controls.addWidget(self.editor, 1)

        row = QHBoxLayout()
        self.run_button = QPushButton("RUN")
        self.run_button.clicked.connect(self.run_formula)
        row.addWidget(self.run_button)

        self.n_button = QPushButton("N")
        self.n_button.setToolTip("Simulationszeit um 1.000.000.000 erhöhen")
        self.n_button.clicked.connect(self.advance_large_step)
        row.addWidget(self.n_button)

        self.cw_button = QPushButton("CW")
        self.cw_button.setToolTip("Ansichtsfenster duplizieren")
        self.cw_button.clicked.connect(self.copy_window)
        row.addWidget(self.cw_button)
        controls.addLayout(row)

        controls.addWidget(QLabel("Zoom"))
        self.zoom_control = QDoubleSpinBox()
        self.zoom_control.setRange(0.1, 10.0)
        self.zoom_control.setSingleStep(0.1)
        self.zoom_control.setValue(1.0)
        self.zoom_control.valueChanged.connect(self.set_zoom)
        controls.addWidget(self.zoom_control)

        controls.addWidget(QLabel("Nachkommastellen von t (d)"))
        self.digits = QSpinBox()
        self.digits.setRange(0, 9)
        self.digits.setValue(2)
        controls.addWidget(self.digits)

        self.time_label = QLabel()
        controls.addWidget(self.time_label)

        self.status = QLabel("Bereit")
        self.status.setWordWrap(True)
        controls.addWidget(self.status)

        inventory = QDockWidget("Inventory (MVP)", self)
        inventory.setWidget(QLabel("Objekt-Drag-and-drop ist in diesem Prototyp noch nicht enthalten."))
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, inventory)
        self.inventory = inventory

        self.add_action("RUN", QKeySequence("Ctrl+R"), self.run_formula)
        self.add_action("Inventory", QKeySequence("I"), self.toggle_inventory)
        self.add_action("CW", QKeySequence("Ctrl+Shift+C"), self.copy_window)
        self.add_action("Beenden", QKeySequence("Ctrl+Q"), self.close)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        self.draw_surface()

    def add_action(self, name: str, shortcut, callback):
        action = QAction(name, self)
        action.setShortcut(shortcut)
        action.triggered.connect(callback)
        self.addAction(action)

    def run_formula(self):
        try:
            self.compiled = compile_formula(self.editor.toPlainText().strip())
            self.draw_surface()
            self.status.setText("Formel ausgeführt.")
        except Exception as exc:
            QMessageBox.warning(self, "Formelfehler", str(exc))
            self.status.setText(f"Fehler: {exc}")

    def tick(self):
        d = self.digits.value()
        self.t += 10.0 ** (-d)
        self.time_label.setText(
            f"Simulation t = {self.t:.{min(d + 2, 12)}f}\n"
            f"Systemzeit = {datetime.now().astimezone().isoformat(timespec='seconds')}"
        )
        self.draw_surface()

    def draw_surface(self):
        axis = np.linspace(-2.0, 2.0, 44)
        x, y, z = np.meshgrid(axis, axis, axis, indexing="ij")
        env = {
            "x": x,
            "y": y,
            "z": z,
            "t": self.t,
            "pi": np.pi,
            **FUNCTIONS,
        }
        try:
            with np.errstate(all="ignore"):
                values = eval(self.compiled, {"__builtins__": {}}, env)
            values = np.asarray(values, dtype=float)
            values = np.broadcast_to(values, x.shape)
            mask = np.isfinite(values) & (np.abs(values) < 0.075)
            points = np.column_stack((x[mask], y[mask], z[mask]))
            if len(points) > 40000:
                points = points[::max(1, len(points) // 40000)]
        except Exception as exc:
            self.status.setText(f"Berechnungsfehler: {exc}")
            return

        for view in self.views:
            for item in list(view.items):
                if isinstance(item, gl.GLScatterPlotItem):
                    view.removeItem(item)
            if len(points):
                view.addItem(gl.GLScatterPlotItem(
                    pos=points,
                    color=(0.2, 0.75, 1.0, 1.0),
                    size=2,
                    pxMode=True,
                ))

    def set_zoom(self, value):
        self.zoom = value
        distance = max(0.5, 7.0 / value)
        for view in self.views:
            view.setCameraPosition(distance=distance)

    def advance_large_step(self):
        self.t += 1_000_000_000
        self.draw_surface()

    def toggle_inventory(self):
        self.inventory.setVisible(not self.inventory.isVisible())

    def copy_window(self):
        window = QMainWindow(self)
        window.setWindowTitle("NC_Engine — CW-Kopie")
        copied_view = gl.GLViewWidget()
        copied_view.setBackgroundColor((20, 24, 32))
        copied_view.setCameraPosition(distance=max(0.5, 7.0 / self.zoom))
        window.setCentralWidget(copied_view)
        self.views.append(copied_view)
        window.resize(640, 480)
        window.show()
        self.draw_surface()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    engine = NCWindow()
    engine.show()
    sys.exit(app.exec())
