# NC_Engine

NC_Engine is a Python-based 3D visualization prototype inspired by the style and intent of a real-time engine, but built as a practical desktop MVP. It lets you enter a formula in terms of x, y, z, and t, then render the resulting point cloud in a 3D OpenGL view.

This project implements the achievable subset of the requested behavior:
- 3D real-time formula visualization
- time-based animation using t
- zoom control
- Windows-style shortcuts/actions
- RUN button to re-evaluate formulas
- N button to advance time by 1,000,000,000
- CW button to duplicate the main view in a separate window

Important notes:
- This is not a complete Unreal Engine 5 clone.
- The project intentionally restricts formulas to safe math expressions.
- A full AI, web research integration, and arbitrary Windows command execution are not implemented in this prototype for safety and portability.

## Features
- 3D point-cloud rendering with PyQtGraph + OpenGL
- formula editor
- zoom control
- time display using system time and simulation time
- keyboard shortcuts: Ctrl+R, Ctrl+Q, I, Ctrl+Shift+C
- copy-view behavior via CW button and shortcut

## Setup

Windows PowerShell:

```powershell
python -m pip install -r requirements.txt
python nc_engine.py
```

## Default formula

```python
x**2 + y**2 + z**2 - (1 + 0.2*sin(t))
```

This is only a demonstration surface. You may replace it with formulas such as:

```python
sin(x + t) + cos(y + t) - z
```

```python
(x**2 + y**2 + z**2) - (1 + 0.25*sin(t))
```

## Shortcuts
- Ctrl+R: RUN
- I: toggle inventory panel
- Ctrl+Shift+C: CW (copy window)
- Ctrl+Q: quit

## Repository status
This repository was created to host the NC_Engine prototype and provide a practical starting point for further extension.
