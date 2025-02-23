#!/bin/bash
set -e

mongosh --eval "
  db.getSiblingDB('admin').createUser({
    user: '$MONGO_INITDB_ROOT_USERNAME',
    pwd: '$MONGO_INITDB_ROOT_PASSWORD',
    roles: ['root']
  });

  db.getSiblingDB('$MONGO_INITDB_DATABASE').createUser({
    user: '$MONGO_INITDB_ROOT_USERNAME',
    pwd: '$MONGO_INITDB_ROOT_PASSWORD',
    roles: ['readWrite', 'dbAdmin']
  });

  db.getSiblingDB('$MONGO_INITDB_DATABASE').createCollection('signals');
  db.getSiblingDB('$MONGO_INITDB_DATABASE').createCollection('trades');
  db.getSiblingDB('$MONGO_INITDB_DATABASE').createCollection('portfolio');
"
