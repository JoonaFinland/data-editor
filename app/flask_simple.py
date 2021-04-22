from flask import Flask, render_template, redirect, flash, request, Response, url_for
import datetime
import yaml
#from werkzeug.utils import secure_filename
import jsonschema
import json
from collections import defaultdict
import pprint
import os
import re
import copy
import ymlvalidator
import copy

app = Flask(__name__)
app.config['SECRET_KEY'] = '123'
#from app import app
from forms import MainForm

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
    #print(type(schema))
    #print(schema)
    #print(type(schema['channels']))
    
    pp = pprint.PrettyPrinter(indent=4)
    if 'channels' in schema and 'channels' in data:
        tmp['channels'] = order_other_dict(schema['channels'],data['channels'])
        #pp.pprint(schema['channels'])
        #pp.pprint(data['channels'])
    return tmp


@app.context_processor
def utility_processor():
    def validate_single(inst, schema):
        return is_valid(inst, schema)
    return dict(validate_single=validate_single)
    
    
@app.route('/', methods=('GET', 'POST'))
@app.route('/single', methods=('GET', 'POST'))
def single():
    LEFT_RIGHT_MAP = {
        '0': 'right',
        '1': 'left'}
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
    out_loc = 'D:\\SVN\\Test_vectors\\'
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
        if "change" in request.form:
            print('WHY IS THIS CALLED!')
            return redirect(url_for('multi'))
        elif "submit" in request.form:
            #print('*'*10)
            #print(ovr)
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
            # get datetime somehow from output svn folder
            data = setInDict(data, ['device','imei'], out_loc.split('\\')[-2].split('_')[-1])
            if ('windtunnel' in out_loc.split('\\')[-1]):
                #print(glob_data['current_file'].split('\\')[-1])    
                data = setInDict(data, ['audioscene','environment','wind_direction'], out_loc.split('\\')[-1].split('_')[2])
            #print(data['device']['imei'])
            datetimes = []
            if os.path.exists(out_loc):
                try:
                    for wav in os.listdir(out_loc):
                        # must check if wav is a correct wav file, otherwise python crashes with the 0 length wav files, wrong format
                        wv = re.search('(.*)b_(.*)k_vpu(.*)', wav)
                        rm = re.search('(.*)b_(.*)k_mic(.*)', wav)
                        er = re.search('(.*)b_(.*)k_ecref', wav)
                        mi = re.search('ref_mic(.*)', wav)
                        # print(rm)
                        if rm or wv:
                            datetimes.append(os.path.getctime(out_loc+'\\'+wav))
                        if rm:
                            data = setInDict(data, ['channels','mic_'+LEFT_RIGHT_MAP[rm.group(3)[0]]+'_'+rm.group(3).split('.')[0][-1],'filename'], wav)
                            #data['channels;mic_'+LEFT_RIGHT_MAP[rm.group(3)[0]]+'_'+rm.group(3).split('.')[0]+';filename'] = wav
                        if wv:
                            data = setInDict(data, ['channels','vpu_'+LEFT_RIGHT_MAP[wv.group(3)[0]],'filename'], wav)
                            #data['channels;vpu_'+LEFT_RIGHT_MAP[wv
                        if er:
                            data = setInDict(data, ['channels','ecref','filename'], wav) 
                        if mi:
                            data = setInDict(data, ['channels','refmic','filename'], wav) 
                    #print(datetimes)
                    if (ovrd=='True'):
                        dt_value = datetime.datetime.fromtimestamp(sum(datetimes)/len(datetimes)).strftime("%Y/%m/%d %H:%M:%S")
                except:
                    flash('no wav files found in folder')
            else:
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
            try:
                ref = setInDict(ref, ['device','imei'], data['device']['imei'])
                ref = setInDict(ref, ['audioscene','environment','wind_direction'], data['audioscene']['environment']['wind_direction'])
            except:
                pass
            
    return render_template('form.html', title='Metadata Editor', form=form, dt_value=dt_value, to_p=order_schema(to_p,data), ref=ref, data=data,
    out_loc=out_loc, def_schema=def_schema, def_ref=def_ref, ovr=ovr, ovrd=ovrd)
 

class tempData():
    def __init__(self, input, output, verbose):
        self.input = input
        self.schema = output
        self.verbose = verbose


def nextMeta(glob_data):
    ''' get the next metadata
    returns: glob_data '''
    glob_data['ind'] += 1
    if glob_data['ind'] >= len(glob_data['subfolders']):
        glob_data['ind'] = 0
    return glob_data


