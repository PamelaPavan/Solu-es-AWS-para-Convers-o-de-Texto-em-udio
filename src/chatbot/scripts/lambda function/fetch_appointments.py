
import json

import pymysql

db_config = {
    'host': 'HOST',
    'user': 'USER',
    'password': 'PASSWORD',
    'database': 'DATABASE'
}
def fetch_appointments(data):
    print("fetch_appointments with data:", data)
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # Buscar consultas do cliente
            query = '''
            SELECT appointments.appointment_id, pets.pet_id, pets.name_pet, appointments.appointment_date 
            FROM appointments 
            JOIN pets ON appointments.pet_id = pets.pet_id 
            WHERE appointments.customer_email = %s
            '''
            cursor.execute(query, (data['email'],))
            appointments = cursor.fetchall()
            print("Resultados da consulta:", appointments)
        if not appointments:
            print("Nenhuma consulta encontrada para o email:", data['email'])
            return {
                'statusCode': 404,
                'body': json.dumps("Nenhuma consulta encontrada para o email fornecido.")
            }

        connection.commit()
        print("Consulta realizada com sucesso")

            # Converter datetime para string no formato brasileiro
        def format_datetime_br(datetime_str):
            from datetime import datetime
            dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d/%m/%Y %H:%M:%S')

        appointments = [(appointment[0], appointment[1], appointment[2], format_datetime_br(appointment[3].strftime('%Y-%m-%d %H:%M:%S'))) for appointment in appointments]
        print("Consultas formatadas:", appointments)

        # Criar a mensagem em formato de tabela com colunas alinhadas
        message = "Suas consultas:\n"
        message += "{:<16} | {:<10} | {:<15} | {:<20}\n".format("ID da Consulta", "ID do Pet", "Nome do Pet", "Data da Consulta")
        message += "-" * 65 + "\n"
        for appointment in appointments:
            message += "{:<25} | {:<17} | {:<15} | {:<20}\n".format(appointment[0], appointment[1], appointment[2], appointment[3])

        return {
            'statusCode': 200,
            'body': json.dumps(message)
        }
    except pymysql.MySQLError as e:
        print(f"Erro ao buscar consultas no banco de dados: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erro ao buscar consultas no banco de dados: {str(e)}")
        }
    finally:
        if connection:
            connection.close()
            print("Conexão fechada")
