import streamlit as st
import mysql.connector
from mysql.connector import Error
from passlib.hash import bcrypt

# connection with the MySQL database
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345', # MySQL passowrd. replcae password with ur passowrd
            database='rail'   # in my sql rail is database name(create databse rail )
        )
        if connection.is_connected():
            return connection
    except Error as e:
        st.error(f"error connecting to mysql: {e}")
        return None

#   database and create tables if they do not exist to handle error we put here 
def initialize_database():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
        create table if not exists user (
            id int auto_increment primary key,
            username varchar(255) unique not null,
            password_hash varchar(255) not null,
            role enum('admin', 'user') not null
        )
        """)
        cursor.execute("""
        create table if not exists train (
            id int auto_increment primary key,
            train_name varchar(255) not null,
            source varchar(255) not null,
            destination varchar(255) not null,
            total_seats int not null
        )
        """)
        cursor.execute("""
        create table if not exists seatavailability (
            id int auto_increment primary key,
            train_id int,
            available_seats int not null,
            foreign key (train_id) references train(id)
        )
        """)
        cursor.execute("""
        create table if not exists booking (
            id int auto_increment primary key,
            user_id int,
            train_id int,
            seat_number int not null,
            booking_time timestamp default current_timestamp,
            foreign key (user_id) references user(id),
            foreign key (train_id) references train(id)
        )
        """)
        connection.commit()
        connection.close()

# register a new user with hashed password and a role
def register_user(username, password, role):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        password_hash = bcrypt.hash(password)
        cursor.execute("insert into user (username, password_hash, role) values (%s, %s, %s)",
                       (username, password_hash, role))
        connection.commit()
        connection.close()
        st.success("user registered successfully!")

# check authenticate a user by checking the provided password against the stored hash is correct or not
def authenticate_user(username, password):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("select password_hash from user where username = %s", (username,))
        result = cursor.fetchone()
        connection.close()
        if result and bcrypt.verify(password, result[0]):
            return True
    return False

#  add a new train to the system
def add_train(train_name, source, destination, total_seats):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("insert into train (train_name, source, destination, total_seats) values (%s, %s, %s, %s)",
                       (train_name, source, destination, total_seats))
        cursor.execute("insert into seatavailability (train_id, available_seats) select id, %s from train where train_name = %s",
                       (total_seats, train_name))
        connection.commit()
        connection.close()
        st.success("train added successfully!")

#  check the availability of seats on different trains are available or not
def check_seat_availability():
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        query = """
        select train.train_name, train.source, train.destination, seatavailability.available_seats, train.id
        from train
        join seatavailability on train.id = seatavailability.train_id
        """
        cursor.execute(query)
        results = cursor.fetchall()
        connection.close()
        return results
    return []

#  book a seat on a train
def book_seat(username, train_id, seat_number):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            
            

            cursor.execute("start transaction")
            
           
            cursor.execute("select id from user where username = %s", (username,))
            user_id = cursor.fetchone()
            if user_id is None:
                st.error("user not found!")
                connection.rollback()
                return
            user_id = user_id[0]

            # Check there are seats available on the selected train or not . 0 means  not available
            cursor.execute("select available_seats from seatavailability where train_id = %s", (train_id,))
            result = cursor.fetchone()
            if result is None:
                st.error("train not found!")
                connection.rollback()
                return
            
            available_seats = result[0]
            if available_seats > 0:
                # If seats are available insert a new booking 
                cursor.execute("insert into booking (user_id, train_id, seat_number) values (%s, %s, %s)",
                               (user_id, train_id, seat_number))
                cursor.execute("update seatavailability set available_seats = available_seats - 1 where train_id = %s",
                               (train_id,))
                connection.commit()
                st.success("seat booked successfully!")
            else:
                st.error("no seats available!")
                connection.rollback()
        except Error as e:
            connection.rollback()
            st.error(f"failed to book seat: {e}")
        finally:
            connection.close()
    else:
        st.error("failed to connect to the database.")

# the booking details 
def get_booking_details(username):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
        select train.train_name, booking.seat_number, booking.booking_time
        from booking
        join user on booking.user_id = user.id
        join train on booking.train_id = train.id
        where user.username = %s
        """, (username,))
        results = cursor.fetchall()
        connection.close()
        return results
    return []

# Streamlit 
def main():
    st.title("railway IRCTC web app")
    st.sidebar.title("Choose option")
    option = st.sidebar.selectbox("choose an option", ["login", "register", "admin", "book seat", "view bookings"])

    if option == "login":
        st.subheader("login")
        username = st.text_input("username")
        password = st.text_input("password", type="password")
        if st.button("login"):
            if authenticate_user(username, password):
                st.session_state['username'] = username
                st.success("logged in successfully!")
            else:
                st.error("invalid username or password.")

    elif option == "register":
        st.subheader("register")
        username = st.text_input("username")
        password = st.text_input("password", type="password")
        role = st.selectbox("role", ["user", "admin"])
        if st.button("register"):
            register_user(username, password, role)
       
    elif option == "admin":
        if 'username' in st.session_state and st.session_state['username']:
            st.subheader("add train")
            train_name = st.text_input("train name")
            source = st.text_input("source")
            destination = st.text_input("destination")
            total_seats = st.number_input("total seats", min_value=1)
            if st.button("submit train"):
                add_train(train_name, source, destination, total_seats)
        else:
            st.warning("please log in as admin to access this section.")
       
    elif option == "book seat":
        if 'username' in st.session_state and st.session_state['username']:
            st.subheader("book a seat")

            # available trains with seat
            train_results = check_seat_availability()

            if train_results:
                train_options = [f"{train_name} (Source: {source}, Destination: {destination})"
                                 for train_name, source, destination, available_seats, train_id in train_results]
                
                selected_train = st.selectbox("plz select train", train_options)
                selected_train_index = train_options.index(selected_train)
                selected_train_id = train_results[selected_train_index][4]
                selected_available_seats = train_results[selected_train_index][3]

                st.write(f"train: {selected_train}")
                st.write(f"available seats: {selected_available_seats}")
                
                seat_number = st.number_input("seat number", min_value=1)
                if st.button("book seat"):
                    book_seat(st.session_state['username'], selected_train_id, seat_number)
            else:
                st.warning("no trains available.")
        else:
            st.warning("please log in to book a seat.")
       
    elif option == "view bookings":
        if 'username' in st.session_state and st.session_state['username']:
            st.subheader("your bookings")
            bookings = get_booking_details(st.session_state['username'])
            if bookings:
                for train_name, seat_number, booking_time in bookings:
                    st.write(f"train: {train_name}, seat number: {seat_number}, booking time: {booking_time}")
            else:
                st.write("no bookings found.")
        else:
            st.warning("please log in to view your bookings.")


if __name__ == "__main__":
    initialize_database()
    main()
