"""Download the official Arabic Vosk model to D; no microphone access."""
import hashlib
import concurrent.futures
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import urllib.request
import zipfile

URL = 'https://alphacephei.com/vosk/models/vosk-model-ar-mgb2-0.4.zip'
ROOT = Path('D:/X-System/models/speech')
NAME = 'vosk-model-ar-mgb2-0.4'


def safe_member(name):
    path = PurePosixPath(name.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts or not path.parts or ':' in name:
        raise ValueError('Unsafe archive member')
    if path.parts[0] != NAME:
        raise ValueError('Unexpected model archive root')
    return path


def main():
    target = ROOT / NAME
    if (target / 'am/final.mdl').is_file():
        print('Speech model already exists; not overwritten.')
        return
    if target.exists():
        raise RuntimeError('An incomplete destination exists; inspect it before retrying.')
    if shutil.disk_usage('D:/').free < 2 * 2**30:
        raise RuntimeError('At least 2 GiB of free D space is required.')
    ROOT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / (NAME + '.zip.part')
    def opener():
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))

    with opener().open(urllib.request.Request(URL, method='HEAD'), timeout=30) as response:
        total = int(response.headers['Content-Length'])
        etag = response.headers.get('ETag', '')
    if not 0 < total < 700 * 2**20:
        raise RuntimeError('Download exceeds expected size limit.')
    # Disjoint ranges keep one slow connection from delaying initial setup.
    # The file is never used as a model until every range and ZIP CRC succeeds.
    with archive.open('wb') as output:
        output.truncate(total)

    def download_range(bounds):
        start, end = bounds
        headers = {'Range': f'bytes={start}-{end}'}
        if etag:
            headers['If-Match'] = etag
        request = urllib.request.Request(URL, headers=headers)
        with opener().open(request, timeout=60) as response, archive.open('r+b') as output:
            if not response.url.startswith('https://alphacephei.com/') or response.status != 206:
                raise RuntimeError('Expected an official partial download response.')
            if response.headers.get('Content-Range') != f'bytes {start}-{end}/{total}':
                raise RuntimeError('Download range mismatch.')
            output.seek(start)
            remaining = end - start + 1
            while remaining:
                block = response.read(min(256 * 1024, remaining))
                if not block:
                    raise RuntimeError('Incomplete download range.')
                output.write(block)
                remaining -= len(block)
        return end - start + 1

    chunk = (total + 7) // 8
    ranges = [(start, min(start + chunk, total) - 1) for start in range(0, total, chunk)]
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for task in concurrent.futures.as_completed([pool.submit(download_range, bounds) for bounds in ranges]):
            completed += task.result()
            print(f'Downloaded {completed // 2**20}/{total // 2**20} MiB', flush=True)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256')
    staging = ROOT / (NAME + '.extracting')
    if staging.exists():
        raise RuntimeError('Previous extraction exists; inspect before retrying.')
    with zipfile.ZipFile(archive) as zf:
        for entry in zf.infolist():
            safe_member(entry.filename)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('Archive symlinks are not accepted.')
        if sum(e.file_size for e in zf.infolist()) > 2 * 2**30:
            raise ValueError('Unpacked model exceeds limit.')
        if zf.testzip():
            raise ValueError('Archive CRC verification failed.')
        zf.extractall(staging)
    extracted = staging / NAME
    if not (extracted / 'am/final.mdl').is_file():
        raise RuntimeError('Expected acoustic model is missing.')
    extracted.rename(target)
    staging.rmdir()
    receipt = {'url': URL, 'bytes': total, 'sha256_local': digest.hexdigest(),
               'publisher_hash_available': False, 'zip_crc': 'PASS', 'license': 'Apache-2.0'}
    (target / 'x-download-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    # Remove only the exact temporary archive created by this run.
    archive.unlink()
    print('PASS: Arabic model prepared; microphone was not opened.', flush=True)


if __name__ == '__main__':
    main()
