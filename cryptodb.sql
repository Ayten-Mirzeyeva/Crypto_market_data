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
  and tc.table_name  in ('dim_coin', 'fact_price')
order by tc.table_name;

create view mart.daily_return as
 select coin_id,
    date,
    price,
    ((price - lag(price) over (partition by coin_id order by date)) / lag(price) over (partition by coin_id order by date)) as daily_return
from staging.fact_price;


alter view mart.daily_return owner to postgres;



create view mart.max_drawdown 
as
with price_peaks as (
         select fact_price.coin_id,
            fact_price.date,
            fact_price.price,
            max(fact_price.price) over (partition by fact_price.coin_id order by fact_price.date rows between unbounded preceding and current row) as running_peak
           from staging.fact_price
        )
 select coin_id,
    date,
    price,
    running_peak,
    ((price - running_peak) / running_peak) as drawdown
   from price_peaks;


alter view mart.max_drawdown owner to postgres;


create view mart.moving_averages as
 select coin_id,
    date,
    price,
    avg(price) over (partition by coin_id order by date asc rows between 6 preceding and current rows) as moving_avg_7d,
    avg(price) over (partition by coin_id order by date asc rows between 29 preceding and current rows) as moving_avg_30d
from staging.fact_price;


alter view mart.moving_averages owner to postgres;


create view mart.rolling_volatility as
 select coin_id,
    date,
    price,
    daily_return,
    round(stddev_samp(daily_return) over (partition by coin_id order by date rows between 29 preceding and current rows), 5) as volatility_30d
   from mart.daily_return;


alter view mart.rolling_volatility owner to postgres;



create view mart.volatility_ranking as
 with latest as (
         select rolling_volatility.coin_id,
            rolling_volatility.date,
            rolling_volatility.price,
            rolling_volatility.daily_return,
            rolling_volatility.volatility_30d,
            row_number() over (partition by rolling_volatility.coin_id order by rolling_volatility.date desc) as rn
           from mart.rolling_volatility
        )
 select coin_id,
    date,
    price as latest_price,
    daily_return as latest_return,
    volatility_30d,
    rank() over (order by volatility_30d desc) as volatility_rank
 from latest
  where (rn = 1)
  order by volatility_30d desc;


alter view mart.volatility_ranking owner to postgres;


create view mart.return_30d as
select
    coin_id,
    date,
    price,
    lag(price, 30) over (partition by coin_id order by date) as price_30d_ago,(
        price /lag(price, 30) over (partition by coin_id order by date) ) - 1 as return_30d
from staging.fact_price;

alter view mart.return_30d owner to postgres;

select*from mart.return_30d;


create table staging.quarantine (
    coin_id character varying(50),
    date date,
    price numeric,
    market_cap numeric,
    volume numeric,
    reason text,
    quarantined_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP );


alter table staging.quarantine owner to postgres;

select coin_id,
    min(date) as min_date,
    max(date) as max_date,
    count(*) as row_count
from staging.fact_price
group by coin_id
order by coin_id;


select*from staging.fact_price
where coin_id = 'ethereum'
order by date desc;

select*from staging.fact_price
where coin_id = 'bitcoin'
order by date desc;

select*from staging.fact_price
where coin_id = 'tether'
order by date desc;

select*from staging.fact_price
where coin_id = 'tron'
order by date desc;

select * from staging.dim_coin;

select * from staging.fact_price;

select * from staging.quarantine;

select count(*) from staging.dim_coin;

select count(*) from staging.fact_price;

select count(*) from staging.quarantine;

