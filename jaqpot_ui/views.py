#from xlrd.xlsx import ET
import datetime
import json
import sys
import urllib2
from collections import OrderedDict
#import logging ; logger = logging.getLogger(__name__)
#logger.warn("method is "+method)
import requests
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, HttpResponse, FileResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from elasticsearch import Elasticsearch

from jaqpot_ui.create_dataset import create_dataset, chech_image_mopac, create_dataset2, create_and_clean_dataset, \
    create_dataset2_with_title, create_and_clean_dataset2_with_title
#from jaqpot_ui.decorators import token_required
from jaqpot_ui.forms import UserForm, BibtexForm, TrainForm, FeatureForm, ContactForm, SubstanceownerForm, \
    UploadFileForm, TrainingForm, InputForm, NoPmmlForm, SelectPmmlForm, DatasetForm, ValidationForm, ExperimentalForm, \
    UploadForm, \
    InterlabForm, ValidationSplitForm, ReadAcrossTrainingForm, InputFormExpX
from jaqpot_ui.get_dataset import paginate_dataset, get_prediction_feature_of_dataset, \
    get_prediction_feature_name_of_dataset, get_number_of_not_null_of_dataset
from jaqpot_ui.get_params import get_params, get_params3, get_params4
from settings import EMAIL_HOST_USER, SERVER_URL


