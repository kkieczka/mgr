#!/bin/bash

# This script takes a directory of Android apps (each app in different subdirectory)
# and, for each of them, tries to obtain a list of external libs that they use.
# It does that by grepping all the java source files for "import ..." lines, sorting them,
# removing repeating lines and submitting the resulting list to a python script. That
# script then tries to determine a list of libraries used (see determine_libs.py source
# code).
# Note: this script assumes 1 parameter will be given: a directory which contains
# subdirectories which are roots for source code of Android apps. It also assumes
# that these subdirectories' names will be package names of corresponding apps.

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <dir_with_apps>"
    exit 1
fi

WORKING_DIR=$1
echo "Working dir is $WORKING_DIR"

for dir in $WORKING_DIR/*/ ; do
    echo "[.] Processing $dir"

    package_name=$(basename $dir)
    # echo "[.] Package name is $package_name"

    # get unique imports, filter out java.*, android.* and package_name.* packages
    # and remove "import" and semicolons from lines
    # todo: dots in $package_name may have impact on regex
    imports=$(egrep -rh --include=*.java "^import " $dir | sort -u \
                | egrep -v "^import (static )?(java|android|$package_name)\..*" \
                | sed 's/import static //;s/import //;s/;//')
    echo "[.] Running libs determinator..."
    # determine unique libraries
    uniq_libs=$(echo $imports | python determine_libs.py)

    echo "$uniq_libs"
    echo ""
done
