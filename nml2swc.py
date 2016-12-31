#coding=utf-8
import sys
import os
import argparse
try:
    from lxml import etree
except ImportError:
    raise ImportError('lxml library is required')
try:
    from cStringIO import StringIO
except ImportError:
    try:
        from io import StringIO
    except:
        from StringIO import StringIO
try:
    from sys import maxint as maxint
except:
    from sys import maxsize as maxint
from copy import deepcopy
from zipfile import ZipFile

__doc__='''
this module helps convert nml or nmx format files to swc format files.
there are two ways to use this module:
(1) python somefile.nml(or somefile.nmx) [-o output file name or directory] [--radius radius of swc node default is 1.0]
(2) use this module in your project:
    from  nml2swc import parseFile
    parseFile(somefile.nml(or somefile.nmx),output file name or directory,radius)
'''

class NmlParser(object):
    def __init__(self,nml,radius,kind):
        super(NmlParser,self).__init__()
        self.processed=[]
        self.id=1
        self.nml=nml
        self.kind=kind
        self.radius=radius
        self.result=[]
   
    def process(self):
        self._getParamsAndComments()
        self._createGraph()
        self._dfs()
        return self.result
    
    def _createGraph(self):
        self.nodes={node.get('id'):
            {'x':node.get('x'),'y':node.get('y'),
             'z':node.get('z'),'visited':False,'index':maxint,'child':[]} 
             for node in self.nml.xpath(r'//node')}
        for edge in self.nml.xpath(r'//edge'):
            s=edge.get('source')
            t=edge.get('target')
            self.nodes[s]['child'].append(t)
            self.nodes[t]['child'].append(s)
    
    def _dfs(self):
        for node,attr in self.nodes.items():
            if not attr['visited']:
                self._dfs_(node,attr,-1)
    
    def _dfs_(self,node,attr,parent):
        attr['visited']=True
        attr['index']=self.id
        self.id+=1
        self._outputNode(attr,parent)
        for c in attr['child']:
            cattr=self.nodes[c]
            #recursively visit children
            if not cattr['visited']: 
                self._dfs_(c,cattr,attr['index'])
            #handle loop when traceback
            else:
                if cattr['index']>attr['index']:
                    nattr=deepcopy(cattr)
                    nattr['index']=self.id
                    self.id+=1
                    self._outputNode(nattr,attr['index'])
  
    def _outputNode(self,attr,parent):
        record="{id} {t} {x} {y} {z} {r} {p}".format(id=attr['index'],
        x=attr['x'],y=attr['y'],z=attr['z'],t=self.kind,r=self.radius,p=parent)
        self.result.append(record)
            
    def _getParamsAndComments(self):        
        for param in self.nml.xpath(r'//parameters'):
            try:
                p=StringIO(etree.tostring(param).decode('utf-8'))
            except:
                p=StringIO(etree.tostring(param))
            for line in p.readlines():
                self.result.append('#'+line)
        for com in self.nml.xpath(r'//comments'):
            try:
                c=StringIO(etree.tostring(com).decode('utf-8'))
            except:
                c=StringIO(etree.tostring(com))
            for line in c.readlines():
                self.result.append('#'+line)
        
        
def write2File(result,fname):
    with open(fname,'w') as f:
        for item in result:
            f.write(item)
            if not item.endswith('\n'):
                f.write('\n')
        f.flush()

    
def checkFileName(filename):
    name,kind='',-1
    if os.path.isfile(filename):
        folder,filename=os.path.split(filename)
        n,ext=os.path.splitext(filename)
        name=n
        n=n.split('_')
        if len(n)>=4 and n[3]=='soma':
            kind=1
        elif len(n)>=4 and n[3]=='skeleton':
            kind=0
    return(name,kind)


def getOutputName(output,name):
    rv=output
    if not rv.endswith('.swc'):
        if not os.path.isdir(rv):
            os.makedirs(rv)
        rv=os.path.join(rv,name+'.swc')
    return rv

def parseOneFile(filename,radius,kind):
    if os.path.isfile(filename):
        nml=etree.parse(filename)
    else:
        nml=etree.fromstring(filename)
    result=NmlParser(nml,radius,kind).process()
    return result
    
    
def parseFile(file,output,radius=1.0):
    if file.lower().endswith('.nml'):
        name,kind=checkFileName(file)
        if kind==-1:
            print('invalid input file name {0}'.format(file))
            return
        result=parseOneFile(file,radius,kind)
        of=getOutputName(output,name)
        write2File(result,of)
        print('parse {0} done ,result saved at {1}'.format(file,of))
    elif file.lower().endswith('.nmx'):
        z=ZipFile(file,'r')
        for f in z.namelist():
            s=z.open(f)
            folder,f=os.path.split(f)
            of=getOutputName(output,f)
            if len(f.split('_'))>=4 and f.split('_')[3]=='soma':    
                result=parseOneFile(s.read(),radius,1)
            elif len(f.split('_'))>=4 and f.split('_')[3]=='skeleton':    
                result=parseOneFile(s.read(),radius,0)
            else:
                print('{0} contains valid file name {1}'.format(file,f))
                continue
            write2File(result,of)
            print('parse {0} done ,result saved at {1}'.format(f,of))
        

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filename')
    parser.add_argument('-o',action='store',default=r'./',help='output file name or directory')
    parser.add_argument('--radius',action='store',default=1.0,type=float,help='radius default=1.0')
    args=parser.parse_args()
    parseFile(args.filename,args.o,args.radius) 


