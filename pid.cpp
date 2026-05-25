#include "pid.hpp"

void PID_Inc_Cal(PID_Inc *pid, float target, float current){
    float err = target - current;
    float Ts = pid->T_ms / 1000.0f;
    if (Ts <= 0.0f) Ts = 0.001f;
    float delta_output = pid->kp * (err - pid->prev_err)
                        + pid->ki * err * Ts
                        + pid->kd * (err - 2*pid->prev_err + pid->prev_prev_err) / Ts;

    float output = pid->pre_output + delta_output;

    // 允许输出为正或负，范围 [-output_max, +output_max]
    if (output > pid->output_max) output = pid->output_max;
    else if (output < -pid->output_max) output = -pid->output_max;

    pid->prev_prev_err = pid->prev_err;
    pid->prev_err = err;
    pid->pre_output = output;
}

void PID_Abs_Cal(PID_Abs *pid, float target, float current){
    float err = target - current;
    float Ts = pid->T_ms / 1000.0f;
    if (Ts <= 0.0f) Ts = 0.001f;

    float output = pid->kp * err 
                 + pid->ki * err * Ts 
                 + pid->kd * (err - pid->prev_err) / Ts;

    // 允许输出为正或负，范围 [-output_max, +output_max]
    if (output > pid->output_max) output = pid->output_max;
    else if (output < -pid->output_max) output = -pid->output_max;

    pid->prev_err = err;
    pid->pre_output = output;
}
