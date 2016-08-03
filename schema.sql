drop table if exists books;
create table books (
	id integer primary key autoincrement,
	title text not null,
	description text not null,
	author text not null
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
