create schema raw;
create schema staging;
create schema mart;

create table staging.dim_coin (
    coin_id varchar(50) PRIMARY KEY,
    symbol varchar(50),
    name varchar(100)
);


create table staging.fact_price (
    coin_id varchar(50) not null,
    date date not null,
    price numeric,
    market_cap numeric,
    volume numeric,
    primary key (coin_id, date),
    foreign key (coin_id) references staging.dim_coin(coin_id)
);

select column_name, data_type
from information_schema.columns
where table_schema = 'staging'
  and table_name in ('dim_coin', 'fact_price')
order by table_name, ordinal_position;


select  tc.table_name,
    tc.constraint_name,
    tc.constraint_type
from information_schema.table_constraints tc
where tc.table_schema = 'staging'
  and tc.table_name in ('dim_coin', 'fact_price')
order by tc.table_name;



create table staging.quarantine (
    coin_id varchar(50),
    date DATE,
    price NUMERIC,
    market_cap NUMERIC,
    volume numeric,
    reason TEXT,
    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

select *from staging.fact_price
order by date desc;

select*from staging.quarantine
order by coin_id DESC;

select *from staging.dim_coin;

select coin_id,date, market_cap, volume,price from staging.fact_price
order by date;

select coin_id, 
       date, 
	   round(price) as price, 
	   round(market_cap) as market_cap, 
	   round(volume) as volume,
dense_rank() over(partition by coin_id 
                  order by price desc) as dense_rank,
lag(round(price)) over (partition by coin_id 
                 order by price),
lead(round(price)) over (partition by coin_id
                  order by price)				 
from staging.fact_price;



select coin_id, 
       date, 
	   round(price) as price,
	   market_cap,
	   volume,
	   dense_rank() over(partition by coin_id order by price),
	   ((lead(price) over(partition by coin_id order by date)) - (lag(price) over( partition by coin_id order by date ))
	    )/(lag(price) over(partition by coin_id order by date)) as daily_returns
from staging.fact_price;

select*from staging.fact_price;

select coin_id,
       date, 
	   round(price,2) as price,
	   round(market_cap,2) as market_cap,
	   round(volume, 2) as volume ,
	   round(avg(price) over(partition by coin_id order by date desc),2) as moving_averages_7
from staging.fact_price
limit 7;

select coin_id,
       date,
	   round(price,2) as price,
	   round(market_cap, 2) as market_cap,
	   round(volume, 2) as volume,
	   round(avg(price) over(partition by coin_id order by date), 2) as moving_averages_30
from staging.fact_price
limit 30;


select coin_id,
       date,
	   round(price,2) as price,
	   round(market_cap,2) as market_cap,
	   round(volume,2) as volume,
	   percent_rank() over(partition by coin_id order by date) as cem,
	   cume_dist() over(partition by coin_id order by date) as cum_cem
from staging.fact_price;

select coin_id,
       date,
	   round(price,2) as price,
	   round(market_cap) as market_cap,
	   round(volume) as volume,
	   dense_rank() over(partition by coin_id order by price) as dense_rank
from staging.fact_price;

select coin_id,
	   round(max(price),3)
from staging.fact_price
group by coin_id 
order by coin_id;
