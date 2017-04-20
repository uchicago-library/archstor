#! /bin/bash

# Silly little bash tests for absolute minimum functionality

api_root=$1
first_id=$RANDOM
second_id=$RANDOM

echo "api url: $api_root"
echo "first id: $first_id"
echo "second_id: $second_id"
echo "PUT: $1$first_id"
curl -s -X PUT $1$first_id -F "object"=@dummy1
echo "GET: $1$first_id"
curl -s -X GET $1$first_id > dl_dummy1
if [[ `md5sum dl_dummy1 | awk '{print $1}'` == `md5sum dummy1 | awk '{print $1}'` ]]; then echo "Pass"; else echo "Fail"; fi
echo "PUT: $1$second_id"
curl -s -X PUT $1$second_id -F "object"=@dummy2
echo "GET: $1$second_id"
curl -s -X GET $1$second_id > dl_dummy2
if [[ `md5sum dl_dummy2 | awk '{print $1}'` == `md5sum dummy2 | awk '{print $1}'` ]]; then echo "Pass"; else echo "Fail"; fi
curl -s -X GET $api_root > archstor_listing.json
echo "Listing should be a file called archstor_listing.json - Look at it to be sure it makes sense"
