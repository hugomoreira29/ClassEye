# 👁️ ClassEye

**ClassEye** is a smart attendance system that uses **computer vision** and **face recognition** to automatically detect students from an image, mark attendance, and export results to Excel.

---

## 🚀 Features

* 📷 Face detection from images
* 👤 Face recognition of students
* ✅ Automatic attendance marking (Present/Absent)
* ⚠️ Unknown face handling
* 🔁 Duplicate detection prevention
* 📊 Export attendance to Excel
* 🖥️ Simple GUI (Tkinter)

---

## 🧠 How It Works

1. Select or capture a classroom image
2. Detect faces using computer vision
3. Recognize students using face encodings
4. Compare with student database
5. Generate attendance list
6. Export results to Excel

---

## 🏗️ Project Structure

```
ClassEye/
│
├── main.py
├── recognition/
│   └── recognizer.py
├── attendance/
│   └── attendance.py
├── ui/
│   └── app.py
├── data/
│   └── students.csv
├── output/
└── README.md
```

---

## 🛠️ Technologies Used

* Python
* OpenCV
* face_recognition
* Pandas
* Tkinter
* OpenPyXL

---

## ⚙️ Installation

```bash
git clone https://github.com/your-username/ClassEye.git
cd ClassEye
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the main application:

```bash
python main.py
```

Or launch the graphical interface:

```bash
python ui/app.py
```

---

## 🎯 Project Goal

The goal of **ClassEye** is to automate attendance tracking, reduce manual work, minimize human error, and bring smart technology into the classroom.

---

## 👨‍💻 Team Roles

* Muhammed Mabrouk — Face Recognition (Computer Vision)
* Rafael Pacheco — Attendance Logic & Data
* Hugo Moreira — Integration, UI & Testing

---

---

## 🧰 Tools & Requirements

### 💻 Software

* Python 3.x
* OpenCV
* face_recognition
* Pandas
* Tkinter
* OpenPyXL

### 🖥️ Hardware

* Raspberry Pi 5
* Raspberry Pi Camera Module
* Computer (for development/testing)

### 📁 Data

* Student images dataset
* `students.csv` file with names and IDs

---

## 💡 Future Improvements

* Real-time camera recognition
* Database integration (SQLite/MySQL)
* Web interface
* Mobile support

---

## 📌 License

This project is for educational purposes.
