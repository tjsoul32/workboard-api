# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from api.models import User as U
from api.models import Task as T
from api.models import Tasklevel as TL
from api.models import Commit as C

import json, uuid
from datetime import datetime, timedelta
from django.utils import timezone

def genToken():
    token = ''
    genid = str(uuid.uuid1())
    token = ''.join(genid.split('-'))

    return token


def genResponse(res):
    response = HttpResponse(json.dumps(res), content_type = "application/json")
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "*"

    return response


def genDatetime():
    return timezone.now() + timedelta(hours = 8)


# 用户登录验证
@csrf_exempt
def user_login(request):
    postData = request.POST.dict()
    username = postData["username"].strip()
    password = postData["password"].strip()

    try:
        user = U.objects.get(username = username, state = 1)
        get_pass = user.password
    except:
        get_pass = ''

    token = genToken() if len(password) > 0 and password == get_pass else ''
    U.objects.filter(username = username).update(token = token)

    res = {}
    res["token"] = token

    return genResponse(res)


# 用户登出
@csrf_exempt
def user_logout(request):
    postData = request.POST.dict()
    token = postData["token"].strip()
    U.objects.filter(token = token).update(token = '')

    res = {}
    res["token"] = token

    return genResponse(res)


# 任务列表
@csrf_exempt
def task_list(request):
    getData = request.GET
    username = getData["username"]
    user = U.objects.get(username = username)

    get_tasks = T.objects.values("taskid", "creator", "operator", "member", "create_time", "update_time", "description", "state").filter(state = 1, member__contains = ',' + str(user.userid) +',')
    get_level = TL.objects.values("taskid", "level").filter(userid = user.userid)
    levels = { l["taskid"]: l["level"] for l in get_level }

    tasks = [
        {
            "taskid": t["taskid"],
            "creator": t["creator"],  
            "operator": t["operator"],
            "member": t["member"],
            "create_time": t["create_time"].strftime('%Y-%m-%d %H:%M:%S'),
            "update_time": t["update_time"].strftime('%Y-%m-%d %H:%M:%S'),
            "description": t["description"],
            "state": t["state"],
            "level": levels[t["taskid"]] if t["taskid"] in levels else 0
        } 
        for t in get_tasks if t 
    ]
    res = tasks

    return genResponse(res)


# task detail
@csrf_exempt
def task_detail(request):
    getData = request.GET
    taskid = getData["taskid"] if getData["taskid"] else 0

    get_task = T.objects.values("taskid", "creator", "operator", "member", "create_time", "update_time", "description", "state").filter(taskid = taskid, state = 1)
    get_commits = C.objects.values("commitid", "taskid", "author_id", "content", "create_time", "edit_time").filter(taskid = taskid, state = 1).order_by("create_time")
    users_id = [ c["author_id"] for c in get_commits]

    get_users = U.objects.values("userid", "username").filter(userid__in = users_id)
    users = { u["userid"]: u["username"] for u in get_users }

    commits = [         
        {
            "commitid": c["commitid"],
            "taskid": c["taskid"],
            "author_name": users[c["author_id"]],
            "content": c["content"],
            "create_time": c["create_time"].strftime('%Y-%m-%d %H:%M:%S'),
            "edit_time": c["edit_time"].strftime('%Y-%m-%d %H:%M:%S'),
        }
        for c in get_commits if c 
    ]

    res = {}
    res["task"] = get_task[0] if get_task else {}
    res["commits"] = commits 

    if res["task"]:
        res["task"]["create_time"] = res["task"]["create_time"].strftime('%Y-%m-%d %H:%M:%S')
        res["task"]["update_time"] = res["task"]["update_time"].strftime('%Y-%m-%d %H:%M:%S')

    return genResponse(res)


# new content
@csrf_exempt
def content_new(request):
    postData = request.POST
    username = postData["username"]
    content = postData["content"]
    taskid = postData["taskid"]
    author_id = U.objects.values("userid").get(username = username)["userid"]
    create_time = edit_time = genDatetime()

    try:
        cmt = C.objects.create(taskid = taskid, author_id = author_id, content = content, create_time = create_time, edit_time = edit_time, state = 1)
        res = {"result": "ok"}
        res["commit"] = {
            "taskid": taskid,
            "commitid": cmt.commitid,
            "author_name": username,
            "content": content,
            "create_time": create_time.strftime('%Y-%m-%d %H:%M:%S'),
            "edit_time": edit_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
    except Exception as e:
        print e
        res = {"result": "failed"}

    return genResponse(res)


# edit content
@csrf_exempt
def content_edit(request):
    postData = request.POST  
    commitid = postData["commitid"]
    content = postData["content"]
    edit_time = genDatetime()

    try:
        C.objects.filter(commitid = commitid).update(content = content, edit_time = edit_time)
        res = {"result": "ok"}
    except:
        res = {"result": "failed"}

    return genResponse(res)


# delete content
@csrf_exempt
def content_del(request):
    postData = request.POST
    commitid = postData["commitid"]
    username = postData["username"]
    author_id = U.objects.values("userid").get(username = username)["userid"]    

    try:
        C.objects.filter(commitid = commitid, author_id = author_id).update(state = 0)
        res = {"result": "ok"}
    except Exception as e:
        print e
        res = {"result": "failed"}

    return genResponse(res)


