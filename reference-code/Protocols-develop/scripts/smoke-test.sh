#!/usr/bin/env bash

# NOTE Ian 2018-04-25: this is meant to be run manually to check OT2 protocols.
# For now, the user is responsible for installing the appropriate
# python opentrons library for OT2 protocols.
# 'otcustomizers' also must be installed.

# Clean smoketest dir
echo "Clearing smoketest/ dir"
rm -rf smoketest/
mkdir smoketest

python -c 'import opentrons; print("Smoke testing *.ot2.py protocols. Opentrons version:", opentrons.__version__)'

echo "*****"

# copy all *.ot2.py files to smoketest/
find . -name '*.ot2.py' | sort -f | while read filename; do
    cp $filename smoketest/
done


find smoketest/ -name '*.ot2.py' | sort -f | while read pyfile; do
  if grep -Eq "^def run_custom_protocol\(" $pyfile; then
    echo "Processing CUSTOMIZABLE protocol '$pyfile' with default arguments"
    # add run_custom_protocol() call to end of all customizable protocols
    echo 'run_custom_protocol()' >> $pyfile
  else
    echo "Processing protocol '$pyfile'"
  fi

  # you can use the env var OT_TESTING to bypass time.sleep steps in protocols
  OT_TESTING=True python "$pyfile" || exit 1
done
