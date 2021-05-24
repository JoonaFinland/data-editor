from flask import Flask, render_template, redirect, flash, request, Response, url_for
import datetime
import yaml
#from werkzeug.utils import secure_filename already in Flask, no need to import
import jsonschema
import json
from collections import defaultdict
import pprint
import os
import re
import copy
import ymlvalidator
import copy
import secrets


app = Flask(__name__)
# set the app secret key using random hex
secret_key = secrets.token_hex(16)
app.config['SECRET_KEY'] = secret_key

#from app import app
from forms import MainForm

# create a dict
class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

def is_valid(obj, schema):
    try:
        jsonschema.validate(obj, schema)
    except jsonschema.ValidationError:
        return False
    else:
        return True


def order_other_dict(sche,dict):
    tmp = Vividict()
    for key,val in sche.items():
        if key in dict and dict[key]['filename'] != 'None':
            tmp[key] = val
    for key,val in sche.items():
        if key not in dict or dict[key]['filename'] == 'None':
            tmp[key] = val
    return tmp

def order_schema(schema,data):
    tmp = copy.deepcopy(schema)
    
    pp = pprint.PrettyPrinter(indent=4)
    return tmp


@app.context_processor
def utility_processor():
    def validate_single(inst, schema):
        return is_valid(inst, schema)
    return dict(validate_single=validate_single)
    
    
@app.route('/', methods=('GET', 'POST'))
@app.route('/single', methods=('GET', 'POST'))
def single():
    form = MainForm()
    dt_value=''
    data={}
    with open('schema.yml','r') as fi:
        sche=yaml.load(fi)
    to_p = schemaToDict(sche)
    ref = {}
    ovr='False'
    ovrd='False'
    def_ref = "No File Chosen"
    def_schema = "No File Chosen, Default Schema Loaded"
    out_loc = 'B:\\Uni\\Secure\\test\\'
    if request.method == "POST":
        #print(request.form)
        data = generate_meta(request.form.to_dict())
        #print(data)
        if request.files['ref_file'].filename != '':
            def_ref = request.files['ref_file'].filename
        if request.files['schema_file'].filename != '':
            schema_ref = request.files['schema_file'].filename
        out_loc = request.form.to_dict().get('output_loc')
        ovr = request.form.to_dict().get('overwrite')
        if "submit" in request.form:
            name_ = ''
            if os.path.exists(out_loc):
                if ovr:
                    flash('generating metadata.yaml to '+out_loc)
                    data = generate_meta(request.form.to_dict())
                    yaml_data = yaml.dump(data, sort_keys=False)
                    with open(out_loc+'\\metadata.yaml', 'w') as f:
                        f.write(yaml_data)
                    name_ = out_loc+'\\metadata.yaml'
                else:
                    int_ = 0
                    prev_name = "metadata.yaml"
                    while True:
                        if int_ == 0:
                            name = "metadata.yaml"
                        else:
                            name = "metadata"+str(int_)+".yaml"
                        if os.path.exists(out_loc+'\\'+name):
                            int_ += 1
                            prev_name=name
                        else:
                            flash(name+' is new file in '+out_loc)
                            data = generate_meta(request.form.to_dict())
                            yaml_data = yaml.dump(data, sort_keys=False)
                            with open(out_loc+'\\'+name, 'w') as f:
                                f.write(yaml_data)
                            name_ = out_loc+'\\'+name
                            break
                if def_schema == 'No File Chosen, Default Schema Loaded':
                    schem_ = 'schema.yml'
                fil = open(schem_,'r')
                args = tempData([name_], fil, False)
                if ymlvalidator.main(args) != 0:
                    flash('Warning File validation failed! Check CMD for log. File still generated')
                fil.close()
            else:
                flash('output location does not exist')
            #return Response(yaml_data, mimetype='text/plain')
        elif "upload" in request.form:
            data = generate_meta(request.form.to_dict())
            out_loc = request.form.to_dict().get('output_loc')
            if request.files['schema_file'].filename !='':
                try:
                    e = request.files['schema_file']
                    sche = fixNull(yaml.load(e))
                    def_schema = request.files['schema_file'].filename
                except Exception as er:
                    print(er)
                    flash('file error')
            else:
                with open('schema.yml','r') as fi:
                    sche=yaml.load(fi)
            if request.files['ref_file'].filename != '':
                try:
                    f = request.files['ref_file']
                    #f.save(secure_filename(f.filename))
                    ref = fixNull(yaml.load(f))
                    def_ref = request.files['ref_file'].filename
                except Exception as er:
                    print(er)
                    flash('file error')
            else:
                ref = {}
            
            to_p_raw = sche
            to_p = schemaToDict(to_p_raw)
            #print(to_p)
            #to_p = to_p_raw['properties']
        
        elif "update" in request.form:
            datetimes = []
            if not os.path.exists(out_loc):
                flash('output location does not exist')
            # try to get existing metadata file 
            if os.path.exists(out_loc+'/metadata.yaml'):
                try:
                    with open(out_loc+'/metadata.yaml','r') as f:
                    #f.save(secure_filename(f.filename))
                        ref = fixNull(yaml.load(f))
                    #def_ref = request.files['ref_file'].filename
                except Exception as er:
                    print(er)
                    flash('file error')
            
    return render_template('form.html', title='Data Editor', form=form, dt_value=dt_value, to_p=order_schema(to_p,data), ref=ref, data=data,
    out_loc=out_loc, def_schema=def_schema, def_ref=def_ref, ovr=ovr, ovrd=ovrd)
 

