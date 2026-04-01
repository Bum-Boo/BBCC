from PyQt5.QtWidgets import QApplication
import sys

from zero2_input_inspector.application import ControllerMapperApplication

qt_app = QApplication(sys.argv)

app = ControllerMapperApplication(qt_app, start_hidden=True)
svc = app._service

snap = svc.current_snapshot()

print("=== DEVICES ===")

for d in snap.devices:
    print(f"\nDevice: {d.display_name} ({d.device_id})")

    for ap in d.app_profiles:
        if ap.process_name == "*":
            print("\n[YouTube PROFILE FOUND]")
            print(f"Name: {ap.name}")
            print(f"Active preset index: {ap.active_preset_index}")

            preset = ap.presets[ap.active_preset_index]
            print(f"Preset name: {preset.name}")

            print("\nMappings:")
            for k, v in preset.mappings.items():
                print(f"{k:12} -> {v.shortcut} ({v.label})")
