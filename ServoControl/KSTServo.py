from machine import Pin, PWM
import time

class KSTServo:
    def __init__(self, pin, min_duty=23, max_duty=130, freq=50):
        self.pin = pin
        self.min_duty = min_duty
        self.max_duty = max_duty
        self.freq = freq
        self.pwm = PWM(Pin(self.pin), freq=self.freq)
        self.current_angle = 0
        print(f"Servo initialized on pin {self.pin} with frequency {self.freq} Hz")

    def angle_to_duty(self, angle):
        duty = self.min_duty + (self.max_duty - self.min_duty) * (angle / 180)
        return int(duty)

    def set_angle(self, angle):
        if 0 <= angle <= 180:
            duty = self.angle_to_duty(angle)
            self.pwm.duty(duty)
            self.current_angle = angle
            print(f"Set angle to {angle} degrees (duty: {duty})")
        else:
            raise ValueError("Angle must be between 0 and 180 degrees")

    def rotate_by(self, delta_angle):
        new_angle = self.current_angle + delta_angle
        if new_angle < 0:
            new_angle = 0
        elif new_angle > 180:
            new_angle = 180
        self.set_angle(new_angle)

    def rotate_by_rotations(self, rotations):
        degrees = rotations * 360
        self.rotate_by(degrees)

    def sweep(self, start_angle=0, end_angle=180, delay=0.01):
        if start_angle < end_angle:
            step = 1
        else:
            step = -1
        for angle in range(start_angle, end_angle + step, step):
            self.set_angle(angle)
            time.sleep(delay)

    def get_current_angle(self):
        return self.current_angle

    def deinit(self):
        self.pwm.deinit()
        print("Servo deinitialized")

# Example usage
if __name__ == "__main__":
    servo = KSTServo(pin=12)

    try:
        # Set the servo to 90 degrees
        servo.set_angle(90)
        time.sleep(1)

        # Rotate the servo by 45 degrees (total 135 degrees)
        servo.rotate_by(45)
        time.sleep(1)

        # Rotate the servo by 0.5 rotations (total 315 degrees, will be limited to 180)
        servo.rotate_by_rotations(0.5)
        time.sleep(1)

        # Sweep the servo from 0 to 180 degrees and back
        servo.sweep(0, 180)
        servo.sweep(180, 0)

        """servo.set_angle(0)
        time.sleep(1)
        # Print the current angle
        print("Current Angle:", servo.get_current_angle())
        servo.set_angle(110)
        time.sleep(1)
        print("Current Angle:", servo.get_current_angle())
        # servo.set_angle(220)
        time.sleep(1)
        print("Current Angle:", servo.get_current_angle())"""
        
        
        servo.deinit()

    except KeyboardInterrupt:
        servo.deinit()
