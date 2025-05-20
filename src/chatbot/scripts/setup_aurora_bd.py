'''Script responsável por configurar o banco de dados aurora_bd e criar as tabelas necessárias.'''

import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env localizado em uma pasta anterior
from pathlib import Path
env_path = Path('../.env')
load_dotenv(dotenv_path=env_path)

RDS_HOST = os.getenv('HOST')
RDS_USER = os.getenv('USER')
RDS_PASSWORD = os.getenv('PASSWORD')

# Função para criar a conexão com o banco de dados MySQL
def create_connection(database=None):
    try:
        connection = mysql.connector.connect(
            user=RDS_USER,
            password=RDS_PASSWORD,
            host=RDS_HOST,
            database=database
        )
        return connection
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Erro de usuário ou senha")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Banco de dados não existe")
        else:
            print(err)
        return None

# Função para criar o banco de dados
def create_database():
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS aurora_bd")
        print("Banco de dados 'aurora_bd' criado com sucesso!")
    except mysql.connector.Error as err:
        print(f"Erro ao criar o banco de dados: {err.msg}")
    finally:
        cursor.close()
        connection.close()

# Função para criar as tabelas
def create_tables():
    connection = create_connection(database="aurora_bd")
    cursor = connection.cursor()
    create_customers_table = """
    CREATE TABLE IF NOT EXISTS customers (
        email VARCHAR(255) PRIMARY KEY,
        first_name VARCHAR(255),
        phone VARCHAR(20)
    );
    """
    create_pets_table = """
    CREATE TABLE IF NOT EXISTS pets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        customer_email VARCHAR(255),
        FOREIGN KEY (customer_email) REFERENCES customers(email)
    );
    """
    create_appointments_table = """
    CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INT AUTO_INCREMENT PRIMARY KEY,
        pet_id INT,
        customer_email VARCHAR(255),
        appointment_date DATETIME,
        FOREIGN KEY (pet_id) REFERENCES pets(id),
        FOREIGN KEY (customer_email) REFERENCES customers(email)
    );
    """
    try:
        cursor.execute(create_customers_table)
        cursor.execute(create_pets_table)
        cursor.execute(create_appointments_table)
        print("Tabelas criadas com sucesso!")
    except mysql.connector.Error as err:
        print(f"Erro ao criar as tabelas: {err.msg}")
    finally:
        cursor.close()
        connection.close()

# Função principal
def main():
    create_database()
    create_tables()

if __name__ == "__main__":
    main()
