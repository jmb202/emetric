#!/usr/bin/env python
# -------------------------------------------------------------------
#  @author Justin Kirby <jkirby@voalte.com>
#  @copyright (C) 2011 Justin Kirby
#  @end
# 
#  This source file is subject to the New BSD License. You should have received
#  a copy of the New BSD license with this software. If not, it can be
#  retrieved from: http://www.opensource.org/licenses/bsd-license.php
# -------------------------------------------------------------------


import os
import sys
import getopt
import itertools


class DepFail(Exception):
    def __init__(self,pkg):
        self.pkg = pkg
        (distro,a,b,c,d) = os.uname()
        self.os = distro
        self.msgs={
            "Linux":{
                "gtk":"Use your linux pkg manager to install pygtk",
                "numpy":"Use your linux pkg manager to install numpy",
                "matplotlib":"Use your linux pkg manager to install matplotlib",
                },
            "Darwin":{
                "gtk":"""
Do not bother trying to install pygtk. This is just too
painful. Instead use the headless option for this program and use a
tool that can importdata from csv files.
""",
                "numpy":"Use ports to install numpy. sudo port install py26-numpy",
                "matplotlib":"Use ports to install matplotlib, or the dmg from 1.0 on sf.net"
                }
            }

    def message(self):
        if self.os in self.msgs:
            if self.pkg in self.msgs[self.os]:
                return self.msgs[self.os][self.pkg]
            else:
                return "Sorry I don't know what to tell you about %s\nThis is a bug"%self.pkg
        else:
            return "Sorry I don't know anything about this OS, %s\nThis is probably not a bug"%self.os

def validate_sys(opts):
    """
    Make sure the required deps exist. Be friendly by not doing anything    
    """
    reqs=["numpy","matplotlib"]
    if opts["graph"]:
        reqs.extend(["gtk","pygtk","matplotlib.pyplot"])

    for r in reqs:
        try:
            __import__(r)
        except ImportError,e:
            raise DepFail(r)
    return True
        


class Usage(Exception):
    def __init__(self,msg):
        self.msg = msg
def usage():
    return """
plotr.py [options]

This will display a list of 'interesting' fields in which you can compare in line graphs.  It works best when you only compare two metrics. If you try for more, then good luck.

-h|--help:
    print this help message

-g|--graph:
    Enables graphing using pltr, e.g. the gui. This require pygtk to be installed.

-o file|--out=file:
    File to write cleaned csv data to.  This is required if --graph is not specified 

-d file|--data=file :
    Specify the file to parse. This must be a csv file. Preferably one generated by emetric, though it shouldn't really matter. If no file specified, then a file chooser window will appear. You need a file, if you don't provide one, this tool just exits.

-b|--boring :
   Include boring stuff.

Definition of Interesting: if the standard deviation of a column is > 0. (There is some change in the value.)

I am trying to find a way to make this tool useful for comparing more than two metrics.


Examples:

Without graphing support
$python plotr.py --data=emetric_ejabberd\@localhost_123456789.csv --out=clean_emetric.csv

With graphing support
$python plotr.py --graph --data=emetric_ejabberd\@localhost_123456789.csv 
"""

