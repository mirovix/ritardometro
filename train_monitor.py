import yaml
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from plyer import notification


class ConfigLoader:
    def __init__(self, path="config.yaml"):
        self.path = path

    def load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {
            "current_station": data.get("current_station", "").upper(),
            "destinations": [d.upper() for d in data.get("destinations", [])],
            "hours": [str(h).zfill(2) for h in data.get("hours", [])],
            "minutes": [str(m).zfill(2) for m in data.get("minutes", [])],
            "lead_time": int(data.get("lead_time", 20)),
            "max_delay": int(data.get("max_delay_minutes", 0))
        }


class TrainMonitor:
    def __init__(self, station, destinations, hours, minutes, lead_time, max_delay, log_file="monitor.log"):
        self.station = station
        self.destinations = destinations
        self.hours = hours
        self.minutes = minutes
        self.lead_time = lead_time
        self.max_delay = max_delay
        self.log_file = log_file
        self.driver = None
        self._init_log()

    def run(self):
        while True:
            next_activation = self._get_next_activation()
            if not next_activation:
                self._log("All trains checked today. Waiting for tomorrow...")
                self._wait_until_next_day()
                continue

            self._wait_until_activation(next_activation)
            self._check_trains()

    def _get_next_activation(self):
        now = datetime.now()
        today = now.date()
        times = []

        for h in self.hours:
            for m in self.minutes:
                departure = datetime.strptime(f"{h}:{m}", "%H:%M").replace(
                    year=today.year, month=today.month, day=today.day
                )
                activation = departure - timedelta(minutes=self.lead_time)
                if activation > now:
                    times.append(activation)

        return min(times) if times else None

    def _wait_until_next_day(self):
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        seconds_until_tomorrow = (tomorrow - datetime.now()).total_seconds()
        self._log("Sleeping until tomorrow...")
        time.sleep(seconds_until_tomorrow)

    def _wait_until_activation(self, activation_time):
        now = datetime.now()
        if activation_time > now:
            wait_seconds = (activation_time - now).total_seconds()
            activation_str = activation_time.strftime("%H:%M")
            self._log(f"Waiting until {activation_str} to check trains ({int(wait_seconds/60)} min)...")
            time.sleep(wait_seconds)

    def _check_trains(self):
        check_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._log(f"Checking trains for {self.station} at {check_time}...")
        self._setup_driver()
        try:
            self._open_page()
            self._search_station()
            trains = self._parse_trains()
            filtered = self._filter_trains(trains)
            self._notify_delays(filtered)
            self._print_and_log_results(filtered)
        finally:
            self.driver.quit()

    def _setup_driver(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    def _open_page(self):
        self.driver.get("http://www.viaggiatreno.it/infomobilita/index.jsp")
        self._click(By.ID, "bottone-cerca")

    def _search_station(self):
        field = self._wait_clickable(By.ID, "dati-treno")
        field.click()
        field.clear()
        field.send_keys(self.station)
        self._wait_present(By.CSS_SELECTOR, ".ui-menu-item").click()
        self._click(By.XPATH, "//input[@type='submit' and @value='Cerca']")

    def _parse_trains(self):
        self._wait_present(By.CSS_SELECTOR, ".contenitore-partenze tbody tr")
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        rows = soup.select(".contenitore-partenze tbody tr")
        trains = []
        for r in rows:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]
            if len(cols) < 7:
                continue
            trains.append({
                "code": cols[0],
                "destination": cols[1].upper(),
                "time": cols[2],
                "delay": cols[6]
            })
        return trains

    def _filter_trains(self, trains):
        result = []
        for t in trains:
            if ":" not in t["time"]:
                continue
            hour, minute = t["time"].split(":")
            if self._match_time(hour, minute) and self._match_destination(t["destination"]):
                result.append(t)
        return result

    def _notify_delays(self, trains):
        for t in trains:
            delay = t["delay"]
            if not delay or "min" not in delay.lower():
                continue
            digits = "".join(ch for ch in delay if ch.isdigit())
            if digits and int(digits) > self.max_delay:
                notification.notify(
                    title="🚆 Train Delay Alert",
                    message=f"{t['code']} | Departure: {t['time']} | Delay: {t['delay']}",
                    timeout=10
                )
                self._log(f"NOTIFICATION SENT: {t['code']} | Delay {t['delay']}")

    def _print_and_log_results(self, trains):
        label_dest = ", ".join(self.destinations)
        header = f"\n🚆 Departures from {self.station} for {label_dest}\n"
        print(header)
        self._log(header.strip())

        if trains:
            for t in trains:
                line = f"{t['time']} | {t['code']} → {t['destination']} | Delay: {t['delay']}"
                print(line)
                self._log(line)
        else:
            print("No trains found.")
            self._log("No trains found.")

    def _click(self, by, selector):
        self._wait_clickable(by, selector).click()

    def _wait_clickable(self, by, selector, timeout=15):
        return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, selector)))

    def _wait_present(self, by, selector, timeout=15):
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, selector)))

    def _match_time(self, hour, minute):
        h = not self.hours or hour in self.hours
        m = not self.minutes or minute in self.minutes
        return h and m

    def _match_destination(self, destination):
        return any(d in destination for d in self.destinations)

    def _init_log(self):
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("=== Train Monitor Log ===\n")

    def _log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    dir_config = os.path.dirname(os.path.abspath(__file__))
    path_config = os.path.join(dir_config, "config.yaml")
    path_log = os.path.join(dir_config, "monitor.log")
    config = ConfigLoader(path=path_config).load()
    monitor = TrainMonitor(
        station=config["current_station"],
        destinations=config["destinations"],
        hours=config["hours"],
        minutes=config["minutes"],
        lead_time=config["lead_time"],
        max_delay=config["max_delay"],
        log_file=path_log
    )
    monitor.run()
