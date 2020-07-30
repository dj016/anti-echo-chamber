from flask import Flask,redirect,url_for,render_template, session, request, flash, make_response,jsonify
from flask_sqlalchemy import SQLAlchemy
import json
import random
import pandas as pd 
import numpy as np

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
    with open('C:/Users/dhagarw/projects/aec/Source.json',encoding="utf8") as f:
        data=json.load(f)
        for x in data:
            art= article(x.get('title'),x.get('body'),x.get('published_at'),x.get('source'),False)
            db.session.add(art)
        db.session.commit()
    return "Database populated with all the articles !"

@app.route("/getArticleById/<uid>")
def getArticleById(uid):
    session['presentArticle']=uid
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
    session['presentArticle']=uid
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
    presentArticle= int(session['presentArticle'])
    #############################################    Here we need to get the recomendation from the model
    recommendation=get_recommendations(presentArticle)
    #recommendation=[8,17,21]
    print(recommendation)
    result=[]
    for x in recommendation:
        art={}
        news=article.query.filter_by(_id=int(x)).first()
        if news != None:
            art['title']=news.title
            art['id']=str(x)
            art['source']=news.source
            art['date']=news.date
            result.append(art)
        else:
            print("couldnot find the article")
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


def load_file():
    article_list = []
    with open(f'News.json', encoding='utf8') as f:
        article_list.extend(json.load(f))

    df = pd.DataFrame(article_list)
    df_bert = pd.DataFrame(df.bert_embeddings.to_list()).add_prefix('bert_')
    df = pd.concat([df.iloc[:, 0:6], df_bert], axis = 1)
    
    return df

def load_dictcluster():
    d_cluster = {}
    dict_cluster = {}

    with open('DictCluster.json', encoding='utf8') as f:
        d_cluster = json.load(f)

    for k in d_cluster.keys():
        values = []
        values.append(np.asarray(d_cluster[k][0]))
        values.append(pd.Series(d_cluster[k][1]))
        dict_cluster[k]= values
        
    return dict_cluster

    
def f_get_distance(a, b, dist = 'euclidean'):
    """
    compute distance 
    """

    return np.sum(np.square(a-b)) if dist == 'euclidean' else -np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))


def f_get_top_n_dist_cluster(article_data, cluster_centers, top_n = 3, offset = 0):
    """
    return the farthest [offset+1, offset+n_top] sub-clusters for recommendation
    """
    
    clust_to_rec = pd.DataFrame(cluster_centers).apply(lambda x: f_get_distance(x, article_data), axis = 1).argsort()[-(1+offset):-(offset+top_n+1):-1]

    return clust_to_rec.to_list()

def f_get_article(article_data, cluster_centers, clust_assign, top_n = 3, offset = 0):
    """
    return idx of recommended articles
    """

    clust_to_rec = f_get_top_n_dist_cluster(article_data, cluster_centers, top_n, offset)

    return [np.random.choice(clust_assign.index[clust_assign == i]) for i in clust_to_rec]

def get_recommendations(article_number):
    
    n_data = 3      # from 1 to 119
    n_c = 20          # num of clusters within each topic group
    offset = n_c//2   # recommend from the farthest [offset+1, offset+n_top] clusters within each topic group
    n_top = 3
    
    df = load_file()
    dict_cluster = load_dictcluster()
    
    idx_article = article_number
    
    idx_col = df.columns[df.columns.str.contains('bert')]
    article_data = df.loc[idx_article, idx_col]
    clust_article = df.loc[idx_article, 'dominant_topic']

    clust_centers = dict_cluster[clust_article][0]
    clust_assign = dict_cluster[clust_article][1]

    idx_rec = f_get_article(article_data, clust_centers, clust_assign, top_n = n_top, offset = offset)
    
    return idx_rec


if __name__ =="__main__":
    db.create_all()
    app.run(debug=True)
