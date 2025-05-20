import json

import pymysql

# Configurações do banco de dados
db_config = {
    'host': 'HOST',
    'user': 'USER',
    'password': 'PASSWORD',
    'database': 'DATABASE'
}
def cancel_appointment(data):
        print("cancel_appointment with data:", data)
        print(f"Email: {data['email']}, Pet ID: {data['pet_id']}, Appointment ID: {data['appointment_id']}")

        try:
            connection = pymysql.connect(**db_config)
            with connection.cursor() as cursor:
                # Cancelar consulta
                query = '''
                DELETE a 
                FROM appointments a
                JOIN pets p ON a.pet_id = p.pet_id
                WHERE a.customer_email = %s AND p.pet_id = %s AND a.appointment_id = %s
                '''
                cursor.execute(query, (data['email'], data['pet_id'], data['appointment_id']))

            connection.commit()
            if cursor.rowcount > 0:
                return {
                    'statusCode': 200,
                    'body': json.dumps("Consulta cancelada com sucesso")
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps("Consulta não encontrada")
                }

        except pymysql.MySQLError as e:
            print(f"Erro ao cancelar consulta no banco de dados: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps(f"Erro ao cancelar consulta no banco de dados: {str(e)}")
            }
        finally:
            connection.close()