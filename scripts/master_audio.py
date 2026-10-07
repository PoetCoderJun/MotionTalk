#!/usr/bin/env python3
"""Source-based voice retiming and one-stage measured normalization. No listening claim."""
import argparse
import json
import math
import re
import subprocess
from pathlib import Path

def tempo_ratio(source_speed, target_speed):
    if not all(math.isfinite(x) and x > 0 for x in (source_speed, target_speed)):
        raise ValueError('Speeds must be finite and positive')
    ratio = target_speed / source_speed
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("Tempo ratio is not representable")
    return ratio

def retime_srt(text, ratio, duration=None):
    tempo_ratio(1, ratio)
    timestamp = r'(\d{2}):(\d{2}):(\d{2}),(\d{3})'
    def millis(value):
        h, minute, sec, ms = map(int, re.fullmatch(timestamp, value).groups())
        return h*3600000 + minute*60000 + sec*1000 + ms
    def stamp(n):
        return f'{n//3600000:02}:{n//60000%60:02}:{n//1000%60:02},{n%1000:03}'
    previous_end = -1
    chunks = re.split(r'(\r?\n\s*\r?\n)', text)
    for index in range(0, len(chunks), 2):
        if not chunks[index].strip(): continue
        rows = chunks[index].splitlines(keepends=True)
        ti = 1 if rows[0].strip().lstrip('\ufeff').isdigit() else 0
        raw = rows[ti].rstrip('\r\n'); ending = rows[ti][len(raw):]
        match = re.fullmatch(r'(\d{2}:\d{2}:\d{2},\d{3})(\s+-->\s+)(\d{2}:\d{2}:\d{2},\d{3})(.*)',raw)
        if not match: raise ValueError('Invalid SRT timing line')
        start, end = round(millis(match[1])/ratio), round(millis(match[3])/ratio)
        if start < previous_end or end <= start:
            raise ValueError('Retime makes subtitles overlap or zero-length')
        if duration is not None and end > round(duration*1000):
            raise ValueError('Subtitle extends beyond picture')
        previous_end = end
        rows[ti] = stamp(start)+match[2]+stamp(end)+match[4]+ending
        chunks[index] = ''.join(rows)
    return ''.join(chunks)

def completion_status(technical_passed, listened):
    if not technical_passed:
        return 'technical_failed'
    return 'technical_passed_listened' if listened else 'technical_passed_listening_pending'

def run(args, log=None):
    p = subprocess.run(args, capture_output=True, text=True)
    if log:
        Path(log).write_text(p.stderr, encoding='utf-8')
    if p.returncode:
        raise RuntimeError(p.stderr[-5000:])
    return p.stdout, p.stderr

def metadata(path):
    return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)])[0])

def norm_json(text):
    matches = re.findall(r'\{\s*"input_i".*?\}', text, re.S)
    if not matches:
        raise ValueError('No loudnorm measurement returned')
    return json.loads(matches[-1])

def measure(path, target, peak, lra, log):
    _, err = run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-map','0:a:0','-af',
                 f'loudnorm=I={target}:TP={peak}:LRA={lra}:print_format=json','-f','null','-'],log)
    return norm_json(err)

