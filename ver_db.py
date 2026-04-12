import sqlite3

conn = sqlite3.connect("clientes.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM clientes")
dados = cursor.fetchall()

print("DADOS DO BANCO:\n")

for d in dados:
    print(d)

conn.close()
