"""Heatwave's blue fire: recolour the Chapter 5 FireShock sprites (hue shift of the fire colours only) and pack them into one atlas + json.
Input : <src>/<sprite>_<frame>.png exported from the Chapter 5 data file (export_ui.csx).   Output: <out>/blue_atlas.png, <out>/blue_atlas.json
The build (build.csx) imports the atlas as new sprites that copy the donor sprite's size/origin/masks."""
import sys,json,colorsys,os,glob
from PIL import Image
src=sys.argv[1]; out=sys.argv[2]
SPR={'spr_bluefire_flame':'spr_firespell_flame','spr_bluefire_smallflame':'spr_firespell_smallflame','spr_bluefire_ball':'spr_spell_fireball','spr_ralsei_spell_bluefireball_right':'spr_ralsei_spell_fireball_right'}
def recolor(im):
    im=im.convert('RGBA'); px=im.load(); w,h=im.size
    for y in range(h):
        for x in range(w):
            r,g,b,a=px[x,y]
            if a==0: continue
            hh,ss,vv=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            deg=hh*360
            if ss>0.35 and (deg<=70 or deg>=350):
                if deg>=350: deg=0
                nd=(220-(deg/70.0)*35)/360.0       # orange -> deep blue, yellow -> light cyan
                r2,g2,b2=colorsys.hsv_to_rgb(nd,ss,vv)
                px[x,y]=(int(r2*255+.5),int(g2*255+.5),int(b2*255+.5),a)
    return im
frames=[]   # (newname, index, image)
for new,old in SPR.items():
    fs=sorted(glob.glob(os.path.join(src,old+'_*.png')),key=lambda p:int(p.rsplit('_',1)[1][:-4]))
    assert fs,old
    for i,f in enumerate(fs): frames.append((new,old,i,recolor(Image.open(f))))
W=max(f[3].size[0] for f in frames)+2; H=sum(f[3].size[1]+2 for f in frames)+2
atlas=Image.new('RGBA',(W,H),(0,0,0,0)); y=1; meta={}
for new,old,i,im in frames:
    atlas.paste(im,(1,y)); meta.setdefault(new,{'donor':old,'frames':[]})['frames'].append({'x':1,'y':y,'w':im.size[0],'h':im.size[1]}); y+=im.size[1]+2
os.makedirs(out,exist_ok=True)
atlas.save(os.path.join(out,'blue_atlas.png'))
json.dump({'width':W,'height':H,'sprites':meta},open(os.path.join(out,'blue_atlas.json'),'w'),indent=1)
print('atlas',W,H,{k:len(v['frames']) for k,v in meta.items()})
