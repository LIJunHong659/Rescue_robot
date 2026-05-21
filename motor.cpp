#include "motor.hpp"


void Motor_Init(Motor* Imotor, Motor config){
  Imotor->pin_inA = config.pin_inA;
  Imotor->pin_inB = config.pin_inB;
  Imotor->dir     = config.dir;

  pinMode(Imotor->pin_inA, OUTPUT);
  pinMode(Imotor->pin_inB, OUTPUT);
}

void Motor_SetDir(Motor* Imotor, int dir){
  Imotor->dir = dir;
}

void Motor_Output(Motor* Imotor){
  switch(Imotor->dir){
    case Forward:
      digitalWrite(Imotor->pin_inA, LOW);
      digitalWrite(Imotor->pin_inB, HIGH);
      break;
    case Backward:
      digitalWrite(Imotor->pin_inA, HIGH);
      digitalWrite(Imotor->pin_inB, LOW);
      break;
    case Stop:
      digitalWrite(Imotor->pin_inA, LOW);
      digitalWrite(Imotor->pin_inB, LOW);
      break;
    default:
      break;
  }

}