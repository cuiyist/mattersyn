"""Reject filesystem aliases in bounded publication work directories."""
from pathlib import Path
import os
import stat

def checked_path(root, target):
    root = Path(os.path.abspath(root))
    target = Path(os.path.abspath(target))
    if not target.is_relative_to(root):
        raise RuntimeError('Path is outside the intended work directory')
    for item in [*reversed(target.parents), target]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise RuntimeError('Symlink or reparse-point paths are not accepted')
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
            raise RuntimeError('Multiply linked files are not accepted')
    if not target.resolve().is_relative_to(root.resolve()):
        raise RuntimeError('Resolved path escapes the work directory')
    return target

def preflight_tree(root):
    root = checked_path(root, root)
    if root.exists():
        for directory, directories, files in os.walk(root, followlinks=False):
            for name in directories + files:
                checked_path(root, Path(directory) / name)
    return root
