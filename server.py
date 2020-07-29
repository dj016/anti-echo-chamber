from flask import Flask,redirect,url_for,render_template, session, request, flash, make_response,jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import random

app= Flask(__name__)
app.secret_key="hello"

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///articles.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False
db= SQLAlchemy(app)

class article(db.Model):
    _id= db.Column("id",db.Integer,primary_key=True)
    title = db.Column("title", db.String())
    body= db.Column("body",db.String())
    date=db.Column("date",db.String())
    source=db.Column("source",db.String())
    completed= db.Column("completed",db.Boolean)


    def __init__(self,title,body,date,source,completed):
        self.title=title
        self.body=body
        self.date=date
        self.source=source
        self.completed=completed

@app.route("/getCompletedList")
def getCompletedList():
    result=[]
    news=article.query.filter_by(completed=True).all()
    for x in news:
        result.append(x._id)
    return make_response(jsonify(result),200)

@app.route("/populateDatabase")
def populateDatabase():
    with open('C:/Users/dhagarw/projects/aec/ParsedDataSet/news.json') as f:
        data=json.load(f)
        for x in data:
            art= article(x.get('title'),x.get('body'),x.get('published_at'),x.get('source'),False)
            db.session.add(art)
        db.session.commit()
    return "Database populated with all the articles !"

@app.route("/getArticleById/<uid>")
def getArticleById(uid):
    art={}
    news=article.query.filter_by(_id=uid).first()
    news.completed= True
    db.session.commit()
    art['body']=news.body
    art['title']= news.title
    art['source']= news.source
    art['date']=news.date
    art['id']=news._id
    res= make_response(jsonify(art),200)
    return  res

@app.route("/getRandomArticle")
def getRandomArticle():
    uid=random.randint(0,1427)
    art={}
    news=article.query.filter_by(_id=uid).first()
    news.completed= True
    db.session.commit()
    art['body']=news.body
    art['title']= news.title
    art['source']= news.source
    art['date']=news.date
    art['id']=news._id
    res= make_response(jsonify(art),200)
    return  res

@app.route("/getScore")
def getScore():
    score=random.randint(0,100)########################################## here we need to add the logic for the score.
    res={}
    res['score']=score
    res= make_response(jsonify(res),200)
    return res

@app.route("/getRecommendations")
def getrecommendations():
    recommendation=[]
    #############################################    Here we need to get the recomendation from the model
    for x in range(3):
        recommendation.append(random.randint(0,1427))
    result=[]
    for x in recommendation:
        art={}
        news=article.query.filter_by(_id=x).first()
        art['title']=news.title
        art['id']=x
        art['source']=news.source
        art['date']=news.date
        result.append(art)
    res= make_response(jsonify(result),200)
    return res

@app.route("/")
def home():
    if not "user" in session:
        return redirect(url_for("login"))
    else:
        return render_template("home.html",loggedin=True, user=session["user"])

@app.route("/logout")
def logout():
    session.pop("user",None) 
    news=article.query.filter_by(completed=True).all()
    for x in news:
        x.completed=False
    db.session.commit()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))



@app.route("/login",methods=["POST","GET"])
def login():
    if request.method == "POST":
        session["user"]= request.form["nm"]
        return redirect(url_for("home"))
    elif "user" in session:
        return redirect(url_for("home"))
    else:
        return render_template("login.html")


@app.route("/about")
def about():
    if "user" in session:
        return render_template("about.html",loggedin=True )
    else:
        return render_template("about.html",loggedin= False)


if __name__ =="__main__":
    db.create_all()
    app.run(debug=True)
