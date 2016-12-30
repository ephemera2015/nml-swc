#!/usr/bin/python
try:
    from lxml import etree
except ImportError:
    print 'lxml library is required'
    raise
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
    
from copy import deepcopy
import sys
import os

class NmlParser(object):
    def __init__(self,filename,radius,kind):
        super(NmlParser,self).__init__()
        self.processed=[]
        self.id=1
        self.filename=filename
        self.kind=kind
        self.radius=radius
        self.mapping={}
        self.result=[]
        self.stack=[]
        self.queue=[]      
        
    def process(self):
        self.nml=etree.parse(self.filename)
        self._getParamsAndComments()
        self._getNodes()
        self._getEdges()
        for node in self.nodes.keys():
            self._process(node)
        return self.result
    
    def _getParamsAndComments(self):        
        for param in self.nml.xpath(r'//parameters'):
            p=StringIO(etree.tostring(param))
            for line in p.readlines():
                self.result.append('#'+line)
        for com in self.nml.xpath(r'//comments'):
            c=StringIO(etree.tostring(com))
            for line in c.readlines():
                self.result.append('#'+line)
        
    def _process(self,node):
        if node  in self.processed:
            return
        parents=self.inedges.get(node,[])
        #if node has no parents than we output it
        if not parents:
            self._outputNode(node)
        #if node has parents we should recursively output its parents first
        else:
            self._instack(node,parents)   
    
    def _outputNode(self,node):
        if node not in self.processed:
            self.mapping[node]=self.id
            parents=self.o_inedges.get(node,[])
            if parents:
                for p in parents:
                    #ensure that node output behind all its parents 
                    assert (p in self.processed)
                    record="{id} {t} {x} {y} {z} {r} {p}".format(id=self.id,
                    x=self.nodes[node][0],y=self.nodes[node][1],z=self.nodes[node][2],
                    p=self.mapping[p],r=self.radius,t=self.kind)
                    self.result.append(record)
                    self.id+=1
            else:
                record="{id} {t} {x} {y} {z} {r} {p}".format(id=self.id,
                x=self.nodes[node][0],y=self.nodes[node][1],z=self.nodes[node][2],
                p=-1,r=self.radius,t=self.kind)
                self.result.append(record)
                self.id+=1 
            self._disconnectKids(node)
            self.processed.append(node)        
            
    def _instack(self,node,parents):
        self.stack.append(node)
        for p in parents:
            self.queue.append(p)
        while self.queue:
            n=self.queue[0]
            parents=self.inedges.get(n,[])
            self.queue.pop(0)
            #probably has a loop
            if n in self.stack:
                self._checkStack(n)
            else:
                if not parents:
                    self._outputNode(n)
                else:
                    self.stack.append(n)
                    for p in parents:
                        self.queue.append(p)
        self.stack.reverse()
        for n in self.stack:
            self._outputNode(n)
        self.stack=[]
        
    def _checkStack(self,node):
        #this is because some nodes have more than one parent
        if node==self.stack[-1]:
            return
        i=-1
        loop=[node]
        prev=node
        while self.stack[i]!=node:
            if prev in self.inedges.get(self.stack[i],[]):
                loop.append(self.stack[i])
                prev=self.stack[i]
            i-=1
        self.outedges[node].remove(loop[1])
        self.inedges[loop[1]].remove(node)
        self.o_inedges[loop[1]].remove(node)
        newnode=node+'\''
        self.nodes[newnode]=deepcopy(self.nodes[node])
        self.outedges[newnode]=[loop[1]]
        self.o_inedges[loop[1]].append(newnode)
        self.inedges[loop[1]].append(newnode)
        self._outputNode(newnode)
        #print self.stack
    
    def _disconnectKids(self,node):
        kids=self.outedges.get(node,[])
        for kid in kids:
            self.inedges[kid].remove(node)
        if self.outedges.has_key(node):
            self.outedges[node]=[]
            
    def _getNodes(self):
        self.nodes={node.get('id'):(node.get('x'),node.get('y'),node.get('z')) for node in self.nml.xpath(r'//node') }
    
    def _getEdges(self):
        self.inedges={}
        self.outedges={}
        self.o_inedges={}
        for edge in self.nml.xpath(r'//edge'):
            s=edge.get('source')
            t=edge.get('target')
            self.inedges.setdefault(t,[]).append(s)
            self.outedges.setdefault(s,[]).append(t)
        self.o_inedges=deepcopy(self.inedges)
    
    
def parseOneFile(filename,radius,kind):    
    try:
        result=NmlParser(filename,radius,kind).process()
    except:
        print 'sorry,fail to parse '+filename
        return[]
    return result
    
def write2File(result,fname):
    with open(fname,'wb') as f:
        for item in result:
            f.write(item)
            if not item.endswith('\n'):
                f.write('\n')
            f.flush()

    
def checkFileName(filename):
    type,name,kind='','',0
    if os.path.isfile(filename):
        folder,filename=os.path.split(filename)
        n,ext=os.path.splitext(filename)
        name=n
        if ext.lower()=='.nml':
            type='nml'
        elif ext.lower()=='.nmx':
            type='nmx'
        n=n.split('_')
        if len(n)>=4 and n[3]=='soma':
                kind=1
    return(type,name,kind)
    
def getOptions(options,output):
    radius=1.0
    if options[0]=='-o':
        flag=True
        output=options[1]
    elif options[0]=='--radius':
        flag=False
        radius=options[1]
    else:
        print 'error: invalid options'
        return 
    if(len(options)==4):
        options=options[2:]
        if flag and options[0]=='--radius':
            radius=options[1]
        elif (not flag) and options[0]=='-o':
            output=options[1]
        else:
            print 'error: invalid options'
            return
    return output,radius
    
def process():
    num=len(sys.argv)
    if num==1 :
         print 'error: nml or nmx file required'
         return 
    else:
        filename=sys.argv[1]
    type,name,kind=checkFileName(filename)
    if not type:
        print 'error: invalid nml/nmx file name'
        return
        
    output=r'./'+name+'.swc'
    radius=1.0
    if(len(sys.argv)>2):
        options=sys.argv[2:]
        if len(options)==2 or len(options)==4:
            output,radius=getOptions(options,output)
        else:
            print 'error: invalid options'
            return
    if not output.endswith('.swc'):
        if not os.path.isdir(output):
            os.makedirs(output)
        output=os.path.join(output,name+'.swc')
    if type=='nml':
        result=parseOneFile(filename,radius,kind)
        write2File(result,output)
        print 'result saved at '+output
    elif type=='nmx':
        pass
    
if __name__=='__main__':
    process()    


