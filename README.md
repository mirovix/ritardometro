# 🚆 Ritardometro – Smart Train Delay Monitor

**Ritardometro** is an automated train monitoring tool that checks departures from a selected Italian station, filters by a destination and departure time, and sends desktop notifications **20 minutes before** the train leaves — **only if it has a delay greater than your tolerance**.

It is designed to run seamlessly on **Ubuntu**, automatically starting when you log in, even if your PC isn’t always on.

---

## 📸 Example Notification

<p align="center">
  <img src="pic/notification.png" alt="Train Delay Notification" width="491"/>
</p>

---

## 🧠 Features

✅ Real-time train monitoring via [ViaggiaTreno](http://www.viaggiatreno.it/)  
✅ Filters by:
- Departure station
- Destinations
- Specific hours and minutes  
  ✅ Sends notification **20 minutes before departure**  
  ✅ Customizable **maximum delay tolerance**  
  ✅ Fully configurable with YAML  
  ✅ Auto-starts on Ubuntu login.

---

## ⚙️ Configuration (`config.yaml`)

Create a file named `config.yaml` in the project directory:

```yaml
current_station: PADOVA
destinations:
  - VENEZIA S.L.
  - VERONA PORTA NUOVA
hours:
  - "7"
  - "8"
minutes:
  - "10"
  - "40"
lead_time: 20              # minutes before departure to trigger the check
max_delay_minutes: 5       # maximum tolerated delay (notifications only for > 5 min)
```

---

## 🧩 Installation & Autostart (Ubuntu)

1️⃣ **Install Python and pip**
```bash
sudo apt update
sudo apt install -y python3 python3-pip
```

2️⃣ **Clone the project**
```bash
git clone https://github.com/mirodev/ritardometro.git
cd ritardometro
```

3️⃣ **Install dependencies**
```bash
pip install selenium beautifulsoup4 plyer webdriver-manager pyyaml
```

4️⃣ **Test the script manually**
```bash
python3 train_monitor.py
```

**Expected output example:**
```
🚆 Departures from PADOVA for VENEZIA S.L. at 07:10
07:10 | REG 2224 → VENEZIA S.L. | Delay: 5 min
```

You will also receive a desktop notification like this. 👇

<p align="center"><img src="pic/notification.png" alt="Train Notification Example" width="491"/></p>

---

### ⚙️ Autostart on Ubuntu

To make Ritardometro run automatically every day at a login, create an autostart entry.

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/train_monitor.desktop
```

Paste the following content:
```
[Desktop Entry]
Type=Application
Exec=/usr/bin/python3 /home/miro/workspace/personal/ritardometro/train_monitor.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=TrainMonitor
Comment=Start Train Monitor automatically on login
```

Make it executable:
```bash
chmod +x ~/.config/autostart/train_monitor.desktop
```

Check autostart configuration:
```bash
gnome-session-properties
```

You should see **TrainMonitor** listed and enabled.

---

### 🧪 Testing the Startup

To test manually without rebooting:
```bash
/usr/bin/python3 /home/miro/workspace/personal/ritardometro/train_monitor.py
```

To verify it started correctly:
```bash
tail -n 10 monitor.log
```

**Example output:**
```
[2025-10-08 07:20:00] TrainMonitor started successfully.
[2025-10-08 07:20:05] Checking trains for PADOVA at 07:30...
🚆 07:30 | REG 2224 → VENEZIA S.L. | Delay: 6 min
```

---

## 📅 Daily Routine

When your PC turns on, Ritardometro starts automatically.  
It reads your `config.yaml` file.  
It waits until 20 minutes before each scheduled departure.  
It checks real-time train info and notifies you if there’s a delay greater than your defined tolerance.  
Once all trains for the day have been checked, it sleeps until the next day.

---

## 🧰 Project Structure

```
ritardometro/
├── train_monitor.py       # main program
├── config.yaml            # configuration file
├── monitor.log            # daily log file
└── pic/
    └── notification.png   # example notification image
```

---

## 🪄 Author

**Miro Uango**  
💻 GitHub: [github.com/mirovix](https://github.com/mirovix)  
🚆 Created for personal use on Linux / Ubuntu systems.

---

## 🧾 License

**MIT License © 2025** — Feel free to fork, modify, and share.
