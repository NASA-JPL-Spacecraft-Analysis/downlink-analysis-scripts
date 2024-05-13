def parse_commands(data: dict, collection_id: str) -> list:
    commands = []
    commands_data = data['command_dictionary']['command_definitions']['fsw_command']
    for command in commands_data:
        command_data = {}
        command_data['collectionId'] = collection_id
        command_data['type'] = 'command'
        command_data['editable'] = True
        for key, value in command.items():
            if key == '@stem':
                command_data['displayName'] = value
                command_data['identifier'] = value
            if key == 'description':
                description = value
            if key == 'categories':
                category = value.get('ops_category')
            if key == '@class':
                command_class = value
        command_data['description'] = f'{command_class} {category} {description}'
        commands.append(command_data)
        
    return commands