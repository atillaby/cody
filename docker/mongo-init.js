db.auth('admin', 'admin123')

db = db.getSiblingDB('admin');

db.createUser({
  user: 'admin',
  pwd: 'admin123',
  roles: [
    { role: 'userAdminAnyDatabase', db: 'admin' },
    { role: 'readWriteAnyDatabase', db: 'admin' },
    { role: 'dbAdminAnyDatabase', db: 'admin' }
  ]
});

db = db.getSiblingDB('trading_bot');

db.createUser({
  user: 'admin',
  pwd: 'admin123',
  roles: [
    { role: 'readWrite', db: 'trading_bot' },
    { role: 'dbAdmin', db: 'trading_bot' }
  ]
});

// Collections
db.createCollection('signals');
db.createCollection('trades');
db.createCollection('portfolio');

// Indexes
db.signals.createIndex({ "timestamp": -1 });
db.trades.createIndex({ "symbol": 1, "timestamp": -1 });
db.portfolio.createIndex({ "timestamp": -1 });
