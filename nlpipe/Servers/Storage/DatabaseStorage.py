import logging
import sys
from peewee import *
import datetime
from peewee import Model, CharField, DateTimeField, TextField

# check if testing is happening
if 'pytest' in sys.modules.keys():
    logging.warning("Unit testing is happening. In memory db")
    db = SqliteDatabase(":memory", pragmas={'foreign_key': 1})
else:
    db = SqliteDatabase('nlpipe.db', pragmas={'foreign_keys': 1})


class BaseModel(Model):
    """A base model that will use our Sqlite database."""
    class Meta:
        database = db


class Task(BaseModel):
    created_date = DateTimeField(default=datetime.datetime.now, unique=False)
    tool = CharField(unique=False)
    docs = TextField(unique=False)
    status = CharField(unique=False)


class Docs(BaseModel):
    doc_id = CharField(unique=True)
    task_id = ForeignKeyField(Task, to_field="id")
    path = CharField(unique=False)
    status = CharField(unique=False)


def initialize_if_needed():
    db.create_tables([Task, Docs])
