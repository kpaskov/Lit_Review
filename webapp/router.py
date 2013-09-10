#!/usr/bin/python

"""

This is a small application that provides a login page for curators to view/edit the
information in Oracle database. This application is using Flask-Login package (created
by Matthew Frazier, MIT) for handling the login sessions and everything. 

"""
from flask import request, render_template, redirect, url_for, flash
from flask.app import Flask
from flask_login import login_required, current_user
from queries.associate import link_paper, get_ref_summary, \
    check_form_validity_and_convert_to_tasks
from queries.misc import get_reftemps, get_recent_history, \
    find_genes_in_abstract
from queries.move_ref import move_reftemp_to_refbad, MoveRefException
from webapp.forms import LoginForm
from webapp.litreview_logger import log_it_info, log_it
from webapp.login_handler import confirm_login_lit_review_user, \
    logout_lit_review_user, login_lit_review_user, setup_app, LoginException, \
    LogoutException, check_for_other_users
import json
import logging


app = Flask(__name__)
setup_app(app)
model = None

#Configure logger
logging.basicConfig(filename='litreview_log',#/www/logs/litreview_log', 
                    format='%(asctime)s %(levelname)s: %(message)s', 
                    level=logging.DEBUG)

def setup_app():
    setup_app(app)

@app.route("/")
def index():
    labels = []
    data = []
    try:
        if not current_user.name == 'Anonymous':
            recent_history = model.execute(get_recent_history(), current_user.name)
            sorted_history = recent_history.items()
            sorted_history.sort() 
            for k, v in sorted_history:
                labels.append(k.strftime("%m/%d"))
                data.append([v.refbad_count, v.ref_count])    
    except Exception as e:
        flash(str(e), 'error')

    return render_template("index.html", history_labels=labels, history_data=data) 

@app.route("/reference", methods=['GET', 'POST'])
@login_required
def reference():
    refs=[]
    num_of_refs=0
    try:
        check_for_other_users(current_user.name)
    
        refs = model.execute(get_reftemps(), current_user.name)  
        
        num_of_refs = len(refs) 
    except Exception as e:
        flash(str(e), 'error')
        
    return render_template('literature_review.html',
                           ref_list=refs,
                           ref_count=num_of_refs, 
                           user=current_user.name)     
    
@app.route("/reference/remove_multiple/<pmids>", methods=['GET', 'POST'])
@login_required
def remove_multiple(pmids):
    log_it_info('remove_multiple', 'BEGIN', str(pmids))
    try:
        check_for_other_users(current_user.name)
        if request.method == "POST":
            to_be_removed = pmids.split('_')
            to_be_removed.remove('')

            for pmid in to_be_removed:
                moved = model.execute(move_reftemp_to_refbad(pmid), current_user.name, commit=True)
                if not moved:
                    raise MoveRefException('An error occurred when deleting the reference for pmid=" + pmid + " from the database.')
            
            #Reference deleted
            flash("References for pmids= " + str(to_be_removed) + " have been removed from the database.", 'success')
            log_it_info('remove_multiple', 'SUCCESS')
    except Exception as e:
        flash(e.message, 'error')
        log_it_info('remove_multiple', 'FAILURE')
        logging.error(e.message)
        
    return redirect(request.args.get("next") or url_for("reference")) 

@app.route("/reference/extract_genes/<pmid>", methods=['GET'])
def extract_genes(pmid):
    log_it_info('extract_genes', 'BEGIN', str(pmid))
    try:
        check_for_other_users(current_user.name)
        words = model.execute(find_genes_in_abstract(pmid), current_user.name) 
        feature_name_words = words['features'].keys()
        alias_name_words = words['aliases'].keys()
        
        message = 'No genes found.'
        feature_message = words['feature_message']
        alias_message = words['alias_message']
        
        if feature_message != '' and alias_message != '':
            message = feature_message + ', ' + alias_message
        elif feature_message != '':
            message = feature_message
        elif alias_message != '':
            message = alias_message
        
        log_it_info('extract_genes', 'SUCCESS')    
        return_value = json.dumps({'message':message, 'highlight_red':list(alias_name_words), 'highlight_blue':list(feature_name_words)})
        return return_value 
    except Exception as e:
        flash(e.message, 'error')
        log_it_info('extract_genes', 'FAILURE')
        logging.error(e.message)
    return 'Error.'
    
    

@app.route("/reference/delete/<pmid>", methods=['GET', 'POST'])
@login_required
def discard_ref(pmid):
    log_it_info('discard_ref', 'BEGIN', str(pmid))
    response = ""
    try:
        check_for_other_users(current_user.name)
        #if request.method == "POST":
        moved = model.execute(move_reftemp_to_refbad(pmid), current_user.name, commit=True)
        if not moved:
            raise MoveRefException('An error occurred when deleting the reference for pmid=" + pmid + " from the database.')
            
        #Reference deleted
        response = "Reference for pmid=" + pmid + " has been removed from the database."
        log_it_info('discard_ref', 'SUCCESS')
    except Exception as e:
        response = "Error:<br>" + e.message
        log_it_info('discard_ref', 'FAILURE')
        logging.error(e.message)
    return response

@app.route("/reference/link/<pmid>", methods=['GET', 'POST'])
@login_required 
def link_ref(pmid):
    log_it_info('link_ref', 'BEGIN', str(pmid))
    response = ""
    try:
        check_for_other_users(current_user.name)
        log_it('check_for_other_users', 'SUCCESS')
        
        #if request.method == "POST":
        tasks = check_form_validity_and_convert_to_tasks(request.form) 
        log_it('check_form_validity_and_convert_to_tasks', 'SUCCESS', str(tasks))

        model.execute(link_paper(pmid, tasks), current_user.name, commit=True)   
        log_it('link_paper', 'SUCCESS')
            
        #Link successful
        summary = model.execute(get_ref_summary(pmid), current_user.name)  
        response = summary
        log_it_info('link_ref', 'SUCCESS')
    except Exception as e: 
        response = "Error:<br>" + e.message;
        log_it_info('link_ref', 'FAILURE')
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    log_it_info('login', 'BEGIN')
    form = LoginForm(request.form)
    try:
        if request.method == "POST" and form.validate():
            username = form.username.data.lower()
            password = form.password.data
            remember = False
            check_for_other_users(username)  
            logged_in = login_lit_review_user(username, password, model, remember)
            if not logged_in:
                raise LoginException('Login unsuccessful. Reason unknown.')
            
            #Login successful.
            flash("Logged in!", 'login')
            current_user.login()
            log_it_info('login', 'SUCCESS')
            return redirect(request.args.get("next") or url_for("index"))   
    except Exception as e:
        flash(e.message, 'error')
        log_it_info('login', 'FAILURE')
        logging.error(e.message)
        
    return render_template("login.html", form=form)

@app.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    try:
        if request.method == "POST":
            output = confirm_login_lit_review_user()
            flash(output, 'login')
            return redirect(url_for("index"))    
    except Exception as e:
        flash(e.message, 'error')
        
    return render_template("reauth.html")

@app.route("/logout")
def logout():
    log_it_info('logout', 'BEGIN')
    try:
        current_user.logout()
        logged_out = logout_lit_review_user()
        if not logged_out:
            raise LogoutException('Logout unsuccessful. Reason unknown.')
        
        #Logout successful
        flash('Logged out.', 'login')   
        log_it_info('logout', 'SUCCESS')
    except Exception as e:
        flash(e.message, 'error')
        log_it_info('logout', 'FAILURE')
        logging.error(e.message)
        
    return redirect(url_for("index"))