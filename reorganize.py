#!/usr/bin/env python3
"""
reorganize.py  -  tidy the GitHub-XH website folder using website-structure-rules.md

What it does
  1. Puts every image, document and video under one "assets" folder (the assets wrapper).
  2. Gives every file and folder a lowercase name with hyphens and no spaces.
  3. Moves motion.css and motion.js into assets/css and assets/js.
  4. Moves the big <style> and <script> blocks out of index.html into assets/css/style.css and assets/js/main.js.
  5. Rewrites every path inside index.html to the new relative path (no leading "./").
  6. Moves old backup files OUT of the website folder, into a sibling folder called GitHub-XH-backup.
  Nothing is deleted. index.html is copied to the backup folder first.

How to run (copy this file into C:\\Users\\user\\OneDrive\\Documents\\GitHub-XH, next to index.html)
  python reorganize.py --dry-run     shows what would happen and changes nothing
  python reorganize.py               does it
"""
import re, shutil, sys
from pathlib import Path

DRY    = '--dry-run' in sys.argv
ROOT   = Path(__file__).resolve().parent                 # the website folder
BACKUP = ROOT.parent / (ROOT.name + '-backup')           # old files go here (not published)

# old folder  ->  new folder   (the first match wins, so longer paths come first)
FOLDERS = [
    ('Jobimages/ForntPage',            'assets/images/covers'),            # card cover pictures ("ForntPage" was a typo)
    ('Jobimages/Math_Unity_Game',      'assets/images/projects/math-game'),
    ('Jobimages/3D-UnityGame',         'assets/images/projects/education-game'),
    ('Jobimages/UnityAssignmentProject','assets/images/projects/3d-game'),
    ('Jobimages/PeriodApp',            'assets/images/projects/period-app'),
    ('Jobimages/Wix',                  'assets/images/projects/wix-website'),
    ('Jobimages/PureMed',              'assets/images/projects/puremed'),
    ('Jobimages/Raffles',              'assets/images/projects/raffles'),
    ('Jobimages/SelfLearn/Blender',    'assets/images/projects/blender'),
    ('main',                           'assets/images/slides'),            # first picture of each project pop up
    ('image',                          'assets/images'),                   # character.png
    ('files',                          'assets/docs'),
    ('videos',                         'assets/videos'),
]
# single files that get a specific new name or place
SINGLE = {
    'motion.css': 'assets/css/motion.css',
    'motion.js':  'assets/js/motion.js',
    'files/Pang Jia Qi - ATS Resume.pdf': 'assets/docs/xu-hui-cv.pdf',      # no spaces, no personal name in the file name
}
OLD_FILES = ['Oldmotion.js', 'Oldmotion.css', 'htmlNewAnimation.txt', 'person.txt']   # moved to the backup folder
TOP_ASSET_FOLDERS = ['Jobimages', 'main', 'image', 'files', 'videos']

def clean(name):
    """EducationGame.png -> education-game.png | 'GoutFizz MAY Post 2.png' -> gout-fizz-may-post-2.png"""
    stem, dot, ext = name.rpartition('.') if '.' in name else (name, '', '')
    stem = stem.replace('3DGame', '3d-game').replace('EZFirgi', 'ez-firgi')
    stem = re.sub(r'(?<=[a-z])(?=[A-Z])', '-', stem)          # camelCase -> camel-Case
    stem = re.sub(r'[^A-Za-z0-9]+', '-', stem).strip('-').lower()
    return stem + (dot + ext.lower() if dot else '')

def new_rel(old):
    """old relative path (forward slashes) -> new relative path"""
    old = old.replace('\\', '/')
    if old.startswith('./'): old = old[2:]
    if old in SINGLE: return SINGLE[old]
    for src, dst in FOLDERS:
        if old == src or old.startswith(src + '/'):
            rest = old[len(src):].strip('/')
            return dst + ('/' + '/'.join(clean(p) for p in rest.split('/')) if rest else '')
    return old                                              # not an asset path: leave it alone

planned = set()                                             # every destination we create (for the check at the end)
def move(src: Path, dst: Path):
    rel = dst.relative_to(ROOT).as_posix() if ROOT in dst.parents else str(dst)
    if dst.exists():
        print(f'  SKIP (already exists): {rel}'); return
    print(f'  {src.relative_to(ROOT).as_posix() if ROOT in src.parents else src}  ->  {rel}')
    planned.add(rel)
    if not DRY:
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(dst))

