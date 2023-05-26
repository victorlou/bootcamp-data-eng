import boto3

client = boto3.client('sqs')
response = client.receive_message(
    QueueUrl='https://sqs.us-east-1.amazonaws.com/695099411134/api-pagamentos-consumidor-criado')
print(response)