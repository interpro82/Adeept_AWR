import threading
from inputs import get_gamepad, devices

# Default deadzone for analog axes
DEADZONE = 5000

# Default mappings
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
    def __init__(self, axis_map=None, button_map=None, deadzone=None, callback=None):
        """
        Initializes the joystick listener.
        """
        self.axis_map = axis_map or AXIS_COMMANDS
        self.button_map = button_map or BUTTON_COMMANDS
        self.deadzone = deadzone if deadzone is not None else DEADZONE
        self.callback = callback
        self.running = False
        self.thread = None

        if not devices.gamepads:
            raise RuntimeError("No gamepad detected. Plug one in and try again.")
        self.gamepad_names = [d.name for d in devices.gamepads]
        print(f"🎮 Detected gamepads: {self.gamepad_names}")

    def _listen_loop(self):
        while self.running:
            try:
                events = get_gamepad()
                for event in events:
                    # Axis events
                    if event.ev_type == "Absolute" and event.code in self.axis_map:
                        neg_cmd, pos_cmd = self.axis_map[event.code]
                        if event.state < -self.deadzone:
                            if self.callback:
                                self.callback(neg_cmd)
                        elif event.state > self.deadzone:
                            if self.callback:
                                self.callback(pos_cmd)
                    # Button events
                    elif event.ev_type == "Key" and event.code in self.button_map and event.state == 1:
                        if self.callback:
                            self.callback(self.button_map[event.code])
            except Exception as e:
                print(f"⚠️  Error reading gamepad: {e}")

    def start(self):
        """
        Start listening in a background thread.
        """
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🟢 Joystick listener started.")

    def stop(self):
        """
        Stop listening.
        """
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join()
        print("🔴 Joystick listener stopped.")


