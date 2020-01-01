import datetime
import json
import time

import requests


def startTime(Lesson):
    TimeTable = ["080000", "085500", "095500", "105000", "114500", "133000", "142500", "152500", "162000", "183000",
                 "192500", "202000"]
    return TimeTable[Lesson - 1]


def endTime(Lesson):
    TimeTable = ["084500", "094000", "104000", "113500", "123000", "141500", "151000", "161000", "170500", "191500",
                 "201000", "210500"]
    return TimeTable[Lesson - 1]


def calcStartDate(week, weekday, FirstDay):
    if week.split("-")[0] != "1":
        FirstDay = FirstDay + datetime.timedelta(7 * int(week.split("-")[0]) - 7)
    FirstDay = FirstDay + datetime.timedelta(int(weekday) - 1)
    return FirstDay.strftime("%Y%m%d")


def calcEndDate(week, weekday, FirstDay):
    LastDay = FirstDay + datetime.timedelta(7 * int(week.split("-")[1].split("\\u546")[0]) - 7)
    LastDay = LastDay + datetime.timedelta(int(weekday))
    return LastDay.strftime("%Y%m%d")


def calcStartTime(LessonTime):
    StartLesson = int(LessonTime.split("-")[0])
    return startTime(StartLesson)


def calcEndTime(LessonTime):
    EndLesson = int(LessonTime.split("-")[1])
    return endTime(EndLesson)


def out(ClassName, Classroom, teacher, week, weekday, LessonTime, Campus, FirstDay, out):
    out.write("BEGIN:VEVENT\n")
    out.write("SUMMARY:" + ClassName + "\n")
    out.write(
        "DTSTART;TZID=Asia/Shanghai:" + calcStartDate(week, weekday, FirstDay) + "T" + calcStartTime(LessonTime) + "\n")
    out.write(
        "DTEND;TZID=Asia/Shanghai:" + calcStartDate(week, weekday, FirstDay) + "T" + calcEndTime(LessonTime) + "\n")
    out.write("RRULE:FREQ=WEEKLY;UNTIL=" + calcEndDate(week, weekday, FirstDay) + "T" + calcEndTime(LessonTime) + "\n")
    out.write("LOCATION:" + Campus + "  " + Classroom + "  " + teacher + "\n")
    out.write("END:VEVENT\n")


def calcSemester(t):
    if t == "1":
        return "3"
    if t == "2":
        return "12"
    if t == "3":
        return "16"


if __name__ == '__main__':
    headers = {
        "Host": "api.jh.zjut.edu.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/79.0.3945.88 Safari/537.36 Edg/79.0.309.54 "
    }
    FirstDay = datetime.datetime.strptime(input("请输入学期第一个星期一，如20190916:"), "%Y%m%d")
    while FirstDay.weekday() != 0:
        print("你的输入有误")
        FirstDay = datetime.datetime.strptime(input("请输入学期第一个星期一，如20190916:"), "%Y%m%d")
    url = "http://api.jh.zjut.edu.cn/student/classZf.php?username=" + input("请输入学号:") + "&password=" + input(
        "请输入密码:") + "&year=" + input("请输入学年:") + "&term=" + calcSemester(input("请输入学期：1-上学期 2-下学期 3-短学期:"))
    content = requests.get(url, headers=headers).content.decode().encode("GBK")

    JSON = json.loads(content)
    n = 0
    while JSON["status"] == "error":
        print("遇到了错误，正在重试")
        content = requests.get(url, headers=headers).content.decode().encode("GBK")
        JSON = json.loads(content)
        time.sleep(3)
        n = n + 1
        if n == 10:
            print("获取失败，请重新输入")
            exit(0)
    print(content)
    output = open('output.ics', 'w', encoding="utf-8")
    output.write("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//HHR//ZJUTClass2ICS//EN\n")
    for each in JSON["msg"]:
        ClassName = each["kcmc"]
        Classroom = each["cdmc"]
        Teacher = each["xm"]
        weekday = each["xqj"]
        LessonTime = each["jcor"]
        Campus = each["xqmc"]
        week = each["zcd"][:-1]
        flag = 0
        try:
            tmp = week.index("单")
        except ValueError:
            flag = 1
        if flag == 0:
            week = week[:-3]
            startWeek = int(week.split("-")[0])
            endWeek = int(week.split("-")[1])
            for i in range(startWeek, endWeek):
                if i % 2 == 0:
                    out(ClassName, Classroom, Teacher, str(i) + "-" + str(i), weekday, LessonTime, Campus, FirstDay,
                        output)
            continue
        flag = 0
        try:
            tmp = week.index("双")  # 处理形如 2-16周(双) 的情况
        except ValueError:
            flag = 1
        if flag == 0:
            week = week[:-3]
            startWeek = int(week.split("-")[0])
            endWeek = int(week.split("-")[1])
            for i in range(startWeek, endWeek):
                if i % 2 != 0:
                    out(ClassName, Classroom, Teacher, str(i) + "-" + str(i), weekday, LessonTime, Campus, FirstDay,
                        output)
            continue
        try:
            week1 = week.split(",")[1]  # 处理形如 2-8周,10-16周 的情况
        except IndexError:
            while not ('0' <= week[-1] <= '9'):  # 剪掉后面的所有中文
                week = week[:-1]
            week = week + "-" + week[0]  # 避免某课程只上一周导致的异常
            out(ClassName, Classroom, Teacher, week, weekday, LessonTime, Campus, FirstDay, output)
            continue
        week = week.split(",")[0]
        while not ('0' <= week[-1] <= '9'):  # 剪掉后面的所有中文
            week = week[:-1]
        week = week + "-" + week[0]  # 避免某课程只上一周导致的异常
        out(ClassName, Classroom, Teacher, week, weekday, LessonTime, Campus, FirstDay, output)
        while not ('0' <= week1[-1] <= '9'):  # 剪掉后面的所有中文
            week1 = week1[:-1]
        week1 = week1 + "-" + week1[0]  # 避免某课程只上一周导致的异常
        out(ClassName, Classroom, Teacher, week1, weekday, LessonTime, Campus, FirstDay, output)
    output.write("END:VCALENDAR")
    output.close()
    print("文件生成成功")
