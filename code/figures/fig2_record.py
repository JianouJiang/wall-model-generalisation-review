#!/usr/bin/env python3
"""Show why a scope decision cannot establish absence of validation."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from style import *

def main():
    evidence=json.load(open(os.path.join(DATA,'revision/agrawal_validation.json')))
    fig=plt.figure(figsize=(W*MM,74*MM))
    ax=fig.add_axes([.02,.06,.96,.84])
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    xs=[.00,.43,.76]
    ax.text(xs[1],.98,'Speed bump',ha='center',va='top',fontsize=FS,fontweight='bold')
    ax.text(xs[2],.98,'Transonic bump',ha='center',va='top',fontsize=FS,fontweight='bold')
    rows=[
        ('Coupled LES reported','Yes','Yes'),
        ('Compared quantities','Pressure, friction, velocity,\nReynolds shear stress','Pressure, velocity,\nseparation'),
        ('Low-Mach review scope','Case regime remains\nunresolved here','Outside scope'),
        ('Transfer beyond calibration','Calibration needs a\nseparate assessment','Calibration needs a\nseparate assessment'),
    ]
    for y,(q,a,b) in zip([.79,.57,.34,.12],rows):
        ax.text(xs[0],y,q,ha='left',va='center',fontsize=FS)
        for x,s in [(xs[1],a),(xs[2],b)]:
            ax.text(x,y,s,ha='center',va='center',fontsize=FS,color=BLUE if s=='Yes' else INK,linespacing=1.4)
    for y in [.88,.68,.44,.23]:ax.plot([0,.98],[y,y],color=G2,lw=.5)
    fig.text(.02,.96,'Agrawal et al. (2024): the published validation record',fontsize=FS,fontweight='bold')
    json.dump(evidence,open(os.path.join(RES,'fig2_values.json'),'w'),indent=2)
    save(fig,'fig2_record')
if __name__=='__main__':main()
