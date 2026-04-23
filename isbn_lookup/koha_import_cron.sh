#!/bin/bash
# ---------------------------------------------------------
# Koha MARCXML auto-import script
# Plaats dit in /root/koha_import_cron.sh
# Draait als gebruiker bib-koha via cron
# ---------------------------------------------------------
# crontab -l
# # m h  dom mon dow   command
# * * * * * /var/lib/koha/bib/koha_import_cron.sh
#
# rights and permissions bib-koha
# 4 -rwxr-x--x 1 bib-koha bib-koha 1272 Nov 12 20:05 koha_import_cron.sh

# Omgeving instellen voor Koha
export KOHA_CONF=/etc/koha/sites/bib/koha-conf.xml
export PERL5LIB=/usr/share/koha/lib:/usr/share/koha/lib/perl5
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

UPLOAD_DIR="/var/lib/koha/bib/uploads"
KOHA_CMD_STAGE="/usr/share/koha/bin/stage_file.pl"
KOHA_CMD_COMMIT="/usr/share/koha/bin/commit_file.pl"

cd "$UPLOAD_DIR" || exit 1

# Loop over alle XML bestanden
for file in *.xml; do
    [ -e "$file" ] || continue
    echo "Processing $file"

    # Stage file
    batch=$($KOHA_CMD_STAGE --file "$file" \
        --format MARCXML \
        --add-items \
        --item-action always_add \
        --match do_not_look_for_matching_record \
        --comment "Batch import via script" | awk '/Batch number assigned/ {print $NF}')

    if [ -n "$batch" ]; then
        # Commit batch
        $KOHA_CMD_COMMIT --batch-number "$batch"
        echo "Committed batch $batch"
        # Bestand verwijderen na import
        rm -f "$file"
    else
        echo "No batch created for $file"
    fi
done
