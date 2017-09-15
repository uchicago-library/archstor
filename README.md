# archstor

v0.0.1

[![Build Status](https://travis-ci.org/bnbalsamo/archstor.svg?branch=master)](https://travis-ci.org/bnbalsamo/archstor) [![Coverage Status](https://coveralls.io/repos/github/bnbalsamo/archstor/badge.svg?branch=master)](https://coveralls.io/github/bnbalsamo/archstor?branch=master)

Archstor is a web API wrapper which provides a simplified API for several object storage backends/interfaces.

# Debug Quickstart
Set environmental variables appropriately
```
./debug.sh
```

# Docker Quickstart
Inject environmental variables appropriately at either buildtime or runtime
```
# docker build . -t archstor
# docker run -p 5000:80 archstor --name my_archstor
```

# Endpoints
## /
### GET
#### Parameters
* None
#### Returns
* JSON: {"status": "Not broken!"}

# Environmental Variables
* None

# Author
Brian Balsamo <brian@brianbalsamo.com>