def main():
    index = ROOT / 'index.html'
    if not index.exists(): sys.exit('index.html not found. Put reorganize.py in the website folder.')
    print(('DRY RUN: nothing will change\n' if DRY else '') + f'Website folder: {ROOT}\nBackup folder:  {BACKUP}\n')

    # ---- 1. read index.html (newline='' keeps your Windows line endings) ----
    with open(index, encoding='utf-8', newline='') as fh: html = fh.read()   # newline='' keeps Windows line endings
    if not DRY:
        BACKUP.mkdir(exist_ok=True); shutil.copy2(index, BACKUP / 'index.before-reorganize.html')

    # ---- 2. pull the big <style> and <script> blocks out of index.html ----
    css = js = None
    m = re.search(r'<style>\r?\n(.*?)</style>', html, re.S)
    if m:
        css = m.group(1)
        html = html.replace(m.group(0), '<link rel="stylesheet" href="assets/css/style.css">')
    for m in re.finditer(r'<script>\r?\n(.*?)</script>', html, re.S):
        if 'const projects' in m.group(1):                   # the projects list script (not the tiny 'js' one)
            js = m.group(1)
            html = html.replace(m.group(0), '<script src="assets/js/main.js"></script>')
            break
    html = html.replace('<link rel="stylesheet" href="motion.css">', '<link rel="stylesheet" href="assets/css/motion.css">')
    html = html.replace('<script src="motion.js"></script>', '<script src="assets/js/motion.js"></script>')
    html = re.sub(r'File map:.*', 'File map: assets/css/style.css = looks | index.html = content + illustration | assets/js/main.js = projects list | assets/js/motion.js + motion.css = animation', html, count=1)

    # ---- 3. rewrite every asset path (only text inside quotes that starts with one of the old folders) ----
    pattern = re.compile(r'''(?<=['"])(?:\./)?(?:Jobimages|main|image|files|videos)/[^'"\r\n]+(?=['"])''')
    seen = {}
    def fix(m):
        old = m.group(0); old_clean = old[2:] if old.startswith('./') else old
        seen[old_clean] = new_rel(old_clean); return seen[old_clean]
    html = pattern.sub(fix, html)
    if js: js = pattern.sub(fix, js)
    html = html.replace('download="Xu_Hui_CV.pdf"', 'download="xu-hui-cv.pdf"')

    # ---- 4. move the real files ----
    print('Moving files:')
    for top in TOP_ASSET_FOLDERS:
        base = ROOT / top
        if base.is_dir():
            for f in sorted(p for p in base.rglob('*') if p.is_file()):
                move(f, ROOT / new_rel(f.relative_to(ROOT).as_posix()))
    for name in ('motion.css', 'motion.js'):
        if (ROOT / name).exists(): move(ROOT / name, ROOT / SINGLE[name])
    if not DRY:                                              # remove the old folders if they are now empty
        for top in TOP_ASSET_FOLDERS:
            base = ROOT / top
            if base.is_dir():
                for d in sorted((p for p in base.rglob('*') if p.is_dir()), reverse=True):
                    try: d.rmdir()
                    except OSError: pass
                try: base.rmdir()
                except OSError: print(f'  note: {top}/ still has files in it, left in place')

    # ---- 5. write the new files ----
    print('\nWriting:')
    for rel, text in (('assets/css/style.css', css), ('assets/js/main.js', js), ('index.html', html)):
        if text is None: print(f'  WARNING: could not find the block for {rel}'); continue
        print(f'  {rel}'); planned.add(rel)
        if not DRY:
            (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
            with open(ROOT / rel, 'w', encoding='utf-8', newline='') as fh: fh.write(text)

    # ---- 6. old backups leave the website folder ----
    print('\nMoving old files out of the website (to the backup folder):')
    for name in OLD_FILES:
        if (ROOT / name).exists(): move(ROOT / name, BACKUP / name)

    # ---- 7. check: every path in index.html and main.js must now point at a real file ----
    print('\nChecking paths:')
    bad = [p for p in sorted(set(re.findall(r'''(?<=['"])assets/[^'"\r\n]+(?=['"])''', html + (js or ''))))
           if not ((ROOT / p).exists() or p in planned)]
    for p in bad: print(f'  MISSING: {p}')
    print('  all paths OK' if not bad else f'  {len(bad)} path(s) point at files that do not exist (see MISSING above).\n'
          '  The file name on disk probably differs from the name used in index.html (extra space, spelling).')
    print('\nDone.' if not DRY else '\nDry run finished. Run again without --dry-run to apply.')

main()
