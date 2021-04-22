from flask_wtf import FlaskForm
from wtforms import StringField, FileField, DateTimeField, SubmitField
from wtforms.validators import DataRequired
from wtforms.fields import core
import re

class MainForm(FlaskForm):
    schema_file = FileField('Schema File')
    ref_file = FileField('Reference File')
    #datetime = DateTimeField('Date and Time', format='%Y/%m/%d %H:%M:%S')
    output_loc = StringField('Output Location')
    comment = StringField('Comment')
    #get_dt = SubmitField('Update DateTime')
    submit = SubmitField('Generate')
    next = SubmitField('Change')
'''                     
record = {}
if ref_file:
    with open(ref_file) as f:
        record = yaml.safe_load(f)
    for key,val in record.items()

class DynForm(FlaskForm):
    fieldlist = {}
'''