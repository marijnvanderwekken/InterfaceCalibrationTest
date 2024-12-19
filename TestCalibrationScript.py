import json

message = input("Fill in message: ")
statuscode = input("Fill in statuscode: ")    
data = {
    'message': message,
    'statuscode': statuscode
}

with open('test.json', 'w') as f:
    json.dump(data, f)

