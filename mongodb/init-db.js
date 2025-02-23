db = db.getSiblingDB('trading_bot');

// Create user if not exists
if (!db.getUser("admin")) {
    db.createUser({
        user: "admin",
        pwd: "admin123",
        roles: [
            { role: "readWrite", db: "trading_bot" },
            { role: "dbAdmin", db: "trading_bot" }
        ]
    });
}

// Create collections
db.createCollection("signals");
db.createCollection("trades");
db.createCollection("portfolio");

// Create indexes
db.signals.createIndex({ "timestamp": -1 });
db.trades.createIndex({ "symbol": 1, "timestamp": -1 });
db.portfolio.createIndex({ "timestamp": -1 });
