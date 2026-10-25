"""Vector PDF of the saved graph plus a readable resource/connection inventory."""
from io import BytesIO
from math import atan2, cos, sin
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth

INK=HexColor('#243c39'); GREEN=HexColor('#2f6557'); MUTED=HexColor('#52665d'); SAGE=HexColor('#edf4ee')
from diagram_catalog import LABELS

def lines(value,width,size):
    # Character wrapping also handles long DNS names without spaces.
    result=['']
    for char in str(value):
        if char=='\n' or stringWidth(result[-1]+char,'Helvetica',size)>width:
            result.append('' if char=='\n' else char)
        else: result[-1]+=char
    return result

def render_pdf(row):
    doc=row['document']; nodes=doc['nodes']; edges=doc['edges']; by_id={n['id']:n for n in nodes}
    buffer=BytesIO(); width,height=landscape(A3)
    c=Canvas(buffer,pagesize=(width,height)); c.setTitle(row['name']); c.setAuthor('Koodaria')
    page=0
    def header(title):
        nonlocal page
        page+=1
        c.setFillColor(INK);c.setFont('Helvetica-Bold',24);c.drawString(36,height-44,'koodaria.');c.setFont('Helvetica',15)
        for i,line in enumerate(lines(title,width-300,15)[:2]): c.drawString(220,height-36-i*19,line)
        c.setFont('Helvetica',9);c.setFillColor(MUTED);c.drawString(36,22,f'Diagramas · Versión {row["revision"]}');c.drawRightString(width-36,22,str(page))
    def xy(n):
        parent=by_id.get(n.get('parentId'))
        return (n['position']['x']+(parent['position']['x'] if parent else 0), n['position']['y']+(parent['position']['y'] if parent else 0))
    sizes={n['id']:(n.get('style',{}).get('width',380),n.get('style',{}).get('height',260)) if n['type']=='resourceGroup' else (190,max(95,40+len(lines(n['data']['label'],160,13))*16+len(lines(n['data'].get('address','')+' '+n['data'].get('port',''),160,10))*12)) for n in nodes}
    # Match the derived hosting layout used by the editor, including old maps.
    children={}
    for edge in edges:
        if edge.get('relation')=='hosts':children.setdefault(edge['source'],[]).append(edge['target'])
    nested_positions={};ordered=[]
    def footprint(n):
        data=n['data'];fields=data.get('server_instance' if data['kind'] in ['servidor','virtual'] else 'component_instance',{}).get('identification',{})
        values=[fields.get('hostname') or fields.get('name'),fields.get('environment'),fields.get('criticality'),fields.get('technology') or data.get('technology'),fields.get('location') or data.get('location'),data.get('address')]
        count=len(list(dict.fromkeys(v for v in values if v and v!=data['label']))[:3])
        if not count and data['label']!=LABELS[data['kind']]:count=1
        return 62+14*count
    def size_host(key):
        if key not in children:return sizes[key]
        child_sizes=[size_host(k) for k in children[key]]
        sizes[key]=(max(320,*[w for w,h in child_sizes])+20,footprint(by_id[key])+8+sum(h+8 for w,h in child_sizes))
        return sizes[key]
    # Every hosted real component uses the compact node footprint.
    if children:
        for n in nodes:
            if n['type']=='resource':sizes[n['id']]=(320,footprint(n))
        targets={k for values in children.values() for k in values}
        def place_host(key,x,y):
            nested_positions[key]=(x,y);ordered.append(by_id[key]);cy=y+footprint(by_id[key])+8
            for child in children.get(key,[]):
                place_host(child,x+10,cy);cy+=sizes[child][1]+8
        for n in nodes:
            if n['id'] not in targets:
                size_host(n['id']);place_host(n['id'],*xy(n))
        nodes=ordered
        old_xy=xy
        def xy(n):return nested_positions.get(n['id'],old_xy(n))
    header(row['name'])
    if nodes:
        left=min(xy(n)[0] for n in nodes)-20; top=min(xy(n)[1] for n in nodes)-20
        right=max(xy(n)[0]+sizes[n['id']][0] for n in nodes)+20; bottom=max(xy(n)[1]+sizes[n['id']][1] for n in nodes)+20
        scale=min((width-72)/(right-left),(height-140)/(bottom-top),1.3)
        ox=36+(width-72-(right-left)*scale)/2; oy=height-100-(height-140-(bottom-top)*scale)/2
        c.saveState();c.translate(ox,oy);c.scale(scale,scale)
        def rect(n):
            x,y=xy(n);w,h=sizes[n['id']];return x-left,-(y-top)-h,w,h
        for n in nodes:
            if n['type']!='resourceGroup':continue
            x,y,w,h=rect(n);c.setFillColor(SAGE);c.setStrokeColor(HexColor('#88ab96'));c.roundRect(x,y,w,h,16,fill=1,stroke=1);c.setFillColor(INK);c.setFont('Helvetica',13)
            for i,line in enumerate(lines(n['data']['label'],w-28,13)[:2]):c.drawString(x+14,y+h-22-i*15,line)
        for e in edges:
            if e.get('relation')=='hosts':continue
            a,b=by_id[e['source']],by_id[e['target']];ax,ay,aw,ah=rect(a);bx,by,bw,bh=rect(b)
            x1,y1=ax+aw,ay+ah/2;x2,y2=bx,by+bh/2;mx=(x1+x2)/2
            c.setStrokeColor(GREEN);c.setLineWidth(1.5);p=c.beginPath();p.moveTo(x1,y1);p.lineTo(mx,y1);p.lineTo(mx,y2);p.lineTo(x2,y2);c.drawPath(p)
            angle=atan2(y2-y1,x2-x1) if abs(x2-mx)<1 else (0 if x2>mx else 3.14159)
            p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-8*cos(angle-.5),y2-8*sin(angle-.5));p.lineTo(x2-8*cos(angle+.5),y2-8*sin(angle+.5));p.close();c.setFillColor(GREEN);c.drawPath(p,fill=1)
            if e.get('label'):
                label=e['label'];tw=min(stringWidth(label,'Helvetica',10),240);c.setFillColor(HexColor('#ffffff'));c.rect(mx-tw/2-4,(y1+y2)/2+2,tw+8,16,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Helvetica',10);c.drawCentredString(mx,(y1+y2)/2+7,lines(label,240,10)[0])
        for n in nodes:
            if n['type']=='resourceGroup':continue
            x,y,w,h=rect(n);c.setFillColor(HexColor('#ffffff'));c.setStrokeColor(HexColor('#7e9e8c'));c.roundRect(x,y,w,h,12,fill=1,stroke=1);c.setFillColor(MUTED);c.setFont('Helvetica',10);c.drawString(x+14,y+h-18,LABELS[n['data']['kind']]);cy=y+h-38
            for line in lines(n['data']['label'],w-28,13):c.setFont('Helvetica',13);c.setFillColor(INK);c.drawString(x+14,cy,line);cy-=16
            for line in lines((n['data'].get('address','')+' '+n['data'].get('port','')).strip(),w-28,10):c.setFont('Helvetica',10);c.setFillColor(MUTED);c.drawString(x+14,cy-3,line);cy-=12
        c.restoreState()
    else:
        c.setFillColor(MUTED);c.setFont('Helvetica',15);c.drawString(36,height/2,'Este diagrama todavía no tiene recursos.')
    c.showPage()
    # Full text is retained in detail pages, including labels shortened on overview.
    for title,items in [('Recursos',[f'{LABELS[n["data"]["kind"]]} · {n["data"]["label"]}\n'+ ' · '.join(v for v in [n['data'].get('address'),n['data'].get('port'),('Grupo: '+by_id[n['parentId']]['data']['label']) if n.get('parentId') else None] if v) for n in nodes]),('Conexiones',[f'{by_id[e["source"]]["data"]["label"]}  ->  {by_id[e["target"]]["data"]["label"]}\n{e.get("label", "")}' for e in edges])]:
        if not items:continue
        header(title);y=height-110
        for item in items:
            wrapped=lines(item,width-100,12);needed=len(wrapped)*17+22
            if y-needed<50:c.showPage();header(title+' (continuación)');y=height-110
            c.setFillColor(INK);c.setFont('Helvetica',12)
            for line in wrapped:c.drawString(42,y,line);y-=17
            y-=12;c.setStrokeColor(HexColor('#d9e4dc'));c.line(36,y,width-36,y);y-=20
        c.showPage()
    c.save();buffer.seek(0);return buffer
