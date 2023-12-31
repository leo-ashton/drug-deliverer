#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import threading

import rospy
from scheduler import CoolingTimePlan, NeedToSeePlan, NeedToChangeStatus
from scheduler_ros import SchedulerROS
from SocketService import SocketServiceMaster

# Future warning 不知道是干什么的
# sys.path.append("/home/ncut/scheduler_ws/devel/lib/python2.7/dist-packages")


DEBUG = 0
# WARNING: 网络环境变化时，多处IP需要修改，建议通过环境变量获取地址和端口等信息
SLAVE_ADDR = "192.168.137.172"
SLAVE_PORT = 12345
SLAVE_READY_PORT = 11515
FIXED_PERIOD = False


def SchedulerServerMain():
    rospy.spin()


def DrugCoolingTimeHandlerMain():
    # ROS 版本
    # needToChangeService = rospy.ServiceProxy("changetime", ChangeTimeResult)
    rospy.loginfo("[scheduler] 等待changetime服务...")

    # socket 版本
    needToChangeService = SocketServiceMaster(
        slave_addr=SLAVE_ADDR, slave_port=SLAVE_PORT, slave_ready_port=SLAVE_READY_PORT
    )
    rospy.loginfo("[scheduler] 等待连接到slave...")
    needToChangeService.wait_for_service()
    rospy.loginfo("[scheduler] 成功连接到slave!")

    while not rospy.is_shutdown():
        need = deliverScheduler.GetNeedToChangeStatus()
        if need != NeedToChangeStatus.DONT_CHANGE.value:
            if need == NeedToChangeStatus.SPEED_UP.value:
                rospy.logwarn("[scheduler to watcher] 请减少配药时间！")
            if need == NeedToChangeStatus.SLOW_DOWN.value:
                rospy.logwarn("[scheduler to watcher] 请增加配药时间！")
            rospy.loginfo("[scheduler] 发出修改请求...")
            change_success = needToChangeService.call(need)
            if need != deliverScheduler.GetNeedToChangeStatus():
                # 可能存在到达手写数字点后，已经不需要更新配送时间的情况
                # TODO 存在bug: 当小车第一轮有 2A 需求时，
                rospy.logwarn("[scheduler] 更新时间需求与发出请求时不同!")
                rospy.logwarn("[scheduler] 发出请求时: %d", need)
                rospy.logwarn("[scheduler] 当前: %d", deliverScheduler.GetNeedToChangeStatus())
            if change_success:
                deliverScheduler.UpdateDrugCoolingTime(need)
                rospy.logwarn("[watcher to scheduler] 修改成功!")
                print(
                    "当前状态:" + str(deliverScheduler.coolingTimeStateMachine.current_state.value)
                )


if __name__ == "__main__":
    deliverScheduler = SchedulerROS()
    print(deliverScheduler.reminder.interval)
    deliverScheduler.RegisterService()
    if FIXED_PERIOD:
        rospy.logwarn("scheduler 正在以固定的周期运行!")
        deliverScheduler.UpdateNeedToSeeInterval(NeedToSeePlan.PERIOD_2)
        deliverScheduler.UpdateDrugCoolingTime(CoolingTimePlan.PERIOD_3)
    deliverScheduler.start()

    rospy.loginfo("[scheduler] 调度器就绪!")

    SchedulerServerMain()
