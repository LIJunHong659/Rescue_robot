
// 例程---引脚需要修改

#include "chassis.hpp"
#include "servo_arm.hpp"
#include <esp_timer.h>

const Motor Motor_Left_config = {.pin_inA = PIN_Left_Motor_InA,
                           .pin_inB = PIN_Left_Motor_InB,
                           .dir     = Stop};

const Motor Motor_Right_config = {.pin_inA = PIN_Right_Motor_InA,
                           .pin_inB = PIN_Right_Motor_InB,
                           .dir     = Stop};                           




Arm Iarm;
Chassis Ichassis;
esp_timer_handle_t timerHandle = nullptr;

void update(void* arg){
  // 处理相机传回来的物体偏差，进而选择车运动方式


}

void setup() {
  Chassis_Init(&Ichassis, Motor_Left_config, Motor_Right_config);
  Arm_Init(&Iarm);
  // 开定时中断20ms
  esp_timer_create_args_t timerArgs = {
    .callback = &update,
    .arg = NULL,
    .name = "updateTimer"
  };
  esp_timer_create(&timerArgs, &timerHandle);
  // 每 20ms 触发一次（单位：微秒）
  esp_timer_start_periodic(timerHandle, 20000);

}

void loop() {
  // put your main code here, to run repeatedly:

}
