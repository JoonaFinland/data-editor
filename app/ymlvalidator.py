
# This file has the validator logic, which is used in the flask app
# to validate the data file according to schema rules


from jsonschema import validate
import pprint
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict
from glob import glob
import collections
import argparse
import yaml
import sys
import os
from multiprocessing import Pool
import dateutil.parser

dependencies = [
    'jsonschema',
    'pyaml'
]

class EvaluationError(Exception):
    pass

def findFile(dirName, name):
    arr = []
    while True:
        dirName = os.path.dirname(dirName)
        fileName = os.path.join(dirName, name)
        if os.path.isfile(fileName):
            arr.append(fileName)
        if dirName == os.path.dirname(dirName):
            break
    return reversed(arr)

class Node():

    def __init__(self, path, d):
        self.path = path
        self.d = dict(d)
        self.description = yaml.safe_load(self.d.get('description', ""))

    def isLeaf(self):
        return 'properties' not in self.d

    def getChild(self):
        for k, v in self.d.get('properties', {}).items():
            yield Node(self.path + [k], v)

    def eval(self, d):
        if self.description is None or 'eval' not in self.description:
            return

        for i in self.path:
            try:
                d = d[i]
            except KeyError:
                return

        if d is not None:
            try:
                eval(self.description['eval'])(d)
            except:
                raise EvaluationError("{}: Evaluation exception: {}({})".format("/".join(self.path), self.description['eval'], d))

        return

    def xvalidate(self, d, dirName):
        if self.description is None or 'type' not in self.description:
            return

        for i in self.path:
            try:
                d = d[i]
            except KeyError:
                return

        if d is not None:
            if not os.path.isfile(os.path.join(dirName, d)):
                raise EvaluationError("{}: Xvalidation exception: {}({})".format("/".join(self.path), "file not found", d))
        return


def schemaWalk(d):
    stack = [Node([], d)]
    while stack:
        node = stack.pop(0)
        if node.isLeaf():
            yield node
        else:
            for n in node.getChild():
                stack.append(n)
                
def validateJson(schema, instance, dirName):
    try:
        validate(instance=instance, schema=schema)
    except Exception as e:
        print(e, file = sys.stderr)
        return False

    if not instance:
        return True

    for node in schemaWalk(schema):
        node.xvalidate(instance, dirName)
        try:
            node.eval(instance)
        except EvaluationError as e:
            print(e, file = sys.stderr)
            return False
    return True
    
def main(args):
    '''
    schemasFound = {}
    for root, dirs, files in os.walk(os.environ.get('FA_TEST')):
        for file in files:
            if file == 'schema.yml':
                fileName = os.path.join(root, file)
                with open(fileName) as f:
                    schemasFound[os.path.normcase(fileName)] = yaml.safe_load(f)
                    if args.verbose:
                        print(schemasFound)'''

    inputs = []
    print(args.input)
    for i in args.input:
        if os.path.isfile(i):
            inputs.append(i)
        else:
            for root, dirs, files in os.walk(i):
                for file in files:
                    if file == 'metadata.yaml':
                        inputs.append(os.path.join(root, file))
    #print(inputs)
    ret = 0
    schema = yaml.safe_load(args.schema)

    for n, i in enumerate(inputs, 1):
        #print(n)
        instance = {}
        #for s in findFile(os.path.normcase(os.path.abspath(i)), 'metadata.yaml'):
        with open(i) as f:
            instance.update(yaml.safe_load(f))

        if args.verbose:
            print("\n", instance)

        if not validateJson(schema, instance, os.path.dirname(i)):
            print("[{}/{}]".format(n, len(inputs)) + i, "failed")
            return -1

        print("[{}/{}]".format(n, len(inputs)) + i, "ok")
    return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate metadata.yml')
    parser.add_argument('input', help="inputs-files", action='append')
    parser.add_argument("-s", "--schema", type=argparse.FileType('r'), default="schema.yml", help="default schema file")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    tmp = parser.parse_args()
    #print(tmp)
    print(main(parser.parse_args()))
