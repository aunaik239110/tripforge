import psycopg

connection = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="tripforge",
    user="tripforge",
    password="tripforge_dev",
)

print("Database connection successful!")

connection.close()
