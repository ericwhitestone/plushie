#!/bin/bash
if . create_plushie_db.sh; then
	cat mock_data.sql | sqlite3 $PLUSHIE_DB_NAME
fi

