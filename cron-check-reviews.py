#!/usr/bin/env python

from config import make_session
from models import User, Trade, App, Review
import google_play_scraper
import pprint


def feedreviews(app, langs):
    for lang in langs:
        result, continuation_token = google_play_scraper.reviews(
            app.appidstring,
            lang=lang, # defaults to 'en'
            count=200,
            # continuation_token=continuation_token
        )

        for x in result:
            if 'content' in x and 'at' in x and 'score' in x and 'userName' in x:
                try:
                    aitem = dbsession.query(Review).filter(Review.google_id==x['reviewId']).first()
                    if not aitem:
                        aitem = Review()
                        aitem.reviewtext = x['content']
                        aitem.reviewtime = x['at']
                        aitem.reviewrating = x['score']
                        aitem.locale = lang
                        aitem.google_id = x['reviewId']
                        aitem.username = x['userName']
                    dbsession.add(aitem)

                except Exception as e:
                    print(e)
        dbsession.commit()


dbsession = make_session()
allapps = dbsession.query(App).all()

for value in allapps:

    print(value.all_users())
    test = set([item for sublist in value.all_users() for item in sublist])
    # print(test)
    # listoflangs = list(set([x.locale for x in test if x.locale]))
    #
    #
    # feedreviews(value, listoflangs)



dbsession.close()
