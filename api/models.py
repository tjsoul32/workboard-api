# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class Commit(models.Model):
    commitid = models.AutoField(primary_key=True)
    taskid = models.IntegerField()
    author_id = models.IntegerField()
    content = models.TextField()
    create_time = models.DateTimeField()
    edit_time = models.DateTimeField()
    state = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'commit'


class Task(models.Model):
    taskid = models.AutoField(primary_key=True)
    creator = models.CharField(max_length=255)
    operator = models.CharField(max_length=255)
    member = models.CharField(max_length=255)
    create_time = models.DateTimeField()
    update_time = models.DateTimeField()
    description = models.CharField(max_length=255)
    state = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'task'


class Tasklevel(models.Model):
    taskid = models.IntegerField()
    userid = models.IntegerField()
    level = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tasklevel'


class User(models.Model):
    userid = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    state = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'user'


