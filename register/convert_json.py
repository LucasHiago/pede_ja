import decimal
from datetime import date
import datetime


def objects_to_json(field):
    if isinstance(field, decimal.Decimal):
        return float(field)
    if isinstance(field, date):
        return str(field)
    raise TypeError(repr(field) + " is not JSON serializable")


def convert_data(field):
    if isinstance(field, (datetime.date, datetime.datetime)):
        return field.isoformat()
