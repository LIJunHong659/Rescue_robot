#ifndef MOTOR_HPP
#define MOTOR_HPP

#include <Arduino.h>

#define PIN_Left_Motor_InA 26
#define PIN_Left_Motor_InB 27

#define PIN_Right_Motor_InA 28
#define PIN_Right_Motor_InB 29

#define Forward     1
#define Backward    -1
#define Stop        0


typedef struct{
    uint8_t pin_inA;
    uint8_t pin_inB;
    int dir;
}Motor;

void Motor_Init(Motor* Imotor, Motor config);
void Motor_SetDir(Motor* Imotor, int dir);
void Motor_Output(Motor* Imotor);




#endif // MOTOR_HPP