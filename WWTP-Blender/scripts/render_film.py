"""Portable render/QA/encode entry point. Requires Python 3.10+, Pillow and Blender 5.2."""
import argparse,json,os,subprocess,sys,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'data/film.json').read_text(encoding='utf8'))
def arguments():
    p=argparse.ArgumentParser()
    p.add_argument('--blender',default=os.environ.get('BLENDER','blender'))
    p.add_argument('--device',choices=['CPU','OPTIX','CUDA','HIP','METAL','ONEAPI'],default='CPU')
    p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=D['frames'])
    p.add_argument('--shot',choices=[s['id'] for s in D['shots']])
    p.add_argument('--qa',action='store_true');p.add_argument('--samples',type=int)
    p.add_argument('--scale',type=int,default=100);p.add_argument('--output',type=Path)
    p.add_argument('--encode',action='store_true');p.add_argument('--ffmpeg',default='ffmpeg')
    p.add_argument('--worker',action='store_true')
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    if not 1<=a.start<=a.end<=D['frames']:p.error('Invalid frame interval')
    if not 1<=a.scale<=100:p.error('Scale must be 1..100')
    if a.samples is not None and a.samples<1:p.error('Samples must be positive')
    a.output=(a.output or R/('renders/film-qa' if a.qa else 'renders/film')).resolve()
    return a

def selected(a):
    shots=[s for s in D['shots'] if not a.shot or s['id']==a.shot]
    if a.qa:return sorted({round(s['start']+(s['end']-s['start'])*.2) for s in shots}|{round((s['dry_start']+s['dry_end'])/2) for s in shots})
    return [f for s in shots for f in range(max(a.start,s['start']),min(a.end,s['end'])+1)]

