from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

import dearpygui.dearpygui as dpg
import pytz


@dataclass
class WorldClock:
    timezone: str
    label: str
    text_tag: str = field(default="")


@dataclass
class AlertRule:
    name: str
    interval_minutes: int
    color: tuple[int, int, int]
    last_trigger_at: float = field(default_factory=time.time)
    next_due_tag: str = field(default="")


class PyClocks:
    def __init__(self) -> None:
        self.world_clocks: List[WorldClock] = [
            WorldClock("UTC", "🌍 UTC"),
            WorldClock("America/New_York", "🗽 New York"),
            WorldClock("Asia/Tokyo", "🗼 Tokyo"),
        ]
        self.stopwatch_running = False
        self.stopwatch_start = 0.0
        self.stopwatch_elapsed = 0.0
        self.stopwatch_laps: List[str] = []
        self.alert_rules: List[AlertRule] = [
            AlertRule("👀 Close eyes break", 30, (255, 0, 255)),
            AlertRule("🚶 2 minute walk", 60, (0, 255, 255)),
        ]
        self.active_glow_until = 0.0

        self._clock_group_tag = "clock_rows"
        self._laps_tag = "lap_list"
        self._alerts_tag = "alert_rows"

    @staticmethod
    def _fmt_duration(total_seconds: float) -> str:
        minutes, seconds = divmod(int(total_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        millis = int((total_seconds % 1) * 100)
        return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:02}"

    def _world_time_text(self, timezone: str) -> str:
        zone = pytz.timezone(timezone)
        now = datetime.now(zone)
        return now.strftime("%a, %d %b %Y  %H:%M:%S")

    def _setup_modern_theme(self) -> None:
        with dpg.theme(tag="global_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 14)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 14, 12)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 8)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)

                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (18, 21, 31), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 30, 42), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (32, 36, 52), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (53, 64, 94), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (67, 99, 220), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (92, 125, 242), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (49, 79, 197), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (38, 43, 58), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (50, 58, 82), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (64, 73, 103), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (72, 82, 112), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Separator, (85, 97, 131), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (226, 233, 248), category=dpg.mvThemeCat_Core)

        with dpg.theme(tag="card_theme"):
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_style(dpg.mvStyleVar_ChildBorderSize, 1)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (29, 36, 50), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (84, 98, 139), category=dpg.mvThemeCat_Core)

        dpg.bind_theme("global_theme")

    def _render_clock_rows(self) -> None:
        dpg.delete_item(self._clock_group_tag, children_only=True)
        for clock in self.world_clocks:
            clock.text_tag = f"clock_{clock.label}_{clock.timezone}".replace(" ", "_")
            with dpg.child_window(parent=self._clock_group_tag, height=72, border=True):
                dpg.bind_item_theme(dpg.last_item(), "card_theme")
                dpg.add_text(clock.label, color=(170, 198, 255))
                dpg.add_text(clock.timezone, color=(129, 143, 180))
                dpg.add_text(self._world_time_text(clock.timezone), tag=clock.text_tag, color=(245, 250, 255))

    def _render_alert_rows(self) -> None:
        dpg.delete_item(self._alerts_tag, children_only=True)
        for i, rule in enumerate(self.alert_rules):
            rule.next_due_tag = f"next_due_{i}"
            with dpg.child_window(parent=self._alerts_tag, height=62, border=True):
                dpg.bind_item_theme(dpg.last_item(), "card_theme")
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{rule.name} • every {rule.interval_minutes} min", color=(190, 222, 255))
                    dpg.add_spacer(width=15)
                    dpg.add_text("next in --", tag=rule.next_due_tag, color=rule.color)

    def add_world_clock(self) -> None:
        timezone = dpg.get_value("timezone_input").strip()
        label = dpg.get_value("label_input").strip() or timezone
        if timezone not in pytz.all_timezones:
            dpg.set_value("clock_error", f"Unknown timezone: {timezone}")
            return
        self.world_clocks.append(WorldClock(timezone, label))
        dpg.set_value("clock_error", "")
        self._render_clock_rows()

    def add_alert_rule(self) -> None:
        name = dpg.get_value("alert_name_input").strip()
        minutes_raw = dpg.get_value("alert_interval_input")
        if not name:
            dpg.set_value("alert_error", "Alert name is required")
            return
        if minutes_raw <= 0:
            dpg.set_value("alert_error", "Interval must be greater than 0")
            return
        palette = [(255, 80, 80), (80, 255, 80), (80, 180, 255), (255, 80, 255), (255, 200, 80)]
        color = palette[len(self.alert_rules) % len(palette)]
        self.alert_rules.append(AlertRule(name, int(minutes_raw), color))
        dpg.set_value("alert_error", "")
        self._render_alert_rows()

    def start_stopwatch(self) -> None:
        if not self.stopwatch_running:
            self.stopwatch_running = True
            self.stopwatch_start = time.time() - self.stopwatch_elapsed

    def pause_stopwatch(self) -> None:
        if self.stopwatch_running:
            self.stopwatch_running = False
            self.stopwatch_elapsed = time.time() - self.stopwatch_start

    def reset_stopwatch(self) -> None:
        self.stopwatch_running = False
        self.stopwatch_start = 0.0
        self.stopwatch_elapsed = 0.0
        self.stopwatch_laps.clear()
        dpg.delete_item(self._laps_tag, children_only=True)

    def lap_stopwatch(self) -> None:
        current = time.time() - self.stopwatch_start if self.stopwatch_running else self.stopwatch_elapsed
        lap_text = self._fmt_duration(current)
        self.stopwatch_laps.append(lap_text)
        dpg.add_text(f"Lap {len(self.stopwatch_laps):02}  •  {lap_text}", parent=self._laps_tag, color=(196, 232, 255))

    def update(self) -> None:
        now = time.time()
        for clock in self.world_clocks:
            if clock.text_tag and dpg.does_item_exist(clock.text_tag):
                dpg.set_value(clock.text_tag, self._world_time_text(clock.timezone))

        elapsed = time.time() - self.stopwatch_start if self.stopwatch_running else self.stopwatch_elapsed
        dpg.set_value("stopwatch_display", self._fmt_duration(elapsed))

        for rule in self.alert_rules:
            elapsed_sec = now - rule.last_trigger_at
            due_in = max(0, rule.interval_minutes * 60 - elapsed_sec)
            if rule.next_due_tag and dpg.does_item_exist(rule.next_due_tag):
                dpg.set_value(rule.next_due_tag, f"next in {int(due_in // 60):02}:{int(due_in % 60):02}")
            if elapsed_sec >= rule.interval_minutes * 60:
                rule.last_trigger_at = now
                self.active_glow_until = now + 8.0
                dpg.set_value("alert_status", f"ALERT: {rule.name}")

        pulse = (45, 60, 95)
        if now < self.active_glow_until:
            pulse = (255, 0, 180) if int((now * 8) % 2) else (0, 240, 255)
        dpg.bind_item_theme("alerts_window", self._make_alert_theme(pulse))
        if now >= self.active_glow_until:
            dpg.set_value("alert_status", "All alerts idle")

    def _make_alert_theme(self, border_color: tuple[int, int, int]):
        theme_tag = f"alerts_theme_{border_color[0]}_{border_color[1]}_{border_color[2]}"
        if dpg.does_item_exist(theme_tag):
            return theme_tag
        with dpg.theme(tag=theme_tag):
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_color(dpg.mvThemeCol_Border, (*border_color, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 4, category=dpg.mvThemeCat_Core)
        return theme_tag

    def build_ui(self) -> None:
        dpg.create_context()
        self._setup_modern_theme()

        with dpg.window(label="🌐 World Clocks", width=560, height=470, pos=(20, 20)):
            dpg.add_text("Track global time zones", color=(172, 198, 255))
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="timezone_input", hint="Timezone (e.g. Europe/Berlin)", width=250)
                dpg.add_input_text(tag="label_input", hint="Label", width=130)
                dpg.add_button(label="Add Clock", callback=lambda: self.add_world_clock())
            dpg.add_text("", tag="clock_error", color=(255, 120, 120))
            dpg.add_separator()
            dpg.add_child_window(tag=self._clock_group_tag, autosize_x=True, height=350, border=False)
            self._render_clock_rows()

        with dpg.window(label="⏱️ Stopwatch", width=560, height=360, pos=(20, 510)):
            dpg.add_text("Precision timer with lap tracking", color=(172, 198, 255))
            dpg.add_spacer(height=2)
            dpg.add_text("00:00:00.00", tag="stopwatch_display", color=(255, 235, 167))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Start", callback=lambda: self.start_stopwatch(), width=120)
                dpg.add_button(label="Pause", callback=lambda: self.pause_stopwatch(), width=120)
                dpg.add_button(label="Lap", callback=lambda: self.lap_stopwatch(), width=120)
                dpg.add_button(label="Reset", callback=lambda: self.reset_stopwatch(), width=120)
            dpg.add_separator()
            dpg.add_child_window(tag=self._laps_tag, height=230, border=True)
            dpg.bind_item_theme(self._laps_tag, "card_theme")

        with dpg.window(label="🔔 Wellness Alerts", tag="alerts_window", width=600, height=850, pos=(610, 20)):
            dpg.add_text("All alerts idle", tag="alert_status", color=(255, 220, 80))
            dpg.add_text("Healthy reminder system", color=(172, 198, 255))
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="alert_name_input", hint="Custom alert name", width=250)
                dpg.add_input_int(tag="alert_interval_input", default_value=45, min_value=1, min_clamped=True, width=110)
                dpg.add_button(label="Add Alert", callback=lambda: self.add_alert_rule())
            dpg.add_text("", tag="alert_error", color=(255, 120, 120))
            dpg.add_separator()
            dpg.add_child_window(tag=self._alerts_tag, autosize_x=True, height=700, border=False)
            self._render_alert_rows()

        dpg.create_viewport(title="py-clocks • DearPyGui", width=1240, height=920)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self.update()
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


if __name__ == "__main__":
    PyClocks().build_ui()
