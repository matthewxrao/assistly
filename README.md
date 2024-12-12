---
# **assistly** 
---

## **Overview**

Assistly is your basketball companion app, tracking and analyzing shots in **real-time** using computer vision. Whether practicing solo or competing with friends, it turns every session into a thrilling experience, complete with:

- **Dynamic visual effects**
- **Customizable audio feedback**
- **Detailed shooting stats and insights**

---

## **Features**

###  Real-Time Detection

Uses YOLO for **basketballs, rims, and shot events** detection.

### Shot Tracking

Captures makes, misses, and **shooting percentages**.

### Dynamic Visual Effects

Exciting animations, such as **lightning strikes** for streaks.

### Customizable Audio Feedback

Choose sound themes:

- Arena Cheers
- Dog Barks
- Minion Reactions
- Cow Moos

### Performance Analysis

Session stats, streaks (hot/cold), and **exportable session logs**.

---

## **Requirements**

To run the project, install these:

- Python 3.6-3.11 (cmu_graphics requirement)
- OpenCV
- PyTorch
- Ultralytics
- NumPy
- CMU Graphics
- Pillow
- Pathlib
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
python src/main.py
```

---

## **How to Use**

1. **Start a Session**:

   - Select **automatic/manual modes**.
   - Customize crowd sounds.
   - Begin tracking shots!

2. **Analyze in Real-Time**:

   - View annotated stats and enjoy **effects**.
   - Press 'm' to simulate a made shot, 's' to simulate a missed shot, and 'f' to end your current session and view the session summary.


3. **Session Summary**:
   - Review detailed stats and **export data**.

---


Recognized 2nd out of 441 Students at 15-112 Fall 2024 Term Project Showcase.

Youtube Link: https://youtu.be/a7-833gmraQ

---

## **Acknowledgments**
- **https://www.youtube.com/watch?v=9X3jGGnbcvU & https://automaticaddison.com/extended-kalman-filter-ekf-with-python-code-example/ for help on implementing Extended Kalman Filter** 
- **https://www.101soundboards.com/ for soundboard**
- **https://vectr.com/ for all graphic assets**
- **ChatGPT for debugging, particularly with getting pillow to work with my computer**

---

### 🎉 **Transform your basketball sessions with Assistly!** 🏀
