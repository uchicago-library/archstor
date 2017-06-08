# Archstor
[![Build Status](https://travis-ci.org/bnbalsamo/archstor.svg?branch=master)](https://travis-ci.org/bnbalsamo/archstor) [![Coverage Status](https://coveralls.io/repos/github/bnbalsamo/archstor/badge.svg?branch=master)](https://coveralls.io/github/bnbalsamo/archstor?branch=master)
(Note: Coverage status out of coveralls looks crummy, as it's not testing any of the swift backend code (though it has tests which pass in local environments) or the rough draft s3 code which is inaccessible at the moment.)

## About

Archstor is a web API wrapper which provides a simplified API for several object storage backends/interfaces.

## Endpoints

### /

#### GET

##### Args

- offset (int): A listing offset
- limit (int): A suggested number of returned listing values

##### Returns

```{"objects": ["identifier": <object_id>, "_link": <object_link> for each object in the listing], "pagination": {"cursor": <listing_cursor>, "limit": <listing_limit>, "next_cursor": <next_cursor_to_continue_listing>}}```



---

### /\<string:identifier\>

#### GET

##### Returns

The object bytestream


#### PUT

##### Args

- object: The bytestream to store

##### Returns

```{"identifier": <id>, "added": True}```

#### DELETE

##### Returns

```{"identifier": <id>, "deleted": True}```

## Currently Supported Backends

- GridFS
- swift

## On the docket

- s3
