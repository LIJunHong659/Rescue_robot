#include "chassis.hpp"


void Chassis_Init(Chassis* Ichassis, Motor config_motor_left, Motor config_motor_right){
  Motor_Init(&Ichassis->motor_left, config_motor_left);
  Motor_Init(&Ichassis->motor_right, config_motor_right);
  Ichassis->state = DIR_STOP;
  Ichassis->offset = 0;
}

void Chassis_Move_Forward(Chassis* Ichassis){
  Ichassis->state = DIR_FORWARD;
  // 装的时候应该会导致两个电机方向不一致
  Ichassis->motor_left.dir = Forward;
  Ichassis->motor_right.dir = -Forward;   

  Motor_Output(&Ichassis->motor_left);
  Motor_Output(&Ichassis->motor_right);
}

void Chassis_Move_Backward(Chassis* Ichassis){
  Ichassis->state = DIR_BACKWARD;
  // 装的时候应该会导致两个电机方向不一致
  Ichassis->motor_left.dir = Backward;
  Ichassis->motor_right.dir = -Backward;   

  Motor_Output(&Ichassis->motor_left);
  Motor_Output(&Ichassis->motor_right);
}

void Chassis_Turn_Left(Chassis* Ichassis){
  Ichassis->state = DIR_TURN_LEFT;
  // 装的时候应该会导致两个电机方向不一致
  Ichassis->motor_left.dir = Backward;
  Ichassis->motor_right.dir = -Forward;   

  Motor_Output(&Ichassis->motor_left);
  Motor_Output(&Ichassis->motor_right);
}

void Chassis_Turn_Right(Chassis* Ichassis){
  Ichassis->state = DIR_TURN_RIGHT;
  // 装的时候应该会导致两个电机方向不一致
  Ichassis->motor_left.dir = Forward;
  Ichassis->motor_right.dir = -Backward;   

  Motor_Output(&Ichassis->motor_left);
  Motor_Output(&Ichassis->motor_right);
}

void Chassis_Stop(Chassis* Ichassis){
  Ichassis->state = DIR_STOP;
  // 装的时候应该会导致两个电机方向不一致
  Ichassis->motor_left.dir = Stop;
  Ichassis->motor_right.dir = -Stop; 

  Motor_Output(&Ichassis->motor_left);
  Motor_Output(&Ichassis->motor_right);
}
