#!/usr/bin/python
from flask import Flask, render_template, request, make_response, url_for
import datetime, feedparser, json, urllib2, urllib, os

#initialize flask app instance
app = Flask(__name__)

#dict of rss site feeds
rss_feeds = {"BBC":"http://feeds.bbci.co.uk/news/rss.xml","CBS Sports":"http://rss.cbssports.com/rss/headlines","NBC News":"http://feeds.nbcnews.com/feeds/topstories"}

#abc 11 local News http://abc11.com/feed/


# set defualts to use for site
defaults = {"site":"NBC News", "city":"raleigh","currency_from":"GBP","currency_to":"USD"}

#decorator for the root dir
@app.route("/", methods=['GET', 'POST'])
#this function sets the home page
def home():
    #get site from form and get corresponding articles
    site = get_value_with_fallback("site")
    articles = get_news(site)

    #get city form and get corresponding weather details
    city = get_value_with_fallback("city")
    weather = get_weather(city)

    #get currency exchange rates
    currency_from = get_value_with_fallback("currency_from")
    currency_to = get_value_with_fallback("currency_to")
    rate, currencies = get_rate(currency_from, currency_to)

    #pass html template key/value pairs
    response = make_response(render_template("home.html", articles=articles, weather=weather, currency_from=currency_from, currency_to=currency_to, rate=rate, currencies=sorted(currencies), sites=rss_feeds, site=site))

    #set cookies
    expires = datetime.datetime.now() + datetime.timedelta(days=365)
    response.set_cookie("site", site, expires=expires)
    response.set_cookie("city", city, expires=expires)
    response.set_cookie("currency_from", currency_from, expires=expires)
    response.set_cookie("currency_to", currency_to, expires=expires)
    return response

def get_value_with_fallback(key):
    if request.form.get(key):
        return request.form.get(key)
    if request.cookies.get(key):
        return request.cookies.get(key)
    return defaults[key]

def get_news(query):
    feed = feedparser.parse(rss_feeds[query])
    articles = feed['entries']
    #return list of rss feed entries
    return articles

#this function takes an arg for weather location
def get_weather(query):
    api_url = "http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=aec4c15d465269f84e535e107e9d7fe0".format(query)
    #get api_url
    data = urllib2.urlopen(api_url).read()
    parsed = json.loads(data)
    #initialize weather variable
    weather = None
    if parsed.get("weather"):
        weather = {"city":parsed["name"],"temp":parsed["main"]["temp"],"description":(parsed["weather"][0]["description"]).title(),"country":parsed["sys"]["country"]}
    #weather key exists in dict from parsed.get, will return weather info. Else return nothing
    return weather

def get_rate(frm, to):
    api_url ="https://openexchangerates.org/api/latest.json?app_id=6a85177639c44e6eb2ee72112714e726"
    data = urllib2.urlopen(api_url).read()
    #load json data and then get rates key/value
    parsed = json.loads(data).get('rates')
    frm_rate = parsed.get(frm.upper())
    to_rate = parsed.get(to.upper())
    #return rate calculation and list of rate keys
    return (to_rate/frm_rate, parsed.keys())

@app.context_processor
def override_url_for():
    """
    Generate a new token on every request to prevent the browser from
    caching static files.
    """
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

if __name__ == '__main__':
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0')
