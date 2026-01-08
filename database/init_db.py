from database.db import db
from database.models import SearchHistory

def init_db():
    db.connect(reuse_if_open=True)
    db.create_tables([SearchHistory])
    db.close()
