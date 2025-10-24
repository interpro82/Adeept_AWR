import threading
import time
from inputs import get_gamepad, devices

# -----------------------------
# Configurable mappings
# -----------------------------
DEADZONE = 5000

AXIS_MAP = {
    'ABS_X': ('LEFT', 'RIGHT'),
    'ABS_Y': ('FORWARD', 'BACKWARD'),
}

BUTTON_MAP = {
    'BTN_SOUTH': 'FIRE',
    'BTN_EAST': 'JUMP',
}

POLL_INTERVAL = 0.01  # hot-plug detection interval in seconds

# -----------------------------
# Placeholder motor functions
# Replace these with your real motor control code
# -----------------------------



# -----------------------------
# Joystick Listener Class
# -----------------------------
class JoystickMotorListener:
    def __init__(self, callback=None, axis_map=None, button_map=None, deadzone=None, poll_interval=None):
        self.callback = callback
        self.axis_map = axis_map or AXIS_MAP
        self.button_map = button_map or BUTTON_MAP
        self.deadzone = deadzone if deadzone is not None else DEADZONE
        self.poll_interval = poll_interval if poll_interval is not None else POLL_INTERVAL

        self.running = False
        self.thread = None
        self.connected_gamepads = set()
        self.axis_state = {}

    def _poll_gamepads(self):
        return set(d.name for d in devices.gamepads)

    def _handle_event(self, event):
        code = event.code
        state = event.state
        prev_state = self.axis_state.get(code, 0)

        # Axis handling
        if event.ev_type == "Absolute" and code in self.axis_map:
            neg_cmd, pos_cmd = self.axis_map[code]

            # Movement
            if state < -self.deadzone and prev_state >= -self.deadzone:
                self.set_motor_speed(neg_cmd)
            elif state > self.deadzone and prev_state <= self.deadzone:
                self.set_motor_speed(pos_cmd)

            # Release
            if prev_state < -self.deadzone and state >= -self.deadzone:
                self.stop_motor(neg_cmd)
            elif prev_state > self.deadzone and state <= self.deadzone:
                self.stop_motor(pos_cmd)

            self.axis_state[code] = state

        # Button handling
        elif event.ev_type == "Key" and code in self.button_map:
            cmd = self.button_map[code]
            if state == 1:
                self.set_motor_speed(cmd)
            elif state == 0:
                self.stop_motor(cmd)

    def _listen_loop(self):
        while self.running:
            # Hot-plug detection
            current_gamepads = self._poll_gamepads()
            new_gamepads = current_gamepads - self.connected_gamepads
            removed_gamepads = self.connected_gamepads - current_gamepads

            if new_gamepads:
                print(f"🟢 Gamepads connected: {list(new_gamepads)}")
            if removed_gamepads:
                print(f"🔴 Gamepads disconnected: {list(removed_gamepads)}")

            self.connected_gamepads = current_gamepads

            # Only read events if a gamepad is connected
            if self.connected_gamepads:
                try:
                    events = get_gamepad()  # blocking call
                    for e in events:
                        self._handle_event(e)
                except Exception:
                    # Ignore device disconnect errors
                    pass

            time.sleep(self.poll_interval)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🟢 Joystick motor listener started.")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join()
        print("🔴 Joystick motor listener stopped.")

    def set_motor_speed(self, command):
        print(f"[Motor] {command} START")
        self.callback(command)

    def stop_motor(self, command):
        print(f"[Motor] {command} STOP")
        self.callback("STOP")


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    listener = JoystickMotorListener()
    listener.start()

    try:
        while True:
            # Main program can run other tasks
            time.sleep(1)
    finally:
        listener.stop()

