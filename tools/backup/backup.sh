#!/usr/bin/env bash
while [ 1 ]; do

    filename=backup-$(date +%Y-%m-%d)

    echo 'Making a backup.'
    mkdir $filename
    pg_dump $DATABASE_URI -f $filename/database.sql

    echo 'Compressing backup.'
    tar cfzv $filename.tar.xz $filename
    rm -rf $filename

    echo 'Uploading backup.'
    s3cmd put $filename.tar.xz $S3_URL/$filename.tar.xz
    rm $filename.tar.xz

    echo 'Waiting one day.'
    sleep 1d

done
