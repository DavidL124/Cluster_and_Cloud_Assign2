from numpy import (
    place,
)
from flask import Flask, make_response, jsonify, request
import tweepy
from tweepy import OAuthHandler
import time, datetime, os, copy
#from logger.logger import log

#To run the text_sentiment function:
#from twitter.text_sentiment import attach_sentiment
import json, re
from couchdb import Server, Document

#To get the suburb:
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, shape
from shapely.geometry.polygon import Polygon


##
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json, re, contractions

shapefile = gpd.read_file("SA2_2021_AUST_SHP_GDA2020/SA2_2021_AUST_GDA2020.shp")
sa2_name21 = shapefile.SA2_NAME21
sa2_code21 = shapefile.SA2_CODE21

sa3_name21 = shapefile.SA3_NAME21
sa3_code21 = shapefile.SA3_CODE21

sa4_name21 = shapefile.SA4_NAME21
sa4_code21 = shapefile.SA4_CODE21
#shapefile = shapefile.loc[shapefile["STE_NAME21"].isin(["New South Wales", "Victoria"])]

def attach_sentiment(tweet_object):

    analyzer = SentimentIntensityAnalyzer()
    sentence = tweet_object["doc"]['text']
    #Remove url from string
    sentence = re.sub(r'http\S+', '', sentence).strip()
    #fix contractions
    sentence = contractions.fix(sentence, slang=True)
    #remove punctuation from string
    sentence = re.sub(r'[^\w\s]','', sentence).strip()
    #remove extra whitespace
    sentence = re.sub(r' +', ' ', sentence).strip()
    #lowercase everything
    sentence = sentence.lower()

    sentiment_dict = analyzer.polarity_scores(sentence)
    #Using the sentiment results, can also obtain the general sentiment:
        
    neg = sentiment_dict["neg"]
    neu = sentiment_dict["neu"]
    pos = sentiment_dict["pos"]
    
    if neg > neu and neg > pos:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "negative_sentiment"})
        return tweet_object

    elif neu > pos and neu > neg:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "neutral_sentiment"})
        return tweet_object

    elif pos > neu and pos > neg:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "positive_sentiment"})
        return tweet_object

    elif pos == neu and pos == neg:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "no_clear_sentiment"})
        return tweet_object

    elif pos == neu and pos != neg:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "positive_neutral_sentiment"}) 
        return tweet_object

    elif neg == neu and neu != neg:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "negative_neutral_sentiment"})    
        return tweet_object

    elif neg == pos and neu != pos:
        tweet_object["doc"].update({"sentiments" : sentiment_dict})
        tweet_object["doc"].update({"overall_sentiment" : "positive_negative_sentiment"})    
        return tweet_object

    tweet_object["doc"].update({"sentiments" : sentiment_dict})
    return tweet_object
##

#Read through the historical_tweets data frame.
username = "user"
password = "password"

couchserver = Server("http://user:password@172.26.130.155:5984")
#couchserver = Server("http://user:pass@localhost:5984")
#for dbname in couchserver:
#    print(dbname)
#    pass

db = couchserver["historical_tweets"]

#Create a new couchdb for the adjusted tweets.

#Now iterate through the database one document at a time.
#https://stackoverflow.com/questions/55510000/how-to-retrieve-all-docs-from-couchdb-and-convert-it-as-csv-using-python
#Use for row in db.view('_all_docs'):
#https://stackoverflow.com/questions/37050231/how-to-display-all-documents-in-couchdb-using-python
#<class 'couchdb.client.Document'>
def get_suburb(tweet_coords):
    #First read in the shapefile.
    #This will be used to check if the Point objects are in Australia or not.
    #Then obtain the point as a Point object.
    pt = Point(tweet_coords[1], tweet_coords[0])
    #Now iterate through the shapes.
    count = 0
    suburb = ['', '', '', '', '', '']
    for shape in shapefile.geometry:
        if shape != None:
            if shape.contains(pt) or shape.touches(pt):
                #surburb is determined:
                suburb[0] = sa2_name21[count]
                suburb[1] = sa2_code21[count]
                #SA3
                suburb[2] = sa3_name21[count]
                suburb[3] = sa3_code21[count]
                #SA4
                suburb[4] = sa4_name21[count]
                suburb[5] = sa4_code21[count]
                return suburb
        count += 1
     #In this case the location is outside Australia.
    return ["ZZZZZZZZZ", "ZZZZZZZZZ", "ZZZZZZZZZ", "ZZZZZZZZZ", "ZZZZZZZZZ", "ZZZZZZZZZ"]

count = 0

for item in db.view('_design/GeoInfo/_view/TweetsWithGeoInfo'):

    print(item["id"], str(count))
    tweet_id = item["id"]
    tmp = dict(db[tweet_id])
    res = get_suburb(tmp["doc"]["geo"]["coordinates"])
    tmp["doc"]["suburb"] = res[0]
    tmp["doc"]["suburb_code"] = res[1]

    tmp["doc"]["suburb_SA3"] = res[2]
    tmp["doc"]["suburb_code_SA3"] = res[3]

    tmp["doc"]["suburb_SA4"] = res[4]
    tmp["doc"]["suburb_code_SA4"] = res[5]

    tmp = attach_sentiment(tmp)

    if "suburb_name" in list(tmp.keys()):
        tmp.pop("suburb_name")
    
    if "suburb" in list(tmp.keys()):
        tmp.pop("suburb")

    if "suburb_code" in list(tmp.keys()):
        tmp.pop("suburb_code")
    
    if "sentiments" in list(tmp.keys()):
        tmp.pop("sentiments")
    
    if "overall_sentiment" in list(tmp.keys()):
        tmp.pop("overall_sentiment")


    db[str(tmp["_id"])] = tmp
    count += 1

print("count is", str(count))

