

create table barcode(pkey INTEGER PRIMARY KEY asc, 
	barcode_value TEXT UNIQUE NOT NULL, freeplays INTEGER DEFAULT 0,
	added_by_admin INTEGER DEFAULT 0);
create table access_log(pkey INTEGER PRIMARY_KEY asc,
	 barcode_fk INTEGER REFERENCES barcode(pkey),
	 access_timestamp DEFAULT(CURRENT_TIMESTAMP));
