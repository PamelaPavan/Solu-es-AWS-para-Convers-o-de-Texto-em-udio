import json
import os
import re
import urllib.request
from urllib.error import HTTPError, URLError

import boto3
import pymysql
from botocore.exceptions import ClientError
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from cancel_appointment import cancel_appointment
from fetch_appointments import fetch_appointments
from insert_into_db import insert_into_db

# Configurar os clientes boto3
s3 = boto3.client('s3')

# Configurações do banco de dados
db_config = {
    'host': 'HOST',
    'user': 'USER',
    'password': 'PASSWORD',
    'database': 'DATABASE'
}

def generate_audio(phrase):
    print("generate_audio(phrase)",phrase)
    api_url = "APU_URL"
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps({'phrase': phrase}).encode('utf-8')
    req = urllib.request.Request(api_url, data=data, headers=headers)

    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise HTTPError(response.url, response.status, response.msg, response.headers, None)
        response_data = response.read()
        data = json.loads(response_data.decode('utf-8'))

    audio_url = data['url_to_audio']
    return audio_url

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    print(f"Elicit slot {slot_to_elicit} with message: {message}")
    return {
        'sessionState': {
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': {
                'name': intent_name,
                'slots': slots
            }
        },
        'messages': [{
            'contentType': 'PlainText',
            'content': message
        }]
    }

def delegate(intent_request):

    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Delegate'
            },
            'intent': intent_request['sessionState']['intent']
        }
    }
    
def close_with_message(intent_request, fulfillment_state, message, message2):

    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': intent_request['sessionState']['intent']['name'],
                'state': fulfillment_state
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message
            },
            {
                'contentType': 'PlainText',
                'content': message2
            }
        ]
    }
def close(intent_request, fulfillment_state, message):

    return {
        'sessionState': {
            'dialogAction': {
                'type': 'Close'
            },
            'intent': {
                'name': intent_request['sessionState']['intent']['name'],
                'state': fulfillment_state
            }
        },
        'messages': [
            {
                'contentType': 'PlainText',
                'content': message
            }
        ]
    }

def remove_mailto(text):
    pattern = r'<mailto:(.*?\|)(.*?)>'
    result = re.sub(pattern, r'\2', text)
    return result

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def lambda_handler(event, context):

    try:
        intent_name = event['sessionState']['intent']['name']
        slots = event['sessionState']['intent']['slots']

        if intent_name == 'AgendarConsulta':
            
            if event['invocationSource'] == 'FulfillmentCodeHook':
                data = {
                    'nome': slots['nome']['value']['interpretedValue'],
                    'celular': slots['celular']['value']['interpretedValue'],
                    'nomeAnimal': slots['nomeAnimal']['value']['interpretedValue'],
                    'email': slots['email']['value']['originalValue'],
                    'especie': slots['especie']['value']['interpretedValue'],
                    'data': slots['data']['value']['interpretedValue'],
                    'horario': slots['horario']['value']['interpretedValue']
                }
  
                email_novo = remove_mailto(data['email'])
                if is_valid_email(email_novo):
                    data['email'] = email_novo
                else:
                    return elicit_slot(event['sessionState']['sessionAttributes'], intent_name, slots, 'email', f' O e-mail digitado não é válido. Insira um e-mail válido.')
                    
                response = insert_into_db(data)
                if response['statusCode'] == 200:
                    audio_url = generate_audio('Consulta marcada com sucesso')
                    return close_with_message(event, 'Fulfilled', 'Consulta marcada com sucesso!',audio_url)
                else:
                    audio_url = generate_audio('Erro ao inserir os dados no banco de dados.')
                    return close_with_message(event, 'Failed', 'Erro ao inserir os dados no banco de dados.',audio_url)
            else:
                return delegate(event)
            
        if intent_name == 'BuscarConsulta':
   
            if event['invocationSource'] == 'FulfillmentCodeHook':
                data = {
                    'email': slots['email']['value']['interpretedValue']
                }
                
                email_novo = remove_mailto(data['email'])
                
                if is_valid_email(email_novo):
                    data['email'] = email_novo
                else:
                    return elicit_slot(event['sessionState']['sessionAttributes'], intent_name, slots, 'email', f'Insira um email válido.')
                
                response = fetch_appointments(data)
               
                if response['statusCode'] == 200:
                    audio_url = generate_audio('Consulta realizada com sucesso!')
                    message = json.loads(response['body'])
                    return close_with_message(event, 'Fulfilled', message,audio_url)
                elif response['statusCode'] == 404:
                    audio_url = generate_audio('Nenhuma consulta encontrada para o email fornecido.')
                    return close_with_message(event, 'Failed', 'Nenhuma consulta encontrada para o email fornecido.',audio_url)
                else:
                    return close(event, 'Failed', 'Erro ao buscar as consultas no banco de dados.')

            else:
                return delegate(event)
        if intent_name == 'DesmarcarConsulta':

                if event['invocationSource'] == 'FulfillmentCodeHook':
                    data = {
                        'email': slots['email']['value']['interpretedValue'],
                        'pet_id': slots['pet_id']['value']['interpretedValue'],
                        'appointment_id': slots['appointment_id']['value']['interpretedValue']
                    }
                    
                    email_novo = remove_mailto(data['email'])
                    
                    if is_valid_email(email_novo):
                        data['email'] = email_novo
                    else:
                        return elicit_slot(event['sessionState']['sessionAttributes'], intent_name, slots, 'email', f'Insira um email válido.')
                        
                    response = cancel_appointment(data)
                    
                    if response['statusCode'] == 200:
                        audio_url = generate_audio('Consulta cancelada com sucesso!')
                        return close_with_message(event, 'Fulfilled', 'Consulta cancelada com sucesso! \n', audio_url)
                    elif response['statusCode'] == 404:
                        audio_url = generate_audio('Consulta não encontrada.')
                        return close_with_message(event, 'Failed', 'Consulta não encontrada.',audio_url)
                    else:
                        return close(event, 'Failed', 'Erro ao cancelar a consulta no banco de dados.')
                else:
                    return delegate(event)
             
        if intent_name == 'Localizacao':
            audio_url = generate_audio('Avenida Dálmata, nº 101, Bairro Zeca Urubu, Cidade de Garfield!')
            return close(event, 'Fulfilled', audio_url)
                
        return close(event, 'Failed', 'Erro ao processar a intenção.')
                
    except Exception as e:
        return close(event, 'Failed', f"Erro ao processar a intenção: {str(e)}")
    
    