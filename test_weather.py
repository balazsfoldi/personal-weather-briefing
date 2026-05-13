import unittest
from unittest.mock import patch
import json
import io
from datetime import datetime

# Importáljuk a script függvényeit
from weather_notifier import (
    outfit_for_temp, comfort_score, weather_summary, 
    get_hourly_rain_message, get_max_in_window, get_temp_for_hour, main
)

class TestWeatherUnitLogic(unittest.TestCase):
    """MINDEN apró logikai ág letesztelése (Unit tesztek)"""

    def test_outfit_for_temp_all_levels(self):
        self.assertIn("🤷", outfit_for_temp(None))
        self.assertIn("Winter coat", outfit_for_temp(4))
        self.assertIn("Jacket", outfit_for_temp(11))
        self.assertIn("Sweater", outfit_for_temp(17))
        self.assertIn("T-shirt", outfit_for_temp(23))
        self.assertIn("Shorts", outfit_for_temp(25))

    def test_outfit_for_temp_tolerance(self):
        # JAVÍTVA: A kódod 13 fokra (18-5) "Sweater or light jacket"-et ad vissza
        self.assertIn("Sweater", outfit_for_temp(18, -5))  
        self.assertIn("T-shirt", outfit_for_temp(18, 5))

    def test_comfort_score_penalties(self):
        # Tökéletes idő
        self.assertEqual(comfort_score(25, 0, 10, 3, 25), 100)
        
        # Csak eső büntetések (40% felett -15, 70% felett -25)
        self.assertEqual(comfort_score(25, 50, 10, 3, 25), 85)
        self.assertEqual(comfort_score(25, 80, 10, 3, 25), 75)
        
        # Csak szél büntetések (25 felett -10, 40 felett -20)
        self.assertEqual(comfort_score(25, 0, 30, 3, 25), 90)
        self.assertEqual(comfort_score(25, 0, 50, 3, 25), 80)
        
        # Csak UV büntetések (6 felett -5, 8 felett -10)
        self.assertEqual(comfort_score(25, 0, 10, 7, 25), 95)
        self.assertEqual(comfort_score(25, 0, 10, 9, 25), 90)

    def test_weather_summary_combinations(self):
        self.assertEqual(weather_summary(29, 0, 10, 3), "warm")
        self.assertEqual(weather_summary(5, 0, 10, 3), "cold")
        self.assertEqual(weather_summary(20, 80, 40, 9), "pleasant and rainy and windy and very sunny")

    def test_rain_message_in_and_out_of_window(self):
        times = [f"2023-01-01T{str(i).zfill(2)}:00" for i in range(24)]
        
        # JAVÍTVA: Az előző tesztben a 20:00 óra benne volt a 7-22 ablakban!
        # Most csak 0:00-6:00 között és 23:00-kor esik.
        rain_outside = [100]*7 + [0]*16 + [100]*1
        msg1 = get_hourly_rain_message(times, rain_outside, 7, 22)
        self.assertIn("No umbrella needed", msg1)

        # Esik délben (12:00)
        rain_inside = [0]*12 + [100] + [0]*11
        msg2 = get_hourly_rain_message(times, rain_inside, 7, 22)
        self.assertIn("Heavy rain expected around 12:00", msg2)


class TestWeatherMainIntegrationScenarios(unittest.TestCase):
    """TELJES SCENARIÓK TESZTELÉSE MOCKOLVA"""

    def generate_fake_json(self, t_morn=20, t_aft=20, t_eve=20, 
                           uv=5, sun_hours=5, wind_day=10, wind_eve=10, 
                           rain_night=0, rain_day=0, rain_eve=0):
        sun_seconds = sun_hours * 3600
        temps = [t_morn]*12 + [t_aft]*6 + [t_eve]*6
        winds = [wind_day]*18 + [wind_eve]*6
        rains = [rain_night]*7 + [rain_day]*12 + [rain_eve]*5

        return {
            "current": {"temperature_2m": t_morn, "apparent_temperature": t_morn, "relative_humidity_2m": 50},
            "daily": {
                "temperature_2m_max": [max(temps)], "temperature_2m_min": [min(temps)],
                "precipitation_probability_max": [max(rains)], "wind_speed_10m_max": [max(winds)],
                "uv_index_max": [uv], "sunshine_duration": [sun_seconds]
            },
            "hourly": {
                "time": [f"2023-01-01T{str(i).zfill(2)}:00" for i in range(24)],
                "temperature_2m": temps, "apparent_temperature": temps,
                "precipitation_probability": rains, "wind_speed_10m": winds
            }
        }

    def run_main_and_get_output(self, mock_urlopen, json_data):
        fake_response = io.BytesIO(json.dumps(json_data).encode("utf-8"))
        mock_urlopen.return_value.__enter__.return_value = fake_response
        
        with patch('sys.argv', ['weather_notifier.py', '--morning', '8', '--afternoon', '17', '--evening', '21', '--channel', 'test_channel']):
            with patch('sys.stdout', new=io.StringIO()):
                main()
        
        ntfy_request = mock_urlopen.call_args_list[1][0][0]
        return ntfy_request.data.decode('utf-8')

    @patch('urllib.request.urlopen')
    def test_scenario_perfect_day(self, mock_urlopen):
        data = self.generate_fake_json(t_morn=20, t_aft=22, t_eve=19)
        msg = self.run_main_and_get_output(mock_urlopen, data)
        self.assertIn("No special warnings today.", msg)

    @patch('urllib.request.urlopen')
    def test_scenario_night_rain_ignored(self, mock_urlopen):
        data = self.generate_fake_json(rain_night=90, rain_day=0, rain_eve=0)
        msg = self.run_main_and_get_output(mock_urlopen, data)
        self.assertIn("No umbrella needed during the day", msg)

    @patch('urllib.request.urlopen')
    def test_scenario_sunglasses_glare_vs_uv(self, mock_urlopen):
        data = self.generate_fake_json(uv=3, sun_hours=8.5)
        msg = self.run_main_and_get_output(mock_urlopen, data)
        self.assertIn("SUNGLASSES recommended!", msg)
        self.assertNotIn("sunscreen needed", msg)

    @patch('urllib.request.urlopen')
    def test_scenario_layering(self, mock_urlopen):
        # Reggel 8 fok, délután 22 fok -> különbség > 10 fok
        data = self.generate_fake_json(t_morn=8, t_aft=22, t_eve=15)
        msg = self.run_main_and_get_output(mock_urlopen, data)
        self.assertIn("Dress in layers!", msg)

    @patch('urllib.request.urlopen')
    def test_scenario_evening_ruined(self, mock_urlopen):
        data = self.generate_fake_json(t_morn=25, t_aft=25, t_eve=8, wind_day=10, wind_eve=40, rain_day=0, rain_eve=80)
        msg = self.run_main_and_get_output(mock_urlopen, data)
        self.assertIn("Rain is likely during your evening plans", msg)
        self.assertIn("Bring a jacket for the evening!", msg)


if __name__ == "__main__":
    unittest.main()
