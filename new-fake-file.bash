#!/usr/bin/env bash

# Define base media directory
BASE_DIR="/opt/media"

# Define category options
CATEGORIES=("tv.kids" "tv.docs" "Exit")

echo "📺 Select a category:"
select CATEGORY in "${CATEGORIES[@]}"
    do
        case $CATEGORY in
            "tv.kids"|"tv.docs")
                echo "👉 Selected category: $CATEGORY"
                break
                ;;
            "Exit")
                echo "👋 Exiting..."
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please choose again."
                ;;
        esac
    done


# Prompt for series name
while [[ -z "$SERIES_NAME" ]]
    do
        read -r -p "📛 Enter the series name: " SERIES_NAME
    done

# Prompt for series year
while [[ -z "$SERIES_YEAR" ]]
    do
        read -r -p "📅 Enter the series year: " SERIES_YEAR
    done


# Build the full show path
SHOW_PATH="${BASE_DIR}/${CATEGORY}/${SERIES_NAME} (${SERIES_YEAR}) {tvdb-xxxxx}"

# Create directory if needed
if [[ ! -d "${SHOW_PATH}" ]]
    then
        echo "📁 Creating directory: ${SHOW_PATH}"
        mkdir -p "${SHOW_PATH}"
fi


# Create the fake 10MB MP4 file
FAKE_FILE="${SHOW_PATH}/S01E01_fake.mp4"

echo "📼 Generating fake episode: ${FAKE_FILE}"

( echo -ne '\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom'; dd if=/dev/zero bs=1M count=100 status=none ) > "${FAKE_FILE}"

echo "✅ Fake episode created successfully!"

echo "📂 Directory contents:"
ls -Alh "${SHOW_PATH}"