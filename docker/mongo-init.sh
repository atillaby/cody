#!/bin/bash
set -e

mongosh "$MONGO_INITDB_DATABASE" --authenticationDatabase admin \
    -u "$MONGO_INITDB_ROOT_USERNAME" \
    -p "$MONGO_INITDB_ROOT_PASSWORD" \
    --eval '
    db.createCollection("signals");
    db.createCollection("trades");
    db.createCollection("portfolio");
    db.signals.createIndex({"timestamp": -1});
    db.trades.createIndex({"symbol": 1, "timestamp": -1});
    db.portfolio.createIndex({"timestamp": -1});
    '
