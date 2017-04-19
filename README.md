# Archstor

## About

Archstor is a web API wrapper which provides a simplified API for several object storage backends/interfaces.

## Endpoints

### /

#### GET

##### Args

- offset (int): A listing offset
- limit (int): A suggested number of returned listing values

##### Returns

```{"objects": ["identifier": <object_id>, "_link": <object_link> for each object in the listing], "offset": <listing_offset>, "limit": <listing_limit>}```



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

## Currently Supported Backends

- GridFS

## On the docket

- s3
- swift
