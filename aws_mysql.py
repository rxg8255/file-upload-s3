import mysql.connector
import os

ENDPOINT = "xxxxxxxxxxxx.rds.amazonaws.com"
PORT = "3306"
USER = "admin"
REGION = "us-east-2"
DBNAME = "s3_files_info"
os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'


token = ""

try:
    conn = mysql.connector.connect(host=ENDPOINT, user=USER, passwd=token, port=PORT, database=DBNAME,
                                   ssl_ca='SSLCERTIFICATE')
    cur = conn.cursor()
    cur.execute("""SELECT now()""")
    query_results = cur.fetchall()
    print(query_results)
except Exception as e:
    print("Database connection failed due to {}".format(e))
