#!/usr/bin/env python3
"""A source-checked example of relative improvement and residual error."""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from style import *

def main():
    d=json.load(open(os.path.join(DATA,'revision/dupuy_table5.json')))
    fig=plt.figure(figsize=(W*MM,73*MM))
    ax=fig.add_axes([.13,.22,.49,.66])
    x=d['message_passing_steps']
    y1=np.asarray(d['magnitude'])/d['baseline_magnitude']
    y2=np.asarray(d['streamwise_component'])/d['baseline_streamwise_component']
    ax.axhline(1,color=G1,lw=.8,ls='--')
    ax.plot(x,y1,'o-',color=BLUE,ms=4,lw=1,label='Stress magnitude')
    ax.plot(x,y2,'s-',color=RED,ms=4,lw=1,label='Streamwise component')
    ax.set(xlim=(.7,5.3),ylim=(0,1.07),xticks=x,yticks=[0,.25,.5,.75,1],
           xlabel='message-passing steps',ylabel='squared-error integral / baseline')
    for side in ('right','top'):ax.spines[side].set_visible(False)
    ax.legend(loc='upper left',bbox_to_anchor=(1.03,1.02),frameon=False,fontsize=FS,
              handlelength=1.1,borderaxespad=0)
    fig.text(.68,.60,'At four steps',fontsize=FS,fontweight='bold')
    fig.text(.68,.47,'Both errors are lower\nthan the baseline.',fontsize=FS,linespacing=1.6)
    fig.text(.68,.28,'Reattachment remains\nunderestimated.',fontsize=FS,linespacing=1.6)
    fig.text(.02,.96,'Relative improvement can coexist with remaining reference error',fontsize=FS,fontweight='bold')
    assert y1[3]<1 and y2[3]<1
    json.dump(dict(source=d['doi'],table=5,x=x,magnitude_ratio=y1.tolist(),streamwise_ratio=y2.tolist()),
              open(os.path.join(RES,'fig3_values.json'),'w'),indent=2)
    save(fig,'fig3_contrast')

if __name__=='__main__':main()
