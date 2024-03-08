#!/usr/bin/env bash

# --------------------------------------------------------------
# Copyright (C) 2024: Snyder Business And Technology Consulting. - All Rights Reserved
#
# Licensing:
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Date:
# February 13, 2024
#
# Author:
# Alexander Snyder
#
# Email:
# alexander@sba.tc
#
# Repository:
# https://github.com/thisguyshouldworkforus/bash
#
# Dependency:
# None.
#
# Description:
# Run python scripts in a virtual environment.
# --------------------------------------------------------------

# Path to the virtual environment's activate script
VENV_PATH="/opt/projects/mytube/venv/bin/activate"

# Check if an argument was provided
if [[ "$#" -ne 1 ]]
    then
        echo "Usage: $0 <path-to-python-script>"
        exit 1
fi

# We know we have an argument, but lets verify it's a python script:
if [[ $(file "$1" | awk '{print $2}' | tr -d '[:space:]') = 'Python' ]]
    then
        PYTHON_SCRIPT_NAME="$1"
    else
        echo -en "\n\nThis launcher only accepts mytube python scripts!\n\n"
        exit 1
fi

# shellcheck disable=SC1090
# Check if the virtual environment exists and activate it
if [[ -f "$VENV_PATH" ]]
    then
        source "$VENV_PATH"
        if grep -q 'VIRTUAL_ENV' < <(env)
            then
                echo "Starting $PYTHON_SCRIPT_NAME ..."
                # Run the specified Python script that requires the virtual environment's packages
                python3.11 "$PYTHON_SCRIPT_NAME" &
            else
                echo -en "Did not find proper Virtual Environment value ...\n\n"
                exit 1
        fi
    else
        echo "Virtual environment not found"
        exit 1
fi

# Deactivate the virtual environment if needed
deactivate