def gtk_ui(interest,dat):
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import EngFormatter


    import pygtk
    pygtk.require('2.0')
    import gtk

    class SelectWin:
        def __init__(self, interesting, data):
            self.interesting = interesting
            self.data = data
            self.have_graphs=False
            self.pretty_cnt = 0
            self.keys_plot = []
            self.pivot_per = False
            self.tick_key = ""
            self.colors = ['b','g','r','c','m','y','k']
            self.shapes = ['.',',','o','v','^','<','>','1','2','3','4','s','p',
                           '*','h','H','+','x','D','d','|','_']
                       

            #figure out which tick name to use, should make tick name
            #more findable, e.g. tick
            for tn in ['sys_tick','ejd_tick','mnesia_tick']:
                if tn in interesting:
                    self.tick_key=tn
                    break
                
                
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window.set_title("The Ugly Voalte Prettiness Maker")
            self.window.connect("delete_event",self.delete_event)
            
            
            vcomp = gtk.VBox(False,2)
            self.window.add(vcomp)
            
            
            
            bplot = gtk.Button("Plot")
            bplot.connect("clicked",self.plot)
            vcomp.pack_start(bplot,False,True,2)
            
            bper = gtk.CheckButton("Pivot Per")
            bper.connect("toggled",self.toggle_per)
            vcomp.pack_start(bper,False,True,2)
            
            
            cpivot = gtk.combo_box_new_text()
            cpivot.connect("changed",self.change_pivot)
            vcomp.pack_start(cpivot,False,True,2)

            sz = len(self.interesting)
            row_cnt = 20
            cols_cnt = sz/row_cnt
            
            table = gtk.Table(row_cnt,cols_cnt,False)
            vcomp.pack_start(table,False,True,2)
            
            self.interesting.sort()
            col = 0
            for r,i in itertools.izip(itertools.cycle(range(0,20)),self.interesting):
                label = i.replace("_"," ")
                bcomp = gtk.CheckButton(label)
                bcomp.connect("toggled", self.toggle_interest, i)

                table.attach(bcomp, col,col+1, r,r+1)

                if r == 19:
                    col += 1
                    

                
                

                
                cpivot.append_text(i)
                    
                    
                    
            self.window.show_all()

        def delete_event(self, widget, event, data=None):
            gtk.main_quit()
            return False
        
        def toggle_interest(self, widget, data=None):
            if not widget.get_active():
            #remove data from list if exists
                try:
                    del self.keys_plot[self.keys_plot.index(data)]
                except ValueError,err:
                    pass
            else:
                self.keys_plot.append(data)
                
        def toggle_per(self,widget):
            self.pivot_per = widget.get_active()
            
        def change_pivot(self,widget):
            model = widget.get_model()
            index = widget.get_active()
            if index >= 0:
                self.pivot = model[index][0]
            else:
                self.pivot = None
                
                
        def plot(self,widget,data=None):
            for d in self.data:
                self.create_plot(d)
            
            
            
        def create_plot(self,data):
            self.pretty_cnt = self.pretty_cnt+1
            
            
            # simple combinitorial product of shapes and colors so we can
            # iterate over them. matlib likes things such as 'r.' and
            # 'g-', etc.. 
            line_style = itertools.product(self.shapes,self.colors)
            def next_style():
                s = list(next(line_style))
                s.reverse()
                return s
            
            #hacky toggle, cause if we clear the plot state, we end up
            #with am extra window
            # if self.have_graphs:
            #     plt.clf()
            # else:
            #     self.have_graphs = True
                
            kp = self.keys_plot# just to make it easier to reference
            
            fig = plt.figure()
            plt.subplots_adjust(hspace=0.01)
            
            
            x_set= data[self.tick_key]
            pivot_set = data[self.pivot]
            color_pivot,shape_pivot = next_style()
            
            labels_to_hide=[]
            
            for k,i in zip(kp, range(0,len(kp))):
                
                sp = fig.add_subplot(len(kp),1,i+1)
                sp.set_xlabel("ticks (s)")
                sp.grid(True)
                
                plt.plot(x_set,pivot_set, color_pivot+shape_pivot)
                sp.set_ylabel(self.pivot,color=color_pivot)
                for tl in sp.get_yticklabels():
                    tl.set_color(color_pivot)
                    
                if not self.pivot_per:
                    y_set = data[k]
                else:
                    y_set = data[k]/data[self.pivot]
                color_y,shape_y = next_style()
                ax2 = sp.twinx()
                ax2.plot(x_set,y_set,color_y+shape_y)
                ax2.set_ylabel(k,color=color_y)
                for tl in ax2.get_yticklabels():
                    tl.set_color(color_y)
                    
            #hid all but the last ones
                if i < len(kp):
                    labels_to_hide.append(sp.get_xticklabels())
                    
                    plt.setp(labels_to_hide,visible=False)
                    
                    
            plt.show()
    #end of class  <-- this is bad, I know
    
    selwin = SelectWin(interest,dat)
    gtk.main()
            
            
        

