"""
This file contains endpoints and functions relating to client access to the cloud infrastructure. The RESTful api here can be queried
to e.g. return tweets, or aggregate statistics from couchdb.
"""

from flask import Blueprint, request
from couchdb import Server
import requests
import json
import os
from collections import defaultdict

# couchDB anonymous server connection

username = "admin"
password = "password"

couchserver = Server(f"{os.getenv('COUCHDB_DATABASE')}/")
for dbname in couchserver:
    # print(dbname)
    pass

db = couchserver["test2"]

api_bp = Blueprint("api", __name__)


@api_bp.route("/tweets/languages_by_time/")
# api functions and routes below
def get_languages_by_time_view():
    """
    map:
        function (document) {
            // e.g. "Wed Jul 20 11:59:07 +0000 2011"
            const [day, month, month_date, time, offset, year] = document.doc.created_at.split(" ");
            // const [city,year,month,day] = document.key
            const lang = document.doc.lang;
            emit([lang, year, month, month_date], 1);
        }
    reduce:
        _count

    also see: https://blog.pablobm.com/2019/07/18/map-reduce-with-couchdb-a-visual-primer.html
    """
    acc = defaultdict(lambda: defaultdict(lambda: 0))
    # example of iterating a view
    months = {
        "Jan": "01",
        "Feb": "02",
        "Mar": "03",
        "Apr": "04",
        "May": "05",
        "Jun": "06",
        "Jul": "07",
        "Aug": "08",
        "Sep": "09",
        "Oct": "10",
        "Nov": "11",
        "Dec": "12",
    }
    for item in db.view(
        "_design/LanguageInfo/_view/TestView", group=True, group_level=3
    ):
        # where the positions of the keys are derived from the order in the 'emit' function in couchdb
        # print(item)
        date_key = f"{item['key'][1]}-{months[item['key'][2]]}"
        if date_key == "2017-06":
            print("------")
            print(item["key"])
            continue
        lang = item["key"][0]
        # print(date_key, str(item["value"]))
        acc[date_key][lang] = acc[date_key][lang] + item["value"]
    return acc


def test1():
    return get_languages_by_time_view()


def get_tweet_n(id):
    return db[id]


@api_bp.route("/tweets/latest/")
def get_latest_tweets():
    r = requests.get(
        f"{os.getenv('COUCHDB_DATABASE')}/test/_changes?descending=true&limit=10"
    )
    # print(json.loads(r.content)["results"][0])
    return r.content


@api_bp.route("/tweet/")
def get_tweet():
    tweet_id = request.args.get("id")
    return db[tweet_id]


@api_bp.route("/sentiments/suburb", methods=["GET"])
def suburb_sentiment():
    suburb_name = request.args.get("suburb", "")
    # request to couchDB
    return "happy"


@api_bp.route("/external_service_acess_confirmation", methods=["GET"])
def external_service_acess_confirmation():
    r = requests.get("http://172.26.128.165/wp-admin/install.php")
    return r.content
