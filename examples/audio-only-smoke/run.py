#!/usr/bin/env python3
"""Synthetic two-second audio-only Hyperframes smoke test; no ASR/network API calls."""
import argparse, hashlib, json, math, subprocess, sys, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_audio import prepare

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--render',action='store_true');p.add_argument('--trim-breaths',choices=['yes','no'],default='no');args=p.parse_args()
    out=args.output_dir.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):p.error('Use a new empty directory; previous output is preserved')
    out.mkdir(parents=True,exist_ok=True);audio=out/'synthetic.wav'
    with wave.open(str(audio),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000)
        w.writeframes(b''.join(int(2000*math.sin(i*2*math.pi*220/48000) if i<24000 or i>=72000 else 0).to_bytes(2,'little',signed=True) for i in range(96000)))
    # Authored fixture, not a real ASR result; no model is called.
    transcript={'duration_seconds':2,'segments':[{'start':0,'end':.5,'text':'Synthetic audio','words':[{'start':0,'end':.5,'text':'Synthetic audio'}]},{'start':1.5,'end':2,'text':'Audio-first composition','words':[{'start':1.5,'end':2,'text':'Audio-first composition'}]}]}
    review=None
    if args.trim_breaths=='yes':
        review={'audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'gaps':[{'start':.5,'end':1.5,'kind':'breath','approved':True,'reason':'Authored silence fixture for the sample mapping test; not real breath detection or a listening claim.'}]}
    r=prepare(audio,transcript,out/'prepared',trim_breaths=args.trim_breaths,review=review)
    plan=json.loads((ROOT/'examples/plan-validation/plan.json').read_text());plan['source'].update(audio=r['audio'],subtitles=r['subtitles']);plan['audio_preparation']['trim_breaths']=args.trim_breaths;duration=r['duration_seconds'];end_frame=round(duration*plan['render_spec']['fps']);split=(end_frame//2)/plan['render_spec']['fps'];plan['cues'][0]['end_seconds']=split;plan['cues'][1]['start_seconds']=split;plan['cues'][1]['end_seconds']=end_frame/plan['render_spec']['fps'];plan['source']['duration_seconds']=duration;plan_path=out/'plan.json';plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    project=out/'hyperframes'
    subprocess.run(['node',str(ROOT/'scripts/init_project.mjs'),'--plan',str(plan_path),'--project-dir',str(project)],check=True)
    subprocess.run(['node',str(ROOT/'scripts/hf.mjs'),'lint',str(project)],check=True)
    if args.render:
        final=out/'final/smoke.mp4'
        subprocess.run(['node',str(ROOT/'scripts/render_master.mjs'),'--plan',str(plan_path),'--project-dir',str(project),'--output',str(final),'--purpose','smoke','--encoding','software'],check=True)
        subprocess.run(['node',str(ROOT/'scripts/validate_master.mjs'),'--plan',str(plan_path),'--final',str(final),'--output-dir',str(out)],check=True)
    print('Synthetic smoke complete; not a creative production or listening evaluation.')
if __name__=='__main__':main()
