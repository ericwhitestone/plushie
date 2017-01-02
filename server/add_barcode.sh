DB="plushie.db"

usage()
{
	echo "$0 barcode #freeplays"
}

if [ ! -e $DB ]; then
	echo "The file $DB does not exist. Run the create script first."
	exit 2
fi

if [ $# -ne 2 ]; then
	usage
	exit 2
fi

sql="insert into barcode(barcode_value, freeplays, added_by_admin) values('$1', '$2', '1')";
sqlite3 $DB "$sql"
