#!/bin/bash

# The script which downloads source code of apps from fdroid repository.
# Takes as argument a file with a list of entries in the form of
# <package_name>:<version_code>

if [[ "$#" -ne 1 ]]; then
    echo "Usage: $0 <pkg_names_list_file>"
    exit 0
fi

RED='\033[0;31m'
NC='\033[0m'

while read p 
do
    echo -e "${RED}Invoking fdroid scanner $p${NC}"
    fdroid scanner $p
done < $1
