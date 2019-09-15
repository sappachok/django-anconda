import os
import signal
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.core.management.base import BaseCommand
from django.http import HttpResponse, JsonResponse
from django.template import RequestContext

from chartjs.views.lines import BaseLineChartView

from sys import stdout, stdin, stderr
from subprocess import Popen, PIPE, STDOUT, check_output, CalledProcessError

import requests
import json
from html.parser import HTMLParser
import psycopg2

from io import StringIO
import time
from datasci.src import multicommand, clientsocket, run_multiscript, interact_subprocess

import fcntl
import select
import time

app_dir = os.path.abspath(os.path.dirname(__file__))

connection = psycopg2.connect(user="postgres",
                               password="postgres",
                               host="db",
                               port="5432",
                               database="postgres")
# python manage.py shell
# Create your views here.
def datasci(request):
    # db_output = connectdb()
    db_output = []
    template_dir = 'http://localhost:8000/static/templates/admin-lte'
    data = {'blog_title': 'Datasci App', 'get_project_url': 'getproject', 'template_dir': template_dir}
    return render(request, 'index.html', data)

def project(request, pid):
    # db_output = connectdb()
    # output = []
    project_info = get_project_info(pid)
    output = Command(["python", os.path.join(app_dir, "runscript.py"), pid])
    # output.append(test)
    # command = "print('test')"
    # process = Popen(command, stdout=PIPE, stderr=STDOUT)
    # db_output.append(process.stdout.read())
    # parser = HTMLParser()
    # parser.feed(output)

    if output["result"] == True:
        output_print = output["output"][0]
        output_list = output["output"][1]
        error = ""
    else:
        output_print = ""
        output_list = ""
        error = output["error"]

    data = {'blog_title': 'Datasci App', 'project_info': project_info, 'error': error, 'output_print': output_print, 'output_list': output_list}
    # pretty_data = db_output
    # return HttpResponse(pretty_data, content_type="application/json")
    return render(request, 'view-data.html', data)

def project_ex(request, pid):
    project_info = get_project_info(pid)
    project_script = project_info[3]
    script = project_script.split("\n")
    
    cmd = []
    for sc in script:
        cmd.append("{}\n".format(sc))
    cmd.append('from datasci.src import util_interactive')
    cmd.append('util_interactive.printfigs("fig", None, ".png")')
    cmd.append("quit()\n")

    output, error = run_multiscript.run(cmd)
    data = {'blog_title': 'Datasci App', 'project_info': project_info, 'output': output, 'error': error, 'script': cmd}
    return render(request, 'view-data-ex.html', data)

def get_project_info(pid):
    try:
        cursor = connection.cursor()
        select = """SELECT name, title, description, script FROM editor_pythonlab WHERE name='{0}'""".format(pid)
        cursor.execute(select)
        record = cursor.fetchone()
        return record
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL : {0}" + format(error))

def Command(cmd):
    command = cmd
    try:
        process = Popen(command, stdout=PIPE, stderr=STDOUT, encoding="utf-8")
        tmp = process.stdout.read()
        exoutput = tmp.split('### OUTPUT ###')

        if len(exoutput) > 1:
            output = [exoutput[0], json.loads(exoutput[1])]
        else:
            output = tmp

        exitstatus = process.poll()

        if (exitstatus == 0):
            return {"result": True, "output": output}
        else:
            return {"result": False, "error": tmp, "output": ''}
    except Exception as e:
        return {'result':False, 'error': str(e)}

class OBufferParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        # print("Encountered a start tag:", tag)
        if tag == "!output":
            self.output = ""

    def handle_endtag(self, tag):
        if tag == "!output":
            self.output = ""

    def handle_data(self, data):
            self.output = data

def connectdb():
    arr_output = []
    try:
        connection = psycopg2.connect(user="postgres",
                                      password="postgres",
                                      host="db",
                                      port="5432",
                                      database="postgres")
        cursor = connection.cursor()
        # Print PostgreSQL Connection properties
        arr_output.append(connection.get_dsn_parameters())
        # Print PostgreSQL version
        cursor.execute("SELECT version();")
        record = cursor.fetchone()
        arr_output.append("You are connected to - {0}".format(record))

        cursor.execute("""SELECT
           *
        FROM
           editor_pythoncode
        """)
        records = cursor.fetchall()
        for rec in records :
           arr_output.append("Record - {0}".format(rec))

        return arr_output
        # query_python_code()
    except (Exception, psycopg2.Error) as error:
        arr_output.append("Error while connecting to PostgreSQL : {0}" + format(error))
        return arr_output
        # return False

class SampleView(TemplateView):
    template_name = 'about.html'

def websocket_console(request):
    # project_info = get_project_info(pid)
    data = {'blog_title': 'Python Editor'}
    
    return render(request, 'websocket-console.html', data)
    
def editor(request, pid=""):
    project_info = get_project_info(pid)
    data = {'blog_title': 'Python Editor', 'project_info': project_info}
    
    return render(request, 'python-editor.html', data)

def run_command(proc, commands):
    for cmd in commands:
        if cmd :
            try :
                tmp = '{0}\n'.format(cmd)
                proc.stdin.write(tmp.encode())
                proc.stdin.flush()
            except Exception as e:
                return "Error : {0}".format(e)
        else :
            pass
    return proc

def kill_process(request, pid):
    os.kill(pid, signal.SIGTERM)
    return HttpResponse("Kill Process {}".format(pid))

def get_interactive_output(request):
    result = interact_subprocess.run('print("Hello!!")')
    return HttpResponse(result)
    
def editor_process(request):
    cmd = request.POST.get("command")
    commands = prepaire_command(cmd)
    
    
    return HttpResponse(json.dumps(output), content_type="application/json")

def prepaire_command(cmd, sp='\r\n'):
    command_list = cmd.split(sp)
    data = []
    for c in command_list:
        data.append(c)

    return data

def client_socket(request):
    '''
    command = ['python3', os.path.join(app_dir, 'client.py')]
    process = Popen(command, stdout=PIPE, stderr=STDOUT, encoding="utf-8")
    tmp = process.stdout.read()
    '''
    '''
    clientsocket.connect()
    return HttpResponse("Hello Server")
    '''
    data = []
    try :
        data = clientsocket.test_command()
    except:
        data.append("Error")
    
    # data.append(proc.stdout.readline())
    
    return HttpResponse(data)
        
def chartjs(request):
    data = {'blog_title': 'Datasci App'}
    # pretty_data = db_output
    # return HttpResponse(pretty_data, content_type="application/json")         
    return render(request, 'chartjs.html', data)

def chart_data(request):
    data = {
        'type': 'bar',
        'data': {
            'labels': ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
            'datasets': [{
                'label': '# of Votes',
                'data': [12, 19, 3, 5, 2, 3],
                'backgroundColor': [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                'borderColor': [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                'borderWidth': 1
            }]
        },
        'options': {
            'scales': {
                'yAxes': [{
                    'ticks': {
                        'beginAtZero': True
                    }
                }]
            }
        }
    }

    return JsonResponse(data)

def chart_data_2(request):
    return True