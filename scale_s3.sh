#!/bin/sh
for i in `seq 1 10`;
do
    deis scale s3=$i;
    sleep 5;
done
