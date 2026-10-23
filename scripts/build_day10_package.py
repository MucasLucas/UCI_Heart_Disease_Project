"""Build a deterministic public evidence ZIP; never package models or raw inputs."""
import hashlib
import json
import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'reports/day10'


def main():
    state = json.loads((OUT/'verification.json').read_text())
    if state.get('evidence',{}).get('status') != 'passed_with_documented_provenance_limits':
        raise ValueError('Evidence verification must pass before packaging')
    names = subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'], cwd=ROOT).decode().split('\0')
    selected=[]
    for name in sorted(set(names)):
        if not name or name in ['reports/day10/release_candidate.zip','reports/day10/package_manifest.json']:
            continue
        path = Path(name)
        public_root = path.parts[0] in ['docs','scripts','tests','reports']
        public_top = len(path.parts)==1 and name in ['README.md','.gitignore','requirements.txt','requirements-evidence.txt']
        if (public_root or public_top or name=='data/raw/README.md') and not (path.name.startswith('local_') or '__pycache__' in path.parts):
            if (ROOT/path).is_file(): selected.append(name)
    files={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in selected}
    metadata=dict(status='evidence_release_candidate_not_verified_model_release',
                  basis_commit='235391be80158a0614108cdeb8c91270833c8598',
                  model_included=False, raw_inputs_included=False,
                  tagged_release_created=False, file_sha256=files)
    def write(z, name, data):
        info=ZipInfo(name, date_time=(2026,10,23,0,0,0));info.compress_type=ZIP_DEFLATED
        info.external_attr=0o100644 << 16
        z.writestr(info,data)
    with ZipFile(OUT/'release_candidate.zip','w') as archive:
        for name in selected: write(archive,name,(ROOT/name).read_bytes())
        write(archive,'PACKAGE_MANIFEST.json',(json.dumps(metadata,indent=2)+'\n').encode())
    metadata['zip_sha256']=hashlib.sha256((OUT/'release_candidate.zip').read_bytes()).hexdigest()
    (OUT/'package_manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')
    with ZipFile(OUT/'release_candidate.zip') as archive:
        if archive.testzip() is not None: raise ValueError('ZIP CRC failure')
        for name, expected in files.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=expected:
                raise ValueError(f'Packaged bytes differ: {name}')
    print(f'Packaged {len(files)} files; SHA-256 {metadata["zip_sha256"]}')


if __name__=='__main__':
    main()
