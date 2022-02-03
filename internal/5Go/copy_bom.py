import shutil
import sys
from pathlib import Path

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f'Usage: {sys.argv[0]} <path/to/bom.txt> <base> <destination>')
        sys.exit(1)

    bom = Path(sys.argv[1]).absolute().read_text().split('\n')
    base = Path(sys.argv[2]).absolute()
    dst = Path(sys.argv[3]).absolute()

    shutil.rmtree(dst, ignore_errors=True)
    for line in bom:
        if not line:
            continue
        path = base / line
        if not path.exists():
            print(f'Invalid path {line}, skipping')
        if path.is_dir():
            shutil.copytree(path, dst / line)
        else:
            shutil.copy2(path, dst / line)
