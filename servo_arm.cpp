#include "servo_arm.hpp"

// 舵机功能
void Servo_Init(IServo* servo, int pin, uint16_t angle_min, uint16_t angle_max){
  servo->servo_pin = pin;
  servo->servo_angle_min = angle_min;
  servo->servo_angle_max = angle_max;
  servo->servo.attach(pin);
  servo->servo_angle_cur = 0;   
}

void Servo_SetPWM(IServo* servo, uint16_t angle){
  if (!servo->servo.attached()){
    // 报错：舵机未初始化
  }

  if (angle <= servo->servo_angle_max && angle >= servo->servo_angle_min){
    servo->servo.write(angle);
    servo->servo_angle_cur = angle;
  }
  // TODO：报错
}



// 机械臂功能（懒得再开新文件了）
void Arm_Init(Arm* arm){
  Servo_Init(&arm->joint, Servo_PIN, Servo_Angle_Min, Servo_Angle_Max);
  arm->state = Open;
  Arm_Release(arm);
}

void Arm_Grab(Arm* arm){
  Servo_SetPWM(&arm->joint, Angle_CLOSE);
}

void Arm_Release(Arm* arm){
  Servo_SetPWM(&arm->joint, Angle_OPEN);
}