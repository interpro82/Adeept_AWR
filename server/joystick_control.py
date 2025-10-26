import time
from inputs import devices, get_gamepad
import move

# --- CONFIG ---
DEADZONE = 5000  # Axis tolerance for "neutral"


# --- Robot control logic as a separate function ---
def control_robot(x_axis, y_axis):
    """
    Controls the robot based on joystick axes.
    x_axis: left/right value (-128..127)
    y_axis: forward/backward value (-128..127)
    """
    #print(x_axis, y_axis)
    direction_command = 'no'
    turn = 'no'
    speed = 0
    if abs(y_axis) < DEADZONE and abs(x_axis) < DEADZONE:
        print("Stop")
    elif abs(y_axis) > abs(x_axis):
        speed = int(abs(y_axis) / 330)
        if y_axis < 0:
            direction_command = 'forward'
        else:
            direction_command = 'backward'
    elif abs(x_axis) > abs(y_axis):
        speed = int(abs(x_axis) / 330)
        if x_axis < 0:
            turn = 'left'
        else:
            turn = 'right'
    print(speed, direction_command, turn)

    move.move(speed, direction_command, turn)


def wait_for_gamepad():
    """Wait until a gamepad is connected, refreshing device list each time."""
    while True:
        # Force reinitialization of device manager
        devices._devices = None  # clear cached devices
        devices._manager = None
        # Try to access gamepads again
        gamepads = devices.gamepads
        if gamepads:
            print(f"✅ Gamepad connected: {gamepads[0].name}")
            return gamepads[0]
        print("🔍 Waiting for gamepad...")
        time.sleep(2)


def listen_gamepad(callback=None):
    """Continuously read gamepad events and handle disconnects/reconnects."""
    gamepad = wait_for_gamepad()

    x_axis = 0
    y_axis = 0

    while True:
        try:
            events = get_gamepad()
            for event in events:
                if event.ev_type == "Absolute":
                    if event.code == "ABS_X":
                        x_axis = event.state - 128 if event.state else 0
                    elif event.code == "ABS_Y":
                        y_axis = event.state - 128 if event.state else 0

                    # Call robot control function
                    control_robot(x_axis, y_axis)
            # if event.code in ["ABS_X", "ABS_Y"]:
            #         if event.state == 0:
            #             print(f"{event.code} released")
            #         else:
            #             print(f"{event.code} moved: {event.state}")
            #         if callback:
            #             callback(event.code, event.state)
            # elif event.ev_type == "Key":
            #     print(f"{event.code}: {'pressed' if event.state else 'released'}")
            #     if callback:
            #         callback(event.code, event.state)



        except OSError:
            print("⚠️ Gamepad disconnected! Waiting for reconnection...")
            gamepad = wait_for_gamepad()



if __name__ == "__main__":
    move.setup()
    listen_gamepad()