def interesting_out(opts,interesting,data):
    """
    Take a list of fields, and the recs
    output recs as csv to opts["out"], e.g. --out
    """
    header = True
    from matplotlib import mlab
    for d in data:
        cleaned = mlab.rec_keep_fields(d,interesting)
        mlab.rec2csv(cleaned,opts["out"],withheader=header)
        header=False
        



def extract_interesting(options):
    """
    grab any fields that have a std deviation > 0,
    e.g. they changed
    """
    from matplotlib import mlab
    def extract(data):
        data_recs  = mlab.csv2rec(data)
        rv=[]

        for k,v in data_recs.dtype.fields.iteritems():
            try:#note that datetime will raise
                s = data_recs[k].std()
                if s > 0 or options["boring"]:
                    rv.append(k)
            except TypeError,e:
                pass  #non number type, e.g. date
        return (rv,data_recs)

    interesting=[]
    recs=[]
    
    for d in options["data"]:
        (interest, rec) = extract(d)
        interesting.extend(interest)
        #need to make these unique. files could have different 'interesting-ness'
        interesting = [k for k,v in itertools.groupby(sorted(interesting))]
        recs.append(rec)

    return (interesting,recs)
        
        
            


def ask_for_file(options):
    """
    If no gtk, then we just error
    If gtk, then we pop up a pretty dialog file chooser

    We are only here if --data wasn't specified
    """
    if not options["graph"]:
        print >>sys.stderr,"No file specified, see --help"
        return (1,"")
    else:
        import pygtk
        pygtk.require('2.0')
        import gtk
    
        fs = gtk.FileChooserDialog("Open..",None,
                                   gtk.FILE_CHOOSER_ACTION_OPEN,
                                   (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        fs.set_default_response(gtk.RESPONSE_OK)
        fs.set_select_multiple(True)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*.*")
        fs.add_filter(filter)
        
        filter = gtk.FileFilter()
        filter.set_name("CSV")
        filter.add_pattern("*.csv")
        fs.add_filter(filter)
        
        response = fs.run()
        if response == gtk.RESPONSE_OK:
            rv = (0,fs.get_filenames())
        else:
            rv = (1,"")
        fs.destroy()
        return rv




def get_options(argv):
    if argv is None:
        argv = sys.argv
    
    try:
        try:
            opts,args = getopt.getopt(argv[1:], "hd:bgo:",
                                      ["help","data=","boring","graph","out="])
        except getopt.error,msg:
            raise Usage(msg)
    except Usage,err:
        print >>sys.stderr,err.msg
        print >>sys.stderr," for help use --help"
        return (1,{})

    config = {"boring":False,
              "graph":False}
    for o,a in opts:
        if o in ("-h","--help"):
            print usage()
            return (2,{})
        if o in ("-d","--data"):
            config["data"] = a.split(',')
        if o in ("-b","--boring"):
            config["boring"] = True
        if o in ("-g","--graph"):
            config["graph"] = True
        if o in("-o","--out"):
            config["out"] = a
            
            
    return (0,config)
        
    
def main(argv=None):
    rv,options = get_options(argv)
    if rv: return rv #we die if there was a problem

    try:
        validate_sys(options)
    except DepFail,e:
        print >>sys.stderr,e.message()
        return 255
    

    if "data" not in options:
        rv,options["data"] = ask_for_file(options)
        if rv: return rv

    (interesting,data) = extract_interesting(options)

    if options["graph"]:
        gtk_ui(interesting,data)
    else:
        if "out" not in options:
            print >>sys.stderr,"You need to specify --out file if not running with graph, see --help"
            return 1
        interesting_out(options,interesting,data)

    return 0

if __name__ == "__main__":
    sys.exit(main())

    