def worker(a):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(R/'blender/plant_film.blend'))
    s=bpy.context.scene
    if a.device!='CPU':
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type=a.device;prefs.refresh_devices()
        devices=[d for d in prefs.devices if d.type==a.device]
        if not devices:raise RuntimeError('Requested GPU unavailable: '+a.device)
        for d in prefs.devices:d.use=d in devices
        s.cycles.device='GPU'
    else:s.cycles.device='CPU'
    s.cycles.samples=a.samples or (12 if a.qa else D['samples'])
    s.render.resolution_percentage= a.scale if not a.qa else 17
    # Set camera explicitly per shot even when rendering a disjoint frame subset.
    for f in selected(a):
        path=a.output/'raw'/f'{f:06}.png'
        if path.exists():continue
        sh=next(x for x in D['shots'] if x['start']<=f<=x['end'])
        s.frame_set(f);s.camera=bpy.data.objects['FILM_CAM_'+sh['id']]
        s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    # Audit after reopening, including paths and moving mechanisms in later shots.
    missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()]
    motion={}
    moving=[o for o in bpy.data.objects if o.name.startswith(('FILM_ROTOR_','ROTOR_','RAKE_','BLADE_'))]
    for f in (3000,3007):
        s.frame_set(f);bpy.context.view_layer.update()
        for o in moving:motion.setdefault(o.name,[]).append(list(o.location)+list(o.rotation_euler))
    stuck=[n for n,v in motion.items() if v[0]==v[1]]
    invalid_drivers=[f'{o.name}:{fc.data_path}' for o in bpy.data.objects if o.animation_data for fc in o.animation_data.drivers if not fc.driver.is_valid]
    reveals=[]
    for sh in D['shots']:
        if not sh['water']:continue
        s.frame_set(round((sh['dry_start']+sh['dry_end'])/2));bpy.context.view_layer.update()
        for o in s.objects:
            if any(o.name.startswith(prefix) for prefix in sh['water']) and o.type=='MESH' and not o.hide_render:
                factors=[n.inputs[0].default_value for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='MIX_SHADER' and any(link.from_node.type=='BSDF_TRANSPARENT' for link in n.inputs[2].links)]
                reveals.append({'shot':sh['id'],'object':o.name,'fully_hidden':bool(factors) and all(v>.999 for v in factors)})
    audit={'invalid_drivers':invalid_drivers,'water_reveals':reveals,'missing_images':missing,'motion_objects':len(motion),'stationary_motion_objects':stuck,'frames':D['frames'],'fps':s.render.fps,'device':a.device,'samples':s.cycles.samples,'rendered_frames':selected(a)}
    (a.output/'validation.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    assert not missing and not stuck and not invalid_drivers and all(x['fully_hidden'] for x in reveals),audit

def main():
    a=arguments();a.output.mkdir(parents=True,exist_ok=True);(a.output/'raw').mkdir(exist_ok=True)
    if a.worker:return worker(a)
    from PIL import Image,ImageDraw
    settings={'qa':a.qa,'scale':a.scale,'samples':a.samples or (12 if a.qa else D['samples']),'blend_sha256':hashlib.sha256((R/'blender/plant_film.blend').read_bytes()).hexdigest(),'config_sha256':hashlib.sha256((R/'data/film.json').read_bytes()).hexdigest()}
    settings_file=a.output/'settings.json'
    if settings_file.exists() and json.loads(settings_file.read_text())!=settings:raise RuntimeError('Output contains a different render configuration. Choose another --output directory.')
    settings_file.write_text(json.dumps(settings,indent=2))
    if not a.encode:
        # Verify files before resuming; never accept a truncated image as a completed frame.
        for f in selected(a):
            path=a.output/'raw'/f'{f:06}.png'
            if path.exists():
                try:
                    with Image.open(path) as im:im.verify()
                except Exception:path.rename(path.with_name(f'{path.stem}.corrupt-{time.time_ns()}.png'))
        cmd=[a.blender,'-b','--factory-startup','--python-exit-code','1','--python',str(Path(__file__).resolve()),'--']+sys.argv[1:]+['--worker']
        subprocess.run(cmd,check=True)
        frames=a.output/'frames';frames.mkdir(exist_ok=True)
        for f in selected(a):
            sh=next(s for s in D['shots'] if s['start']<=f<=s['end'])
            mode='dry' if sh['dry_start']<=f<=sh['dry_end'] else 'wet'
            with Image.open(a.output/'raw'/f'{f:06}.png') as source:
                im=source.convert('RGBA');ratio=im.width/3840
                with Image.open(R/'assets/video_captions'/f'{sh["id"]}_{mode}.png') as cap:
                    cap=cap.resize((round(cap.width*ratio),round(cap.height*ratio)),Image.Resampling.LANCZOS)
                    im.alpha_composite(cap,(round(90*ratio),im.height-cap.height-round(70*ratio)))
                temp=frames/f'{f:06}.tmp.png';im.convert('RGB').save(temp);temp.replace(frames/f'{f:06}.png')
        if a.qa:
            files=[frames/f'{f:06}.png' for f in selected(a)]
            sheet=Image.new('RGB',(960,290*((len(files)+1)//2)),(20,24,27));draw=ImageDraw.Draw(sheet)
            for i,path in enumerate(files):
                with Image.open(path) as im:sheet.paste(im.resize((480,270)),((i%2)*480,(i//2)*290))
                draw.text(((i%2)*480+8,(i//2)*290+271),path.stem,fill='white')
            sheet.save(a.output/'contact.jpg')
    else:
        absent=[f for f in range(1,D['frames']+1) if not (a.output/'frames'/f'{f:06}.png').exists()]
        if absent:raise RuntimeError(f'Cannot encode: {len(absent)} frames missing, first {absent[:5]}')
        for f in range(1,D['frames']+1):
            with Image.open(a.output/'frames'/f'{f:06}.png') as im:im.verify()
        subprocess.run([a.ffmpeg,'-n','-framerate','24','-start_number','1','-i',str(a.output/'frames/%06d.png'),'-frames:v','6480','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output/'wwtp-process-4m30s.mp4')],check=True)
if __name__=='__main__':main()
