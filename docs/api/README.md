# API Documentation

## Overview

The QuantHybrid API provides programmatic access to the trading system's functionality through a RESTful API and WebSocket connections.

## Authentication

### Obtain Access Token

```http
POST /api/auth/login
```

Request:
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

### Authentication Header

Include the token in all API requests:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## REST API Endpoints

### Market Data

#### Get Latest Price

```http
GET /api/market-data/{symbol}/price
```

Response:
```json
{
    "symbol": "RELIANCE",
    "price": 2500.50,
    "timestamp": "2025-08-16T10:30:00Z"
}
```

#### Get Historical Data

```http
GET /api/market-data/{symbol}/history
```

Parameters:
- `start_date`: ISO date string
- `end_date`: ISO date string
- `interval`: string (1m, 5m, 1h, 1d)

Response:
```json
{
    "symbol": "RELIANCE",
    "data": [
        {
            "timestamp": "2025-08-16T10:30:00Z",
            "open": 2500.0,
            "high": 2505.0,
            "low": 2498.0,
            "close": 2503.0,
            "volume": 10000
        }
    ]
}
```

### Trading

#### Place Order

```http
POST /api/orders
```

Request:
```json
{
    "symbol": "RELIANCE",
    "quantity": 100,
    "side": "BUY",
    "order_type": "MARKET",
    "price": 2500.0,
    "time_in_force": "DAY"
}
```

Response:
```json
{
    "order_id": "ord_123456",
    "status": "PENDING",
    "timestamp": "2025-08-16T10:30:00Z"
}
```

#### Get Order Status

```http
GET /api/orders/{order_id}
```

Response:
```json
{
    "order_id": "ord_123456",
    "symbol": "RELIANCE",
    "quantity": 100,
    "side": "BUY",
    "order_type": "MARKET",
    "status": "EXECUTED",
    "executed_price": 2500.0,
    "timestamp": "2025-08-16T10:30:00Z"
}
```

#### Cancel Order

```http
DELETE /api/orders/{order_id}
```

Response:
```json
{
    "order_id": "ord_123456",
    "status": "CANCELLED",
    "timestamp": "2025-08-16T10:31:00Z"
}
```

### Positions

#### Get All Positions

```http
GET /api/positions
```

Response:
```json
{
    "positions": [
        {
            "symbol": "RELIANCE",
            "quantity": 100,
            "average_price": 2500.0,
            "current_price": 2550.0,
            "unrealized_pnl": 5000.0
        }
    ]
}
```

#### Get Position Details

```http
GET /api/positions/{symbol}
```

Response:
```json
{
    "symbol": "RELIANCE",
    "quantity": 100,
    "average_price": 2500.0,
    "current_price": 2550.0,
    "unrealized_pnl": 5000.0,
    "day_pnl": 3000.0,
    "last_updated": "2025-08-16T10:30:00Z"
}
```

### Portfolio

#### Get Portfolio Summary

```http
GET /api/portfolio/summary
```

Response:
```json
{
    "total_equity": 1000000.0,
    "cash_balance": 500000.0,
    "margin_used": 250000.0,
    "day_pnl": 15000.0,
    "total_pnl": 50000.0
}
```

#### Get Performance Metrics

```http
GET /api/portfolio/metrics
```

Response:
```json
{
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.15,
    "win_rate": 0.65,
    "profit_factor": 1.8
}
```

### Strategy Management

#### Get Active Strategies

```http
GET /api/strategies
```

Response:
```json
{
    "strategies": [
        {
            "id": "strat_001",
            "name": "MA_Crossover",
            "status": "ACTIVE",
            "symbols": ["RELIANCE", "TCS"],
            "performance": {
                "day_pnl": 5000.0,
                "total_pnl": 15000.0
            }
        }
    ]
}
```

#### Update Strategy Parameters

```http
PUT /api/strategies/{strategy_id}
```

Request:
```json
{
    "parameters": {
        "short_window": 10,
        "long_window": 30
    }
}
```

Response:
```json
{
    "strategy_id": "strat_001",
    "status": "UPDATED",
    "parameters": {
        "short_window": 10,
        "long_window": 30
    }
}
```

## WebSocket API

### Market Data Stream

Connect to:
```
ws://your-server/ws/market-data
```

Subscribe message:
```json
{
    "action": "subscribe",
    "symbols": ["RELIANCE", "TCS"]
}
```

Data message:
```json
{
    "type": "tick",
    "symbol": "RELIANCE",
    "data": {
        "price": 2500.5,
        "volume": 1000,
        "timestamp": "2025-08-16T10:30:00.123Z"
    }
}
```

### Order Updates Stream

Connect to:
```
ws://your-server/ws/orders
```

Data message:
```json
{
    "type": "order_update",
    "order_id": "ord_123456",
    "status": "EXECUTED",
    "executed_price": 2500.0,
    "timestamp": "2025-08-16T10:30:00Z"
}
```

## Rate Limits

- REST API: 100 requests per minute per user
- WebSocket: No rate limit for market data
- Order submission: 10 orders per second per user

## Error Codes

```json
{
    "400": "Bad Request - Invalid parameters",
    "401": "Unauthorized - Invalid or missing token",
    "403": "Forbidden - Insufficient permissions",
    "404": "Not Found - Resource doesn't exist",
    "429": "Too Many Requests - Rate limit exceeded",
    "500": "Internal Server Error",
    "503": "Service Unavailable - System maintenance"
}
```

## Best Practices

1. **Connection Management**
   - Implement reconnection logic for WebSocket
   - Handle connection drops gracefully
   - Maintain heartbeat mechanism

2. **Error Handling**
   - Implement exponential backoff for retries
   - Handle rate limits appropriately
   - Log all API errors for troubleshooting

3. **Data Management**
   - Cache frequently used data
   - Implement proper data serialization
   - Handle timezone conversions properly

## Support

For API support:
- Email: api-support@quantsystem.com
- Documentation: http://docs.quantsystem.com/api
- Status: http://status.quantsystem.com
