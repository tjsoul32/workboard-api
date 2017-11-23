# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from django.db.models import Q, Count

from api.models import User as U
from api.models import Task as T
from api.models import Tasklevel as TL
from api.models import Commit as C

import json, uuid
from datetime import datetime, timedelta


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
    response["Access-Control-Allow-Headers"] = "*, X-Token, X-Un"

    return response


def genDatetime():
    return timezone.now() + timedelta(hours = 8)


# http request 身份验证
def id_verification(func):
    def wrapper(request):
        metaData = request.META
        token = metaData["HTTP_X_TOKEN"] if "HTTP_X_TOKEN" in metaData else ''
        un = metaData["HTTP_X_UN"] if "HTTP_X_UN" in metaData else ''

        try:
            res = U.objects.get(username = un, token = token, state = 1)
        except:
            res = ''

        if res:
            return func(request)            
        else:
            return genResponse({'code': -1})
    return wrapper


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
    res["token"] = ''

    return genResponse(res)


# 用户列表
@csrf_exempt
@id_verification
def user_list(request):
    getData = request.GET
    username = getData["username"]
    get_users = U.objects.values("username").filter(state = 1)
    users = [
        {
            "username": u["username"]
        }
        for u in get_users if u["username"] != username
    ]
    res = users

    return genResponse(res)

###########################################################
# 添加任务
@csrf_exempt
@id_verification
def task_add(request):
    postData = request.POST
    username = postData["username"]
    description = postData["description"]
    member = postData["member"].split(',')
    operator = postData["operator"].split(',')
    level = postData["level"]
    if not username in member: member.append(username)
    if not username in operator: operator.append(username) 

    get_users = U.objects.values("userid", "username").filter(username__in = member)
    users = { u["username"]: u["userid"] for u in get_users }

    creator = users[username] 
    member_str = ',' + ','.join([ str(users[m]) for m in member if m]) + ','
    operator = ',' + ','.join([ str(users[o]) for o in operator if o]) + ','
    create_time = update_time = edit_time = genDatetime()

    t = T.objects.create(creator = creator, operator = operator, member = member_str, description = description, create_time = create_time, update_time = update_time, state = 1)
    taskid = t.taskid

    c = C.objects.create(taskid = taskid, author_id = creator, content = description, create_time = create_time, edit_time = edit_time, state = 1)

    for m in member:
        if m: 
            TL.objects.create(taskid = taskid, userid = str(users[m]), level = level)

    res = {"result": "ok"}
    return genResponse(res)


# 修改任务等级
@csrf_exempt
@id_verification
def task_setlevel(request):
    postData = request.POST
    username = postData["username"]
    taskid = postData["taskid"]
    level = postData["level"]

    user = U.objects.values("userid").get(username = username)
    upd = TL.objects.filter(taskid = taskid, userid = user["userid"]).update(level = level)
    if not upd:
        TL.objects.create(taskid = taskid, userid = user["userid"], level = level)

    res = {"result": "ok"}
    return genResponse(res)


# 更新成员
@csrf_exempt
@id_verification
def task_setmember(request):
    postData = request.POST
    username = postData["username"]
    taskid = postData["taskid"]
    member = postData["member"].split(',')
    operator = postData["operator"].split(',')
    level = postData["level"]
    
    get_ops = T.objects.values("operator").get(taskid = taskid)
    get_users = U.objects.values("userid", "username").filter(username__in = member)
    users = { u["username"]: u["userid"] for u in get_users }

    if users[username] in [ int(o) for o in get_ops["operator"].split(',') if o ]:
        member_str = ',' + ','.join([ str(users[m]) for m in member if m]) + ','
        operator_str = ',' + ','.join([ str(users[o]) for o in operator if o]) + ','
        update_time = update_time = edit_time = genDatetime()
        T.objects.filter(taskid = taskid).update(operator = operator_str, member = member_str, update_time = update_time)
        for m in member:
            TL.objects.filter(taskid = taskid, userid = users[m]).update(level = level)

    res = {"result": "ok"}
    return genResponse(res)



# 任务列表
@csrf_exempt
@id_verification
def task_list(request):
    getData = request.GET
    username = getData["username"]
    user = U.objects.get(username = username)

    get_tasks = T.objects.values("taskid", "creator", "operator", "member", "create_time", "update_time", "description", "state").filter(state = 1, member__contains = ',' + str(user.userid) + ',').order_by("-update_time")
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


# task info
@csrf_exempt
@id_verification
def task_info(request):
    getData = request.GET
    taskid = getData["taskid"] if getData["taskid"] else 0
    username = getData["username"]
    user = U.objects.values("userid").get(username = username)

    get_task = T.objects.values("taskid", "creator", "operator", "member", "create_time", "update_time", "description", "state").filter(taskid = taskid, state = 1)
    get_level = TL.objects.values("level").filter(userid = user["userid"], taskid = taskid)
    level = get_level[0]["level"] if len(get_level) > 0 else 1

    #users_id = [ c["author_id"] for c in get_commits ]

    get_users_id = get_task[0]["member"].split(',') if get_task else []
    get_users_id.append(get_task[0]["creator"])
    users_id = [ int(u) for u in get_users_id if u ]

    get_users = U.objects.values("userid", "username").filter(userid__in = users_id)
    users = { u["userid"]: u["username"] for u in get_users }

    res = {}
    res["task"] = get_task[0] if get_task else {}
    res["task"]["level"] = level
 
    if res["task"]:
        res["task"]["creator"] = users[int(res["task"]["creator"])]
        res["task"]["operator"] = [ users[int(o)] for o in res["task"]["operator"].split(',') if o ]
        res["task"]["member"] = [ users[int(m)] for m in res["task"]["member"].split(',') if m ]
        res["task"]["create_time"] = res["task"]["create_time"].strftime('%Y-%m-%d %H:%M:%S')
        res["task"]["update_time"] = res["task"]["update_time"].strftime('%Y-%m-%d %H:%M:%S')

    return genResponse(res)


