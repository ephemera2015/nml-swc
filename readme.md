#nml2swc
##description
this project helps convert nml or mnx format files to swc format files
##installation
###requirements
    lib lxml is required
    to install lxml at your python environment see  http://lxml.de/
###install
    git clone git@github.com:ephemera2015/nml-swc.git
    then you will get source file nml2swc.py
##usage
    there are two ways to use this module
    
    [1]python nml2swc.py somefile.nml(or somefile.nmx) [-o output] [--radius radius]
    
    note that if output ends with .swc than we assume you are specifying a output filename
    otherwise wo assume you are specifying a output directory and the output filename will be 
    output+somefile +'.swc'
    
    if input is somefile.nmx and there are more than one nml files in nmx,you'd better specify
    output a directory,or results will overridden
    radius default is 1.0 if don't specify a value
    
    
    [2]use nml2swc in your project:
    
    from  nml2swc import parseFile
    parseFile(somefile.nml(or somefile.nmx),output file name or directory,radius)
