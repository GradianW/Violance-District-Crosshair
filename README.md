# Violence District (VD) Crosshair Overlay 🎯

A lightweight, customizable, click-through Windows crosshair overlay built with Python and **PyQt6**, specifically designed to assist aiming in **Violence District (Roblox)** where weapons lack built-in reticles or shift-lock camera offsets require custom alignment.

---

## ✨ Features

- **100% Click-Through & Always-on-Top:** Uses native Win32 extended window styles (`WS_EX_TRANSPARENT` & `WS_EX_LAYERED`) so mouse clicks and camera movements pass seamlessly into Roblox.
- **7 Procedural Crosshair Shapes:**
  - `Classic Cross (+)`
  - `T-Cross (⊤)` (unobstructed upper sightline for headshots)
  - `Dot (•)`
  - `Circle (○)` (great for shotguns & spread weapons)
  - `Circle + Cross (⊕)`
  - `Chevron (^)`
  - `X-Mark (×)` (hitmarker style)
- **Fine-Grained Geometry Controls:**
  - Independent sliders for **Size / Length**, **Line Thickness**, **Center Gap**, and **Rotation Angle**.
  - Optional **Center Dot** toggle with adjustable dot size on any shape.
- **Visual & Visibility Enhancements:**
  - **High-Contrast Outline (Stroke):** Toggleable dark/custom outline (`1px–6px`) so your crosshair never disappears against bright skies, muzzle flashes, or dark corners.
  - **Custom Color & Opacity:** One-click neon presets (Green, Cyan, Red, Yellow, Magenta, White) + full RGB/Hex Color Picker and Alpha Transparency slider (`10%–100%`).
  - **Dynamic Right-Click (ADS) Mode (Optional):** Tightens gap or changes scale slightly while holding Right-Click.
- **Screen Position & Shift-Lock Alignment:**
  - Fine-tune **X Offset** and **Y Offset** (`-500px` to `+500px`) to match Roblox third-person shift-lock or first-person weapon alignment.
  - Multi-monitor support.
- **Preset Profiles & Global Hotkeys:**
  - Save, load, and delete custom weapon/camera presets.
  - Global in-game hotkeys to toggle visibility, cycle presets, or nudge the crosshair position live without leaving the game.
  - Minimizes cleanly to the **Windows System Tray**.

---

## 🚀 Quick Start

### 1. Clone & Setup Environment
```powershell
git clone https://github.com/GradianW/Violance-District-Crosshair.git
cd "Violance District Crosshair"

python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Run the Application
```powershell
.\.venv\Scripts\python main.py
```

---

## ⌨️ Default Global Hotkeys

| Hotkey | Action |
| :--- | :--- |
| **`F8`** (or **`Insert`**) | Toggle Crosshair Overlay On / Off |
| **`F9`** | Cycle through saved Preset Profiles |
| **`F10`** | Show / Hide Settings Control Panel |
| **`Ctrl + Arrow Keys`** | Nudge Crosshair Position (`X` / `Y` offset by `1px`) live in-game |
| **`Ctrl + Shift + R`** | Reset Crosshair Position to Screen Center `(0, 0)` |

---

## 📋 Specification-Driven Development
See [SPEC.md](./SPEC.md) for the complete architectural and functional specification of this project.