# Home page
def index(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    return render(request, "mainPage.html", {'token': token, 'username': username})


# Authenticate user
def login(request):
    if request.method == 'GET':
        form = UserForm(initial={'username': ''})

        return render(request, "login.html", {
            'form': form,
            'next': request.GET.get('next', '')
        })
        #return render(request, "login.html", {'form': form})
        #return render_to_response('login.html', form ,context_instance=RequestContext(request))
    if request.method == 'POST':
        form = UserForm(request.POST)
        if not form.is_valid():
            return render(request, "login.html", {'form': form})
        else:
            username = form['username'].value()
            password = form['password'].value()

            # send request to external authenticator
            try:
                r = requests.post(SERVER_URL + '/aa/login', data={'username': username, 'password': password})
                if r.status_code == 200:
                    response = json.loads(r.text)
                    token = 'Bearer ' + str(response['authToken'])

                    # set session request
                    #var  = 'Bearer '
                    request.session['token'] = token
                    request.session['username'] = username

                    next = request.POST.get('next', '/')
                    if next:
                        return redirect(next.split("'")[1])
                    else:
                        return redirect('/')

                elif r.status_code == 401:
                    error = "Wrong username or password"
                    return render(request, "login.html", {'form': form, 'error': error})
                else:
                    error = "An error occurred. Please try again later."
                    return render(request, "login.html", {'form': form, 'error': error})
            except Exception as e:
                return render(request, "error.html", {'server_error':e })


#User logout
def logout(request):
    token = request.session.get('token', '')
    headers = {'Accept': 'application/json', 'Authorization': token}
    if token:
        # send request to logout from auth server
       # try:
            #r = requests.post(SERVER_URL + '/aa/logout', headers=headers)
            #if r.status_code == 200:
                # remove from session
                request.session['token'] = ''
                request.session['username'] = ''

                # send to home page
               # return redirect('/')
            #else:
                return redirect('/login')
        #except Exception as e:
         #   return render(request, "error.html", {'server_error':e, })
    else:
        return redirect('/')


#List of all tasks
##@token_required
def task(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    request.session.get('token', '')

    #go to tasks
    all_tasks = []
    #get all tasks with status Running
    headers = {'Accept': 'text/uri-list', 'Authorization': token}
    headers = {'Accept': 'application/json', 'Authorization': token}
    try:
        res = requests.get(SERVER_URL+'/task?status=RUNNING&start=0&max=10000', headers=headers)
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    list_resp = json.loads(res.text)
    if res.status_code == 200:
        list_run=[]

        for l in list_resp:
            list_run.append({'name': l['_id'], 'status': "running", 'meta': l['meta']})
            all_tasks.append({'name': l['_id'], 'status': "running", 'meta': l['meta']})
        list_run = json.dumps(list_run)
        list_run = json.loads(list_run)

        #get all tasks with status Completed
        try:
            res = requests.get(SERVER_URL+'/task?status=COMPLETED&start=0&max=10000', headers=headers)

        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = json.loads(res.text)
        list_complete=[]
        for l in list_resp:
            list_complete.append({'name': l['_id'], 'status': "completed", 'meta': l['meta']})
            all_tasks.append({'name': l['_id'], 'status': "completed", 'meta': l['meta']})
        list_complete= json.dumps(list_complete)
        list_complete = json.loads(list_complete)

        #get all tasks with status Cancelled
        try:
            res = requests.get(SERVER_URL+'/task?status=CANCELLED&start=0&max=10000', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = json.loads(res.text)

        list_cancelled=[]
        for l in list_resp:

            list_cancelled.append({'name': l['_id'], 'status': "cancelled", 'meta': l['meta']})
            all_tasks.append({'name': l['_id'], 'status': "cancelled", 'meta': l['meta']})
        list_cancelled= json.dumps(list_cancelled)
        list_cancelled = json.loads(list_cancelled)

        #get all tasks with status Error
        try:
            res = requests.get(SERVER_URL+'/task?status=ERROR&start=0&max=10000', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = json.loads(res.text)

        list_error=[]
        for l in list_resp:

            list_error.append({'name': l['_id'], 'status': "error", 'meta': l['meta']})
            all_tasks.append({'name': l['_id'], 'status': "error", 'meta': l['meta']})
        list_error= json.dumps(list_error)
        list_error = json.loads(list_error)


        #get all tasks with status Queued
        try:
            res = requests.get(SERVER_URL+'/task?status=QUEUED&start=0&max=10000', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = json.loads(res.text)

        list_queued=[]
        for l in list_resp:

            list_queued.append({'name': l['_id'], 'status': "queued", 'meta': l['meta']})
            all_tasks.append({'name': l['_id'], 'status': "queued", 'meta': l['meta']})
        list_queued= json.dumps(list_queued)
        list_queued = json.loads(list_queued)
        all_tasks= json.dumps(all_tasks)
        all_tasks = json.loads(all_tasks)

        if request.method == 'GET':
            return render(request, "task.html", {'token': token, 'username': username, 'all_tasks': all_tasks ,'list_run': list_run, 'list_complete': list_complete, 'list_cancelled': list_cancelled, 'list_error': list_error, 'list_queued': list_queued})

#More information about each task
##@token_required
def taskdetail(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')
    #status = request.GET.get('status')
    if request.is_ajax():
        token = request.session.get('token', '')
        username = request.session.get('username', '')
        print('hh')
        output = request.GET.getlist('output')[0]
        name = request.GET.getlist('name')[0]
        print(name)
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            #res = requests.get(SERVER_URL+'/task/ocGR1A5o47Jb', headers=headers)
            res = requests.get(SERVER_URL+'/task/'+name, headers=headers)
            print('hg')
            print(res.text)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        '''if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})'''
        data = json.loads(res.text)
        print('hgvft')
        if data['meta']['date']:
            date=data['meta']['date'].split('T')[0]
            data['meta']['date'] = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%y')
        data = json.dumps(data)
        status = json.loads(res.text)['status']
        print status
        counter=0
        while (status != "COMPLETED"):
            counter=counter+1
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                return render(request, "error.html", {'token': token, 'username': username, 'name': name, 'error': error})
            if(status == "CANCELLED"):
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
            if(status == "REJECTED"):
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
            if(status == "QUEUED"):
                return HttpResponse(data)
            if(status == "RUNNING"):
                return HttpResponse(data)
            if(status == "QUEUED" and counter >100):
                print counter
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
        return HttpResponse(data)

    if request.method == 'GET':
        #get task details in rdf format
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/task/'+name, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        output = json.loads(res.text)
        try:
            if output['meta']['date']:
                date=output['meta']['date'].split('T')[0]
                output['meta']['date'] = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%y')
        except Exception as e:
             return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        status = json.loads(res.text)['status']
        if(status == "ERROR"):
            error = "An error occurred while processing your request.Please try again."
            return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
            elif(status == "CANCELLED"):
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
            elif(status == "REJECTED"):
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
            elif(status == "QUEUED"):
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
            else:
                try:
                    res = requests.get(SERVER_URL+'/task/'+name, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                status = json.loads(res.text)['status']
                print status
                return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})
        return render(request, "taskdetail.html", {'token': token, 'username': username, 'name': name, 'output': output})

#stop running task
##@token_required
def stop_task(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    id = request.GET.get('id')
    if request.method == 'GET':
        #stop task
        headers = {'content-type': 'text/uri-list', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL+'/task/'+id, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return render(request, "mainPage.html", {'token': token, 'username': username })

#List of all BibTex
##@token_required
def bibtex(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')

    if request.method == 'GET':
        final_output=[]
        #get all bibtex
        headers = {'Accept': 'application/json', 'Authorization': token}
        headers1 = {'Accept': 'text/uri-list', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/bibtex?bibtype=Entry&&&start=0&max=10000', headers=headers1)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        list_resp = res.text
        if res.status_code == 403:
            error = "This request is forbidden (e.g., no Authorization token is provided)"
            return render(request, "bibtex.html",
                          {'token': token, 'username': username, 'name': name, 'error': error})
        if res.status_code == 401:
            error = "You are not authorized to access this resource"
            return render(request, "bibtex.html",{'token': token, 'username': username, 'name': name, 'error': error})
        if res.status_code == 500:
            error = "Internal server error - this request cannot be served."
            return render(request, "bibtex.html",{'token': token, 'username': username, 'name': name, 'error': error})
        if res.status_code == 200:
            list_resp = list_resp.splitlines()
            for l in list_resp:
                id = l.split('/bibtex/')[1]
                try:
                    r = requests.get(l, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if r.status_code >= 400:         return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(r.text)})
                #get json data
                info=json.loads(r.text)
                final_output.append( {"id":id, "info": info })

            return render(request, "bibtex.html", {'token': token, 'username': username, 'name': name, 'final_output': final_output})

#Details of each bibtex
#@token_required
def bib_detail(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')
    id = request.GET.get('id')

    if request.is_ajax():
        id = request.GET.getlist('id')[0]
        op = request.GET.getlist('op')[0]
        path = request.GET.getlist('path')[0]
        value = request.GET.getlist('value')[0]
        body = json.dumps([{'op': op, 'path': path, 'value': value}])
        #body = jsonpatch.JsonPatch([{'op': op, 'path': path, 'value': value}])
        headers = {"Content-Type":"application/json-patch+json",'Authorization': token }
        #headers = {'Accept': 'application/json-patch+json', 'Authorization': token}
        try:
            res = requests.patch(url=SERVER_URL+'/bibtex/'+id, data=body, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return HttpResponse(res.text)


    if request.method == 'GET':
        #send request
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/bibtex/'+id, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = res.text
        #get json data
        details = json.loads(res.text)
        return render(request, "bibdetail.html", {'token': token, 'username': username, 'name': name, 'details': details, 'id':details['_id'],})

#Delete Bibtex
#@token_required
def bib_delete(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    id = request.GET.get('id')

    if request.method == 'GET':
        #delete bibtex
        headers = {'content-type': 'text/uri-list', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL+'/bibtex/'+id, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return render(request, "mainPage.html", {'token': token, 'username': username })

#Add a Bibtex
#@token_required
def add_bibtex(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')

    if request.method == 'GET':
        form = BibtexForm(initial={'author': "", 'abstract': "",'title': "",'copyright': "",'address':"", 'year':"", 'pages':"", 'volume':"", 'journal':"", 'keyword':"", 'url':""})

        return render(request, "addbibtex.html", {'token': token, 'username': username, 'name': name, 'form': form})
    if request.method == 'POST':
        form = BibtexForm(request.POST)
        if not form.is_valid():
            error = "Invalid value"
            params = {'form': form, 'error': error, 'token': token, 'username': username, 'name': name}
            return render(request, "addbibtex.html", params)

        json_b= { "bibType":form['type'].value(), 'author': form['author'].value(), 'abstract': form['abstract'].value(), 'title': form['title'].value(),
                 'copyright': form['copyright'].value(),'address':form['address'].value(), 'year': form['year'].value(),
                 'pages':form['pages'].value(), 'volume':form['volume'].value(), 'journal': form['journal'].value(), 'keywords': form['keyword'].value(),
                  'url':form['url'].value()}

        bibtex_entry = json.dumps(json_b)
        bibtex_entry = json.loads(bibtex_entry)
        bibtex_entry = json.dumps(bibtex_entry)

        #send request with the new entry for saving
        headers = {'Content-Type': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/bibtex', data = bibtex_entry, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return render(request, "mainPage.html", {'token': token, 'username': username, 'name': name})

#@token_required
def sub(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')

    if request.method == 'GET':
        return render(request, "bibdetail.html", {'token': token, 'username': username, 'name': name})

#User interface
#@token_required
def user(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')

    if request.method == 'GET':
        headers = {'content-type': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/user/'+ username, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        contacts = json.loads(res.text)
        try:
            res1 = requests.get(SERVER_URL+'/user/'+ username+'/quota', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        percentage = json.loads(res1.text)
        percentage = json.dumps(percentage)
        contacts = json.dumps(contacts)

        return render(request, "user_details.html", {'token': token, 'username': username, 'name': name, 'contacts': contacts, 'percentage': percentage})

#Train model
#@token_required
def trainmodel(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    page = request.GET.get('page')
    last = request.GET.get('last')

    if request.method == 'GET':
        dataset=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_datasets= int(res.headers.get('total'))
        if total_datasets%20 == 0:
            last = total_datasets/20
        else:
            last = (total_datasets/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            print k
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        print res.text
        for d in data:
            dataset.append({'name': d['_id'], 'meta': d['meta']})
        print dataset
        proposed=[]
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta']})
        return render(request, "choose_dataset.html", {'token': token, 'username': username, 'entries2': dataset, 'page': page, 'last':last, 'proposed':proposed})

#choose dataset for training
#@token_required
def choose_dataset(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    form = TrainForm(initial={})

    if request.method == 'GET':
        dataset = request.GET.get('dataset')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm?class=ot:Classification&start=0&max=100', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        classification_alg=json.loads(res.text)
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm?class=ot:Regression&start=0&max=100', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        regression_alg = json.loads(res.text)
        return render(request, "train_model.html", {'token': token, 'username': username, 'classification_alg': classification_alg, 'regression_alg': regression_alg, 'form':form, 'dataset': dataset})
    if request.method == 'POST':
        algorithms=[]
        for alg in request.POST.getlist('radio'):
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.get(SERVER_URL+'/algorithm/'+alg, headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            info = json.loads(res.text)
            algorithms.append({"alg":alg, "info":info })
        dataset = request.GET.get('dataset')
        print dataset
        print algorithms
        if algorithms == []:

            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.get(SERVER_URL+'/algorithm?class=ot:Classification&start=0&max=100', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            classification_alg = json.loads(res.text)
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.get(SERVER_URL+'/algorithm?class=ot:Regression&start=0&max=100', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            regression_alg = json.loads(res.text)
            error = "Please select algorithm."
            return render(request, "train_model.html", {'token': token, 'username': username, 'classification_alg': classification_alg, 'regression_alg': regression_alg, 'form':form, 'dataset': dataset, 'error':error})
        else:
            request.session['alg'] = algorithms[0]['alg']
            request.session['data'] = dataset
            return redirect('/change_params', {'token': token, 'username': username,})

#change algorithms parameters, select pmml, prediction feature, scaling and doa for training
#@token_required
def change_params(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        form = UploadFileForm()
        tform = TrainingForm()
        inputform = InputForm()
        nform = NoPmmlForm()
        pmmlform = SelectPmmlForm()
        dataset = request.session.get('data', '')
        algorithms = request.session.get('alg', '')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print res.text
        al = json.loads(res.text)
        print al
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
            return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'uploadform':form, 'tform':tform ,'features':features, 'inputform':inputform, 'nform':nform, 'pmmlform': pmmlform})


    if request.method == 'POST':
        #get parameters of algorithm
        params={}
        print request.POST

        tform = TrainingForm(request.POST)
        inputform = InputForm(request.POST)
        form = UploadFileForm(request.POST, request.FILES)
        nform = NoPmmlForm(request.POST)
        pmmlform = SelectPmmlForm(request.POST)
        dataset = request.session.get('data', '')
        algorithms = request.session.get('alg', '')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        if request.POST.getlist('parameters'):
            parameters = request.POST.getlist('parameters')
            '''for p in parameters:
                params.append({'name': p, 'value': request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)'''
            for p in parameters:
                #params.update({p: request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)
            print al['parameters']
            for a in al['parameters']:
                params.update({a['name']: a['value']})
            params, al = get_params3(request, parameters, al)
            print json.dumps(params)

        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        predicted_features = json.loads(res2.text)

        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
        if not tform.is_valid():
            return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
        #get transformations
        transformations=""
        prediction_feature = ""
        if request.POST.get('variables') == "none":
            if not nform.is_valid():
                return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            transformations = ""
            prediction_feature = nform['pred_feature'].value()
        elif request.POST.get('variables') == "pm":
            transformations = SERVER_URL+'/pmml/'+pmmlform['pmml'].value()
            prediction_feature = pmmlform['predicted_feature'].value()
        elif request.POST.get('variables') == "input":
            prediction_feature = inputform['output'].value()
            feature_list = inputform['input'].value()
            if not inputform.is_valid():
                return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            headers = {'Accept': 'application/json',  'Authorization': token}
            feat=""
            for f in feature_list:
                feat += str(f)+','
            body = {'features': feat}
            try:
                res = requests.post(SERVER_URL+'/pmml/selection', headers=headers, data=body)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            response = json.loads(res.text)
            transformations = SERVER_URL+'/pmml/'+response['_id']

        elif request.POST.get('variables') == "file":
            prediction_feature = form['feature'].value()
            if form.is_valid:
                if 'file' in request.FILES:
                    pmml= request.FILES['file'].read()
                    print pmml
                    headers = {'Content-Type': 'application/xml',  'Authorization': token }
                    try:
                        res = requests.post(SERVER_URL+'/pmml', headers=headers, data=pmml)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    response = json.loads(res.text)
                    transformations = SERVER_URL+'/pmml/'+response['_id']
                else:
                    return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'tform':tform, 'features':features, 'inputform': inputform, 'nform': nform})

         #get scaling
        scaling=""
        if request.POST.get('scaling') == "scaling1":
            scaling=""
        elif request.POST.get('scaling') == "scaling2":
            scaling=SERVER_URL+'/algorithm/scaling'
        elif request.POST.get('scaling') == "scaling3":
            scaling=SERVER_URL+'/algorithm/standarization'
        #get doa
        doa=""
        if request.POST.get('doa') == "doa1":
            doa=""
        elif request.POST.get('doa') == "doa2":
            doa=SERVER_URL+'/algorithm/leverage'
        elif request.POST.get('doa') == "doa3":
            doa=SERVER_URL+'/algorithm/leverage'
        algorithms = request.session.get('alg', '')
        dataset = request.session.get('data', '')
        title= tform['modelname'].value()
        description= tform['description'].value()
        body = {'dataset_uri': SERVER_URL+'/dataset/'+dataset, 'scaling': scaling, 'doa': doa, 'title': title, 'description':description, 'transformations':transformations, 'prediction_feature': prediction_feature, 'parameters':json.dumps(params), 'visible': True}
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/algorithm/'+algorithms, headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        print json.dumps(params)
        return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})


#Conformer
#@token_required
def conformer(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        return render(request, "conformer.html", {'token': token, 'username': username})
    if request.method == 'POST':
        #add task for descriptors calculation
        return redirect('/task', {'token': token, 'username': username})

#list of models
#@token_required
def model(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        models = []
        #get all models
        headers = {'Accept': 'application/json', "Authorization": token}
        #get total number of models
        try:
            res = requests.get(SERVER_URL+'/model?start=0&max=1', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_models= res.headers.get('total')
        try:
            res = requests.get(SERVER_URL+'/model?start=0&max='+total_models, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = json.loads(res.text)
        #for each model
        for l in list_resp:
            models.append({'name': l['_id'], 'meta': l['meta'] })
        models = json.dumps(models)
        models = json.loads(models)
        #Get selected models
        try:
            res1 = requests.get(SERVER_URL+'/model/featured?start=0&max=10', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_model = json.loads(res1.text)
        proposed = []
        for p in proposed_model:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        return render(request, "model.html", {'token': token, 'username': username, 'models':models, 'proposed':proposed })

#Display details for each model
#@token_required
def model_detail(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')

    #get task details in rdf format
    headers = {'Accept': 'application/json', 'Authorization': token}
    try:
        res = requests.get(SERVER_URL+'/model/'+name, headers=headers)
    except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    details = json.loads(res.text)
    algorithm=details['algorithm']['_id']
    if algorithm:
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithm, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        alg_details=json.loads(res.text)
    else:
        alg_details = ""
    try:
        res = requests.get(SERVER_URL+'/model/'+name+'/required', headers=headers)
        required= json.loads(res.text)
        required_feature = []
        for r in required:
            required_feature.append({'feature': r['uri']})
    except Exception as e:
        required_feature=""
    if res.status_code >= 400:
        #return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        required_feature=""
    if request.method == 'GET':
        return render(request, "model_detail.html", {'token': token, 'username': username, 'details':details, 'name':name, 'alg': alg_details, 'required':required_feature, 'algorithm':algorithm})

#Delete selected model
#@token_required
def model_delete(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    id = request.GET.get('id')
    #delete model
    headers = {'Accept': 'application/json', "Authorization": token}
    try:
        res = requests.delete(SERVER_URL+'/model/'+id, headers=headers)
    except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    reply = res.text
    return redirect('/model')

#@token_required
def model_pmml(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    name = request.GET.get('name')
    headers = {'Accept': 'application/xml', "Authorization": token}

    try:
        res = requests.get(SERVER_URL+'/model/'+name+'/pmml', headers=headers)
    except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    #details = json.loads(res.text)
    if res.status_code == 200:
        pmml = res.text
        response = HttpResponse(pmml, content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="pmml_'+name+'.xml"'
        return response
    else:
        #response = HttpResponse(res.text,  mimetype="application/json")
        print res.text
        headers = {'Accept': 'application/json', "Authorization": token}
        try:
            res1 = requests.get(SERVER_URL+'/model/'+name, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        details = json.loads(res1.text)
        algorithm=details['algorithm']['_id']
        if algorithm:
            try:
                res2 = requests.get(SERVER_URL+'/algorithm/'+algorithm, headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res2.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
            alg_details=json.loads(res2.text)
        else:
            alg_details = ""
        try:
            res3 = requests.get(SERVER_URL+'/model/'+name+'/required', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res3.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res3.text)})
        required= json.loads(res3.text)
        required_feature = []
        for r in required:
            required_feature.append({'feature': r['uri']})

        return render(request, "model_detail.html", {'token': token, 'username': username, 'details':details, 'name':name, 'alg': alg_details, 'required':required_feature, 'error': res.text})

#list of features
#@token_required
def features(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    page = request.GET.get('page')
    last = request.GET.get('last')

    if request.method == 'GET':
        headers = {'Accept': 'application/json', 'Authorization': token}
        if page:
            page1=int(page) * 20 - 20
            k=str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/feature?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            elif last:
                try:
                    res = requests.get(SERVER_URL+'/feature?start='+last+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/feature?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})

        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/feature?start=0&max=20', headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        features=[]
        if res.status_code == 403:
            error = "This request is forbidden (e.g., no Authorization token is provided)"
            return render(request, "features.html", {'token': token, 'username': username, 'error': error})

        if res.status_code == 401:
            error = "You are not authorized to access this resource"
            return render(request, "features.html", {'token': token, 'username': username, 'error': error})

        if res.status_code == 500:
            error = "Internal server error - this request cannot be served."
            return render(request, "features.html", {'token': token, 'username': username, 'error': error})

        if res.status_code == 200:
            #get json feautures
            feature= json.loads(res.text)
            for f in feature:
                features.append({'name': f['_id'], 'meta': f['meta']})
            if len(features)< 20:
                last= page
            return render(request, "features.html", {'token': token, 'username': username, 'features': features, 'page': page, 'last': last})

#Display details of each feature
#@token_required
def feature_details(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')

    if request.method == 'GET':
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/feature/'+name, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        feature_detail=json.loads(res.text)
        return render(request, "feature_details.html", {'token': token, 'username': username, 'name': name, 'feature_detail': feature_detail})

#Add feature
#@token_required
def add_feature(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name')
    if request.method == 'GET':
        form = FeatureForm(initial={'feature': ""})

        return render(request, "add_feature.html", {'token': token, 'username': username, 'name': name, 'form': form})
    if request.method == 'POST':
        form = FeatureForm(request.POST)
        if not form.is_valid():
            error = "Invalid value"
            params = {'form': form, 'error': error, 'token': token, 'username': username, 'name': name}
            return render(request, "add_feature.html", params)

        json_b= {'feature': form['feature'].value() }
        feature_entry = json.dumps(json_b)
        print feature_entry
        #it should send request with the new entry for saving
        return render(request, "mainPage.html", {'token': token, 'username': username, 'name': name})

#Delete feature
#@token_required
def feature_delete(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    id = request.GET.get('id')
    if request.method == 'GET':
        #delete bibtex
        headers = {'content-type': 'text/uri-list', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL+'/feature/'+id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return render(request, "mainPage.html", {'token': token, 'username': username })

#List of algorithms
#@token_required
def algorithm(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
         algorithms = []
         #get all algorithms
         headers = {'Accept': 'application/json', 'Authorization': token}
         try:
             res = requests.get(SERVER_URL + '/algorithm?class=ot:Classification&start=0&max=100', headers=headers)
         except Exception as e:
             return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
         if res.status_code >= 400:
             return render(request, "error.html", {'token': token, 'username': username, 'error': json.loads(res.text)})
         classification_alg = json.loads(res.text)
         headers = {'Accept': 'application/json', 'Authorization': token}
         try:
             res = requests.get(SERVER_URL + '/algorithm?class=ot:Regression&start=0&max=100', headers=headers)
         except Exception as e:
             return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
         if res.status_code >= 400:
             return render(request, "error.html", {'token': token, 'username': username, 'error': json.loads(res.text)})
         regression_alg = json.loads(res.text)
         return render(request, "algorithm.html",
                       {'token': token, 'username': username, 'classification_alg': classification_alg,
                        'regression_alg': regression_alg, 'dataset': dataset})


#Display details of each algorithm
#@token_required
def algorithm_detail(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    algorithm = request.GET.get('name')

    if request.method == 'GET':
        #get task details in rdf format
        headers = {'content-type': 'text/uri-list', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithm, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        #get rdf response and convert to json data with details for bibtex
        details = json.loads(res.text)
        return render(request, "algorithm_detail.html", {'token': token, 'username': username, 'details': details, 'id': algorithm})

#Delete algorithm
#@token_required
def algorithm_delete(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    id = request.GET.get('id')
    if request.method == 'GET':
        #delete algorithm
        headers = {'content-type': 'text/uri-list', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL+'/algorithm/'+id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return render(request, "mainPage.html", {'token': token, 'username': username})

#List of dataset
#@token_required
def dataset(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    page = request.GET.get('page')
    last = request.GET.get('last')
    dataset=[]
    if request.method == 'GET':
        dataset=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_datasets= int(res.headers.get('total'))
        if total_datasets%20 == 0:
            last = total_datasets/20
        else:
            last = (total_datasets/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=100', headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        for d in data:
            dataset.append({'name': d['_id'], 'meta': d['meta']})
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured?start=0&max=100', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        proposed = []
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        return render(request, "dataset.html", {'token': token, 'username': username, 'dataset': dataset, 'page': page, 'last':last, 'proposed':proposed})

#Display details of each dataset
#@token_required
def dataset_detail(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    name = request.GET.get('name', '')
    page = request.GET.get('page', '')

    data_detail, last, page = paginate_dataset(request, name, token, username, page)
    if data_detail and last and page:
            a=[]
            #a=collections.OrderedDict()
            # a contains all compound's properties
            for key in sorted(data_detail['dataEntry']):
                print key
                for k, value in key.items():
                    if k =='values':
                        counter=0
                        for m,n in value.items():
                            if m not in a:
                                a.append(m)
                                '''a[counter]=m
                                counter=counter+1'''

            properties={}
            new=[]
            new_a=[]
            compound = []
            for k in sorted(data_detail['features']):
                for i in range(len(a)):
                    if k['uri'] == a[i]:
                        new.append(k)
                        new_a.append(a[i])

            #get response json
            for key in data_detail['dataEntry']:
                properties[key['compound']['URI']] = []
                properties[key['compound']['URI']].append({"compound": key['compound']['URI']})
                properties[key['compound']['URI']].append({"name": key['compound']['name']})

                #for each compound
                for k, value in key.items():
                    if k =='values':
                        for i in range(len(new_a)):
                            #if a compound haven't value for a property add its value Null
                            if new_a[i] in value:
                                properties[key['compound']['URI']].append({"prop": new_a[i], "value": value[new_a[i]]})
                            else:
                                properties[key['compound']['URI']].append({"prop":  new_a[i], "value": "NULL"})


            return render(request, "dataset_detail.html", {'token': token, 'username': username, 'name': name, 'data_detail':data_detail, 'properties': properties, 'a': a, 'new': new, 'page':page, 'last':last})

#Delete selected dataset
#@token_required
def dataset_delete(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    id = request.GET.get('id')
    #delete dataset
    headers = {'Accept': 'application/json', "Authorization": token}
    try:
        res = requests.delete(SERVER_URL+'/dataset/'+id, headers=headers)
    except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    reply = res.text
    print reply
    return redirect('/data')

#@token_required
def dispay_predicted_dataset(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    name = request.GET.get('name', '')
    page = request.GET.get('page', '')
    model = request.GET.get('model', '')
    headers = {'Accept': 'application/json', 'Authorization': token}
    try:
        r = requests.get(SERVER_URL+'/dataset/'+name+'?rowStart=0&rowMax=0&colStart=0&colMax=0', headers=headers)
    except Exception as e:
        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if r.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(r.text)})
    data_detail, last, page = paginate_dataset(request, name, token, username, page)
    if data_detail and last and page:
        headers = {'Accept': 'text/uri-list', "Authorization": token}
        try:
            res = requests.get(SERVER_URL+'/model/'+model+'/predicted', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        predicted =  res.text
        predicted = predicted.splitlines()
        properties={}
        new=[]
        for i in range(len(predicted)):
            for k in data_detail['features']:
                if k['uri'] == predicted[i]:
                    new.append(k['name'])
        try:
            res = requests.get(SERVER_URL+'/model/'+model+'/dependent', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        dependent =  res.text
        if dependent:
            dependent = dependent.splitlines()
            for i in range(len(dependent)):
                for k in data_detail['features']:
                    if k['uri'] == dependent[i]:
                        new.append(k['name'])
        #get response json
        for key in data_detail['dataEntry']:
            properties[key['compound']['URI']] = []
            properties[key['compound']['URI']].append({"compound": key['compound']['URI']})
            properties[key['compound']['URI']].append({"name": key['compound']['name']})
            print predicted
            for p in predicted:
                properties[key['compound']['URI']].append({"prop": p, "value": key['values'][p]})

        return render(request, "predicted_dataset.html", {'token': token, 'username': username, 'name': name,'data_detail':data_detail, 'properties': properties, 'new': new, 'a':predicted, 'page':page, 'last':last, 'model':model })

#Predict model
#@token_required
def predict(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        m = []
        #get all models
        headers = {'Accept': 'application/json', "Authorization": token}
        try:
            res = requests.get(SERVER_URL+'/model?start=0&max=10000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = res.text
        models = json.loads(res.text)
        print models
        for mod in models:
                m.append({'name': mod['_id'], 'meta': mod['meta']})
        #Get selected models
        try:
            res1 = requests.get(SERVER_URL+'/model/featured?start=0&max=10', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_model = json.loads(res1.text)
        proposed = []
        for p in proposed_model:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        #Display all models for selection
        return render(request, "predict_model.html", {'token': token, 'username': username, 'my_models': m, 'proposed':proposed})


#@token_required
def predict_model(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    #Get the current page
    page = request.GET.get('page')
    #Get the last page
    last = request.GET.get('last')
    if request.method == 'GET':
        #Get the selected model for prediction
        model = request.GET.get('model')
        #Save selected model at session model
        request.session['model'] = model
        dataset=[]
        #Get required feature of selected model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            required_res = requests.get(SERVER_URL+'/model/'+model+'/required?keepOrder=true', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if required_res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(required_res.text)})
        model_req = json.loads(required_res.text)
        #check if is needed image or mocap
        image, mopac = chech_image_mopac(model_req)
        #Firstly, get the datasets of first page if user selects different page get the datasets of the selected page
        if page:
            page1=int(page) * 20 - 20
            k=str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            elif last:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+last+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})

        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        for d in data:
            dataset.append({'name': d['_id'], 'title':d['meta']['titles'][0], 'description': d['meta']['descriptions'][0]})

        if len(dataset)< 20:
            last= page
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured?start=0&max=100', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        proposed = []

        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        #Display all datasets for selection
        return render(request, "predict.html", {'token': token, 'username': username, 'dataset': dataset, 'page': page, 'last':last, 'model_req': model_req, 'model' : model, 'image':image, 'mopac':mopac, 'proposed':proposed})
    if request.method == 'POST':
        #Get the selected model for prediction from session
        selected_model= request.session.get('model', '')
        #Get the method of prediction
        method = request.POST.get('radio_method')
        #Get the required model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            required_res = requests.get(SERVER_URL+'/model/'+selected_model+'/required?keepOrder=true', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if required_res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(required_res.text)})
        required_res = json.loads(required_res.text)
        print required_res
        if request.is_ajax():
            img_descriptors = request.POST.getlist('img_desc[]')
            mopac_descriptors = request.POST.getlist('mopac_desc[]')
            if 'excel_data' in request.POST:
                if img_descriptors:
                    data = request.POST.get('img_desc[]')
                    data = json.loads(data)
                    new_data = create_dataset(data, username, required_res, img_descriptors, mopac_descriptors)
                    json_data = json.dumps(new_data)
                else:
                    data = request.POST.get('excel_data')
                    print data
                    data = json.loads(data)
                    n_data=[]
                    for d in data:
                        n_d = {}
                        n_d1 = {}
                        for key, value in d.items():
                            new_val = value.replace(',', '.')
                            n_d1[''+key+'']=new_val
                            n_d.update(n_d1)
                        n_data.append(n_d)
                    print n_data
                    data = n_data
                    print data
                    #Get data from excel and create dataset to the appropriate format
                    new_data = create_dataset(data,username,required_res, img_descriptors, mopac_descriptors)
                    json_data = json.dumps(new_data)
                headers1 = {'Content-type': 'application/json', 'Authorization': token}
                try:
                    res = requests.post(SERVER_URL+'/dataset', headers=headers1, data=json_data)
                    print res.text
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return JsonResponse({'server_error': json.loads(res.text), "ERROR_REDIRECT": "1"})
                dataset = res.text
                print dataset
                headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': token,}
                body = {'dataset_uri': dataset, 'visible': True}
                print body
                print selected_model
                try:
                    res = requests.post(SERVER_URL+'/model/'+selected_model, headers=headers, data=body)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return JsonResponse({'server_error': json.loads(res.text), "ERROR_REDIRECT": "1"})
                response = json.loads(res.text)
                print response
                id = response['_id']
                print id
                return HttpResponse(id)
        if method == 'select_dataset':
            #Get the selected dataset
            dataset = request.POST.get('radio')
            print request.POST
            if dataset == "" or dataset == None:
                m = []
                #get all models
                headers = {'Accept': 'application/json', "Authorization": token}
                try:
                    res = requests.get(SERVER_URL+'/model?start=0&max=10000', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                models = json.loads(res.text)
                for mod in models:
                        m.append({'name': mod['_id'], 'meta': mod['meta']})
                return render(request, "predict.html", {'token': token, 'username': username,'selected_model': selected_model, 'page': page, 'last':last,'error':"You should select a dataset."})
            else:
                headers = {'Content-Type': 'application/x-www-form-urlencoded', "Authorization": token}
                body = {'dataset_uri': SERVER_URL+'/dataset/'+dataset, 'visible': True}
                try:
                    res = requests.post(SERVER_URL+'/model/'+selected_model, headers=headers, data=body)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                response = json.loads(res.text)
                print response
                id = response['_id']
                return redirect('/t_detail?name='+id+'&model='+selected_model)
@csrf_exempt
def calculate_image_descriptors(request):
    #get data uri od upload image
    data_uri = request.POST.get('data_uri')
    print data_uri
    #send request to data uri
    body = {'image': data_uri, }
    try:
        res = requests.post('http://test.jaqpot.org:8880/imageAnalysis/service/analyze', data=body)
    except Exception as e:
                    return render(request, "error.html", {'server_error':e, })
    #if res.status_code >= 400:
    #      return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    response = json.loads(res.text)
    for r in response:
        if r['id'] == "Average Particle":
            average_particle = r
    print average_particle
    return HttpResponse(json.dumps(average_particle))

#@token_required
def calculate_mopac_descriptors(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    headers = {'Authorization': token}
    mopac_file = request.GET.get('mopac_file')
    body = {'pdbfile': mopac_file ,}
    try:
        res = requests.post('http://test.jaqpot.org:8080/algorithms/service/mopac/calculate', headers=headers, data=body)
    except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    response = json.loads(res.text)
    print response
    return HttpResponse(json.dumps(response))

@csrf_exempt
#@token_required
def error(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    server_error = request.POST.get('server_error')
    server_error = json.loads(server_error)
    return render(request, "error.html", {'token': token, 'username': username,'error':server_error})


#Search
#@token_required
def search(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        search = request.GET.get('search')
        models=[]
        headers = {'Accept': 'text/uri-list', "Authorization": token}
        try:
            res = requests.get(SERVER_URL+'/model?start=0&max=10000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = res.text
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
        #get each line
        list_resp = list_resp.splitlines()
        i=1
        for l in list_resp:
            l = l.split('/model/')[1]
            models.append({'name': l})
            es.index(index='name', doc_type='models', id=i, body={'name': l})
            i=i+1
        models = json.dumps(models)
        models = json.loads(models)
        print es.get(index='name', doc_type='models', id=2)
        return HttpResponse(models)

#Contact form
#@token_required
def contact(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'POST': # If the form has been submitted...
        form = ContactForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            sender = form.cleaned_data['sender']

            recipients = [ EMAIL_HOST_USER ]
            #css the sender mail
            recipients.append(sender)
            send_mail(subject, message, sender, recipients)
            return HttpResponseRedirect('/thanks/') # Redirect after POST
        else:

            return render_to_response('contact_form.html', {'form': form, 'token': token, 'username': username}, context_instance=RequestContext(request))
    else:
        form = ContactForm() # An unbound form

    return render_to_response('contact_form.html', {'form': form, 'token': token, 'username': username}, context_instance=RequestContext(request))

#redirect to thanks page
#@token_required
def thanks(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        return render(request, "thanks.html", {'token': token, 'username': username})

#@token_required
def compound(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        compound= [{'name':'compound1'}, {'name':'compound2'}, {'name':'compound3'}, {'name':'compound4'}]
        return render(request, "compound.html", {'token': token, 'username': username, 'compound': compound})

#@token_required
def compound_details(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    name = request.GET.get('name', '')
    if request.method == 'GET':
        return render(request, "compound_detail.html", {'token': token, 'username': username, 'name': name})

#redirect to source page
#@token_required
def source(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        return render(request, "source.html", {'token': token, 'username': username})

#redirect to documentation page
#@token_required
def documentation(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        return render(request, "documentation.html", {'token': token, 'username': username})

#@token_required
def explore(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    entries = [ "data", "data2", "data3"]
    entries2 = [ "compound", "compound2", "compound3"]
    entries3 = [ "conformer", "conformer2", "conformer3"]
    if request.method == 'GET':
        return render(request, "explore.html", {'token': token, 'username': username, 'entries': entries, 'entries_2':entries2, 'entries_3':entries3})

#Create dataset
#@token_required
def all_substance(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    page=request.GET.get('page')
    if page:
        headers = {'Accept': 'application/json', 'Authorization': token}
        page1=str(int(page)-1)
        try:
            res = requests.get('https://data.enanomapper.net/substanceowner?page='+page1+'&pagesize=20', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        substance_owner=json.loads(res.text)
        substance_owner = substance_owner['facet']
    else:
        headers = {'Accept': 'application/json', 'Authorization': token}
        page=1
        try:
            res = requests.get('https://data.enanomapper.net/substanceowner', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        substance_owner=json.loads(res.text)
        substance_owner = substance_owner['facet']

    if request.method == 'GET':
        form = SubstanceownerForm(initial={'substanceowner': ''})
        if len(substance_owner)<20:
            last=page
            return render(request, "substance.html", {'token': token, 'username': username, 'form':form, 'substance_owner': substance_owner, 'page': page, 'last':last,})
        else:
            return render(request, "substance.html", {'token': token, 'username': username, 'form':form, 'substance_owner': substance_owner, 'page': page})
    if request.method == 'POST':
        method = request.POST.get('radio_method')
        if method=="select":
            substance_owner = request.POST.get('radio')
            if not substance_owner:
                form = SubstanceownerForm(initial={'substanceowner': ''})
                page=request.GET.get('page')
                if page:
                    headers = {'Accept': 'application/json', 'Authorization': token}
                    page1=str(int(page)-1)
                    try:
                        res = requests.get('https://data.enanomapper.net/substanceowner?page='+page1+'&pagesize=20', headers=headers)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    substance_owner=json.loads(res.text)
                    substance_owner = substance_owner['facet']
                else:
                    headers = {'Accept': 'application/json', 'Authorization': token}
                    page=1
                    try:
                        res = requests.get('https://data.enanomapper.net/substanceowner', headers=headers)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    substance_owner=json.loads(res.text)
                    substance_owner = substance_owner['facet']
                error = "Please select substance owner."
                return render(request, "substance.html", {'token': token, 'username': username, 'form':form, 'substance_owner': substance_owner, 'page': page, 'error':error})
            else:
                substance_owner = 'https://data.enanomapper.net/substanceowner/'+substance_owner
                request.session['substanceowner']= substance_owner
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:
                    res = requests.get(substance_owner+'/substance', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                substances=json.loads(res.text)
                request.session['substances'] = substances
                return redirect('/select_substance', {'token': token, 'username': username})
        elif method=="complete":
            form = SubstanceownerForm(request.POST)
            if form.is_valid(): # All validation rules pass
                substanceowner = form.cleaned_data['substanceowner']
                print substanceowner
                request.session['substanceowner']=substanceowner
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:
                    res = requests.get(substanceowner+'/substance', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                substances=json.loads(res.text)
                print substances
                request.session['substances'] = substances
                return redirect('/select_substance', {'token': token, 'username': username})
            else:
                error = "Fill in Substance owner id."
                return render(request, "substance.html", {'token': token, 'username': username, 'form':form, 'error':error,'substance_owner': substance_owner, 'page': page})

#@token_required
def select_substance(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    if request.is_ajax():
            checkall = request.GET.get('checkall')
            print checkall
            print('is ajax')
            substances = request.session.get('substances', '')
            sel = substances['substance']
            checkall=[]
            for s in sel:
                checkall.append(s['URI'])
            print checkall
            checkall=json.dumps(checkall)
            #return redirect('/select_substance', {'token': token, 'username': username, 'checkall':checkall})
            return HttpResponse(checkall)

    if request.method == 'GET':
        substances = request.session.get('substances', '')
        print substances
        return render(request, "select_substance.html", {'token': token, 'username': username, 'substances':substances['substance']})
@csrf_exempt
#@token_required
def get_substance(request):
     token = request.session.get('token', '')
     username = request.session.get('username', '')
     data = []
     if request.method == "POST" and request.is_ajax:
        data = request.POST.getlist('data[]')
        request.session['selected_substances'] = data
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res1 = requests.get(SERVER_URL+'/enm/property/categories', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        properties=json.loads(res1.text)
        request.session['properties'] = properties
        print data
     return HttpResponse(data)

#@token_required
def select_properties(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')


    if request.method == 'GET':
        properties = request.session.get('properties', '')
        return render(request, "properties.html", {'token': token, 'username': username, 'properties':properties})
    if request.method == 'POST':
        sub= request.POST.getlist('checkbox')
        final={}
        pr=[]
        if "P-CHEM" in sub:
            pr.append("P-CHEM")
        if "ENV FATE" in sub:
            pr.append("ENV FATE")
        if "TOX" in sub:
            pr.append("TOX")
        if "ECOTOX" in sub:
            pr.append("ECOTOX")
        i=0
        j=1
        for p in pr:
            sunbst=[]
            if j<len(pr):
                while sub[i] != pr[j]:
                    sunbst.append(sub[i])
                    i=i+1
                final.update({p : sunbst[1:]})
            else:
                 while i<len(sub):
                     sunbst.append(sub[i])
                     i=i+1
                 final.update({p : sunbst[1:]})
            j=j+1
        print final
        request.session['selected_properties'] = final
        return redirect('/descriptors', {'token': token, 'username': username})

#@token_required
def select_descriptors(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')


    if request.method == 'GET':
        form=DatasetForm()
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res1 = requests.get(SERVER_URL+'/enm/descriptor/categories', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        descriptors=json.loads(res1.text)
        print descriptors
        return render(request, "descriptors.html", {'token': token, 'username': username, 'descriptors':descriptors, 'form':form})
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if not form.is_valid():
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res1 = requests.get(SERVER_URL+'/enm/descriptor/categories', headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res1.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
            descriptors=json.loads(res1.text)
            return render(request, "descriptors.html", {'token': token, 'username': username, 'descriptors':descriptors, 'form':form})
        title = form['title'].value()
        description = form['description'].value()
        select_descriptors = request.POST.getlist('checkbox')
        substanceowner = request.session.get('substanceowner', '')
        selected_substances = request.session.get('selected_substances', '')
        selected_properties = request.session.get('selected_properties', '')
       # headers = {'content-type': 'application/json', 'Authorization': token}
       # body = json.dumps()
       # try:
       #     res = requests.post(url=SERVER_URL+'/enm/bundle', data=body, headers=headers)
       # except Exception as e:
       #         return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
       # if res.status_code >= 400:
       #     return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        headers = {'content-type': 'application/json', 'Authorization': token,}
        body = json.dumps({'substanceOwner': substanceowner, 'substances': selected_substances, 'properties': selected_properties, 'descriptors':select_descriptors, 'title': title, 'description':description})
        try:
            res = requests.post(url=SERVER_URL+'/enm/dataset', headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        response = json.loads(res.text)
        task = response['_id']
        #return redirect('/task', {'token': token, 'username': username})
        return render(request, "new_task.html", {'token': token, 'username': username, 'task':task})

#Validate
#@token_required
def validate(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    page = request.GET.get('page')
    last = request.GET.get('last')
    method = request.GET.get('method')
    request.session['method'] = method

    if request.method == 'GET':
        dataset=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_datasets= int(res.headers.get('total'))
        if total_datasets%20 == 0:
            last = total_datasets/20
        else:
            last = (total_datasets/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            print k
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        print res.text
        for d in data:
            dataset.append({'name': d['_id'], 'meta': d['meta']})
        print dataset
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        proposed = []
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        return render(request, "choose_dataset_validate.html", {'token': token, 'username': username, 'entries2': dataset, 'page': page, 'last':last, 'proposed': proposed,})

#choose dataset for validation
#@token_required
def choose_dataset_validate(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    method = request.session.get('method', '')
    print method
    form = TrainForm(initial={})
    if request.method == 'GET':
        dataset = request.GET.get('dataset')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm?class=ot:Classification&start=0&max=100', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        classification_alg = json.loads(res.text)
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm?class=ot:Regression&start=0&max=100', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        regression_alg = json.loads(res.text)
        return render(request, "train_model.html", {'token': token, 'username': username, 'classification_alg': classification_alg, 'regression_alg': regression_alg, 'form':form, 'dataset': dataset, 'validate': True})
    if request.method == 'POST':
        algorithms=[]
        for alg in request.POST.getlist('radio'):
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.get(SERVER_URL+'/algorithm/'+alg, headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            info = json.loads(res.text)
            algorithms.append({"alg":alg, "info":info })
        dataset = request.GET.get('dataset')
        print dataset
        print algorithms
        if algorithms == []:
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.get(SERVER_URL+'/algorithm?class=ot:Classification&start=0&max=100', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            classification_alg = json.loads(res.text)
            try:
                res = requests.get(SERVER_URL+'/algorithm?class=ot:Regression&start=0&max=100', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            regression_alg = json.loads(res.text)
            error = "Please select algorithm."
            return render(request, "train_model.html", {'token': token, 'username': username, 'classification_alg': classification_alg, 'regression_alg': regression_alg, 'form':form, 'dataset': dataset, 'error':error, 'validate':True})
        else:
            request.session['alg'] = algorithms[0]['alg']
            request.session['data'] = dataset
            if method == "cross":
                return redirect('/valid_params', {'token': token, 'username': username,})
            elif method == "split":
                return redirect('/valid_split', {'token': token, 'username': username,})

#@token_required
def valid_params(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    method = request.session.get('method', '')
    print method
    if request.method == 'GET':
        dataset = request.session.get('data', '')
        algorithms = request.session.get('alg', '')
        vform = ValidationForm()
        form = UploadFileForm()
        inputform = InputForm()
        nform = NoPmmlForm()
        pmmlform = SelectPmmlForm()
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2',headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            #vform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]

        return render(request, "validate.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms,'features':features, 'vform':vform, 'uploadform':form, 'inputform':inputform, 'nform':nform, 'pmmlform':pmmlform})
    if request.method == 'POST':
        print("post")

        #get parameters of algorithm
        params={}
        print request.POST
       # parameters = request.POST.getlist('parameters')
       # for p in parameters:
        #    params.append({'name': p, 'value': request.POST.get(''+p)})
        vform = ValidationForm(request.POST)
        inputform = InputForm(request.POST)
        form = UploadFileForm(request.POST, request.FILES)
        nform = NoPmmlForm(request.POST)
        pmmlform = SelectPmmlForm(request.POST)
        dataset = request.session.get('data', '')
        algorithms = request.session.get('alg', '')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})

        al = json.loads(res.text)
        if request.POST.getlist('parameters'):
            parameters = request.POST.getlist('parameters')
            '''for p in parameters:
                params.append({'name': p, 'value': request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)'''
            for p in parameters:
                # params.update({p: request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value'] = request.POST.get('' + p)
            print al['parameters']
            for a in al['parameters']:
                params.update({a['name']: a['value']})
            params, al = get_params3(request, parameters, al)
            print json.dumps(params)

        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            #vform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        if not vform.is_valid():
            print vform
            return render(request, "validate.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'vform':vform,'al':al, 'uploadform':form, 'inputform':inputform, 'nform':nform, 'pmmlform':pmmlform})

         #get transformations
        transformations=""
        prediction_feature = ""
        if request.POST.get('variables') == "none":
            print nform
            if not nform.is_valid():
                return render(request, "validate.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'vform':vform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            transformations = ""
            prediction_feature = nform['pred_feature'].value()
        elif request.POST.get('variables') == "pm":
            transformations = SERVER_URL+'/pmml/'+pmmlform['pmml'].value()
            prediction_feature = pmmlform['predicted_feature'].value()
        elif request.POST.get('variables') == "input":
            prediction_feature = inputform['output'].value()
            feature_list = inputform['input'].value()
            if not inputform.is_valid():
                return render(request, "validate.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'vform':vform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            headers = {'Accept': 'application/json',  'Authorization': token}
            feat=""
            for f in feature_list:
                feat += str(f)+','
            body = {'features': feat}
            try:
                res = requests.post(SERVER_URL+'/pmml/selection', headers=headers, data=body)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            response = json.loads(res.text)
            transformations = SERVER_URL+'/pmml/'+response['_id']

        elif request.POST.get('variables') == "file":
            prediction_feature = form['feature'].value()
            if form.is_valid:
                if 'file' in request.FILES:
                    pmml= request.FILES['file'].read()
                    print pmml
                    headers = {'Content-Type': 'application/xml',  'Authorization': token }
                    try:
                        res = requests.post(SERVER_URL+'/pmml', headers=headers, data=pmml)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    print res.text
                    response = json.loads(res.text)
                    transformations = SERVER_URL+'/pmml/'+response['_id']
                else:
                    return render(request, "validate.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'vform':vform, 'features':features, 'inputform': inputform, 'nform': nform})

        folds = vform['folds'].value()
        stratify = vform['stratify'].value()
        print stratify
        seed = 0
        if stratify == "random":
            seed = vform['seed'].value()
        print seed
        scaling = vform['scaling'].value()
        if scaling == "scaling1":
            scaling=""
        elif scaling == "scaling2":
            scaling=SERVER_URL+'/algorithm/scaling'
        elif scaling == "scaling3":
            scaling=SERVER_URL+'/algorithm/standarization'


        print prediction_feature
        print params

        if stratify != "random" and "normal":
            body = {'training_dataset_uri': SERVER_URL+'/dataset/'+dataset, 'prediction_feature': prediction_feature, 'algorithm_params':json.dumps(params), 'algorithm_uri': SERVER_URL+'/algorithm/'+algorithms, 'folds':folds, 'transformations':transformations, 'seed':seed, 'scaling':scaling}
        else:
            body = {'training_dataset_uri': SERVER_URL+'/dataset/'+dataset, 'prediction_feature': prediction_feature, 'algorithm_params':json.dumps(params), 'algorithm_uri': SERVER_URL+'/algorithm/'+algorithms, 'folds':folds, 'stratify': stratify, 'transformations':transformations, 'seed':seed, 'scaling':scaling}
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/validation/training_test_cross', headers=headers, data=body)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})

#@token_required
def valid_split(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    method = request.session.get('method', '')



    if request.method == 'GET':
        dataset = request.session.get('data', '')
        algorithms = request.session.get('alg', '')
        vform = ValidationSplitForm()
        form = UploadFileForm()
        inputform = InputForm()
        nform = NoPmmlForm()
        pmmlform = SelectPmmlForm()
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2',headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features,})
        else:
            features = predicted_features['features']
            #vform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        print al
        return render(request, "validate_split.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms,'features':features, 'vform':vform, 'uploadform':form, 'inputform':inputform, 'nform':nform, 'pmmlform':pmmlform})
    if request.method == 'POST':
        print("post")
        #get parameters of algorithm
        params={}
        print request.POST

        vform = ValidationSplitForm(request.POST)
        inputform = InputForm(request.POST)
        form = UploadFileForm(request.POST, request.FILES)
        nform = NoPmmlForm(request.POST)
        pmmlform = SelectPmmlForm(request.POST)
        dataset = request.session.get('data', '')
        algorithms = request.session.get('alg', '')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        if request.POST.getlist('parameters'):
            parameters = request.POST.getlist('parameters')
            '''for p in parameters:
                params.append({'name': p, 'value': request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)'''
            for p in parameters:
                # params.update({p: request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value'] = request.POST.get('' + p)
            print al['parameters']
            for a in al['parameters']:
                params.update({a['name']: a['value']})
            params, al = get_params3(request, parameters, al)
            print json.dumps(params)
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        predicted_features = json.loads(res2.text)

        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        print al
        if not vform.is_valid():
            print al
            return render(request, "validate_split.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'vform':vform,'al':al, 'parameters':params, 'uploadform':form, 'inputform':inputform, 'nform':nform, 'pmmlform':pmmlform})
        #get transformations
        transformations=""
        prediction_feature = ""
        if request.POST.get('variables') == "none":
            print nform
            if not nform.is_valid():
                return render(request, "validate_split.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'vform':vform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            transformations = ""
            prediction_feature = nform['pred_feature'].value()
        elif request.POST.get('variables') == "pm":
            transformations = SERVER_URL+'/pmml/'+pmmlform['pmml'].value()
            prediction_feature = pmmlform['predicted_feature'].value()
        elif request.POST.get('variables') == "input":
            prediction_feature = inputform['output'].value()
            feature_list = inputform['input'].value()
            if not inputform.is_valid():
                return render(request, "validate_split.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'vform':vform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            headers = {'Accept': 'application/json',  'Authorization': token}
            feat=""
            for f in feature_list:
                feat += str(f)+','
            body = {'features': feat}
            try:
                res = requests.post(SERVER_URL+'/pmml/selection', headers=headers, data=body)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            response = json.loads(res.text)
            transformations = SERVER_URL+'/pmml/'+response['_id']

        elif request.POST.get('variables') == "file":
            prediction_feature = form['feature'].value()
            if form.is_valid:
                if 'file' in request.FILES:
                    pmml= request.FILES['file'].read()
                    print pmml
                    headers = {'Content-Type': 'application/xml',  'Authorization': token }
                    try:
                        res = requests.post(SERVER_URL+'/pmml', headers=headers, data=pmml)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    response = json.loads(res.text)
                    transformations = SERVER_URL+'/pmml/'+response['_id']
                else:
                    return render(request, "validate_split.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'vform':vform, 'features':features, 'inputform': inputform, 'nform': nform})

         #get scaling
        scaling=""
        if request.POST.get('scaling') == "scaling1":
            scaling=""
        elif request.POST.get('scaling') == "scaling2":
            scaling=SERVER_URL+'/algorithm/scaling'
        elif request.POST.get('scaling') == "scaling3":
            scaling=SERVER_URL+'/algorithm/standarization'

        split_ratio = vform['split_ratio'].value()

        stratify = vform['stratify'].value()
        print stratify
        seed = 0
        if stratify == "random":
            seed = vform['seed'].value()
        print seed

        print prediction_feature
        print params
        if stratify != "random" and "normal":
            body = {'training_dataset_uri': SERVER_URL+'/dataset/'+dataset, 'prediction_feature': prediction_feature, 'algorithm_params':json.dumps(params), 'algorithm_uri': SERVER_URL+'/algorithm/'+algorithms, 'transformations':transformations, 'scaling': scaling,'split_ratio':split_ratio}
        else:
            body = {'training_dataset_uri': SERVER_URL+'/dataset/'+dataset, 'prediction_feature': prediction_feature, 'algorithm_params':json.dumps(params), 'algorithm_uri': SERVER_URL+'/algorithm/'+algorithms, 'transformations':transformations, 'scaling': scaling,'split_ratio':split_ratio, 'stratify':stratify, 'seed':seed}
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/validation/training_test_split', headers=headers, data=body)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})

#External validation
#@token_required
def external_validation(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    # Get the current page
    page = request.GET.get('page')
    # Get the last page
    last = request.GET.get('last')
    if request.method == 'GET':
        # Get the selected model for prediction
        model = request.GET.get('model')
        # Save selected model at session model
        request.session['model'] = model
        dataset = []
        # Get required feature of selected model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            required_res = requests.get(SERVER_URL + '/model/' + model + '/required?keepOrder=true', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if required_res.status_code >= 400:
            return render(request, "error.html",
                          {'token': token, 'username': username, 'error': json.loads(required_res.text)})

        model_req = json.loads(required_res.text)

        # Get predicting feature of selected model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            predicted_res = requests.get(SERVER_URL + '/model/' + model + '/predicting', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if predicted_res.status_code >= 400:
            return render(request, "error.html",
                          {'token': token, 'username': username, 'error': json.loads(predicted_res.text)})
        model_pred=json.loads(predicted_res.text)
        model_req.append(model_pred[0])



        # check if is needed image or mocap
        image, mopac = chech_image_mopac(model_req)
        # Firstly, get the datasets of first page if user selects different page get the datasets of the selected page
        if page:
            page1 = int(page) * 20 - 20
            k = str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL + '/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return render(request, "error.html",
                                  {'token': token, 'username': username, 'error': json.loads(res.text)})
            elif last:
                try:
                    res = requests.get(SERVER_URL + '/dataset?start=' + last + '&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return render(request, "error.html",
                                  {'token': token, 'username': username, 'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL + '/dataset?start=' + k + '&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return render(request, "error.html",
                                  {'token': token, 'username': username, 'error': json.loads(res.text)})

        else:
            page = 1
            try:
                res = requests.get(SERVER_URL + '/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
            if res.status_code >= 400:
                return render(request, "error.html",
                              {'token': token, 'username': username, 'error': json.loads(res.text)})
        data = json.loads(res.text)
        for d in data:
            dataset.append(
                {'name': d['_id'], 'title': d['meta']['titles'][0], 'description': d['meta']['descriptions'][0]})

        if len(dataset) < 20:
            last = page
        try:
            res1 = requests.get(SERVER_URL + '/dataset/featured?start=0&max=100', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username, 'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        proposed = []

        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta']})
        # Display all datasets for selection
        return render(request, "choose_dataset_ext_valid.html",
                      {'token': token, 'username': username, 'dataset': dataset, 'page': page, 'last': last,
                       'model_req': model_req, 'model': model, 'image': image, 'mopac': mopac, 'proposed': proposed})
    if request.method == 'POST':
        # Get the selected model for prediction from session
        selected_model = request.session.get('model', '')
        # Get the method of prediction
        method = request.POST.get('radio_method')
        # Get the required model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            required_res = requests.get(SERVER_URL + '/model/' + selected_model + '/required?keepOrder=true', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if required_res.status_code >= 400:
            return render(request, "error.html",
                          {'token': token, 'username': username, 'error': json.loads(required_res.text)})
        required_res = json.loads(required_res.text)

        # Get predicting feature of selected model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            predicted_res = requests.get(SERVER_URL + '/model/' + selected_model + '/predicting', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if predicted_res.status_code >= 400:
            return render(request, "error.html",
                          {'token': token, 'username': username, 'error': json.loads(predicted_res.text)})
        model_pred = json.loads(predicted_res.text)
        required_res.append(model_pred[0])

        print required_res
        if request.is_ajax():
            img_descriptors = request.POST.getlist('img_desc[]')
            mopac_descriptors = request.POST.getlist('mopac_desc[]')
            if 'excel_data' in request.POST:
                if img_descriptors:
                    data = request.POST.get('img_desc[]')
                    data = json.loads(data)
                    new_data = create_dataset(data, username, required_res, img_descriptors, mopac_descriptors)
                    json_data = json.dumps(new_data)
                else:
                    data = request.POST.get('excel_data')
                    print data
                    data = json.loads(data)
                    n_data = []
                    for d in data:
                        n_d = {}
                        n_d1 = {}
                        for key, value in d.items():
                            new_val = value.replace(',', '.')
                            n_d1['' + key + ''] = new_val
                            n_d.update(n_d1)
                        n_data.append(n_d)
                    print n_data
                    data = n_data
                    print data
                    # Get data from excel and create dataset to the appropriate format
                    new_data = create_dataset(data, username, required_res, img_descriptors, mopac_descriptors)
                    json_data = json.dumps(new_data)
                headers1 = {'Content-type': 'application/json', 'Authorization': token}
                try:
                    res = requests.post(SERVER_URL + '/dataset', headers=headers1, data=json_data)
                    print res.text
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return JsonResponse({'server_error': json.loads(res.text), "ERROR_REDIRECT": "1"})
                dataset = res.text
                print dataset
                body = {'test_dataset_uri': dataset,
                        'model_uri': SERVER_URL + '/model/' + selected_model}
                print body
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:

                    res = requests.post(SERVER_URL + '/validation/test_set_validation', headers=headers, data=body)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return render(request, "error.html",
                                  {'token': token, 'username': username, 'error': json.loads(res.text)})
                response = json.loads(res.text)
                print response
                id = response['_id']
                return HttpResponse(id)
        if method == 'select_dataset':
            # Get the selected dataset
            dataset = request.POST.get('radio')
            print request.POST
            if dataset == "" or dataset == None:
                m = []
                # get all models
                headers = {'Accept': 'application/json', "Authorization": token}
                try:
                    res = requests.get(SERVER_URL + '/model?start=0&max=10000', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return render(request, "error.html",
                                  {'token': token, 'username': username, 'error': json.loads(res.text)})
                models = json.loads(res.text)
                for mod in models:
                    m.append({'name': mod['_id'], 'meta': mod['meta']})
                return render(request, "choose_dataset_ext_valid.html",
                              {'token': token, 'username': username, 'selected_model': selected_model, 'page': page,
                               'last': last, 'error': "You should select a dataset."})
            else:
                body = {'test_dataset_uri': SERVER_URL + '/dataset/' + dataset,
                        'model_uri': SERVER_URL + '/model/' + selected_model }
                print body
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:

                    res = requests.post(SERVER_URL + '/validation/test_set_validation', headers=headers, data=body)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
                if res.status_code >= 400:
                    return render(request, "error.html",
                                  {'token': token, 'username': username, 'error': json.loads(res.text)})
                response = json.loads(res.text)
                print response
                id = response['_id']
                return redirect('/t_detail?name=' + id + '&model=' + selected_model)

#Choose model for external validation
#@token_required
def ext_valid_model(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    #dataset= request.GET.get('dataset')

    if request.method == 'GET':
        m = []
        #get all models
        headers = {'Accept': 'application/json', "Authorization": token}
        try:
            res = requests.get(SERVER_URL+'/model?start=0&max=10000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = res.text
        models = json.loads(res.text)
        print models
        for mod in models:
                m.append({'name': mod['_id'], 'meta': mod['meta']})
        #Get selected models
        try:
            res1 = requests.get(SERVER_URL+'/model/featured?start=0&max=10', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_model = json.loads(res1.text)
        proposed = []
        for p in proposed_model:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        #Display all models for selection
        return render(request, "ext_validation.html", {'token': token, 'username': username, 'my_models': m, 'proposed':proposed,})
#
#@token_required
def get_model_ext_valid(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        model = request.GET.get('model')
        dataset = request.GET.get('dataset')
        body = {'test_dataset_uri': SERVER_URL+'/dataset/'+dataset, 'model_uri': SERVER_URL+'/model/'+model,}
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/validation/test_set_validation', headers=headers, data=body)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})

#Display report after validation
#@token_required
def report(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    if request.is_ajax():
        print('hi')
        id = request.GET.getlist('id')[0]
        op = request.GET.getlist('op')[0]
        path = request.GET.getlist('path')[0]
        value = request.GET.getlist('value')[0]
        print value
        print path
        print request.GET.getlist('value')
        try:
            split_path = path.split('/values')[0]
            split_path = split_path.replace ("_", " ")
            path=split_path+'/values'+path.split('/values')[1]
        except:
            path = path.replace("_", " ")
        print path
        print op

        body = json.dumps([{'op': op, 'path': path, 'value': value}])
        print body
        #body = jsonpatch.JsonPatch([{'op': op, 'path': path, 'value': value}])
        headers = {"Content-Type":"application/json-patch+json",'Authorization': token }
        #headers = {'Accept': 'application/json-patch+json', 'Authorization': token}
        try:
            res = requests.patch(url=SERVER_URL+'/report/'+id, data=body, headers=headers)
            print res.status_code
            print res.text
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        return HttpResponse(res.text)
    if request.method == 'GET':
        name = request.GET.get('name')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/report/'+name, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        report = json.loads(res.text, object_pairs_hook=OrderedDict)
        return render(request, "report.html", {'token': token, 'username': username, 'report': report, 'name':name})


#Experimental design
#@token_required
def experimental(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    page = request.GET.get('page')
    last = request.GET.get('last')
    last = 1
    page=1

    if request.method == 'GET':
        dataset=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_datasets= int(res.headers.get('total'))
        if total_datasets%20 == 0:
            last = total_datasets/20
        else:
            last = (total_datasets/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        for d in data:
            dataset.append({'name': d['_id'], 'meta': d['meta']})
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured?start=0&max=100', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        proposed = []
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        return render(request, "exp_dataset.html", {'token': token, 'username': username, 'dataset': dataset, 'page': page, 'last':last, 'proposed':proposed})

#Select parameters for experimental design with input
#@token_required
def experimental_params(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        dataset = request.GET.get('dataset')
        request.session['data'] = dataset
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res1 = requests.get(SERVER_URL + '/dataset/' + dataset, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username, 'error': json.loads(res1.text)})
        data_detail = json.loads(res1.text)
        try:
            model = json.loads(res1.text)['byModel']
            print model
            # model = 'A0fU5rK7B64r'
            try:
                res = requests.get(SERVER_URL + '/model/' + model, headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
            if res.status_code >= 400:
                return render(request, "error.html",
                              {'token': token, 'username': username, 'error': json.loads(res.text)})
            algorithms = json.loads(res.text)['algorithm']['_id']
            if "expdesign" in algorithms:

                model_detail = json.loads(res.text)
                predictedFeatures = model_detail['predictedFeatures']
                params = json.loads(res.text)['parameters']
                new = []
                for k in sorted(data_detail['features']):
                    new.append(k)
                '''if algorithms == "ocpu-expdesign2-x":
                    algorithms = "ocpu-expdesign2-xy"
                    par = {}
                    for k,v in params.items():
                        if k != "newY":
                            par.update({k:v})
                    params = par'''

                return render(request, "exp_dataset_detail.html",
                              {'token': token, 'username': username, 'new': new, 'data_detail': data_detail,
                               'predicted': predictedFeatures, 'prediction': prediction_feature, 'model': model_detail,
                               'dataset_name': dataset, 'params': params})
        except Exception as e:
            print(e)
        form = UploadForm()
        tform = ExperimentalForm()
        #nform = NoPmmlForm()
        pmmlform = SelectPmmlForm()
        print prediction_feature
        if prediction_feature == "":
            inputform = InputFormExpX()
            request.session['alg'] = "ocpu-expdesign2-x"
            try:
                res = requests.get(SERVER_URL+'/algorithm/ocpu-expdesign2-x', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            inputform = InputForm()
            request.session['alg'] = "ocpu-expdesign2-xy"
            try:
                res = requests.get(SERVER_URL+'/algorithm/ocpu-expdesign2-xy', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            form.fields['feature'] = prediction_feature
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            if prediction_feature == "":
                inputform.fields['output'].choices = [ (prediction_feature, "")]
            else:
                 inputform.fields['output'].choices = [ (prediction_feature, get_prediction_feature_name_of_dataset(dataset, token, prediction_feature) )]
            pmmlform.fields['predicted_feature'] = prediction_feature
            print('evangelia')
            return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'uploadform':form, 'tform':tform ,'features':features, 'inputform':inputform, 'pmmlform': pmmlform, 'exp':True})

    if request.method == 'POST':
        print('------')
        #get parameters of algorithm
        params=[]
        print request.POST

        tform = ExperimentalForm(request.POST)
        form = UploadForm(request.POST, request.FILES)
        #nform = NoPmmlForm(request.POST)
        pmmlform = SelectPmmlForm(request.POST)
        dataset = request.session.get('data', '')
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        algorithms = request.session.get('alg', '')
        print algorithms
        if algorithms == "ocpu-expdesign2-x":
            inputform = InputFormExpX(request.POST)
        else:
            inputform = InputForm(request.POST)
        print prediction_feature
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        parameters = request.POST.getlist('parameters')
        params, al = get_params(request, parameters, al)

        '''for p in parameters:
                params.append({'name': p, 'value': request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)'''
        print al['parameters']
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            #form.fields['feature'] = prediction_feature
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            if prediction_feature== "":
                inputform.fields['output'].choices = [ (prediction_feature, "")]
            else:
                inputform.fields['output'].choices = [ (prediction_feature, get_prediction_feature_name_of_dataset(dataset, token, prediction_feature))]
            pmmlform.fields['predicted_feature'] = prediction_feature
        if not tform.is_valid():
            return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'pmmlform':pmmlform, 'exp':True})
        #get transformations
        transformations=""
        if request.POST.get('variables') == "none":
            transformations = ""
            prediction_feature = prediction_feature
        elif request.POST.get('variables') == "pm":
            transformations = SERVER_URL+'/pmml/'+pmmlform['pmml'].value()
            prediction_feature = prediction_feature
        elif request.POST.get('variables') == "input":
            prediction_feature = prediction_feature
            feature_list = inputform['input'].value()
            if not inputform.is_valid():
                return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'pmmlform':pmmlform, 'exp':True})
            headers = {'Accept': 'application/json',  'Authorization': token}
            feat=""
            for f in feature_list:
                feat += str(f)+','
            body = {'features': feat}
            try:
                res = requests.post(SERVER_URL+'/pmml/selection', headers=headers, data=body)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            response = json.loads(res.text)
            transformations = SERVER_URL+'/pmml/'+response['_id']

        elif request.POST.get('variables') == "file":
            prediction_feature = prediction_feature
            if form.is_valid:
                if 'file' in request.FILES:
                    pmml= request.FILES['file'].read()
                    print pmml
                    headers = {'Content-Type': 'application/xml',  'Authorization': token }
                    try:
                        res = requests.post(SERVER_URL+'/pmml', headers=headers, data=pmml)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    response = json.loads(res.text)
                    transformations = SERVER_URL+'/pmml/'+response['_id']
                else:
                    return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'tform':tform, 'features':features, 'inputform': inputform, 'exp':True})

            #get scaling
        scaling=""
        if request.POST.get('scaling') == "scaling1":
            scaling=""
        elif request.POST.get('scaling') == "scaling2":
            scaling=SERVER_URL+'/algorithm/scaling'
        elif request.POST.get('scaling') == "scaling3":
            scaling=SERVER_URL+'/algorithm/standarization'
        #get doa
        doa=""

        #algorithms = request.session.get('alg', '')
        dataset = request.session.get('data', '')
        title= ""
        description= ""
        params = json.dumps(params)
        print params
        #prediction_feature="https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        if prediction_feature=="":
            prediction_feature="https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"
        body = {'dataset_uri': SERVER_URL+'/dataset/'+dataset, 'scaling': scaling, 'doa': doa, 'title': title, 'description':description, 'transformations':transformations, 'prediction_feature': prediction_feature, 'parameters':params, 'visible': False}
        print('----')
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        #headers = { 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/algorithm/'+algorithms, headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        print res.text
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        #return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})
        try:
            res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        status = json.loads(res1.text)['status']
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'tform':tform, 'features':features, 'inputform': inputform, 'exp':True, 'error':error})

            else:
                try:
                    res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res1.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
                status = json.loads(res1.text)['status']
        #model: model/{id}
        model = json.loads(res1.text)['result']
        print model
        print dataset
        body = {'dataset_uri':SERVER_URL+'/dataset/'+dataset}
        try:
            res2 = requests.post(SERVER_URL+'/'+model, headers=headers, data=body)
        except Exception as e:
                 return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        task_id = json.loads(res2.text)['_id']
        try:
            res3 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res3.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res3.text)})
        status = json.loads(res3.text)['status']
        print task_id
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                print form
                return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'uploadform':form, 'pmmlform':pmmlform, 'tform':tform, 'features':features, 'inputform': inputform, 'exp':True, 'error':error})

            else:
                try:
                    res4 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res4.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res4.text)})
                status = json.loads(res4.text)['status']
        try:
            res4 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        #Delete model
        #model: model/{id}
        '''print('----------------------')
            print(json.loads(res2.text))
            new_model = json.loads(res2.text)['result']
            print new_model
            headers = {'Accept': 'application/json', "Authorization": token}
            try:
                res = requests.delete(SERVER_URL+'/model/'+new_model.split('model/')[1], headers=headers)
            except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})'''
        new_dataset = json.loads(res4.text)['result']
        new_dataset = new_dataset.split('dataset/')[1]
        print new_dataset
        #dataset = 'jREmfXY9E997Ci'
        #model = 'aTqA637F4O00'
        try:
            res5 = requests.get(SERVER_URL+'/dataset/'+new_dataset, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res5.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res5.text)})
        data_detail = json.loads(res5.text)
        try:
            res6 = requests.get(SERVER_URL+'/'+model, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res6.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res6.text)})
        model_detail = json.loads(res6.text)
        predictedFeatures = model_detail['predictedFeatures']
        '''res7 = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        d_detail = json.loads(res7.text)'''
        print predicted_features
        print data_detail
        if prediction_feature == "":
            prediction_feature = get_prediction_feature_of_dataset(new_dataset, token)
            print prediction_feature
        new=[]
        for k in sorted(data_detail['features']):
                new.append(k)
        #body = { 'scaling': scaling, 'doa': doa, 'transformations':transformations, 'prediction_feature': 'https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Net+cell+association/8058CA554E48268ECBA8C98A55356854F413673B/3ed642f9-1b42-387a-9966-dea5b91e5f8a', 'parameters':json.dumps(params), 'visible': False}
        #body
        print model_detail
        #Delete model
        '''headers = {'Accept': 'application/json', "Authorization": token}
            try:
                res = requests.delete(SERVER_URL+'/model/'+model.split('model/')[1], headers=headers)
            except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})'''

        return render(request, "exp_dataset_detail.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':new_dataset, 'params': json.loads(params) })

@csrf_exempt
#@token_required
def exp_submit(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == "POST":
        #queryData = request.GET.get('queryData')
        data = request.POST.get('data')
        dataset = request.POST.get('dataset_name')
        #threshold = request.GET.get('threshold')
        #print threshold
        print data
        #dataset = data['dataset_name']
        dataset = json.loads(dataset)
        #print queryData
        #dataset='ayDPMNB3JcOJAm'
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        print prediction_feature
        #import pdb;pdb.set_trace();
        d_detail = json.loads(res.text)
        print d_detail
        #import pdb;pdb.set_trace();
        data = json.loads(data)
        length = data['length']
        print length
        new = {}
        total=0
        for i in range(0,int(length)):
            if data[str(i)][2] == "None":
                 new[data[str(i)][0]]= None
            else:
                new[data[str(i)][0]]= float(data[str(i)][2])
                total=total+1
        print new
        data_Entry = []
        for det in d_detail['dataEntry']:
            name = det['compound']['name']
            det['values'][prediction_feature] = new[name]
            data_Entry.append(det)
        #d_detail contains dataset with new values
        d_detail['dataEntry']= data_Entry
        #data = json.dumps(d_detail['dataEntry'])
        data = json.dumps(d_detail)

        #data=json.dumps(data1)
        print data
        headers1 = {'content-type': 'application/json', 'Authorization':token}
        #new_data = create_dataset(d_detail['dataEntry'],"guest","", "", "")
        rows= d_detail['totalRows']
        columns = d_detail['totalColumns']
        new_data = create_dataset2( d_detail['dataEntry'], "guest", d_detail['features'], d_detail['byModel'], rows, columns, d_detail['meta']['titles'][0], d_detail['meta']['descriptions'][0])
        print new_data
        json_data = json.dumps(new_data)
        print()
        #import pdb;pdb.set_trace();
        json_data = json.dumps(json_data)
        json_data = json.loads(json_data)
        print json_data
        try:
            res = requests.post(SERVER_URL+'/dataset', headers=headers1, data=json_data, timeout=10)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print res.text
        data = res.text.split('/dataset/')[1]
        print data
        #json_data={"dataset": data, "threshold": threshold}
        #json_data = {'dataset': data}
        #Delete dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        '''try:
            res = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        #prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        #print prediction_feature
        #import pdb;pdb.set_trace();
        data_detail = json.loads(res.text)'''
        try:
            res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
        except Exception as e:
            print('error')

        '''try:
            modelname = data_detail['byModel']
            print modelname
            headers = {'Accept': 'application/json', "Authorization": token}
            try:
                res = requests.delete(SERVER_URL + '/model/' + modelname, headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username, 'error': json.loads(res.text)})
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })'''
        json_data = json.dumps(data)
        return HttpResponse(json_data)

#@token_required
def exp_iter(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'GET':
        dataset = request.GET.get('dataset')
        print dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res1 = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        data_detail = json.loads(res1.text)
        model = json.loads(res1.text)['byModel']
        print model
        #model = 'A0fU5rK7B64r'
        try:
            res = requests.get(SERVER_URL+'/model/'+model, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        model_detail = json.loads(res.text)
        predictedFeatures = model_detail['predictedFeatures']
        algorithms = json.loads(res.text)['algorithm']['_id']
        params = json.loads(res.text)['parameters']
        new=[]
        for k in sorted(data_detail['features']):
            new.append(k)
        if algorithms == "ocpu-expdesign2-x":
            algorithms = "ocpu-expdesign2-xy"
            par = {}
            for k,v in params.items():
                if k != "newY":
                    par.update({k:v})
            params = par
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        if prediction_feature != "":
            total=get_number_of_not_null_of_dataset(dataset, token, prediction_feature)
            if total < 4:
                error="You should change the prediction feature of 4 compounds at least."
                print data_detail
                print prediction_feature
                return render(request, "exp_dataset_detail.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':dataset, 'params': params, 'error':error })
        else:
            prediction_feature="https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"

        body = {'dataset_uri': SERVER_URL+'/dataset/'+dataset, 'scaling': "", 'doa': "", 'title': "", 'description':"", 'transformations':"", 'prediction_feature': prediction_feature, 'parameters':json.dumps(params), 'visible': False}
        print('----')
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        #import pdb;pdb.set_trace();
        try:
            res = requests.post(SERVER_URL+'/algorithm/'+algorithms, headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        print res.text
        task_id = json.loads(res.text)['_id']
        print task_id
        #return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})
        try:
            res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        status = json.loads(res1.text)['status']
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                return render(request, "exp_dataset_detail.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':dataset, 'params': params, 'error':error })

            else:
                try:
                    res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res1.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
                status = json.loads(res1.text)['status']
        #model: model/{id}
        model = json.loads(res1.text)['result']
        body = {'dataset_uri':SERVER_URL+'/dataset/'+dataset}
        try:
            res2 = requests.post(SERVER_URL+'/'+model, headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        task_id = json.loads(res2.text)['_id']
        try:
            res3 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res3.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res3.text)})
        status = json.loads(res3.text)['status']

        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                return render(request, "exp_dataset_detail.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':dataset, 'params': params, 'error':error })
            else:
                try:
                    res4 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res4.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res4.text)})
                status = json.loads(res4.text)['status']
        # Delete
        '''try:
            res = requests.delete('http://test.jaqpot.org:8080/jaqpot/services/dataset/'+dataset, headers=headers)
        except Exception as e:
            print('error')
        try:
            res = requests.delete(SERVER_URL + '/model/' + model, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username, 'error': json.loads(res.text)})'''

        new_dataset = json.loads(res4.text)['result']
        new_dataset = new_dataset.split('dataset/')[1]
        print new_dataset
        try:
            res5 = requests.get(SERVER_URL+'/dataset/'+new_dataset, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res5.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res5.text)})
        data_detail = json.loads(res5.text)
        try:
            res6 = requests.get(SERVER_URL+'/'+model, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res6.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res6.text)})
        model_detail = json.loads(res6.text)
        predictedFeatures = model_detail['predictedFeatures']
        '''try:
            res7 = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res7.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res7.text)})
        d_detail = json.loads(res7.text)'''
        prediction_feature = get_prediction_feature_of_dataset(new_dataset, token)
        print data_detail
        new=[]
        for k in sorted(data_detail['features']):
            new.append(k)
        #body = { 'scaling': scaling, 'doa': doa, 'transformations':transformations, 'prediction_feature': 'https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Net+cell+association/8058CA554E48268ECBA8C98A55356854F413673B/3ed642f9-1b42-387a-9966-dea5b91e5f8a', 'parameters':json.dumps(params), 'visible': False}
        #body
        if prediction_feature=="":
            prediction_feature="https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"
        #Delete dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        '''try:
            modelname = data_detail['byModel']
            print modelname
            headers = {'Accept': 'application/json', "Authorization": token}
            try:
                res = requests.delete(SERVER_URL + '/model/' + modelname, headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
            if res.status_code >= 400:
                return render(request, "error.html",
                              {'token': token, 'username': username, 'error': json.loads(res.text)})
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })'''
        return render(request, "exp_dataset_detail.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':new_dataset, 'params':params})

@csrf_exempt
#@token_required
def fact_submit(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'POST':
        #queryData = request.GET.get('queryData')
        data = request.POST.get('data')
        dataset = request.POST.get('dataset_name')
        #threshold = request.GET.get('threshold')
        #print threshold
        print data
        #dataset = data['dataset_name']
        dataset = json.loads(dataset)
        #print queryData
        #dataset='ayDPMNB3JcOJAm'
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        print prediction_feature
        d_detail = json.loads(res.text)

        data = json.loads(data)
        length = data['length']
        print length
        new = {}
        total=0
        for i in range(0,int(length)):
            if data[str(i)][2] == "None":
                 new[data[str(i)][0]]= None
            else:
                new[data[str(i)][0]]= float(data[str(i)][2])
                total=total+1
        print new
        data_Entry = []
        for det in d_detail['dataEntry']:
            name = det['compound']['name']
            det['values'][prediction_feature] = new[name]
            data_Entry.append(det)
        #d_detail contains dataset with new values
        d_detail['dataEntry']= data_Entry
        #data = json.dumps(d_detail['dataEntry'])
        data = json.dumps(d_detail)

        #data=json.dumps(data1)
        print data
        headers1 = {'content-type': 'application/json', 'Authorization':token}
        rows= d_detail['totalRows']
        columns = d_detail['totalColumns']
        print d_detail
        suggested=""
        for d in d_detail['features']:
            if d['name']=='suggestedTrials':
                suggested= d['uri']
        print('----')
        new_data = create_dataset2_with_title(d_detail['dataEntry'], "guest", d_detail['features'], d_detail['byModel'], rows, columns, d_detail['meta']['titles'][0], d_detail['meta']['descriptions'][0], prediction_feature, suggested)
        print new_data
        json_data = json.dumps(new_data)
        json_data = json.dumps(json_data)
        json_data = json.loads(json_data)
        print json_data
        try:
            res = requests.post(SERVER_URL+'/dataset', headers=headers1, data=json_data, timeout=30)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print res.text
        data = res.text.split('/dataset/')[1]
        print data
        #Delete previous dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
        except Exception as e:
            print('error')
        #Delete model
        try:
            modelname = d_detail['byModel']
            print modelname
            headers = {'Accept': 'application/json', "Authorization": token}
            try:
                res = requests.delete(SERVER_URL + '/model/' + modelname, headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
            if res.status_code >= 400:
                return render(request, "error.html",
                              {'token': token, 'username': username, 'error': json.loads(res.text)})
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username, 'server_error': e, })
        json_data = json.dumps(data)
        return HttpResponse(json_data)

#@token_required
def factorial_dataset(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'GET':
        #Get dataset from request
        dataset = request.GET.get('dataset')
        print dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        #Get dataset json
        try:
            res1 = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        data_detail = json.loads(res1.text)
        #Get model that has created the dataset
        model = json.loads(res1.text)['byModel']
        #Get model details json
        try:
            res = requests.get(SERVER_URL+'/model/'+model, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        model_detail = json.loads(res.text)
        predictedFeatures = model_detail['predictedFeatures']
        #Get prediction feature of dataset
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        total = get_number_of_not_null_of_dataset(dataset, token, prediction_feature)
        new=[]
        for k in sorted(data_detail['features']):
            new.append(k)
        if total < 4:
            error="You should change the prediction feature of 4 compounds at least."
            return render(request, "factorial.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':dataset, 'error':error })

        return render(request, "factorial.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':dataset })


#Factorial Validation
@csrf_exempt
#@token_required
def factorial_validation(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}
    if request.is_ajax():
        datatable = request.POST.get('data')
        datatable=json.loads(datatable)
        print datatable
        error=""
        length = datatable['tabledata']['length']
        if length < 4:
            error="At least 4 variables are needed."
        print length
        for row in range(0, int(length)):
            tp=datatable['tabledata'][str(row)][1]
            print tp
            if "selected" in tp:
                num=tp.split('numerical')[1]
                print num
                if "selected" in num:
                    type ='numerical'
                else:
                    type ="categorical"
            else:
                type="numerical"
            print type
            if type == "categorical":
                for i in range(2, int(len(datatable['tabledata'][str(row)]))):
                    if (datatable['tabledata'][str(row)][i])!="None" and (datatable['tabledata'][str(row)][i])!= "":
                        try:
                            str(datatable['tabledata'][str(row)][i])
                        except:
                            error="Wrong input"
                    else:
                        if i<4:
                            error = "At least 2 levels are needed."
                        for j in range(i+1,int(len(datatable['tabledata'][str(row)]))):
                            if (datatable['tabledata'][str(row)][j])!="None" and (datatable['tabledata'][str(row)][j])!= "":
                                error="Wrong"
            elif type == "numerical":
                for i in range(2, int(len(datatable['tabledata'][str(row)]))):
                    if (datatable['tabledata'][str(row)][i])!="None" and (datatable['tabledata'][str(row)][i])!= "":
                        try:
                            int(datatable['tabledata'][str(row)][i])
                        except:
                            error="Wrong input"
                    else:
                        if i<4:
                            error = "At least 2 levels are needed."
                        for j in range(i+1,int(len(datatable['tabledata'][str(row)]))):
                            if (datatable['tabledata'][str(row)][j])!="None" and (datatable['tabledata'][str(row)][j])!= "":
                                error="Wrong"
        error= json.dumps(error)
        print error
        return HttpResponse(error)

#Experimental design without input
#@token_required
def exp_design(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'GET':
        tform=DatasetForm()
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/ocpu-expdesign2-noxy', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print json.loads(res.text)
        al = json.loads(res.text)

        return render(request, "ocpu_params.html", {'token': token, 'username': username, 'al':al,'tform':tform })

    if request.method == 'POST':

        parameters = request.POST.getlist('parameters')
        datatable=request.POST.get('json')

        datatable=json.loads(datatable)
        length = datatable['tabledata']['length']
        nVars=[int(length)]

        #Create levels and varNames params from datatable json
        varNames=[]
        levels=OrderedDict()
        factors = []
        for row in range(0, int(length)):
            #Find type of row
            tp=datatable['tabledata'][str(row)][1]
            if "selected" in tp:
                num=tp.split('numerical')[1]
                print num
                if "selected" in num:
                    type ='numerical'
                else:
                    type ="categorical"
            else:
                type="numerical"
            if type == "categorical":
                factors.append(int(row+1))
            varNames.append(datatable['tabledata'][str(row)][0])
            l_val=[]
            #if datatable['tabledata'][str(row)][1] == "categorical":
            for i in range(2, int(len(datatable['tabledata'][str(row)]))):
                if (datatable['tabledata'][str(row)][i])!="None":
                    try:
                        l_val.append(int(datatable['tabledata'][str(row)][i]))
                    except:
                        l_val.append(str(datatable['tabledata'][str(row)][i]))
            levels.update({datatable['tabledata'][str(row)][0]: l_val})
        if factors ==[]:
            factors.append(0)
        #print json.dumps(levels)
        print json.dumps(varNames)
        tform=DatasetForm(request.POST)
        title = tform['title'].value()
        description = tform['description'].value()
        nTrials= request.POST.get('Number of trials')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/ocpu-expdesign2-noxy', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        #Create empty dataset
        body = {'title':title, 'description':description}
        try:
            res = requests.post(SERVER_URL+'/dataset/empty', headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print res.text
        dataset = json.loads(res.text)['_id']
        dataset_uri = SERVER_URL+'/dataset/'+dataset

        params, al = get_params(request, parameters, al)
        params.update({"nVars": nVars, "levels":levels, "nTrials":[int(nTrials)], "varNames":varNames, "factors":factors, "newY":['CA']})
        prediction_feature="https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"

        body = {'dataset_uri':dataset_uri, 'parameters':json.dumps(params), 'title':'', 'description':'', 'prediction_feature':prediction_feature }
        headers = {'Accept': 'application/json', 'Authorization': token}
        print body
        try:
            res = requests.post(SERVER_URL+'/algorithm/ocpu-expdesign2-noxy', headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        '''if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})'''
        print res.text
        task_id = json.loads(res.text)['_id']
        print task_id
        try:
            res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
            #Delete empty dataset
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
            except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
             #Delete empty dataset
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.delete(SERVER_URL + '/dataset/' +dataset, headers=headers)
            except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        status = json.loads(res1.text)['status']
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                #Delete empty dataset
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:
                    res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
                except Exception as e:
                            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                error = "An error occurred while processing your request.Please try again."
                return render(request, "ocpu_params.html", {'token': token, 'username': username, 'error':error, 'al':al })
            else:
                try:
                         res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res1.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
            status = json.loads(res1.text)['status']
            #model: model/{id}
        model = json.loads(res1.text)['result']
        model=model.split('model/')[1]
        print(model)
        dataset_uri=SERVER_URL + '/dataset/' +dataset
        #dataset_uri=SERVER_URL + '/dataset/corona'
        body={'dataset_uri':dataset_uri}
        try:
            res2 = requests.post(SERVER_URL+'/model/'+model, headers=headers, data=body)
        except Exception as e:
                #Delete empty dataset
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:
                    res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
                except Exception as e:
                            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            #Delete empty dataset
            headers = {'Accept': 'application/json', 'Authorization': token}
            try:
                res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
            except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        task_id = json.loads(res2.text)['_id']
        try:
            res3 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res3.status_code >= 400:
             return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res3.text)})
        status = json.loads(res3.text)['status']

        while (status != "COMPLETED"):
            if(status == "ERROR"):
                #Delete empty dataset
                headers = {'Accept': 'application/json', 'Authorization': token}
                try:
                    res = requests.delete(SERVER_URL + '/dataset/' +dataset, headers=headers)
                except Exception as e:
                            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                error = "An error occurred while processing your request.Please try again."
                return render(request, "ocpu_params.html", {'token': token, 'username': username,'error':error, 'al':al })
            else:
                try:
                    res4 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res4.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res4.text)})
                status = json.loads(res4.text)['status']
        print json.loads(res4.text)
        new_dataset = json.loads(res4.text)['result']
        new_dataset = new_dataset.split('dataset/')[1]
        print(new_dataset)
        #Delete empty dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL + '/dataset/'+dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print('ehvfhnj')
        try:
            res = requests.get(SERVER_URL+'/algorithm/ocpu-expdesign2-x', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al=json.loads(res.text)
        #for a in al['parameters']:
            #params.update({a['_id']:a['value']})
        params='{"nTrials": [11], "criterion": ["D"], "form": ["linear"], "r2.threshold": [0.9], "newY": "New Y"}'
        prediction_feature="https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"

        body = {'dataset_uri': SERVER_URL+'/dataset/'+new_dataset, 'scaling': '', 'doa': '', 'title': 'new', 'description':'new', 'transformations':'', 'prediction_feature': prediction_feature, 'parameters':params, 'visible': False}
        print('----')
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        #headers = { 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/algorithm/ocpu-expdesign2-x', headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        print res.text
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        #return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})
        try:
            res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        status = json.loads(res1.text)['status']
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                #return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'tform':tform, 'features':features, 'inputform': inputform, 'exp':True, 'error':error})

            else:
                try:
                    res1 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res1.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
                status = json.loads(res1.text)['status']
        #Delete model
        headers = {'Accept': 'application/json', "Authorization": token}
        try:
            res = requests.delete(SERVER_URL + '/model/'+model, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        #model: model/{id}
        model = json.loads(res1.text)['result']
        print model
        #Create dataset with extra column
        body = {'dataset_uri':SERVER_URL+'/dataset/'+new_dataset}
        try:
            res2 = requests.post(SERVER_URL+'/'+model, headers=headers, data=body)
        except Exception as e:
                 return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        task_id = json.loads(res2.text)['_id']
        try:
            res3 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res3.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res3.text)})
        status = json.loads(res3.text)['status']
        print task_id
        while (status != "COMPLETED"):
            if(status == "ERROR"):
                error = "An error occurred while processing your request.Please try again."
                #return render(request, "alg.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'uploadform':form, 'pmmlform':pmmlform, 'tform':tform, 'features':features, 'inputform': inputform, 'exp':True, 'error':error})

            else:
                try:
                    res4 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res4.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res4.text)})
                status = json.loads(res4.text)['status']
        try:
            res4 = requests.get(SERVER_URL+'/task/'+task_id, headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })

        exp_dataset = json.loads(res4.text)['result']
        exp_dataset = exp_dataset.split('dataset/')[1]
        print exp_dataset
        #Delete previous dataset (new_dataset)
        '''headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.delete('http://test.jaqpot.org:8080/jaqpot/services/dataset/'+new_dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})'''
        try:
            res = requests.get(SERVER_URL+'/dataset/'+exp_dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        d_detail = json.loads(res.text)
        #Clean new dataset
        suggested = SERVER_URL + "/feature/289iHuKmMM3M"
        # suggested = "http://localhost:8080/jaqpot/services/feature/289iHuKmMM3M"
        # suggested = "https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"
        '''for d in d_detail['features']:
            if d['name']=='suggestedTrials':
                suggested= d['uri']
        print('----')'''
        rows = d_detail['totalRows']
        columns = d_detail['totalColumns']
        new_data = create_and_clean_dataset2_with_title(d_detail['dataEntry'], "guest", d_detail['features'], d_detail['byModel'], rows, columns, d_detail['meta']['titles'][0], d_detail['meta']['descriptions'][0], prediction_feature, suggested)
        print new_data
        json_data = json.dumps(new_data)
        json_data = json.dumps(json_data)
        json_data = json.loads(json_data)
        print json_data
        headers1 = {'Content-type': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/dataset', headers=headers1, data=json_data, timeout=30)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print res.text
        data = res.text.split('/dataset/')[1]
        print data
        #Delete previous dataset
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL + '/dataset/'+new_dataset, headers=headers)
        except Exception as e:
            print('error')
         #Delete previous dataset (exp_dataset)
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.delete(SERVER_URL + '/dataset/'+exp_dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        exp_dataset=data
        try:
            res5 = requests.get(SERVER_URL+'/dataset/'+exp_dataset, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res5.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res5.text)})
        data_detail = json.loads(res5.text)
        try:
            res6 = requests.get(SERVER_URL+'/'+model, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res6.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res6.text)})
        model_detail = json.loads(res6.text)
        predictedFeatures = model_detail['predictedFeatures']
        '''res7 = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        d_detail = json.loads(res7.text)'''
        print data_detail
        prediction_feature = get_prediction_feature_of_dataset(exp_dataset, token)
        if prediction_feature == "":
            prediction_feature = get_prediction_feature_of_dataset(exp_dataset, token)
            print prediction_feature
        #body = { 'scaling': scaling, 'doa': doa, 'transformations':transformations, 'prediction_feature': 'https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Net+cell+association/8058CA554E48268ECBA8C98A55356854F413673B/3ed642f9-1b42-387a-9966-dea5b91e5f8a', 'parameters':json.dumps(params), 'visible': False}
        #body
        print model_detail
        new=[]
        for k in sorted(data_detail['features']):
            new.append(k)

        #Delete model
        '''headers = {'Accept': 'application/json', "Authorization": token}
        try:
            res = requests.delete(SERVER_URL+'/model/'+model.split('model/')[1], headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})'''
        return render(request, "factorial.html", {'token': token, 'username': username,'new':new, 'data_detail': data_detail, 'predicted': predictedFeatures, 'prediction':prediction_feature, 'model':model_detail, 'dataset_name':exp_dataset })


#Interlab testing select substance owners
'''def interlab_select_substance(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}
    if token:
        r = requests.post(SERVER_URL + '/aa/validate', headers=headers)
        if r.status_code != 200:
            return redirect('/login')
        else:
            page=request.GET.get('page')
            if page:
                headers = {'Accept': 'application/json', 'Authorization': token}
                page1=str(int(page)-1)
                res = requests.get('https://apps.ideaconsult.net:443/enmtest/substanceowner?page='+page1+'&pagesize=20', headers=headers)
                substance_owner=json.loads(res.text)
                substance_owner = substance_owner['facet']
            else:
                headers = {'Accept': 'application/json', 'Authorization': token}
                page=1
                res = requests.get('https://apps.ideaconsult.net:443/enmtest/substanceowner?page=0&pagesize=20', headers=headers)
                substance_owner=json.loads(res.text)
                substance_owner = substance_owner['facet']
    if request.method == 'GET':
        form = SubstanceownerForm(initial={'substanceowner': ''})
        if len(substance_owner)<20:
            last=page
            return render(request, "interlab_substance.html", {'token': token, 'username': username, 'form':form, 'substance_owner': substance_owner, 'page': page, 'last':last,})
        else:
            return render(request, "interlab_substance.html", {'token': token, 'username': username, 'form':form, 'substance_owner': substance_owner, 'page': page})
    if request.method == 'POST':
        method = request.POST.get('radio_method')

        substance_owner = request.POST.get('radio')
        if not substance_owner:
            form = SubstanceownerForm(initial={'substanceowner': ''})
            page=request.GET.get('page')
            if page:
                headers = {'Accept': 'application/json', 'Authorization': token}
                page1=str(int(page)-1)
                res = requests.get('https://apps.ideaconsult.net:443/enmtest/substanceowner?page='+page1+'&pagesize=20', headers=headers)
                substance_owner=json.loads(res.text)
                substance_owner = substance_owner['facet']
            else:
                headers = {'Accept': 'application/json', 'Authorization': token}
                page=1
                res = requests.get('https://apps.ideaconsult.net:443/enmtest/substanceowner?page=0&pagesize=20', headers=headers)
                substance_owner=json.loads(res.text)
                substance_owner = substance_owner['facet']
                error = "Please select substance owner."
                return render(request, "interlab_substance.html", {'token': token, 'username': username, 'form':form, 'substance_owner': substance_owner, 'page': page, 'error':error})
        else:
            substance_owner = 'https://apps.ideaconsult.net/enmtest/substanceowner/'+substance_owner
            request.session['substanceowner']= substance_owner
            headers = {'Accept': 'application/json', 'Authorization': token}
            res = requests.get(substance_owner+'/substance', headers=headers)
            substances=json.loads(res.text)
            request.session['substances'] = substances
            return redirect('/interlab_params', {'token': token, 'username': username})'''

#Train model
#@token_required
def interlab_select_substance(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    page = request.GET.get('page')
    last = request.GET.get('last')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'GET':
        dataset=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_datasets= int(res.headers.get('total'))
        if total_datasets%20 == 0:
            last = total_datasets/20
        else:
            last = (total_datasets/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            print k
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data = json.loads(res.text)
        print res.text
        '''try:
            res = requests.get(SERVER_URL+'/dataset/interlab-dummy', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        d = json.loads(res.text)
        dataset.append({'name': d['_id'], 'meta': d['meta']})'''
        for d in data:
                dataset.append({'name': d['_id'], 'meta': d['meta']})
        print dataset
        proposed=[]
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured?start=0&max=100', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta']})
        return render(request, "interlab_dataset.html", {'token': token, 'username': username, 'entries2': dataset, 'page': page, 'last':last, 'proposed':proposed})

#@token_required
def interlab_params(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'GET':
        dataset=request.GET.get('dataset')
        form=InterlabForm()
        #dataset = "8aj1O7Vny4uJLl"
        return render(request, "interlab_params.html", {'token': token, 'username': username, 'dataset':dataset, 'form':form})
    if request.method == 'POST':
        dataset=request.GET.get('dataset')
        form = InterlabForm(request.POST)
        if not form.is_valid():
            return render(request, "interlab_params.html", {'token': token, 'username': username, 'dataset':dataset, 'form':form})
        modelname = form['modelname'].value()
        description = form['description'].value()
        dataset = SERVER_URL + '/dataset/interlab-dummy'
        prediction = "https://apps.ideaconsult.net/enmtest/property/TOX/UNKNOWN_TOXICITY_SECTION/Log2+transformed/94D664CFE4929A0F400A5AD8CA733B52E049A688/3ed642f9-1b42-387a-9966-dea5b91e5f8a"
        headers = {'Accept': 'application/json', 'Authorization': token}
        body = {'title': modelname, 'descriptions': description, 'dataset_uri': dataset, 'prediction_feature':prediction}
        print body
        try:
            res = requests.post(SERVER_URL+'/interlab/test', headers=headers, data=body)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        print res.text
        print json.loads(res.text)['_id']
        return redirect('/report?name='+json.loads(res.text)['_id'])

#@token_required
def clean_dataset(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    if request.method == 'GET':
        dataset = request.GET.get('dataset')
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/dataset/'+dataset, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        prediction_feature = get_prediction_feature_of_dataset(dataset, token)
        suggested=""
        for d in data['features']:
            if d['name']=='suggestedTrials':
                suggested= d['uri']
        new_data = create_and_clean_dataset(data, prediction_feature, suggested)
        json_data = json.dumps(new_data)
        print json_data
        headers1 = {'Content-type': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/dataset', headers=headers1, data=json_data)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        dataset = res.text.split('/dataset/')[1]
        print dataset
        return redirect('/dataset?dataset=' +dataset)

#List of reports
#@token_required
def report_list(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    page = request.GET.get('page')
    last = request.GET.get('last')
    if request.method == 'GET':
        report=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/report?start=0&max=20', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_reports= int(res.headers.get('total'))
        if total_reports%20 == 0:
            last = total_reports/20
        else:
            last = (total_reports/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/report?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/report?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/report?start=0&max=20', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        for d in data:
            report.append({'id':d['_id'], 'meta':d['meta']})

        return render(request, "reports.html", {'token': token, 'username': username, 'report': report, 'page': page, 'last':last})

#Display details of each dataset
'''def dataset_detail(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    if token:
        request.session.get('token', '')
        #validate token
        #if token is not valid redirect to login page
        r = requests.post(SERVER_URL + '/aa/validate', headers={'Authorization': token})
        if r.status_code != 200:
            return redirect('/login')
    else:

        return redirect('/login')

    name = request.GET.get('name', '')
    page = request.GET.get('page', '')
    data_detail, last, page = paginate_dataset(request, name, token, username, page)
    if data_detail and last and page:
            a=[]
            #a=collections.OrderedDict()
            # a contains all compound's properties
            for key in data_detail['dataEntry']:
                for k, value in key.items():
                    if k =='values':
                        counter=0
                        for m,n in value.items():
                            if m not in a:
                                a.append(m)


            print a
            properties={}
            new=[]
            compound = []
            for i in range(len(a)):
                for k in data_detail['features']:
                    if k['uri'] == a[i]:
                        new.append(k)

            #get response json
            for key in data_detail['dataEntry']:
                properties[key['compound']['URI']] = []
                properties[key['compound']['URI']].append({"compound": key['compound']['URI']})
                properties[key['compound']['URI']].append({"name": key['compound']['name']})

                #for each compound
                for k, value in key.items():
                    if k =='values':
                        for i in range(len(a)):
                            #if a compound haven't value for a property add its value Null
                            if a[i] in value:
                                properties[key['compound']['URI']].append({"prop": a[i], "value": value[a[i]]})
                            else:
                                properties[key['compound']['URI']].append({"prop":  a[i], "value": "NULL"})

            return render(request, "dataset_detail.html", {'token': token, 'username': username, 'name': name, 'data_detail':data_detail, 'properties': properties, 'a': a, 'new': new, 'page':page, 'last':last})'''

#Delete selected report
#@token_required
def report_delete(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    id = request.GET.get('id')
    #delete report
    headers = {'Accept': 'application/json', "Authorization": token}
    try:
        res = requests.delete(SERVER_URL+'/report/'+id, headers=headers)
    except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    reply = res.text
    print reply
    return redirect('/reports')

#Qrf report
#@token_required
def qrf_report(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    headers = {'Accept': 'application/json', 'Authorization': token}

    uri = request.GET.get('uri')
    dataset = request.GET.get('dataset')
    print uri
    print dataset
    headers = {'Accept': 'application/json', 'Authorization': token}
    body={'substance_uri':uri}
    try:
        res = requests.post(SERVER_URL+'/dataset/'+dataset+'/qprf', headers=headers, data=body)
    except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if res.status_code >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
    response = json.loads(res.text)
    name=response['_id']
    headers = {'Accept': 'application/json', 'Authorization': token}
    try:
        res = requests.get(SERVER_URL+'/report/'+name, headers=headers)
    except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })

    if res.status_code >= 400:
        #redirect to error page
        return render(request, "error.html", {'token': token, 'username': username,'error':json.loads(res.text) })
    report = json.loads(res.text, object_pairs_hook=OrderedDict)
    print request

    return render(request, "report.html", {'token': token, 'username': username, 'report': report, 'name':name })

#@token_required
def report_download(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    name = request.GET.get('name')
    headers = {'Accept': 'application/json', "Authorization": token}
    try:
        res = urllib2.Request(SERVER_URL+'/report/'+name+'/pdf', headers=headers)
        pdf = urllib2.urlopen(res)
    except Exception as e:
        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
    if pdf.getcode() >= 400:
        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})

    if pdf.getcode() == 200:
        response = FileResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="report_'+name+'.pdf"'

        # calculate file size
        content_length = None
        for header in pdf.info():
            if 'Content-Length' in header:
                try:
                    content_length = int(header.split(' ')[1].split('\r')[0])
                except ValueError as e:
                    pass
                break
        if content_length:
            response['Content-Length'] = content_length

        return response
    else:
        try:
            res = requests.get(SERVER_URL+'/report/'+name, headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        report = json.loads(res.text, object_pairs_hook=OrderedDict)

    return render(request, "report.html", {'token': token, 'username': username, 'report': report, 'name':name })

#Read Across Training
#@token_required
def read_across_dataset(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')
    page = request.GET.get('page')
    last = request.GET.get('last')

    if request.method == 'GET':
        dataset=[]
        headers = {'Accept': 'application/json', 'Authorization': token}
        #get total number of datasets
        try:
            res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        total_datasets= int(res.headers.get('total'))
        if total_datasets%20 == 0:
            last = total_datasets/20
        else:
            last = (total_datasets/20)+1

        if page:
            #page1 is the number of first dataset of page
            page1=int(page) * 20 - 20
            k=str(page1)
            print k
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        print res.text
        for d in data:
            dataset.append({'name': d['_id'], 'meta': d['meta']})
        print dataset
        proposed=[]
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured', headers=headers)
        except Exception as e:
            return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta']})
        return render(request, "read_across_dataset.html", {'token': token, 'username': username, 'entries2': dataset, 'page': page, 'last':last, 'proposed':proposed})

#read across select parameters for training
#@token_required
def read_across_train(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        form = UploadFileForm()
        tform = ReadAcrossTrainingForm()
        inputform = InputForm()
        nform = NoPmmlForm()
        pmmlform = SelectPmmlForm()
        dataset = request.GET.get('dataset')

        algorithms= "python-readacross"
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        try:
            headers = {'Accept': 'application/json', 'Authorization': token}
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        predicted_features = json.loads(res2.text)
        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            print('----')
            print predicted_features
            if 'features' not in predicted_features:
                return render(request, "error.html", {'token': token, 'username': username,'error':"No features in given dataset"})
            features = predicted_features['features']
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
            return render(request, "read_across_train.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'uploadform':form, 'tform':tform ,'features':features, 'inputform':inputform, 'nform':nform, 'pmmlform': pmmlform})


    if request.method == 'POST':
        #get parameters of algorithm
        params={}
        print request.POST


        tform = ReadAcrossTrainingForm(request.POST)
        inputform = InputForm(request.POST)
        form = UploadFileForm(request.POST, request.FILES)
        nform = NoPmmlForm(request.POST)
        pmmlform = SelectPmmlForm(request.POST)
        dataset = request.GET.get('dataset')
        print dataset
        algorithms= "python-readacross"
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.get(SERVER_URL+'/algorithm/'+algorithms, headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        al = json.loads(res.text)
        if request.POST.getlist('parameters'):
            parameters = request.POST.getlist('parameters')
            '''for p in parameters:
                params.append({'name': p, 'value': request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)'''
            for p in parameters:
                #params.update({p: request.POST.get(''+p)})
                for a in al['parameters']:
                    if (a['name'] == p):
                        print p
                        a['value']=request.POST.get(''+p)
            print al['parameters']
            for a in al['parameters']:
                params.update({a['name']: a['value']})
            params, al = get_params3(request, parameters, al)
            print json.dumps(params)

        try:
            res1 = requests.get(SERVER_URL+'/pmml/?start=0&max=1000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        pmml=json.loads(res1.text)
        if pmml:
            pmmlform.fields['pmml'].choices = [(p['_id'],p['_id']) for p in pmml]
        else:
            pmmlform.fields['pmml'].choices = [("",'No pmml')]
        try:
            res2 = requests.get(SERVER_URL+'/dataset/'+dataset+'?rowStart=0&rowMax=1&colStart=0&colMax=2', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res2.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res2.text)})
        predicted_features = json.loads(res2.text)

        if str(res2) != "<Response [200]>":
            #redirect to error page
            return render(request, "error.html", {'token': token, 'username': username,'error':predicted_features})
        else:
            features = predicted_features['features']
            form.fields['feature'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['output'].choices = [(f['uri'],f['name']) for f in features]
            inputform.fields['input'].choices = [(f['uri'],f['name']) for f in features]
            nform.fields['pred_feature'].choices = [(f['uri'],f['name']) for f in features]
            pmmlform.fields['predicted_feature'].choices = [(f['uri'],f['name']) for f in features]
        if not tform.is_valid():
            return render(request, "read_across_train.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
        #get transformations
        transformations=""
        prediction_feature = ""
        if request.POST.get('variables') == "none":
            if not nform.is_valid():
                return render(request, "read_across_train.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            transformations = ""
            prediction_feature = nform['pred_feature'].value()
        elif request.POST.get('variables') == "pm":
            transformations = SERVER_URL+'/pmml/'+pmmlform['pmml'].value()
            prediction_feature = pmmlform['predicted_feature'].value()
        elif request.POST.get('variables') == "input":
            prediction_feature = inputform['output'].value()
            feature_list = inputform['input'].value()
            if not inputform.is_valid():
                return render(request, "read_across_train.html", {'token': token, 'username': username, 'dataset':dataset, 'algorithms':algorithms, 'tform':tform, 'uploadform':form,'inputform': inputform, 'al':al, 'nform': nform, 'pmmlform':pmmlform})
            headers = {'Accept': 'application/json',  'Authorization': token}
            feat=""
            for f in feature_list:
                feat += str(f)+','
            body = {'features': feat}
            try:
                res = requests.post(SERVER_URL+'/pmml/selection', headers=headers, data=body)
            except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            response = json.loads(res.text)
            transformations = SERVER_URL+'/pmml/'+response['_id']

        elif request.POST.get('variables') == "file":
            prediction_feature = form['feature'].value()
            if form.is_valid:
                if 'file' in request.FILES:
                    pmml= request.FILES['file'].read()
                    print pmml
                    headers = {'Content-Type': 'application/xml',  'Authorization': token }
                    try:
                        res = requests.post(SERVER_URL+'/pmml', headers=headers, data=pmml)
                    except Exception as e:
                        return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                    if res.status_code >= 400:
                        return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                    response = json.loads(res.text)
                    transformations = SERVER_URL+'/pmml/'+response['_id']
                else:
                    return render(request, "read_across_train.html", {'token': token, 'username': username, 'dataset':dataset, 'al': al, 'algorithms':algorithms, 'pmmlform':pmmlform, 'uploadform':form, 'tform':tform, 'features':features, 'inputform': inputform, 'nform': nform})

         #get scaling
        scaling=""
        if request.POST.get('scaling') == "scaling1":
            scaling=""
        elif request.POST.get('scaling') == "scaling2":
            scaling=SERVER_URL+'/algorithm/scaling'
        elif request.POST.get('scaling') == "scaling3":
            scaling=SERVER_URL+'/algorithm/standarization'
        #get doa
        doa=""
        title= tform['modelname'].value()
        description= tform['description'].value()
        body = {'dataset_uri': SERVER_URL+'/dataset/'+dataset, 'scaling': scaling, 'doa': doa, 'title': title, 'description':description, 'transformations':transformations, 'prediction_feature': prediction_feature, 'parameters':json.dumps(params), 'visible': True}
        print body
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            res = requests.post(SERVER_URL+'/algorithm/python-readacross', headers=headers, data=body)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        task_id = json.loads(res.text)['_id']
        print task_id
        print json.dumps(params)
        return redirect('/t_detail?name='+task_id+'&status=queued', {'token': token, 'username': username})


#Read Across Predict
#@token_required
def read_across_predict(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    if request.method == 'GET':
        m = []
        #get all models
        headers = {'Accept': 'application/json', "Authorization": token}
        try:
            res = requests.get(SERVER_URL+'/model?start=0&max=10000', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        list_resp = res.text
        models = json.loads(res.text)
        print models
        for mod in models:
                m.append({'name': mod['_id'], 'meta': mod['meta']})
        #Get selected models
        try:
            res1 = requests.get(SERVER_URL+'/model/featured?start=0&max=10', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_model = json.loads(res1.text)
        proposed = []
        for p in proposed_model:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        #Display all models for selection
        return render(request, "read_across_predict_model.html", {'token': token, 'username': username, 'my_models': m, 'proposed':proposed})

#@token_required
def read_across_predict_model(request):
    token = request.session.get('token', '')
    username = request.session.get('username', '')

    #Get the current page
    page = request.GET.get('page')
    #Get the last page
    last = request.GET.get('last')
    if request.method == 'GET':
        #Get the selected model for prediction
        model = request.GET.get('model')
        #Save selected model at session model
        request.session['model'] = model
        dataset=[]
        #Get required feature of selected model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            required_res = requests.get(SERVER_URL+'/model/'+model+'/required', headers=headers)
        except Exception as e:
                return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if required_res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(required_res.text)})
        model_req = json.loads(required_res.text)
        #check if is needed image or mocap
        image, mopac = chech_image_mopac(model_req)
        #Firstly, get the datasets of first page if user selects different page get the datasets of the selected page
        if page:
            page1=int(page) * 20 - 20
            k=str(page1)
            if page1 <= 1:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            elif last:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+last+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
            else:
                try:
                    res = requests.get(SERVER_URL+'/dataset?start='+k+'&max=20', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})

        else:
            page = 1
            try:
                res = requests.get(SERVER_URL+'/dataset?start=0&max=20', headers=headers)
            except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
            if res.status_code >= 400:
                return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
        data= json.loads(res.text)
        for d in data:
            dataset.append({'name': d['_id'], 'title':d['meta']['titles'][0], 'description': d['meta']['descriptions'][0]})

        if len(dataset)< 20:
            last= page
        try:
            res1 = requests.get(SERVER_URL+'/dataset/featured?start=0&max=100', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if res1.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res1.text)})
        proposed_data = json.loads(res1.text)
        proposed = []
        for p in proposed_data:
            proposed.append({'name': p['_id'], 'meta': p['meta'] })
        #Display all datasets for selection
        return render(request, "predict.html", {'token': token, 'username': username, 'dataset': dataset, 'page': page, 'last':last, 'model_req': model_req, 'model' : model, 'image':image, 'mopac':mopac, 'proposed':proposed})
    if request.method == 'POST':
        #Get the selected model for prediction from session
        selected_model= request.session.get('model', '')
        #Get the method of prediction
        method = request.POST.get('radio_method')
        #Get the required model
        headers = {'Accept': 'application/json', 'Authorization': token}
        try:
            required_res = requests.get(SERVER_URL+'/model/'+selected_model+'/required', headers=headers)
        except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
        if required_res.status_code >= 400:
            return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(required_res.text)})
        required_res = json.loads(required_res.text)
        print required_res
        if request.is_ajax():
            img_descriptors = request.POST.getlist('img_desc[]')
            mopac_descriptors = request.POST.getlist('mopac_desc[]')
            print request.POST
            if 'excel_data' in request.POST:
                data = request.POST.get('excel_data')
                data = json.loads(data)
                n_data=[]
                for d in data:
                    n_d = {}
                    n_d1 = {}
                    for key, value in d.items():
                        new_val = value.replace(',', '.')
                        n_d1[''+key+'']=new_val
                        n_d.update(n_d1)
                    n_data.append(n_d)
                print n_data
                data = n_data
                #data = json.loads(data)
                #data.replace(',','.')'''
                print data
                #Get data from excel and create dataset to the appropriate format
                new_data = create_dataset(data,username,required_res, img_descriptors, mopac_descriptors)
                json_data = json.dumps(new_data)
                print("----------")
                print new_data
                headers1 = {'Content-type': 'application/json', 'Authorization': token}
                try:
                    res15 = requests.post(SERVER_URL+'/dataset', headers=headers1, data=json_data)
                    print res15.text
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res15.status_code >= 400:
                    return render_to_response(request, "error.html", {'token': token, 'username': username,'error': json.loads(res15.text)})
                dataset = res15.text
                print dataset
                headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': token,}
                body = {'dataset_uri': dataset, 'visible': True}
                print body
                print selected_model
                try:
                    res = requests.post(SERVER_URL+'/model/'+selected_model, headers=headers, data=body)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                response = json.loads(res.text)
                print response
                id = response['_id']
                print id
                return HttpResponse(id)
        if method == 'select_dataset':
            #Get the selected dataset
            dataset = request.POST.get('radio')
            print request.POST
            if dataset == "" or dataset == None:
                m = []
                #get all models
                headers = {'Accept': 'application/json', "Authorization": token}
                try:
                    res = requests.get(SERVER_URL+'/model?start=0&max=10000', headers=headers)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                models = json.loads(res.text)
                for mod in models:
                        m.append({'name': mod['_id'], 'meta': mod['meta']})
                return render(request, "read_across_predict.html", {'token': token, 'username': username,'selected_model': selected_model, 'page': page, 'last':last,'error':"You should select a dataset."})
            else:
                headers = {'Content-Type': 'application/x-www-form-urlencoded', "Authorization": token}
                body = {'dataset_uri': SERVER_URL+'/dataset/'+dataset, 'visible': True}
                try:
                    res = requests.post(SERVER_URL+'/model/'+selected_model, headers=headers, data=body)
                except Exception as e:
                    return render(request, "error.html", {'token': token, 'username': username,'server_error':e, })
                if res.status_code >= 400:
                    return render(request, "error.html", {'token': token, 'username': username,'error': json.loads(res.text)})
                response = json.loads(res.text)
                print response
                id = response['_id']
                return redirect('/t_detail?name='+id+'&model='+selected_model)
