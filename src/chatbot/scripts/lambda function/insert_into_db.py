import json

import pymysql

# Função para inserir dados no banco de dados
# Configurações do banco de dados
db_config = {
    'host': 'HOST',
    'user': 'USER',
    'password': 'PASSWORD',
    'database': 'DATABASE'
}
def insert_into_db(data):
    print("insert_into_db with data:", data)
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # Inserir ou atualizar registro na tabela customers
            customer_query = '''
            INSERT INTO customers (email, first_name, phone) 
            VALUES (%s, %s, %s) 
            ON DUPLICATE KEY UPDATE first_name=%s, phone=%s
            '''
            cursor.execute(customer_query, (data['email'], data['nome'], data['celular'], data['nome'], data['celular']))
            
            # Inserir na tabela pets, se não existir
            pet_query = '''
            INSERT INTO pets (customer_email, name_pet, species) 
            SELECT %s, %s, %s 
            FROM DUAL 
            WHERE NOT EXISTS (
                SELECT * FROM pets WHERE customer_email = %s AND name_pet = %s AND species = %s
            )
            '''
            cursor.execute(pet_query, (data['email'], data['nomeAnimal'], data['especie'], data['email'], data['nomeAnimal'], data['especie']))
            
            # Obter o ID do pet
            cursor.execute('SELECT pet_id FROM pets WHERE customer_email = %s AND name_pet = %s AND species = %s', 
                            (data['email'], data['nomeAnimal'], data['especie']))
            pet_id = cursor.fetchone()[0]

            # Inserir na tabela appointments, se não existir
            appointment_query = '''
            INSERT INTO appointments (pet_id, customer_email, appointment_date) 
            SELECT %s, %s, %s 
            FROM DUAL 
            WHERE NOT EXISTS (
                SELECT * FROM appointments WHERE pet_id = %s AND customer_email = %s AND appointment_date = %s
            )
            '''
            appointment_datetime = f"{data['data']} {data['horario']}"
            cursor.execute(appointment_query, (pet_id, data['email'], appointment_datetime, pet_id, data['email'], appointment_datetime))

        connection.commit()

    except pymysql.MySQLError as e:
        print(f"Erro ao inserir no banco de dados: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erro ao inserir no banco de dados: {str(e)}")
        }
    finally:
        connection.close()
    print("inserido")
    return {
        'statusCode': 200,
        'body': json.dumps("Dados inseridos com sucesso")
    }
