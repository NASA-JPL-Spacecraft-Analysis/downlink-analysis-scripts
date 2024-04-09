import close_the_u
ENVIRONMENT = 'dev'

def parse_flight_rules(data: dict, collection_id: str) -> list:
    flight_rules = []
    rules = data['flight_rules']['flight_rule']
    for rule in rules:
        rule_data = {}
        rule_data['collectionId'] = collection_id
        rule_data['type'] = 'flight_rule_check'
        rule_data['editable'] = True
        for key, value in rule.items():
            if key == '@flight_rule_title':
                rule_data['displayName'] = value
            if key == '@flight_rule_id':
                rule_data['identifier'] = value
            if key == 'description':
                description = value
            if key == '@level':
                level = value
            if key == '@operational_category':
                category = value
        rule_data['description'] = f'{level} {category} {description}'
        flight_rules.append(rule_data)
        
    return flight_rules

def create_constraints(collection_id: str, constraints: list):
    close_the_u.state_manager.create_constraints(collection_id, constraints, ENVIRONMENT)