# 🌤️ Personal Weather Briefing (ntfy)

A lightweight, highly customizable Python script that sends a personalized daily weather briefing directly to your phone using [ntfy.sh](https://ntfy.sh/). 

Instead of burying you in raw numbers, this script gives you **action-oriented advice**: it tells you exactly what to wear for your specific commute times, warns you if you need an umbrella, and reminds you to grab sunglasses if the UV index is high.

**Best of all: It uses ZERO external dependencies.** Just standard Python 3.

## ✨ Features
*   **Action-Oriented:** Prioritizes what you *need to do* (grab an umbrella, dress in layers) over raw meteorological data.
*   **Highly Personalized:** Set your exact commute hours, your name, and even your personal **cold tolerance**.
*   **No App Required:** Sends push notifications via `ntfy.sh`.
*   **Zero Dependencies:** Uses built-in Python libraries (`urllib`, `json`, `datetime`, `argparse`). No `pip install` required!

---

## 🚀 Installation & Setup

1. **Download the ntfy app** on your iOS or Android device.
2. **Subscribe to a new topic** in the app. Pick a unique, secret name (e.g., `alex_weather_secret_99`).
3. **Clone this repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/personal-weather-briefing.git](https://github.com/YOUR_USERNAME/personal-weather-briefing.git)
   cd personal-weather-briefing
   
```

---

## 🛠️ Usage & Configuration

You can run the script from the command line and pass arguments to customize your daily briefing. 

### Basic Usage
```bash
python weather_notifier.py --channel "your_secret_channel_name"
```

### Advanced / Personalized Usage
You can customize the location, your daily schedule, and how you perceive temperature.

```bash
python weather_notifier.py \
    --channel "your_secret_channel_name" \
    --name "Alex" \
    --city "London" \
    --lat "51.5074" \
    --lon "-0.1278" \
    --morning 7 \
    --afternoon 18 \
    --tolerance -5
```

### 🎛️ Command Line Arguments

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--channel` | *None* | Your ntfy.sh channel name. (Alternatively, set the `NTFY_CHANNEL` environment variable). |
| `--lat` | `47.4979` | Latitude of your city. |
| `--lon` | `19.0402` | Longitude of your city. |
| `--city` | `Budapest` | Name of the city (used in the notification title). |
| `--name` | `Boss` | The name used to greet you in the message. |
| `--morning` | `8` | The hour (0-23) you leave for work/school. |
| `--afternoon`| `17` | The hour (0-23) you usually head back home. |
| `--evening` | `21` | The hour (0-23) of your evening plans/walk. |
| `--tolerance`| `0` | Your cold tolerance (see guide below). |

### 🌡️ Cold Tolerance Guide (`--tolerance`)
Not sure what to set for your tolerance? The script calculates a "perceived outfit temperature" by adding this number to the actual temperature. 

Here is a quick reference to help you choose:

*   `+5` **("Viking" mode):** You run hot. You wear shorts when others wear jackets. The script will suggest t-shirts much earlier.
*   `+2` **(Warm-blooded):** You prefer fewer layers and rarely feel the chill.
*   `0` **(Default):** Standard clothing suggestions based on the exact temperature:
    *   **Below 5°C:** 🧥 Winter coat, beanie, scarf
    *   **5°C to 11°C:** 🧥 Jacket / Coat
    *   **12°C to 17°C:** 🧥 Sweater or light jacket
    *   **18°C to 23°C:** 👕 T-shirt / Long-sleeve
    *   **24°C and above:** 🩳 Shorts, light summer clothes
*   `-3` **(Easily chilled):** You reach for a sweater as soon as a cloud covers the sun.
*   `-5` **(Always freezing):** You sleep in fluffy socks. The script will tell you to grab a winter coat and a scarf much earlier than a standard weather app would.

---

## 🤖 Automation Guide

To get a true "Daily Briefing", you should automate this script to run every morning before you wake up (e.g., at 6:30 AM).

### 🐧 Linux (Using Cron)

1. Open your terminal and edit your crontab:
   ```bash
   crontab -e
   
```
2. Add the following line to run the script every day at 6:30 AM. Make sure to provide the **absolute paths** to both Python and your script:
   ```bash
   30 6 * * * /usr/bin/python3 /home/yourusername/personal-weather-briefing/weather_notifier.py --channel "your_secret_channel" --name "Alex" --morning 7 --tolerance -5
   
```
3. Save and exit. Cron will now handle the rest!

*Tip: If you prefer using Environment Variables instead of the `--channel` flag, you can structure your cron job like this:*
```bash
30 6 * * * export NTFY_CHANNEL="your_secret_channel" && /usr/bin/python3 /path/to/weather_notifier.py --name "Alex"
```

### 🪟 Windows (Using Task Scheduler)

1. Press `Win + S`, type **Task Scheduler**, and open it.
2. On the right panel, click **Create Basic Task...**
3. **Name:** `Daily Weather Briefing`. Click Next.
4. **Trigger:** Select **Daily**. Set the time you want it to run (e.g., `06:30:00`).
5. **Action:** Select **Start a program**.
6. **Program/script:** Type `python` (or the full path to your `python.exe` if it's not in your PATH, e.g., `C:\Python39\python.exe`).
7. **Add arguments:** Paste your customized flags here. Example:
   ```text
   weather_notifier.py --channel "your_secret_channel" --name "Alex" --city "London"
   
```
8. **Start in:** Paste the exact path to the folder where you cloned the script (e.g., `C:\Users\YourName\Scripts\personal-weather-briefing\`). *Do not put quotes around this path.*
9. Click **Finish**. 

*Optional: To make sure it runs quietly in the background without popping up a console window, you can use `pythonw.exe` instead of `python.exe` in step 6.*

---

## 📄 License
This project is open-source. Feel free to fork, modify, and improve it!
