

from stepper_gcode_machine import Motor

class MockMotor(Motor):

    def __init__(self, name, mode='full', endstop_direction = 1, max_steps = 1100):
        super().__init__(self, name, mode, endstop_direction, max_steps)

class TestMotor:


    def test_move(self):
        motor = MockMotor('Y-Axis', max_steps=200, endstop_direction= -1)
        motor.home()
        expectedSteps = 10 * motor.endstop_direction * -1
        actualSteps = motor.move(10, motor.endstop_direction * -1)
        assert actualSteps == expectedSteps
        assert not motor.is_endstop_triggered()
        assert motor.current_step == expectedSteps
        motor.move(191, motor.endstop_direction * -1)
        assert motor.current_step == 200

    def test_is_endstop_triggered(self):
        motor = MockMotor('Y-Axis', max_steps=200, endstop_direction= -1)
        motor.home()
        motor.move(1,motor.endstop_direction)
        assert motor.is_endstop_triggered()

    def test_home(self):
        motor = MockMotor('Y-Axis', max_steps=200, endstop_direction= -1)
        motor.home()
        assert motor.is_endstop_triggered()
        assert motor.current_step == 0


