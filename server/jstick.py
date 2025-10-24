import threading
import time
from inputs import get_gamepad, devices

DEADZONE = 5000

AXIS_COMMANDS = {
    'ABS_X': ('MOVE_LEFT', 'MOVE_RIGHT'),
    'ABS_Y': ('MOVE_UP', 'MOVE_DOWN'),
}

BUTTON_COMMANDS = {
    'BTN_SOUTH': 'FIRE',
    'BTN_EAST': 'JUMP',
    'BTN_NORTH': 'RELOAD',
    'BTN_WEST': 'SPECIAL',
}


class JoystickListener:
    def __init__(self, axis_map=None, button_map=None, deadzone=None, callback=None, poll_interval=1):
        self.axis_map = axis_map or AXIS_COMMANDS
        self.button_map = button_map or BUTTON_COMMANDS
        self.deadzone = deadzone if deadzone is not None else DEADZONE
        self.callback = callback
        self.poll_interval = poll_interval

        self.running = False
        self.thread = None
        self.connected_gamepads = set()

        # Track last axis state to detect release
        self.axis_state = {}

    def _poll_gamepads(self):
        return set(d.name for d in devices.gamepads)

    def _listen_loop(self):
        while self.running:
            current_gamepads = self._poll_gamepads()
            new_gamepads = current_gamepads - self.connected_gamepads
            removed_gamepads = self.connected_gamepads - current_gamepads

            if new_gamepads:
                print(f"🟢 Gamepads connected: {list(new_gamepads)}")
            if removed_gamepads:
                print(f"🔴 Gamepads disconnected: {list(removed_gamepads)}")

            self.connected_gamepads = current_gamepads

            if self.connected_gamepads:
                try:
                    events = get_gamepad()
                    for event in events:
                        # Axis events
                        if event.ev_type == "Absolute" and event.code in self.axis_map:
                            prev_state = self.axis_state.get(event.code, 0)
                            neg_cmd, pos_cmd = self.axis_map[event.code]

                            # Movement detection
                            if event.state < -self.deadzone:
                                if self.callback:
                                    self.callback(neg_cmd)
                            elif event.state > self.deadzone:
                                if self.callback:
                                    self.callback(pos_cmd)

                            # Release detection: crossing deadzone back to neutral
                            if abs(event.state) <= self.deadzone and abs(prev_state) > self.deadzone:
                                release_cmd = f"{event.code}_RELEASED"
                                if self.callback:
                                    self.callback(release_cmd)

                            # Update last state
                            self.axis_state[event.code] = event.state

                        # Button events
                        elif event.ev_type == "Key" and event.code in self.button_map:
                            # Press
                            if event.state == 1 and self.callback:
                                self.callback(self.button_map[event.code])
                            # Release
                            elif event.state == 0 and self.callback:
                                self.callback(f"{self.button_map[event.code]}_RELEASED")

                except Exception:
                    pass

            time.sleep(self.poll_interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🟢 Joystick listener started.")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join()
        print("🔴 Joystick listener stopped.")
