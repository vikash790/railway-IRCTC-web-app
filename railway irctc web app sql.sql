create database rail;
use rail;



CREATE table User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL
);

CREATE table Train (
    id INT AUTO_INCREMENT PRIMARY KEY,
    train_name VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    total_seats INT NOT NULL
);

CREATE TABLE  SeatAvailability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    train_id INT,
    available_seats INT NOT NULL,
    FOREIGN KEY (train_id) REFERENCES Train(id)
);

CREATE TABLE  Booking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    train_id INT,
    seat_number INT NOT NULL,
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(id),
    FOREIGN KEY (train_id) REFERENCES Train(id)
);
