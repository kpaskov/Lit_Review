#!/usr/bin/python

"""

This is a small application that provides a login page for curators to view/edit the
information in Oracle database. This application is using Flask-Login package (created
by Matthew Frazier, MIT) for handling the login sessions and everything. 

"""
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_login import login_required
from modelOldSchema.model import Model
from queries.associate import associate
from queries.misc import get_reftemps, validate_genes
from queries.move_ref import move_reftemp_to_refbad, move_reftemp_to_ref
from queries.parse import ParseParameters, TaskType, Task
from webapp.config import SECRET_KEY, HOST, PORT
from webapp.login_handler import LoginResult, LogoutResult, \
    confirm_login_lit_review_user, logout_lit_review_user, login_lit_review_user, \
    setup_app

app = Flask(__name__)
conn = Model()
setup_app(app)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/reference")
@login_required
def reference():
    refs = conn.execute(get_reftemps())
    num_of_refs = len(refs)
    return render_template('literature_review.html',
                           ref_list=refs,
                           ref_count=num_of_refs)    

@app.route("/reference/delete/<pmid>", methods=['GET', 'POST'])
@login_required
def discard_ref(pmid):
    moved = conn.execute(move_reftemp_to_refbad(pmid))
    if moved:
        flash("Reference for pmid=" + pmid + " has been removed from the database!")
    else:
        flash("An error occurred when deleting the reference for pmid=" + pmid + " from the database.")
    return redirect(request.args.get("next") or url_for("reference"))

@app.route("/link_paper/<pmid>/", methods=['GET', 'POST'])
@login_required
def link_ref(pmid):
    tasks = []
    all_gene_names = set()
    for key in request.form.keys():
        if key.endswith('_cb'):
            genes = request.form[key[:-2] + 'genes']
            gene_names = []
            if genes:
                gene_names = genes.replace(',',' ').replace('|',' ').replace(';',' ').replace(':',' ').split()
                all_gene_names.update(gene_names)
                
            task_type = {'high_priority': TaskType.HIGH_PRIORITY,
                         'delay': TaskType.DELAY,
                         'htp': TaskType.HTP_PHENOTYPE_DATA,
                         'other': TaskType.OTHER_HTP_DATA,
                         'go': TaskType.GO_INFORMATION,
                         'phenotype': TaskType.CLASSICAL_PHENOTYPE_INFORMATION,
                         'headline': TaskType.HEADLINE_INFORMATION,
                         'review': TaskType.REVIEWS,
                         'add_to_db': TaskType.ADD_TO_DATABASE
                         }
            
            task = Task(task_type, gene_names, request.form[key[:-2] + 'ta'])
            tasks.append(task)
    
    
    name_to_feature = conn.execute(validate_genes(all_gene_names))
    
    #If we don't get back as many features as we have gene names, find the bad ones and show them to the user.
    if len(name_to_feature) < len(gene_names):
        bad_gene_names = set(gene_names) - set(name_to_feature.keys())
        flash("Not found Gene name(s): " + ', '.join(bad_gene_names))
    
    result = conn.execute(move_reftemp_to_ref(pmid))
    if not result:
        flash("Problem moving temporary reference for pmid = " + pmid + " to the reference table.")
    
    
    result = conn.execute(associate(pmid, name_to_feature, tasks))
    if result is not None:
        flash("Reference for pmid = " + pmid + " has been added into the database and associated with the following data:<p>" + result)
    else:
        flash("An error occurred when linking the reference for pmid = " + pmid + " to the info you picked/entered.")
    return redirect(request.args.get("next") or url_for("reference"))

@app.route("/login", methods=["GET", "POST"])
def login():
    result = None
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        remember = request.form.get("remember", "no") == "yes"
        conn.connect(username, password)
        
        if conn.is_connected():
            result = login_lit_review_user(username, remember)
        else:
            result = LoginResult.BAD_USERNAME_PASSWORD
            
        output = {
            LoginResult.SUCCESSFUL: "Logged in!",
            LoginResult.NOT_ON_LIST: "You are not allowed to use this interface. Contact sgd-programmers to add your name to the list.",
            LoginResult.UNSUCCESSFUL: "Sorry, but you could not log in.",
            LoginResult.BAD_USERNAME_PASSWORD: "You typed in an invalid username/password"
        }[result]
        print output  
        flash(output)
        
        if result == LoginResult.SUCCESSFUL:
            return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html")

@app.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    if request.method == "POST":
        output = confirm_login_lit_review_user()
        flash(output)
        return redirect(url_for("index")) 
    return render_template("reauth.html")

@app.route("/logout")
def logout():
    result = logout_lit_review_user()
    output = {
        LogoutResult.SUCCESSFUL: 'Logged out.'
    }[result]
    flash(output)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.secret_key = SECRET_KEY
    app.run(host=HOST, port=PORT, debug=True) 