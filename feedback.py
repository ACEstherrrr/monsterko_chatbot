
import boto3


dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
table = dynamodb.Table('Monster_DB')

def feedback(user_id, user_input, intent):
	table.put_item(Item = {'Function': 'Feedback', 'Course': user_input, 'id': user_id, 'intent': intent})
