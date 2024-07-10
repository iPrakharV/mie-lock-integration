from machine import Pin, PWM
import time

class KSTServo:
    def __init__(self, pin, min_duty=272, max_duty=750, freq=333):
        """
        Initializes the KSTServo object to control a servo motor.
        Parameters:
        - pin (int): GPIO pin number where the servo signal wire is connected.
        - min_duty (int): PWM duty cycle corresponding to -60 degrees.
        - max_duty (int): PWM duty cycle corresponding to +60 degrees.
        - freq (int): PWM frequency, generally 333 Hz for this servo.
        """
        self.pin = pin
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.freq = freq
        self.pwm = PWM(Pin(self.pin), freq=self.freq)
        self.current_angle = 0
        print(f"Servo initialized on pin {self.pin} with frequency {self.freq} Hz")

    def angle_to_duty(self, angle):
        """
        Converts an angle in degrees to a PWM duty cycle.
        """
        if angle < -60:
            angle = -60
        elif angle > 60:
            angle = 60
        duty_span = self.max_duty - self.min_duty
        duty = self.min_duty + (angle + 60) * (duty_span / 120)
        return int(duty)

    def set_angle(self, angle, speed=1):
        """
        Sets the servo to a specific angle within the range of -60 to +60 degrees,
        controlling the speed of movement.
        """
        target_duty = self.angle_to_duty(angle)
        current_duty = self.pwm.duty()

        # Calculate step size based on speed parameter
        step = int((target_duty - current_duty) / (10 / speed))
        if step == 0:
            step = 1 if target_duty > current_duty else -1

        while (step > 0 and current_duty < target_duty) or (step < 0 and current_duty > target_duty):
            current_duty += step
            self.pwm.duty(current_duty)
            time.sleep(0.05 / speed)  # Modify delay based on speed to smooth out the movement
            if (step > 0 and current_duty >= target_duty) or (step < 0 and current_duty <= target_duty):
                break

        self.pwm.duty(target_duty)  # Ensure it reaches the final duty
        self.current_angle = angle
        print(f"Set angle to {angle} degrees at speed {speed}")

    def sweep(self, start_angle=-60, end_angle=60, delay=0.01, speed=1):
        """
        Sweeps the servo between two angles at a specified delay and speed.
        """
        step = 1 if start_angle < end_angle else -1
        for angle in range(start_angle, end_angle + step, step):
            self.set_angle(angle, speed)
            time.sleep(delay)

    def get_current_angle(self):
        """
        Returns the current angle of the servo.
        """
        return self.current_angle

    def deinit(self):
        """
        Deinitializes the PWM signal to safely stop the servo.
        """
        self.pwm.deinit()
        print("Servo deinitialized")

# Example usage
if __name__ == "__main__":
    servo = KSTServo(pin=12)

    try:
        # Sweep from -60 to +60 degrees and back with speed control
        # servo.sweep(start_angle=-60, end_angle=60, speed=1)
        # time.sleep(1)
        # servo.sweep(start_angle=60, end_angle=-60, speed=4)
        # time.sleep(1)

        # Set specific angles to demonstrate range with speed adjustments
        servo.set_angle(-60, speed=1)
        time.sleep(1)
        servo.set_angle(0, speed=8)
        time.sleep(1)
        servo.set_angle(60, speed=1)
        time.sleep(1)
        servo.set_angle(0, speed=9)

        servo.deinit()

    except KeyboardInterrupt:
        servo.deinit()

