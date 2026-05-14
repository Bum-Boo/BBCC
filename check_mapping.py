from PyQt5.QtWidgets import QApplication
import sys

from zero2_input_inspector.application import ControllerMapperApplication

qt_app = QApplication(sys.argv)

app = ControllerMapperApplication(qt_app, start_hidden=True)
svc = app._service

snap = svc.current_snapshot()

print("=== DEVICES ===")

if not snap.device_entries:
    print("No remembered or connected devices.")

for entry in snap.device_entries:
    svc.select_device(entry.device_id)
    snap = svc.current_snapshot()
    device = snap.selected_device_profile
    if device is None:
        continue

    state = "connected" if entry.is_connected else "saved"
    print(f"\nDevice: {device.display_name} ({device.device_id}) [{state}]")

    for ap in device.app_profiles:
        if ap.process_name == "*":
            print("\n[YouTube PROFILE FOUND]")
            print(f"Name: {ap.name}")
            print(f"Active preset index: {ap.active_preset_index}")

            preset = ap.presets[ap.active_preset_index]
            print(f"Preset name: {preset.name}")

            print("\nMappings:")
            for k, v in preset.mappings.items():
                print(f"{k:12} -> {v.shortcut} ({v.label})")
