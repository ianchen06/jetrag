import datetime
import logging

from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert

logger = logging.getLogger(__name__)


def execute(session, stmt):
    cnt = 0
    err = ''
    while cnt < 3:
        try:
            res = session.execute(stmt)
        except Exception as e:
            cnt += 1
            err = str(e)
            if 'ER_LOCK_DEADLOCK' in str(e):
                logger.info(str(e))
                continue
            else:
                raise e
        return res
    raise Exception(err)

def upsert(session, model, constraint, insert_dict):
    """model can be a db.Model or a table(), insert_dict should contain a primary or unique key."""
    inserted = insert(model).values(**insert_dict).prefix_with('IGNORE')
    if 'id' in insert_dict:
        upserted = inserted.on_duplicate_key_update(
            **{k: inserted.inserted[k] for k, v in insert_dict.items()},
            edited=datetime.datetime.now(datetime.timezone.utc),
        )
        res = execute(session, upserted)
        return insert_dict['id']
    
    upserted = inserted.on_duplicate_key_update(
        id=func.LAST_INSERT_ID(model.id),
        **{k: inserted.inserted[k] for k, v in insert_dict.items()},
        edited=datetime.datetime.now(datetime.timezone.utc),
    )

    res = execute(session, upserted)
    return res.lastrowid