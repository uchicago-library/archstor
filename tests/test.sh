#! /bin/bash

# Silly little bash tests for absolute minimum functionality

if [[ $1 == "" ]]; then echo "Must supply an API root. Exiting." && exit; fi

first_id=$RANDOM
second_id=$RANDOM

echo "The following output should be the expected JSON responses to POSTs"

curl -s -X PUT $1$first_id -F "object"=@dummy1 
curl -s -X PUT $1$second_id -F "object"=@dummy2
curl -s -X GET $1$first_id > dl_dummy1
if [[ `md5sum dl_dummy1 | awk '{print $1}'` == `md5sum dummy1 | awk '{print $1}'` ]]; then echo "Pass"; else echo "Fail"; fi
curl -s -X GET $1$second_id > dl_dummy2
if [[ `md5sum dl_dummy2 | awk '{print $1}'` == `md5sum dummy2 | awk '{print $1}'` ]]; then echo "Pass"; else echo "Fail"; fi
curl -s -X GET $1 > archstor_listing.json
echo "Listing should be in a file called archstor_listing.json - Look at it to be sure it makes sense"
