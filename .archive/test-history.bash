#!/usr/bin/env bash

# --------------------------------------------------------------
# Copyright (C) 2022: Snyder Business And Technology Consulting. - All Rights Reserved
#
# Licensing:
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Date:
# September 30, 2022
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
# A simple script to test the history file against the pending downloads.
# --------------------------------------------------------------

# Get the History File
while IFS= read -r ID
    do
        #echo -en "Checking ID: \"$ID\" ... "
        # Checking history file for ID
        if [[ "$ID" =~ ^-.* ]]
            then
                NEWID=$(echo "$ID" | sed -r 's/^-/\\&/g')
                echo -en "Checking ID: \"$NEWID\" ... "
                if grep -qE "$NEWID" "/c/Users/alexa/GitHubCode/mytube/.archive/history.txt"
                    then
                        echo "downloaded."
                elif grep -qE "$ID" "/c/Users/alexa/GitHubCode/mytube/.archive/history.txt"
                    then
                        echo "downloaded. (un-escaped)"
                    else
                        echo "still pending."
                fi
        fi
        #if ! grep -q "$ID" "/c/Users/alexa/GitHubCode/mytube/.archive/history.txt"
        #    then
        #        echo "still pending."
        #    else
        #        echo "downloaded."
        #fi
    done < <(awk -F '=' '{print $2}' < '/c/Users/alexa/GitHubCode/mytube/pending_downloads.txt')