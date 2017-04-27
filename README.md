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

## On the docket

- s3
- swift
