"""Exercise the actual bundled executables without contacting YouTube."""
import json

from acquisition import find_tools, spawn, stop_process
from localization import RESOURCES


def run_tool_checks(output):
    tools = find_tools(RESOURCES / 'tools/download')
    folder = output / 'tool-checks'
    folder.mkdir(exist_ok=True)

    def run(args):
        process = spawn([str(arg) for arg in args])
        try:
            text, _ = process.communicate(timeout=30)
            assert process.returncode == 0, text[-4000:]
            return text
        finally:
            stop_process(process)

    versions = {'yt-dlp': run([tools['yt-dlp'], '--version']).strip(),
                'deno': run([tools['deno'], '--version']).splitlines()[0]}
    assert run([tools['deno'], 'eval', 'console.log(1+1)']).strip() == '2'
    video, audio, merged = [folder / name for name in ('video.mkv', 'audio.wav', 'merged.mkv')]
    run([tools['ffmpeg'], '-nostdin', '-y', '-f', 'lavfi', '-i', 'color=size=64x64:rate=10',
         '-t', '0.5', '-c:v', 'ffv1', video])
    run([tools['ffmpeg'], '-nostdin', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440',
         '-t', '0.5', audio])
    run([tools['ffmpeg'], '-nostdin', '-y', '-i', video, '-i', audio,
         '-map', '0:v', '-map', '1:a', '-c', 'copy', merged])
    info = json.loads(run([tools['ffprobe'], '-v', 'quiet', '-show_streams', '-of', 'json', merged]))
    assert {s['codec_type'] for s in info['streams']} == {'audio', 'video'}
    (folder / 'report.json').write_text(json.dumps({'result': 'PASS', 'versions': versions,
        'checks': ['bundled tool startup', 'Deno execution', 'lossless audio/video merge']}, indent=2), encoding='utf-8')
