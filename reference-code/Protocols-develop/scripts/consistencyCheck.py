# TODO. This is not used yet.
import os


def check_protocol_dir(root, files):
    py_files = [f for f in files if f.endswith('.py')]
    if '.ignore' in files:
        return 'IGNORED: {}'.format(root)
    if 'README.md' not in files:
        return 'ERROR: no README.md in {}'.format(root)
    if len(py_files) == 0:
        if '.embedded-app' in files:
            return 'OK: {} has no py files. is an app'.format(root)
        return 'ERROR: {} has no py files. is an app'.format(root)
    if len(py_files) > 1:
        return 'ERROR: {} has >1 .py files!?! ({})'.format(root, len(py_files))
    return 'OK: will read {}'.format(root + py_files[0])  # TODO: check readme vs slots  # noqa: E501


# TODO: use .gitignore
ignored_dirs = [
    'releases', 'smoketest', 'calibrations', 'smoothie', 'containers', 'logs',
    '.ci', '.git', 'env']

for dirEntry in os.scandir():
    if dirEntry.is_dir() and dirEntry.name not in ignored_dirs:
        print(
            check_protocol_dir(
                dirEntry.name,
                [f.name for f in os.scandir(dirEntry.path)]))
