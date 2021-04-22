import ymlvalidator

class tempData():
    def __init__(self, input, output, verbose):
        self.input = input
        self.schema = output
        self.verbose = verbose
        
name = "D:\\tmp_svn\\Proto9\\2020-06-18\\3Pass_EarsEemi\\3PASS_Airport_EarsEemi\\metadata4.yaml"
fil = open("schema.yml",'r')
args = tempData([name], fil, False)
if ymlvalidator.main(args) != 0:
   print('Warning File validation failed! Check CMD for log. File still generated')
fil.close()