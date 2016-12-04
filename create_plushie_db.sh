#!/bin/bash

PLUSHIE_DB_NAME="plushie.db"
if [ -e $PLUSHIE_DB_NAME ]; then
	echo "The database $PLUSHIE_DB_NAME already exists. If you'd like to recreate"
	echo "the database, remove this file and re-run this script"
	exit 2
fi

cat new_db.sql | sqlite3 $PLUSHIE_DB_NAME

