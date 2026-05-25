#ifndef PID_HPP
#define PID_HPP

#include <Arduino.h>

typedef struct{
  float kp;
  float ki;
  float kd;
  float output_max;
  float T_ms;     // 单位ms
}PID_Config;

typedef struct{
  float kp;
  float ki;
  float kd;
  float prev_err;
  float prev_prev_err;
  float pre_output;
  float output_max;
  float T_ms;   // 单位ms
}PID_Inc;

typedef struct{
  float kp;
  float ki;
  float kd;
  float prev_err;
  float pre_output;
  float output_max;
  float T_ms;   // 单位ms
}PID_Abs;

void PID_Inc_Cal(PID_Inc *pid, float target, float current);
void PID_Abs_Cal(PID_Abs *pid, float target, float current);

 #endif // PID_HPP