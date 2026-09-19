"""Run the opt-in 1080p EEVEE fast profile, encode, and verify the movie.

No machine-specific paths are embedded. Choose --output on a drive with space.
This runner does not rebuild or save the source Blender project.
"""
import argparse
import contextlib
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--blender', default=os.environ.get('BLENDER', 'blender'))
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--ffprobe', default='ffprobe')
    return parser.parse_args()


@contextlib.contextmanager
def output_lock(path):
    with path.open('a+b') as handle:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def verify_video(info):
    stream = info['streams'][0]
    require((stream['width'], stream['height']) == (1920, 1080), 'Unexpected video dimensions')
    require(stream['r_frame_rate'] == '24/1', 'Unexpected frame rate')
    require(int(stream['nb_read_frames']) == 6480, 'Unexpected decoded frame count')
    require(abs(float(info['format']['duration']) - 270) < 0.05, 'Unexpected duration')
    require(stream['codec_name'] == 'h264', 'Unexpected video codec')


def main():
    args = arguments()
    output = args.output.resolve()
    runtime = output / '.runtime'
    for directory in (output, runtime, runtime/'temp', runtime/'cache', runtime/'blender-user'):
        directory.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, TEMP=str(runtime/'temp'), TMP=str(runtime/'temp'),
               TMPDIR=str(runtime/'temp'), PYTHONDONTWRITEBYTECODE='1',
               BLENDER_USER_RESOURCES=str(runtime/'blender-user'),
               CUDA_CACHE_PATH=str(runtime/'cache'), OPTIX_CACHE_PATH=str(runtime/'cache'),
               XDG_CACHE_HOME=str(runtime/'cache'))
    command = [sys.executable, '-B', str(ROOT/'scripts/render_film.py'),
               '--blender', args.blender, '--device', 'OPTIX', '--fast-render',
               '--engine', 'BLENDER_EEVEE', '--frame-step', '2', '--scale', '50',
               '--samples', '4', '--start', '1', '--end', '6480', '--output', str(output),
               '--ffmpeg', args.ffmpeg, '--encode-preset', 'veryfast']
    started = time.monotonic()

    def status(phase, **extra):
        state = dict(phase=phase, elapsed_seconds=round(time.monotonic()-started),
                     raw_frames=len(list((output/'raw').glob('[0-9]'*6+'.png'))),
                     captioned_frames=len(list((output/'frames').glob('[0-9]'*6+'.png'))),
                     required_raw_frames=3257, required_output_frames=6480,
                     free_bytes=shutil.disk_usage(output).free, **extra)
        temporary = output/'pipeline-status.tmp.json'
        temporary.write_text(json.dumps(state, indent=2), encoding='utf-8')
        temporary.replace(output/'pipeline-status.json')

    def run(cmd, phase, log_name):
        with (output/log_name).open('ab', buffering=0) as log:
            log.write(('\nStarted '+time.strftime('%Y-%m-%d %H:%M:%S')+'\n').encode())
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            with subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=log,
                                  stderr=subprocess.STDOUT, creationflags=flags) as process:
                while process.poll() is None:
                    status(phase, child_pid=process.pid)
                    time.sleep(10)
                return process.returncode

    with output_lock(runtime/'pipeline.lock'):
        if os.name == 'nt':
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        try:
            for attempt in range(1, 4):
                code = run(command, 'rendering_and_subtitles', 'render.log')
                if code == 0:
                    break
                status('retrying_render', attempt=attempt, exit_code=code)
                require(shutil.disk_usage(output).free >= 2*1024**3,
                        'Insufficient free space; free space before resuming')
            else:
                raise RuntimeError('Rendering failed three times; inspect render.log')

            audit = json.loads((output/'validation.json').read_text(encoding='utf-8'))
            require(audit['resolution'] == [1920, 1080] and audit['samples'] == 4,
                    'Unexpected render quality settings')
            require(audit['fps'] == 24 and audit['engine'] == 'BLENDER_EEVEE',
                    'Unexpected render engine or frame rate')
            require(len(audit['rendered_frames']) == 3257, 'Incomplete raw frame selection')
            require(not audit['missing_images'] and not audit['invalid_drivers']
                    and not audit['stationary_motion_objects'], 'Scene validation failed')
            require(all(item['fully_hidden'] for item in audit['water_reveals']),
                    'Water reveal validation failed')
            missing = [f for f in range(1, 6481) if not (output/'frames'/f'{f:06}.png').is_file()]
            require(not missing, f'Missing subtitle frames: {missing[:10]}')
            mp4 = output/'wwtp-process-4m30s.mp4'
            if not mp4.exists():
                require(run(command+['--encode'], 'encoding', 'encode.log') == 0,
                        'Encoding failed; preserve existing output and inspect encode.log')
            status('verifying_video')
            probe = subprocess.run([args.ffprobe, '-v', 'error', '-count_frames',
                    '-select_streams', 'v:0', '-show_entries',
                    'stream=codec_name,width,height,r_frame_rate,nb_read_frames,duration:format=duration',
                    '-of', 'json', str(mp4)], env=env, capture_output=True, text=True, check=True)
            info = json.loads(probe.stdout)
            verify_video(info)
            require(run([args.ffmpeg, '-v', 'error', '-xerror', '-i', str(mp4), '-f', 'null', '-'],
                        'checking_decode', 'decode.log') == 0, 'Video decode validation failed')
            report = dict(passed=True, video=mp4.name, missing_frames=[], video_info=info,
                          full_video_decode_exit_code=0,
                          elapsed_seconds=round(time.monotonic()-started))
            (output/'completion.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
            status('complete', video=mp4.name)
            print(mp4)
        except Exception as exc:
            status('failed', error=str(exc))
            raise
        finally:
            if os.name == 'nt':
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


if __name__ == '__main__':
    main()
