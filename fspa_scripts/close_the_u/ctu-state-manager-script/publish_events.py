def parse_evr(data: dict, collection_id: str) -> list:
    evr_events = []
    events = data['evr_dictionary']['evrs']['evr']
    for event in events:
        evr_data = {}
        evr_data['collectionId'] = collection_id
        evr_data['type'] = 'evr'
        for key, value in event.items():
            if key == '@id':
                evr_data['identifier'] = value
            if key == '@name':
                evr_data['displayName'] = value
            # ask Dan about this
            # if key == '@version':
            #     evr_data['version'] = value
            if key == 'format_message':
                format_message = value
            if key == '@level':
                level = value
            if key == 'categories':
                category = value.get('ops_category')
        evr_data['description'] = f'{level} {category} {format_message}'
        evr_events.append(evr_data)
        
    return evr_events