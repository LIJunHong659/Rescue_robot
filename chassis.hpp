#ifndef CHASSIS_HPP
#define CHASSIS_HPP

#include "motor.hpp"

typedef enum{
  DIR_STOP = 0,
  DIR_FORWARD = 1,
  DIR_BACKWARD = 2,
  DIR_TURN_LEFT = 3,
  DIR_TURN_RIGHT = 4
}Chassis_State;

typedef struct{
  Motor motor_left;
  Motor motor_right;
  Chassis_State state;
  float offset;     // 相对球的偏移量
}Chassis;


void Chassis_Init(Chassis* Ichassis, Motor config_motor_left, Motor config_motor_right);
void Chassis_Move_Forward(Chassis* Ichassis);
void Chassis_Move_Backward(Chassis* Ichassis);
void Chassis_Turn_Left(Chassis* Ichassis);
void Chassis_Turn_Right(Chassis* Ichassis);
void Chassis_Stop(Chassis* Ichassis);



#endif