# task detail
@csrf_exempt
@id_verification
def task_detail(request):
    getData = request.GET
    taskid = getData["taskid"] if getData["taskid"] else 0
    username = getData["username"]
    user = U.objects.values("userid").get(username = username)

    get_task = T.objects.values("taskid", "creator", "operator", "member", "create_time", "update_time", "description", "state").get(taskid = taskid, state = 1)
    get_level = TL.objects.values("level").filter(userid = user["userid"], taskid = taskid)
    level = get_level[0]["level"] if len(get_level) > 0 else 1

    get_users_id = get_task["member"].split(',') if get_task else []
    get_users_id.append(get_task["creator"])
    users_id = [ int(u) for u in get_users_id if u ]

    get_users = U.objects.values("userid", "username").filter(userid__in = users_id)
    users = { u["userid"]: u["username"] for u in get_users }

    if not user["userid"] in users:
        return genResponse({"task": [], "commits": []})

    users_id.append(get_task["creator"])
    get_commits = C.objects.values("commitid", "taskid", "author_id", "content", "create_time", "edit_time").filter(taskid = taskid, state = 1, author_id__in = users).order_by("create_time")

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
    res["task"] = get_task if get_task else {}
    res["task"]["level"] = level
    res["commits"] = commits 

    print users
    if res["task"]:
        res["task"]["creator"] = users[int(res["task"]["creator"])]
        res["task"]["operator"] = [ users[int(o)] for o in res["task"]["operator"].split(',') if o ]
        res["task"]["member"] = [ users[int(m)] for m in res["task"]["member"].split(',') if m ]
        res["task"]["create_time"] = res["task"]["create_time"].strftime('%Y-%m-%d %H:%M:%S')
        res["task"]["update_time"] = res["task"]["update_time"].strftime('%Y-%m-%d %H:%M:%S')

    return genResponse(res)


# new content
@csrf_exempt
@id_verification
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
        T.objects.filter(taskid = taskid).update(update_time = create_time)
    except Exception as e:
        print e
        res = {"result": "failed"}

    return genResponse(res)


# edit content
@csrf_exempt
@id_verification
def content_edit(request):
    postData = request.POST  
    taskid = postData["taskid"]
    commitid = postData["commitid"]
    content = postData["content"]
    edit_time = genDatetime()

    try:
        C.objects.filter(commitid = commitid).update(content = content, edit_time = edit_time)
        T.objects.filter(taskid = taskid).update(update_time = edit_time)
        res = {"result": "ok"}
    except Exception as e:
        print e
        res = {"result": "failed"}

    return genResponse(res)


# delete content
@csrf_exempt
@id_verification
def content_del(request):
    postData = request.POST
    commitid = postData["commitid"]
    taskid = postData["taskid"]
    username = postData["username"]
    user_id = U.objects.values("userid").get(username = username)["userid"]    
    task = T.objects.values("creator", "operator").get(taskid = taskid)

    try:
        if task["creator"] == user_id or user_id in [ int(o) for o in task["operator"].split(',') if o ]:
            C.objects.filter(commitid = commitid).update(state = 0)
        res = {"result": "ok"}
    except Exception as e:
        print e
        res = {"result": "failed"}

    return genResponse(res)


#####################################################################
# 任务统计
@csrf_exempt
@id_verification
def task_agg(request):
    metaData = request.META
    username = metaData["HTTP_X_UN"]
    me = U.objects.values("username", "userid").get(username = username)
    userid = str(me["userid"]).strip()
    userid_str = ',' + userid + ','

    mytasks = T.objects.values("taskid", "creator", "operator", "member", "create_time", "update_time", "state").filter(Q(creator = userid) | Q(member__contains = userid_str))    

    task_creator = []
    task_operator = []
    task_member = []
    
    for t in mytasks:
        if userid == t["creator"]:
            task_creator.append(t["taskid"])
        if userid_str in t["operator"]:
            task_operator.append(t["taskid"])
        if userid_str in t["member"]:
            task_member.append(t["taskid"])

    mylevel = TL.objects.values("level").filter(taskid__in = task_member, userid = userid).annotate(num = Count("level"))
    mylevel = { l["level"]: l["num"] for l in mylevel }

    res = {}
    res["roles"] = {
        "creator": len(task_creator),
        "operator": len(task_operator),
        "member": len(task_member)
    }
    res["levels"] = {  i: (mylevel[i] if i in mylevel else 0)  for i in range(1, 5) }

    return genResponse(res)


