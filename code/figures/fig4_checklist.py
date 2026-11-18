#!/usr/bin/env python3
"""Describe the retrospective exercise without claiming predictive validation."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from style import *

def main():
    cases=json.load(open(os.path.join(DATA,'checklist_cases.json')))['cases']
    assert len(cases)==13
    labels=[('same_cause','Same cause'),('same_observable_class','Same quantity class'),('same_factor','Same factor to vary')]
    counts=[sum(bool(c['agreement'][key]) for c in cases) for key,_ in labels]
    both=sum(all(c['agreement'][key] for key,_ in labels) for c in cases)
    labels.append(('all','All three agree'));counts.append(both)
    fig=plt.figure(figsize=(W*MM,58*MM))
    ax=fig.add_axes([.27,.20,.35,.65])
    for i,((key,label),n) in enumerate(zip(labels,counts)):
        y=3-i
        ax.plot([0,n],[y,y],color=BLUE,lw=3,solid_capstyle='butt')
        ax.plot(n,y,'o',color=BLUE,ms=4)
        ax.text(-.4,y,label,ha='right',va='center',fontsize=FS)
        ax.text(n+.4,y,str(n),va='center',fontsize=FS)
    ax.set(xlim=(0,14),ylim=(-.6,3.6),xticks=[0,5,10,13],yticks=[],xlabel='cases')
    for side in ('top','left','right'):ax.spines[side].set_visible(False)
    fig.text(.02,.94,'Agreement between two retrospective applications of the checklist',fontsize=FS,fontweight='bold')
    fig.text(.70,.70,'13 cases',fontsize=FS,fontweight='bold')
    fig.text(.70,.53,'Assurance withheld\nin every case.',fontsize=FS,linespacing=1.6)
    fig.text(.70,.27,'A description of use;\npredictive value\nremains unestablished.',fontsize=FS,linespacing=1.6)
    json.dump(dict(cases=13,agreement=dict((label,n) for (_,label),n in zip(labels,counts))),
              open(os.path.join(RES,'fig4_values.json'),'w'),indent=2)
    save(fig,'fig4_checklist')

if __name__=='__main__':main()