class tempData():
    def __init__(self, input, output, verbose):
        self.input = input
        self.schema = output
        self.verbose = verbose


def fixNull(yaml_file):
    for key1,val1 in yaml_file.items():
        if isinstance(val1, dict):
            for key2,val2 in val1.items():
                if isinstance(val2, dict):
                    for key3,val3 in val1.items():
                        if val3 is None:
                            yaml_file[key1][key2][key3] = 'Null'
                else:
                    if val2 is None:
                        yaml_file[key1][key2] = 'Null'
        else:
           if val1 is None:
                yaml_file[key1] = 'Null'
    return yaml_file

def getFromDict(dataDict, mapList):
    for k in mapList: dataDict = dataDict[k]
    return dataDict
    
def setInDict(dataDict, mapList, val):
    first, rest = mapList[0], mapList[1:]
    if rest:
        try:
            if not isinstance(dataDict[first], dict):
                # if the key is not a dict, then make it a dict
                dataDict[first] = {}
        except KeyError:
            # if key doesn't exist, create one
            dataDict[first] = {}
        setInDict(dataDict[first], rest, val)
    else:
        dataDict[first] = val
    return dataDict

def generate_meta(dict):
    metadata = {}
    # do not generate these as they are helpers used in flask
    denied = ['csrf_token','submit','update','output_loc','overwrite','g_ind',
        'g_subfolders', 'g_current_file', 'ovr', 'ovrd', 'overdate','skip','skip_tags','skipbox']
    for key,val in dict.items():
        if key not in denied:
            if val not in ['', 'Null']:
                if is_digit(val) and key.split(';')[-1] not in ['imei']:
                    val = int(val)
                metadata = setInDict(metadata, key.split(';'), val)
    return metadata

def is_digit(n):
    try:
        int(n)
        return True
    except ValueError:
        return  False

def infoToType(keva, schema):
    tmp = 'Null'
    typ = 'Null'
    if 'description' in keva:
        tmp = keva['description']
        tmp = 'string'
    elif 'enum' in keva:
        tmp = ','.join(changeNoneType(keva['enum']))+',Null'
        typ = 'enum'
    elif '$ref' in keva:
        if 'enum' in schema['definitions'][keva['$ref'].split('/')[-1]]:
            tmp = ','.join(schema['definitions'][keva['$ref'].split('/')[-1]]['enum'])+',Null'
        else:
            tmp = schema['definitions'][keva['$ref'].split('/')[-1]]['type'][0]
    elif 'type' in keva:
        if keva['type'] == "array":
            tmp = 'string'
        else:
            tmp = keva['type']
    else:
        print('else')
        print(keva)
        tmp = 'NON'
        
    return tmp

def changeNoneType(list):
    out = []
    for each in list:
        if isinstance(each, str):
            out.append(each)
        elif each is None:
            out.append('Null')
    return out

def schemaToDict(schema):
    maindict = Vividict()
    need_extra = ['']
    for key1,val1 in schema['properties'].items():
        if 'type' not in val1:
            pass
        elif val1['type'] != 'object':
            maindict[key1] = infoToType(val1,schema)
        else:
            for key2,val2 in val1['properties'].items():
                if 'type' not in val2:
                    maindict[key1][key2] = infoToType(val2,schema)
                elif val2['type'] == 'object':
                    for key3,val3 in val2['properties'].items():
                        if 'type' not in val3:
                            maindict[key1][key2][key3] = infoToType(val3,schema)
                        elif val3['type'] == 'object':
                            for key4,val4 in val3['properties'].items():
                                maindict[key1][key2][key3][key4] = infoToType(val4,schema)
    return maindict

