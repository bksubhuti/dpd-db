#!/bin/bash

exec > >(tee "/home/deva/logs/backup_local.log") 2>&1

SOURCES=(
    "/home/deva/Documents/dpd-db/dps/"
    "/home/deva/Documents/dpd-db/gui"
    "/home/deva/Documents/dpd-db/scripts/"
    "/home/deva/Documents/dpd-db/tools/"
    "/home/deva/Documents/dpd-db/backup_tsv/"
)

DEST="/home/deva/backups"

EXCLUDES=(
    "--exclude=.git/"
    "--exclude=__pycache__/"
    "--exclude=.venv/"
    "--exclude=.vscode/"
    "--exclude=__init__.py"
    "--exclude=.__init__.py"
)

# Ensure the base backup directory exists
mkdir -p "$DEST"

echo "------ Local Backup Script Started at $(date) ------"

for SOURCE in "${SOURCES[@]}"; do
    SOURCE_NAME=$(basename "$SOURCE")
    DESTINATION="${DEST}/${SOURCE_NAME}"

    echo "Backing up ${SOURCE} to ${DESTINATION}"
    
    # Execute rsync command and append output to the log file
    rsync -a "${EXCLUDES[@]}" "$SOURCE" "$DESTINATION"
done

echo "------ Local Backup Script Ended at $(date) ------"


# export VISUAL=nano 
# crontab -e 