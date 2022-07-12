
# 1 Trade A Rate

A project that lets you trade a rating for one of your android apps with somebody else that also wants a android app rated.
Add you app in this web tool or pick an other trading that is pending.
When a trade has two partys and both partys agree to do the rating both parys can commit and a rating of both apps need to be done within two weeks ?.
If both partys did the rating in the correct way both partys get points with enough points you can have more pending ratings etc.

# 2 Structure
It is a flask websites and i beleve it is a typycal flask directory structure.
However lets describe them anyway:
/alembic  version controll for the database
/assets thins like css, javascript and images
/cronscripts this is a bit special, it are the cronscripts that will scrape the playstore etc
/dist the html templates
/lib additional python classes in the form of libs (now sure if it is typylal flask structure)
/tools handy python tools to fake a database, clean the db etc (also not a typical flask structure)
/translations

# 3.5 Things used

What html templates, javascript etc, am i using for the frondend etc?

Well:


# 3 How to run it

This software depends on `pipenv` how one does `pipenv` one can find here: [pipenv](https://docs.python-guide.org/dev/virtualenvs/)

Befor you can run this app in full and not in demo or developer mode you need to provide the SECRETS that are present in the config file. you need google oauth2 api for this and to generate the google oauth2 info.

I suggest you make a run.sh file with the example contents as follows:

`
export FLASK_APP=app
export FLASK_ENV=development
export SECRETKEY='???????'
export SECRETPASS='='???????''
export CLIENTID='='???????''
export CLIENTSECRET='='???????''
export RECAPCHASECRET='='???????''
export RECAPCHASITEKEY='='???????''
export MAILUSERNAME='='???????''
export MAILPASSWORD='='???????''

flask run  --host=0.0.0.0
`

make this file executable and run it.

As to run this project in a live environment, well that is a other story for another time.

# 4 Class diagram

A crude class diagramm that displays the main app diagram:

![packages](./markdownimages/packages_treetareet.png)

![class dia](./markdownimages/classes_treetareet.png)


# 5 Packages used:
`sqlalchemy`
`flask`
`requests`
`flask-login`
`flask-mail`
`cerberus`
`flask-cachecontrol`
`sqlalchemy-utils`
`bs4`
`google-play-scraper`
`toml`
`html5lib`
`lxml`
`cssselect`
`setuptools`
`authlib`
`pylint`
