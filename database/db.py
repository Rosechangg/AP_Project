import pymysql
import sqlalchemy as sa

# Connect to DB
db = {
    'user' : 'root',
    'password' : '5491',
    'host' : '0.0.0.0',
    'port' : '3306',
    'database' : 'GEODATA',
}
DB_URL = f"mysql+pymysql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?charset=utf8"
conn = sa.create_engine(DB_URL, encoding = "utf-8")

# Execute SQL
sql = "select * from parking_lot"
rows = conn.execute(sql)

# Print result
for row in rows:
    print(row)
