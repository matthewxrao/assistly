---
# 🎯 **Assistly: Basketball Shot Tracking Application** 🏀
---

## **Overview**

Assistly is your basketball companion app, tracking and analyzing shots in **real-time** using computer vision. Whether practicing solo or competing with friends, it turns every session into a thrilling experience, complete with:

- **Dynamic visual effects**
- **Customizable audio feedback**
- **Detailed shooting stats and insights**

---

## **Features**

### 🚀 Real-Time Detection

Uses YOLO for **basketballs, rims, and shot events** detection.

### 🏆 Shot Tracking

Captures makes, misses, and **shooting percentages**.

### 🎇 Dynamic Visual Effects

Exciting animations, such as **lightning strikes** for streaks.

### 🎵 Customizable Audio Feedback

Choose sound themes:

- Arena Cheers
- Dog Barks
- Minion Reactions
- Cow Moos

### 📈 Performance Analysis

Session stats, streaks (hot/cold), and **exportable session logs**.

---

## **Requirements**

To run the project, install these:

- Python 3.x
- OpenCV
- PyTorch
- Ultralytics
- NumPy
- CMU Graphics
- Pillow
- PyGetWindow

```bash
pip install -r requirements.txt
```

---

## **Installation**

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/matthewxrao/assistly.git
cd assistly
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the App

```bash
python src/backend/main.py
```

---

## **How to Use**

1. **Start a Session**:

   - Select **automatic/manual modes**.
   - Customize crowd sounds.
   - Begin tracking shots!

2. **Analyze in Real-Time**:

   - View annotated stats and enjoy **effects**.

3. **Session Summary**:
   - Review detailed stats and **export data**.

---

## **File Structure**

```
assistly/
├── audios/             # Audio Packs (humans, dogs, minions, etc.)
├── images/             # UI Graphics (logo, tips)
├── src/
│   ├── backend/        # Core Application Logic
│   │   ├── main.py           # Main Application
│   │   ├── ekf.py            # Extended Kalman Filter (ball tracking)
│   │   ├── loadAudios.py     # Audio Management
│   │   ├── objectDetection.py# YOLO Detection
│   │   ├── visualEffects.py  # Dynamic Visuals
│   └── tests/          # Unit Tests
├── requirements.txt    # Dependencies
├── README.md           # Documentation
```

---

## **Contributing**

### 🛠️ Steps to Contribute:

1. **Fork the Repository**.
2. **Add Your Feature**: Create a branch.
3. **Pull Request**: Submit with descriptions.

---

## **License**

Licensed under the **MIT License**. See `LICENSE` for details.

---

## **Acknowledgments**

- **YOLO Creators**: For enabling cutting-edge object detection.
- **CMU Graphics**: For dynamic rendering tools.

---

### 🎉 **Transform your basketball sessions with Assistly!** 🏀
