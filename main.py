import os
from typing import List, Optional

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy_garden.graph import Graph, MeshLinePlot

# ----------- Konfiguracja -----------
API_URL = "http://192.168.0.213:8000"   # <- poprawione (nie powielaj API_URL = API_URL = ...)
API_KEY = os.getenv("API_KEY")       # opcjonalne
HEAD = {"X-API-Key": API_KEY} if API_KEY else {}
TIMEOUT = 10
DAYS = int(os.getenv("DAYS", "60"))

# ----------- Funkcje HTTP -----------
def fetch_kpi() -> dict:
    r = requests.get(f"{API_URL}/kpi", headers=HEAD, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def fetch_series(days: int = DAYS) -> List[dict]:
    r = requests.get(f"{API_URL}/series", params={"days": days}, headers=HEAD, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

# ----------- UI komponenty -----------
class KpiCard(BoxLayout):
    label = StringProperty("")
    value = StringProperty("")
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(4), **kwargs)
        self.size_hint_y = None
        self.height = dp(80)
        self.add_widget(Label(text=self.label, font_size=dp(12), color=(0.8, 0.8, 0.8, 1)))
        self.v = Label(text=self.value, font_size=dp(22), bold=True)
        self.add_widget(self.v)
    def set_value(self, text: str):
        self.v.text = text

class Dashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(8), padding=dp(12), **kwargs)

        # Header + przyciski
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        header.add_widget(Label(text="KPI Dashboard", bold=True, font_size=dp(18)))
        self.refresh_btn = Button(text="Odśwież", size_hint=(None, None), size=(dp(90), dp(34)))
        self.refresh_btn.bind(on_press=lambda *_: self.reload())
        header.add_widget(self.refresh_btn)
        self.add_widget(header)

        # KPI
        self.kpi_grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        self.kpi_grid.bind(minimum_height=self.kpi_grid.setter("height"))
        self.k1 = KpiCard(label="Dzisiejszy zysk")
        self.k2 = KpiCard(label="MTD (narastająco)")
        self.k3 = KpiCard(label="Śr. 7 dni")
        self.k4 = KpiCard(label="Δ vs wczoraj")
        for k in (self.k1, self.k2, self.k3, self.k4):
            self.kpi_grid.add_widget(k)
        self.add_widget(self.kpi_grid)

        # Wykres
        self.graph = Graph(
            xlabel="Dni", ylabel="Zysk",
            x_ticks_minor=0, x_ticks_major=1,
            y_ticks_minor=1, y_ticks_major=1,
            y_grid_label=True, x_grid=False,
            padding=dp(10), xmin=0, xmax=30, ymin=-10, ymax=10,
            draw_border=False,
        )
        self.plot = MeshLinePlot()
        self.graph.add_plot(self.plot)
        self.add_widget(self.graph)

        # Status
        self.status = Label(text="", font_size=dp(12), color=(0.6, 0.6, 0.6, 1),
                            size_hint_y=None, height=dp(20))
        self.add_widget(self.status)

        Clock.schedule_once(lambda *_: self.reload(), 0)

    def fmt(self, x: Optional[float]) -> str:
        return "—" if x is None else f"{x:,.2f}".replace(",", " ").replace("-", "−")

    def update_graph(self, profits: List[float]):
        """Ustaw/wyczyść wykres bazując na liście profitów."""
        xs = list(range(len(profits)))
        self.plot.points = list(zip(xs, profits))
        self.graph.xmin, self.graph.xmax = 0, max(1, len(xs) - 1)
        if profits:
            ymin, ymax = min(profits), max(profits)
            if ymin == ymax:
                ymin -= 1; ymax += 1
            m = (ymax - ymin) * 0.1
            self.graph.ymin = ymin - m
            self.graph.ymax = ymax + m
        else:
            self.graph.ymin, self.graph.ymax = -10, 10

    def reload(self):
        try:
            self.status.text = f"Pobieram: {API_URL}"
            k = fetch_kpi()
            s = fetch_series(DAYS)
        except Exception as e:
            self.status.text = f"Błąd pobierania: {e}"
            for card in (self.k1, self.k2, self.k3, self.k4):
                card.set_value("—")
            self.update_graph([])   # teraz ta metoda istnieje
            return

        # Ustaw KPI
        self.k1.set_value(self.fmt(k.get("today")))
        self.k2.set_value(self.fmt(k.get("mtd")))
        self.k3.set_value(self.fmt(k.get("avg7")))
        self.k4.set_value(self.fmt(k.get("delta")))
        last_date = k.get("last_date") or "—"
        self.status.text = f"Ostatnia data: {last_date} | dni: {len(s)}"

        # Wykres
        profits = [pt.get("profit", 0.0) for pt in s]
        self.update_graph(profits)

class Root(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.do_scroll_y = True
        self.dashboard = Dashboard(size_hint_y=None)
        self.dashboard.bind(minimum_height=self.dashboard.setter("height"))
        self.add_widget(self.dashboard)

class KpiApp(App):
    def build(self):
        self.title = "KPI Dashboard"
        return Root()

if __name__ == "__main__":
    KpiApp().run()