def decoded_samples(path, sample_rate=48000):
    proc = subprocess.Popen(['ffmpeg','-v','error','-xerror','-i',str(path),'-map','0:a:0',
                             '-ar',str(sample_rate),'-ac','2','-c:a','pcm_f32le','-f','f32le','-'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    count = 0
    while True:
        chunk = proc.stdout.read(1048576)
        if not chunk: break
        count += len(chunk)
    err = proc.stderr.read().decode(errors='replace')
    if proc.wait(): raise RuntimeError(err)
    return count//8

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-audio', type=Path, required=True, help='Unmastered voice with approved cuts')
    ap.add_argument('--source-speed', type=float, default=1)
    ap.add_argument('--target-speed', type=float, required=True)
    ap.add_argument('--duration', type=float, required=True, help='Exact already-retimed picture duration')
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--target-lufs', type=float, default=-13.5)
    ap.add_argument('--true-peak', type=float, default=-2)
    ap.add_argument('--max-final-true-peak', type=float, default=-1.5)
    ap.add_argument('--lra', type=float, help='Optional intentional LRA constraint; default preserves measured source LRA')
    ap.add_argument('--subtitles', type=Path, help='SRT copy; text is not changed')
    ap.add_argument('--subtitle-source-speed', type=float, help='Required with --subtitles; independent of audio speed')
    a = ap.parse_args()
    if a.subtitles and a.subtitle_source_speed is None:
        ap.error('--subtitles requires --subtitle-source-speed')
    ratio = tempo_ratio(a.source_speed, a.target_speed)
    if not math.isfinite(a.duration) or a.duration <= 0:
        raise ValueError('duration must be finite and positive')
    if a.output_dir.exists() and any(a.output_dir.iterdir()):
        raise ValueError('Use a new empty output directory; never overwrite a source or earlier master')
    source = metadata(a.source_audio)
    audio = next(s for s in source['streams'] if s['codec_type']=='audio')
    source_duration = float(audio.get('duration') or source['format']['duration'])
    source_start = float(audio.get('start_time',0))
    if abs(source_start)>1/48000:
        raise ValueError('Nonzero source audio origin; align the approved source explicitly before resetting PTS')
    if abs(source_duration/ratio-a.duration) > .05:
        raise ValueError('Source speed/duration do not match picture; do not hide mismatch with -shortest')
    a.output_dir.mkdir(parents=True,exist_ok=True)
    n = round(a.duration*48000)
    # Factor extreme values into supported atempo stages; each speed is applied exactly once.
    stages=[]; remaining=ratio
    while remaining>2: stages.append('atempo=2');remaining/=2
    while remaining<.5: stages.append('atempo=0.5');remaining/=.5
    if abs(remaining-1)>1e-12:stages.append(f'atempo={remaining:.15g}')
    stages += ['aresample=48000','asetpts=PTS-STARTPTS']
    pre=','.join(stages)
    pcm=a.output_dir/'retimed-source.wav'; wav=a.output_dir/'master.wav';aac=a.output_dir/'master.m4a'
    natural=a.output_dir/'retimed-natural.wav'
    run(['ffmpeg','-v','error','-xerror','-n','-i',str(a.source_audio),'-map','0:a:0','-af',pre,
         '-ar','48000','-ac','2','-c:a','pcm_f32le',str(natural)],a.output_dir/'retime.log')
    natural_samples=decoded_samples(natural)
    if abs(natural_samples-n)>2400:
        raise ValueError('Decoded retimed source differs by more than 50ms; inspect timebase instead of padding')
    run(['ffmpeg','-v','error','-xerror','-n','-i',str(natural),'-af',
         f'apad,atrim=end_sample={n},asetpts=PTS-STARTPTS','-c:a','pcm_f32le',str(pcm)])
    measured=measure(pcm,a.target_lufs,a.true_peak,a.lra or 50,a.output_dir/'measure-discovery.log')
    effective_lra=a.lra if a.lra is not None else max(5,float(measured['input_lra']))
    if effective_lra != (a.lra or 50):
        measured=measure(pcm,a.target_lufs,a.true_peak,effective_lra,a.output_dir/'measure-source.log')
    else:
        (a.output_dir/'measure-source.log').write_text((a.output_dir/'measure-discovery.log').read_text())
    if not all(math.isfinite(float(measured[k])) for k in ['input_i','input_tp','input_lra','input_thresh']):
        raise ValueError('Silent/non-finite measurement; do not normalize automatically')
    # No compressor, makeup gain, or EQ inserted between measurement and second pass.
    filt=(f'loudnorm=I={a.target_lufs}:TP={a.true_peak}:LRA={effective_lra}:'
          f'measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}:'
          f'measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}:'
          f'offset={measured["target_offset"]}:linear=true:print_format=json,'
          'aresample=48000,asetpts=PTS-STARTPTS')
    normalized=a.output_dir/'normalized-natural.wav'
    finalization=f'apad,atrim=end_sample={n},asetpts=PTS-STARTPTS'
    _, process_log=run(['ffmpeg','-hide_banner','-nostats','-n','-i',str(pcm),'-af',filt,
                       '-ar','48000','-ac','2','-c:a','pcm_f32le',str(normalized)],a.output_dir/'normalize.log')
    normalized_samples=decoded_samples(normalized)
    if abs(normalized_samples-n)>2400:
        raise ValueError('Normalization changed length by more than 50ms; inspect latency before padding')
    run(['ffmpeg','-v','error','-xerror','-n','-i',str(normalized),'-af',finalization,
         '-ar','48000','-ac','2','-c:a','pcm_s24le',str(wav)])
    run(['ffmpeg','-v','error','-n','-i',str(wav),'-c:a','aac','-b:a','320k','-ar','48000',str(aac)])
    final=measure(aac,a.target_lufs,a.true_peak,effective_lra,a.output_dir/'measure-aac.log')
    wav_samples=decoded_samples(wav);aac_samples=decoded_samples(aac)
    final_audio=next(s for s in metadata(aac)['streams'] if s['codec_type']=='audio')
    checks={'finite_measurements':all(math.isfinite(float(final[k])) for k in ['input_i','input_tp','input_lra']),
            'true_peak':float(final['input_tp'])<=a.max_final_true_peak,
            'duration':abs(float(final_audio['duration'])-n/48000)<=1/48000+.001,
            'start_zero':abs(float(final_audio.get('start_time',0)))<=1/48000,
            'wav_samples_exact':wav_samples==n,
            'aac_codec_padding_only':0<=aac_samples-n<=1024,
            'loudness_target':abs(float(final['input_i'])-a.target_lufs)<=.8}
    if a.subtitles:
        (a.output_dir/'retimed.srt').write_text(retime_srt(a.subtitles.read_text(),tempo_ratio(a.subtitle_source_speed,a.target_speed),a.duration),encoding='utf-8')
    report={'status':completion_status(all(checks.values()),False),'technical_checks':checks,
            'source_audio':str(a.source_audio.resolve()),'source_speed':a.source_speed,'target_speed':a.target_speed,
            'applied_tempo_ratio':ratio,'target_duration':n/48000,
            'samples':{'natural_retimed':natural_samples,'retime_tail_adjustment':n-natural_samples,
                       'normalized_natural':normalized_samples,'normalization_tail_adjustment':n-normalized_samples,
                       'target':n,'wav':wav_samples,'decoded_aac':aac_samples,'aac_padding':aac_samples-n},
            'source_start_time':source_start,'effective_lra':effective_lra,'source_measurement':measured,
            'pre_filter':pre,'master_filter':filt,'finalization_filter':finalization,'normalization':norm_json(process_log),
            'final_aac_measurement':final,'target_lufs':a.target_lufs,
            'loudness_target_met':abs(float(final['input_i'])-a.target_lufs)<=.8,
            'listening':{'performed':False,'result':'pending','note':'True peak/LUFS do not establish absence of audible distortion. Compare source and processed opening/problem passages at matched playback loudness.'}}
    (a.output_dir/'audio-master-report.v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'status':report['status'],'wav':str(wav),'aac':str(aac),'measured':final,'target_lufs':a.target_lufs,'target_met':report['loudness_target_met'],
                      'normalization_mode':report['normalization']['normalization_type']},ensure_ascii=False))
    if not all(checks.values()):raise RuntimeError('Technical check failed; inspect report, do not claim delivery passed')
if __name__=='__main__':main()
