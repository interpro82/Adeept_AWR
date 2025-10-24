import threading
import time
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
    def __init__(self, axis_map=None, button_map=None, deadzone=None, callback=None, poll_interval=2):
        """
        Initializes the joystick listener.
        - poll_interval: seconds between checking for new gamepads
        """
        self.axis_map = axis_map or AXIS_COMMANDS
        self.button_map = button_map or BUTTON_COMMANDS
        self.deadzone = deadzone if deadzone is not None else DEADZONE
        self.callback = callback
        self.running = False
        self.thread = None
        self.poll_interval = poll_interval
        self.connected_gamepads = set()

    def _poll_gamepads(self):
        """
        Returns a set of currently connected gamepad names.
        """
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

            # Only try to read events if there is at least one gamepad
            if self.connected_gamepads:
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
                    # Ignore errors if device is removed mid-read
                    pass

            time.sleep(self.poll_interval)

    def start(self):
        """
        Start listening in a background thread.
        """
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print("🟢 Joystick listener started (hot-plug supported).")

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
