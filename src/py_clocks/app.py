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


class WorldClocksWindow:
    def __init__(self) -> None:
        self.timezone_choices = sorted(pytz.all_timezones)
        self.clocks: List[WorldClock] = [
            WorldClock("Asia/Kolkata", "Kolkata"),
            WorldClock("America/New_York", "New York"),
            WorldClock("Asia/Tokyo", "Tokyo"),
        ]
        self.clock_group_tag = "clock_rows"

    def world_time_text(self, timezone: str) -> str:
        zone = pytz.timezone(timezone)
        return datetime.now(zone).strftime("%a, %d %b %Y  %H:%M:%S")

    def render_rows(self) -> None:
        dpg.delete_item(self.clock_group_tag, children_only=True)
        for i, clock in enumerate(self.clocks):
            clock.text_tag = f"clock_{clock.label}_{clock.timezone}".replace(" ", "_")
            with dpg.group(parent=self.clock_group_tag):
                dpg.add_text(clock.label, color=(170, 198, 255))
                dpg.add_text(f"{clock.timezone} | {self.world_time_text(clock.timezone)}", tag=clock.text_tag, color=(245, 250, 255))
                if i < len(self.clocks) - 1:
                    dpg.add_separator()

    def filter_timezones(self) -> None:
        query = dpg.get_value("timezone_search").strip().lower()
        matches = self.timezone_choices[:300] if not query else [tz for tz in self.timezone_choices if query in tz.lower()][:300]
        dpg.configure_item("timezone_combo", items=matches)
        if matches:
            dpg.set_value("timezone_combo", matches[0])

    def add_clock(self) -> None:
        combo_choice = dpg.get_value("timezone_combo").strip()
        typed = dpg.get_value("timezone_search").strip()
        timezone = combo_choice if combo_choice in self.timezone_choices else typed
        label = dpg.get_value("label_input").strip() or timezone.split("/")[-1].replace("_", " ")
        if timezone not in self.timezone_choices:
            dpg.set_value("clock_error", f"Unknown timezone: {timezone}")
            return
        self.clocks.append(WorldClock(timezone, label))
        dpg.set_value("clock_error", "")
        self.render_rows()

    def update(self) -> None:
        for clock in self.clocks:
            if clock.text_tag and dpg.does_item_exist(clock.text_tag):
                dpg.set_value(clock.text_tag, f"{clock.timezone} | {self.world_time_text(clock.timezone)}")

    def build(self) -> None:
        with dpg.window(label="World Clocks", width=560, height=430, pos=(10, 10), no_scrollbar=False):
            dpg.add_text("Track global time zones", color=(172, 198, 255))
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="timezone_search", hint="Type timezone name", width=150, callback=lambda: self.filter_timezones())
                dpg.add_combo(self.timezone_choices[:300], tag="timezone_combo", width=150)
                dpg.add_input_text(tag="label_input", hint="Optional label", width=130)
                dpg.add_button(label="Add", callback=lambda: self.add_clock(), width=70)
            dpg.add_text("", tag="clock_error", color=(255, 120, 120))
            dpg.add_child_window(tag=self.clock_group_tag, autosize_x=True, height=280, border=False, no_scrollbar=True)
            self.render_rows()


