.PHONY: build run
REPO=cae-artifactory.jpl.nasa.gov:16002/gov/nasa/jpl/eurc/gds/fspa

IMAGE=transpire_dps
CONTAINER=transpire_dps
VERSION=latest
CWD=$(shell pwd)

FSW_DICTS=$(CWD)/fsw_dicts
# flight machines probably use the below directory for fsw dictionaries
# FSW_DICTS=/dict/

build:
	docker build \
	-t $(REPO)/$(IMAGE):$(VERSION) .

run:
	docker run -d \
	--dns=137.78.160.19 \
	--dns-search=jpl.nasa.gov \
	--env-file ./transpire_dps.env \
	-v $(CWD):/transpire_dps \
	-v $(FSW_DICTS):/transpire_dps/fsw_dicts \
	--name $(CONTAINER) \
	$(REPO)/$(IMAGE):$(VERSION)

clean:
	docker rm -f $(CONTAINER)

update:
	$(MAKE) build

shell:
	docker exec -it $(CONTAINER) /bin/bash

log:
	docker logs -f $(CONTAINER)
