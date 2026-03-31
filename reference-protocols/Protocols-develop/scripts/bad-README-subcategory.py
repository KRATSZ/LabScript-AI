# This is a quick fix to catch when READMEs have subcategories
# that are 2 spaces instead of a tab.
# (4 spaces should be OK, but 2 is not)
# TODO Ian 2018-01-02: this is a HACK, should be dealt with in protolib

# Note: this script must be run from the Protocols base dir
import glob

failure = False

for filename in glob.iglob('protocols/**/README.md', recursive=True):
    with open(filename) as f:
        for i, line in enumerate(f.readlines()):
            if line.startswith('  *'):
                failure = True
                print('{} has spaces not tab on line: {}'.format(
                    filename, i + 1))

if failure:
    raise Exception('Bad subcategories in README. See above for details.')
