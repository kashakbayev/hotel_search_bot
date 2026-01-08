from peewee import Model, AutoField, IntegerField, TextField, DateTimeField
from datetime import datetime
from database.db import db

class BaseModel(Model):
    class Meta:
        database = db

class SearchHistory(BaseModel):
    id = AutoField()
    user_id = IntegerField()
    command = TextField()          # "lowprice" / "bestdeal" / "guest_rating"
    city = TextField()
    dest_id = TextField()
    search_type = TextField()
    checkin = TextField()          # YYYY-MM-DD
    checkout = TextField()         # YYYY-MM-DD
    min_price = TextField(null=True)
    max_price = TextField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)

    hotels_json = TextField()      # store full hotels list as JSON string
