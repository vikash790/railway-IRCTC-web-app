use rail;
select *from  booking;
select *from seatavailability ;
select train_name from train;
select total_seats from train;
select train_name,total_seats from train;
select train_name,count(source) from train group by train_name;
select count(id) from train;
select count(username) from user;