def prevMeta(glob_data):
    ''' get the previous metadata
    returns: glob_data '''
    glob_data['ind'] -= 1
    if glob_data['ind'] < 0:
        glob_data['ind'] = len(glob_data['subfolders'])-1
    return glob_data


def nextMetaTag(glob_data, skip_tags):
    ''' get the next metadata using tags
    returns: glob_data '''
    stop = False
    while not stop:
        if glob_data['ind'] >= len(glob_data['subfolders']):
            glob_data['ind'] = 0
            stop=True
            flash('reached end of files')
            break
        if all(ext in glob_data['subfolders'][glob_data['ind']] for ext in skip_tags):
            stop=True
            break
        else:
            glob_data['ind'] += 1
    return glob_data


def prevMetaTag(glob_data, skip_tags):
    ''' get the previous metadata using tags
    returns: glob_data '''
    stop=False
    while not stop:
        if glob_data['ind'] < 0:
            glob_data['ind'] = len(glob_data['subfolders'])-1
            stop=True
            flash('reached end of files')
            break
        if all(ext in glob_data['current_file'] for ext in skip_tags):
            stop=True
            break
        else:
                glob_data['ind'] -= 1
    return glob_data


def nextMetaNot(glob_data):
    ''' get the next metadata without existing metadata.yaml file
    returns: glob_data '''
    name='metadata.yaml'
    while (os.path.exists(glob_data['subfolders'][glob_data['ind']]+'\\'+name)):
        if glob_data['ind'] >= len(glob_data['subfolders'])-1:
            glob_data['ind'] = 0
            break
        else:
            glob_data['ind'] += 1
    return glob_data


def prevMetaNot(glob_data):
    ''' get the previous metadata without existing metadata.yaml file
    returns: glob_data '''
    name='metadata.yaml'
    while (os.path.exists(glob_data['subfolders'][glob_data['ind']]+'\\'+name)):
        if glob_data['ind'] <= 0:
            glob_data['ind'] = len(glob_data['subfolders'])-1
            break
        else:
            glob_data['ind'] -= 1
    return glob_data


def nextMetaTagNot(glob_data, skip_tags):
    ''' get the next metadata with tags and non existing metadata.yaml file
    returns: glob_data '''
    name='metadata.yaml'
    print('nextmetatagnotd')
    print(skip_tags)
    stop = False
    while not stop:
        stop = False
        if glob_data['ind'] >= len(glob_data['subfolders']):
            glob_data['ind'] = 0
            stop=True
            flash('reached end of files')
            break
        if (all(ext in glob_data['subfolders'][glob_data['ind']] for ext in skip_tags) and 
                not os.path.exists(glob_data['subfolders'][glob_data['ind']]+'\\'+name)):
            stop=True
        else:
            glob_data['ind'] += 1
        
    return glob_data


def prevMetaTagNot(glob_data, skip_tags):
    ''' get the previous metadata with tags and non existing metadata.yaml file
    returns: glob_data '''
    name='metadata.yaml'
    stop = False
    while not stop:                            
        stop = False
        if glob_data['ind'] < 0:
            glob_data['ind'] = len(glob_data['subfolders'])-1
            stop=True
            flash('reached end of files')
            break
        if (all(ext in glob_data['subfolders'][glob_data['ind']] for ext in skip_tags) and 
                not os.path.exists(glob_data['subfolders'][glob_data['ind']]+'\\'+name)):
            stop=True
        else:
            glob_data['ind'] -= 1

    return glob_data


