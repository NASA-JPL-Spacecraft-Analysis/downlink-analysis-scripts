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


def parse_fault_monitors(data: dict, collection_id: str) -> list:
    fault_monitors = []
    monitors = data['monitor_response_dictionary']['monitors']['monitor']
    for monitor in monitors:
        fault_data = {}
        fault_data['collectionId'] = collection_id
        fault_data['type'] = 'guideline'
        fault_data['editable'] = True
        for key, value in monitor.items():
            if key == '@monitor_id':
                fault_data['identifier'] = value
            if key == '@monitor_name':
                fault_data['displayName'] = value
            if key == 'categories':
                category = value.get('ops_category')
            if key == '@monitor_description':
                description = value
        fault_data['description'] = f'{category} {description}'
        fault_monitors.append(fault_data)
        
    return fault_monitors