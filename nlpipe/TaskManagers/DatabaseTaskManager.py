import logging
import sys
from peewee import *
import datetime
from peewee import Model, CharField, DateTimeField, TextField

if 'pytest' in sys.modules.keys():  # if testing is happening
    logging.warning("Unit testing is happening. In memory db")
    db = SqliteDatabase(":memory", pragmas={'foreign_key': 1})
else:
    db = SqliteDatabase('nlpipe.db', pragmas={'foreign_keys': 1})  # create a SQLLite database


class BaseModel(Model):
    """A base model that will use our Sqlite database."""
    class Meta:
        database = db


class Task(BaseModel):  # TASK table
    created_date = DateTimeField(default=datetime.datetime.now, unique=False)  # date of the task first created
    tool = CharField(unique=False)  # NLP tool associated with task (1-1 relation)
    # todo
    status = CharField(unique=False)  # current status of the task


class Docs(BaseModel):  # DOCS table
    doc_id = CharField(unique=True)  # id of the document, needs to be unique
    task_id = ForeignKeyField(Task, to_field="id")  # related task_id
    path = CharField(unique=False)  # stored location (can be local or another endpoint)
    status = CharField(unique=False)  # current status


def initialize_if_needed():  # when server starts, it creates the database if needed
    db.create_tables([Task, Docs])  # creates the two tables
