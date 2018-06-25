create database item_catalog;

\c item_catalog

create table category (
    id serial primary key,
    name varchar(30)
);

create table item (
    id serial primary key,
    title varchar(30) not null,
    description varchar(10000) not null,
    created_at timestamp default now(),
    category_id integer references category
);