class StopwatchWindow:
    def __init__(self) -> None:
        self.running = False
        self.start_time = 0.0
        self.elapsed = 0.0
        self.laps: List[str] = []
        self.laps_tag = "lap_list"

    @staticmethod
    def fmt_duration(total_seconds: float) -> str:
        minutes, seconds = divmod(int(total_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        millis = int((total_seconds % 1) * 100)
        return f"{hours:02}:{minutes:02}:{seconds:02}.{millis:02}"

    def start(self) -> None:
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.elapsed

    def pause(self) -> None:
        if self.running:
            self.running = False
            self.elapsed = time.time() - self.start_time

    def reset(self) -> None:
        self.running = False
        self.start_time = 0.0
        self.elapsed = 0.0
        self.laps.clear()
        dpg.delete_item(self.laps_tag, children_only=True)

    def lap(self) -> None:
        current = time.time() - self.start_time if self.running else self.elapsed
        text = self.fmt_duration(current)
        self.laps.append(text)
        dpg.add_text(f"Lap {len(self.laps):02} - {text}", parent=self.laps_tag, color=(196, 232, 255))

    def update(self) -> None:
        current = time.time() - self.start_time if self.running else self.elapsed
        dpg.set_value("stopwatch_display", self.fmt_duration(current))

    def build(self) -> None:
        with dpg.window(label="Stopwatch", width=560, height=300, pos=(10, 450), no_scrollbar=True):
            dpg.add_text("Precision timer with lap tracking", color=(172, 198, 255))
            dpg.add_text("00:00:00.00", tag="stopwatch_display", color=(255, 235, 167))
            with dpg.group(horizontal=True):
                dpg.add_button(label="Start", callback=lambda: self.start(), width=110)
                dpg.add_button(label="Pause", callback=lambda: self.pause(), width=110)
                dpg.add_button(label="Lap", callback=lambda: self.lap(), width=110)
                dpg.add_button(label="Reset", callback=lambda: self.reset(), width=110)
            dpg.add_child_window(tag=self.laps_tag, height=150, border=True)


class AlertsWindow:
    def __init__(self) -> None:
        self.alert_rules: List[AlertRule] = [
            AlertRule("Close eyes break", 30, (255, 0, 255)),
            AlertRule("2 minute walk", 60, (0, 255, 255)),
        ]
        self.alerts_tag = "alert_rows"
        self.active_glow_until = 0.0

    def render_rows(self) -> None:
        dpg.delete_item(self.alerts_tag, children_only=True)
        for i, rule in enumerate(self.alert_rules):
            rule.next_due_tag = f"next_due_{i}"
            with dpg.child_window(parent=self.alerts_tag, height=54, border=True):
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{rule.name} every {rule.interval_minutes} min", color=(190, 222, 255))
                    dpg.add_spacer(width=16)
                    dpg.add_text("next in --", tag=rule.next_due_tag, color=rule.color)

    def add_alert(self) -> None:
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
        self.render_rows()

    def update(self) -> None:
        now = time.time()
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
        dpg.bind_item_theme("alerts_window", self.make_alert_theme(pulse))
        if now >= self.active_glow_until:
            dpg.set_value("alert_status", "All alerts idle")

    def make_alert_theme(self, border_color: tuple[int, int, int]):
        theme_tag = f"alerts_theme_{border_color[0]}_{border_color[1]}_{border_color[2]}"
        if dpg.does_item_exist(theme_tag):
            return theme_tag
        with dpg.theme(tag=theme_tag):
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_color(dpg.mvThemeCol_Border, (*border_color, 255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 4, category=dpg.mvThemeCat_Core)
        return theme_tag

    def build(self) -> None:
        with dpg.window(label="Wellness Alerts", tag="alerts_window", width=620, height=740, pos=(590, 10), no_scrollbar=True):
            dpg.add_text("All alerts idle", tag="alert_status", color=(255, 220, 80))
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="alert_name_input", hint="Custom alert name", width=240)
                dpg.add_input_int(tag="alert_interval_input", default_value=45, min_value=1, min_clamped=True, width=100)
                dpg.add_button(label="Add Alert", callback=lambda: self.add_alert(), width=100)
            dpg.add_text("", tag="alert_error", color=(255, 120, 120))
            dpg.add_child_window(tag=self.alerts_tag, autosize_x=True, height=590, border=False)
            self.render_rows()


class PyClocks:
    def __init__(self) -> None:
        self.world_clocks_window = WorldClocksWindow()
        self.stopwatch_window = StopwatchWindow()
        self.alerts_window = AlertsWindow()

    def setup_theme(self) -> None:
        with dpg.theme(tag="global_theme"):
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 10)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 7)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (18, 21, 31), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 30, 42), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (32, 36, 52), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (53, 64, 94), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (67, 99, 220), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (92, 125, 242), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (49, 79, 197), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (38, 43, 58), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (226, 233, 248), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (72, 82, 112), category=dpg.mvThemeCat_Core)
        dpg.bind_theme("global_theme")

    def update(self) -> None:
        self.world_clocks_window.update()
        self.stopwatch_window.update()
        self.alerts_window.update()

    def build_ui(self) -> None:
        dpg.create_context()
        self.setup_theme()

        self.world_clocks_window.build()
        self.stopwatch_window.build()
        self.alerts_window.build()

        dpg.create_viewport(title="py-clocks - DearPyGui", width=1230, height=800, resizable=False)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        while dpg.is_dearpygui_running():
            self.update()
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


if __name__ == "__main__":
    PyClocks().build_ui()
