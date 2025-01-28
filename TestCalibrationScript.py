import json

message = input("Fill in message: ")

data = {
    'message': message
}

with open('test.json', 'w') as f:
    json.dump(data, f)

