#ifndef SERVO_ARM_HPP
#define SERVO_ARM_HPP

#include <Arduino.h>
#include <ESP32Servo.h>


// 舵机功能
#define Servo_PIN 0
#define Servo_Angle_Min 500
#define Servo_Angle_Max 1800

typedef struct{
  Servo servo;
  int servo_pin;
  uint16_t servo_angle_cur;
  uint16_t servo_angle_min;
  uint16_t servo_angle_max;
}IServo;

void Servo_Init(IServo* servo, int pin, uint16_t angle_min, uint16_t angle_max);
void Servo_SetPWM(IServo* servo, uint16_t angle);


// 机械臂功能（懒得再开新文件了）
// 注：本文件的angle均为角度
#define Angle_OPEN 50
#define Angle_CLOSE 100

typedef enum{
  Open = 0,
  Close = 1
}Arm_State;

typedef struct{
  IServo joint;
  Arm_State state;
}Arm;

void Arm_Init(Arm* arm);
void Arm_Grab(Arm* arm);
void Arm_Release(Arm* arm);


#endif