@app.route('/multi', methods=('GET', 'POST'))
def multi():
    LEFT_RIGHT_MAP = {
        '0': 'right',
        '1': 'left'}
    glob_data = {'ind': 0,
                'subfolders': [''],
                'subfolders_str': '',
                'current_file': 'None',
                'hide': {}}
    form = MainForm()
    dt_value=''
    data={}
    ovr='False'
    ovrd='False'
    skip='False'
    with open('schema.yml','r') as fi:
        sche=yaml.load(fi)
    to_p = schemaToDict(sche)
    ref = {}
    def_ref = "No File Chosen"
    def_schema = "No File Chosen, Default Schema Loaded"
    out_loc = 'D:\\SVN\\Test_vectors\\'
    skip_tags = ''
    if request.method == "POST":
        #print(request.form.to_dict())
        if request.files['schema_file'].filename != '':
            schema_ref = request.files['schema_file'].filename
        ovr = request.form.to_dict().get('overwrite')
        ovrd = request.form.to_dict().get('overdate')
        skip = request.form.to_dict().get('skipbox')
        skip_tags = request.form.to_dict().get('skip_tags').split(',')
        #print('ovrd:',ovrd)
        glob_data = {'ind': int(request.form.to_dict().get('g_ind')),
            'subfolders': request.form.to_dict().get('g_subfolders').split(';'),
            'subfolders_str': request.form.to_dict().get('g_subfolders'),
            'current_file': request.form.to_dict().get('g_current_file')}
        #glob_data = request.form.to_dict.get('glob_data')
        #glob_data['ind']+=1
        tmp = copy.deepcopy(glob_data)
        tmp['current_file'] = glob_data['subfolders'][glob_data['ind']]
        glob_data = copy.deepcopy(tmp)
        data = generate_meta(request.form.to_dict())
        out_loc = glob_data['current_file']
        
        if "next" in request.form:
            #glob_data = request.form.to_dict().get('glob_data')
            glob_data = nextMeta(glob_data)
            if skip_tags != [''] and skip:
                glob_data = nextMetaTagNot(glob_data,skip_tags)
            if skip_tags:
                glob_data = nextMetaTag(glob_data,skip_tags)
            if skip:
                glob_data = nextMetaNot(glob_data)
            tmp = copy.deepcopy(glob_data)
            tmp['current_file'] = glob_data['subfolders'][glob_data['ind']]
            glob_data = copy.deepcopy(tmp)
            data = generate_meta(request.form.to_dict())
            out_loc = glob_data['current_file']
            
        elif "back" in request.form:
            #glob_data = request.form.to_dict().get('glob_data')
            glob_data = prevMeta(glob_data)
            if skip_tags != [''] and skip:
                glob_data = prevMetaTagNot(glob_data,skip_tags)
            if skip_tags:
                glob_data = prevMetaTag(glob_data,skip_tags)
            if skip:
                glob_data = prevMetaNot(glob_data)
            tmp = copy.deepcopy(glob_data)
            tmp['current_file'] = glob_data['subfolders'][glob_data['ind']]
            glob_data = copy.deepcopy(tmp)
            data = generate_meta(request.form.to_dict())
            out_loc = glob_data['current_file']
            
        elif "change" in request.form:
            return redirect(url_for('single'))
        elif "submit" in request.form:
            #glob_data = request.form.to_dict.get('glob_data')
            name = 'metadata.yaml'
                                        
            if os.path.exists(out_loc):
                name_ = ''
                if ovr:
                    flash('generating metadata.yaml to '+out_loc)
                    data = generate_meta(request.form.to_dict())
                    yaml_data = yaml.dump(data, sort_keys=False)
                    name_ = out_loc+'\\metadata.yaml'
                    with open(out_loc+'\\metadata.yaml', 'w') as f:
                        f.write(yaml_data)
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
                            name_ = out_loc+'\\'+name
                            with open(out_loc+'\\'+name, 'w') as f:
                                f.write(yaml_data)
                            break
                # test validate
                #print(name_)
                fil = open("schema.yml",'r')
                args = tempData([name_], fil, False)
                if ymlvalidator.main(args) != 0:
                    flash('Warning File validation failed! Check CMD for log. File still generated')
                fil.close()
                glob_data = nextMeta(glob_data)
                if skip_tags != [''] and skip:
                    glob_data = nextMetaTagNot(glob_data,skip_tags)
                if skip_tags:
                    glob_data = nextMetaTag(glob_data,skip_tags)
                if skip:
                    glob_data = nextMetaNot(glob_data)
                tmp = copy.deepcopy(glob_data)
                tmp['current_file'] = glob_data['subfolders'][glob_data['ind']]
                glob_data = copy.deepcopy(tmp)
                data = generate_meta(request.form.to_dict())
                out_loc = glob_data['current_file']
                
            #return Response(yaml_data, mimetype='text/plain')
        elif "upload" in request.form:
            data = generate_meta(request.form.to_dict())
            out_loc = request.form.to_dict().get('output_loc')
            glob_data['ind'] = 0
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
            # check parent directory is legit
            if os.path.exists(out_loc):
                # assume folder is only IMEI folder TODO: CHECK IF IMEI;ELSE RECUSIVELY THROUGH THOSE
                old = glob_data['subfolders']
                glob_data['subfolders'] = [f.path for f in os.scandir(out_loc) if f.is_dir()]
                glob_data['subfolders_str'] = ";".join(glob_data['subfolders'])
                tmp = copy.deepcopy(glob_data)
                print(out_loc)
                print(tmp)
                print('_'*34)
                print(glob_data['ind'])
                print(glob_data['subfolders'])
                if glob_data['subfolders'] == []:
                    flash('No files found, make sure parent directory is IMEI folder')
                    glob_data['subfolders'] = old
                else:
                    tmp['current_file'] = glob_data['subfolders'][glob_data['ind']]
                    glob_data = copy.deepcopy(tmp)
                    data = generate_meta(request.form.to_dict())
                    out_loc = glob_data['current_file']
                
            else:
                flash('Parent Directory Invalid: '+out_loc)
            
            to_p_raw = sche
            to_p = schemaToDict(to_p_raw)
            if skip_tags != [''] and skip:
                glob_data = nextMetaTagNot(glob_data,skip_tags)
            if skip_tags:
                glob_data = nextMetaTag(glob_data,skip_tags)
            if skip:
                glob_data = nextMetaNot(glob_data)
            tmp = copy.deepcopy(glob_data)
            tmp['current_file'] = glob_data['subfolders'][glob_data['ind']]
            glob_data = copy.deepcopy(tmp)
            data = generate_meta(request.form.to_dict())
            out_loc = glob_data['current_file']
            #print(to_p)
            #to_p = to_p_raw['properties']
        
        if "next" in request.form or "back" in request.form or "submit" in request.form:
            dt_value = ''
        
        if "upload" in request.form or "update" in request.form or "next" in request.form or "back" in request.form or "submit" in request.form:
            # get datetime and wav filenames from folder
            data = setInDict(data, ['device','imei'], glob_data['current_file'].split('\\')[-2].split('_')[-1])
            if ('windtunnel' in glob_data['current_file'].split('\\')[-1]):
                #print(glob_data['current_file'].split('\\')[-1])    
                data = setInDict(data, ['audioscene','environment','wind_direction'], glob_data['current_file'].split('\\')[-1].split('_')[2])
            #print(data['device']['imei'])
            datetimes = []
            if os.path.exists(out_loc):
                try:
                    for wav in os.listdir(out_loc):
                        # must check if wav is a correct wav file, otherwise python crashes with the 0 length wav files, wrong format
                        wv = re.search('(.*)b_(.*)k_vpu(.*)', wav)
                        rm = re.search('(.*)b_(.*)k_mic(.*)', wav)
                        er = re.search('(.*)b_(.*)k_ecref', wav)
                        mi = re.search('ref_mic(.*)', wav)
                        # print(rm)
                        if rm or wv:
                            datetimes.append(os.path.getctime(out_loc+'\\'+wav))
                        if rm:
                            data = setInDict(data, ['channels','mic_'+LEFT_RIGHT_MAP[rm.group(3)[0]]+'_'+rm.group(3).split('.')[0][-1],'filename'], wav)
                            #data['channels;mic_'+LEFT_RIGHT_MAP[rm.group(3)[0]]+'_'+rm.group(3).split('.')[0]+';filename'] = wav
                        if wv:
                            data = setInDict(data, ['channels','vpu_'+LEFT_RIGHT_MAP[wv.group(3)[0]],'filename'], wav)
                            #data['channels;vpu_'+LEFT_RIGHT_MAP[wv
                        if er:
                            data = setInDict(data, ['channels','ecref','filename'], wav) 
                        if mi:
                            data = setInDict(data, ['channels','refmic','filename'], wav) 
                    #print(datetimes)
                    if (ovrd=='True'):
                        dt_value = datetime.datetime.fromtimestamp(sum(datetimes)/len(datetimes)).strftime("%Y/%m/%d %H:%M:%S")
                except:
                    flash('no wav files found in folder')
            else:
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
            try:
                ref = setInDict(ref, ['device','imei'], data['device']['imei'])
                ref = setInDict(ref, ['audioscene','environment','wind_direction'], data['audioscene']['environment']['wind_direction'])
            except:
                pass
            
    return render_template('multi.html', title='Metadata Editor', form=form, dt_value=dt_value, to_p=order_schema(to_p,data), 
    glob_data=glob_data, data=data, out_loc=out_loc, def_schema=def_schema, def_ref=def_ref, ovr=ovr, 
    ovrd=ovrd, ref=ref, skip=skip, skip_tags=','.join(skip_tags),length=len(glob_data['subfolders']),cur=glob_data['ind']+1)
 


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
        if keva['$ref'].split('/')[-1] == 'impact':
            # IMPACT
            tmp = 'string'
        elif keva['$ref'].split('/')[-1] == 'channel':
            # DO CHANNEL
            tmp = schemaToDict(schema['definitions']['channel'])
        else:
            # check from definitions
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

