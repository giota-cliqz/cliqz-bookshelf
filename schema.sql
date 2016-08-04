drop table if exists books;
create table books (
	id integer primary key autoincrement,
	title text not null,
	description text not null,
	author text not null,
	thumbnail text null
);


drop table if exists users;
create table users (
	id integer primary key autoincrement,
	first_name text not null,
	last_name text not null,
	email text not null,
	password text not null,
	admin boolean not null
);

drop table if exists borrowed;
create table borrowed (
	id integer primary key autoincrement,
	user_id integer not null,
	book_id integer not null,
	start_date date null,
	return_date date null,
	expected_date date null,
	FOREIGN KEY (user_id) REFERENCES users(ID),
    FOREIGN KEY (book_id) REFERENCES books(ID)
);

