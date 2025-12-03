# 🗄️ Three Database Workflow - Detailed Explanation

## 📋 Overview

Your Potato project uses **three different databases** working together, each with a specific purpose. Think of it like a well-organized kitchen where different tools handle different tasks.

---

## 🏗️ Database Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │    MongoDB      │    │     Redis       │
│   (Primary DB)  │    │  (Secondary DB) │    │  (Cache Layer)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   User Accounts          Price Entries           Session Data
   Shop Information       Reports                Notifications
   Categories             Dynamic Content        Background Tasks
   Locations              Price History          Real-time Data
```

---

## 1. 🐘 PostgreSQL (Primary Database)

### **What it stores:**
- **User accounts** (login, registration, profiles)
- **Shop information** (shop names, locations, owners)
- **Categories** (Oils & Spices, Grains & Cereals, etc.)
- **Items** (Rice, Oil, Tomatoes, etc.)
- **Regions & Townships** (Yangon, Mandalay, etc.)
- **User relationships** (who owns which shop)

### **Why PostgreSQL?**
- **ACID Compliance** - Ensures data is always consistent
- **Complex Relationships** - Can handle complex connections between users, shops, and locations
- **PostGIS Extension** - Perfect for location-based data (coordinates, distances)

### **Example Data Structure:**
```sql
-- Users table
users: id, email, password_hash, full_name, role, region_id

-- Shops table  
shops: id, shop_name, owner_id, township_id, created_at

-- Items table
items: id, name, category_id, default_unit

-- Categories table
categories: id, name, description
```

---

## 2. 🍃 MongoDB (Secondary Database)

### **What it stores:**
- **Price entries** (actual price data)
- **Reports** (user reports about wrong prices)
- **Dynamic content** (data that changes frequently)
- **Price history** (historical price trends)

### **Why MongoDB?**
- **Flexibility** - Can store different types of price data without rigid structure
- **Performance** - Fast for reading large amounts of price data
- **JSON-like** - Natural fit for varied price entry structures

### **Example Data Structure:**
```json
// Price Entry Document
{
  "_id": "ObjectId('...')",
  "itemId": 123,
  "price": 2500,
  "unit": "kg",
  "type": "RETAIL",
  "timestamp": "2024-01-15T10:30:00Z",
  "location": {
    "township_id": 5,
    "region_id": 1,
    "township_name": "Hlaing",
    "region_name": "Yangon"
  },
  "submittedBy": {
    "id": 456,
    "full_name": "John Doe",
    "role": "CONTRIBUTOR"
  },
  "shopId": 789,
  "shop_name": "ABC Market"
}
```

---

## 3. 🔴 Redis (Caching Layer)

### **What it stores:**
- **User sessions** (who is logged in)
- **Frequently accessed data** (cached results)
- **Background task queue** (Celery tasks)
- **Real-time notifications** (price alerts)

### **Why Redis?**
- **Speed** - In-memory storage (very fast)
- **Real-time** - Perfect for live data
- **Message Broker** - Handles background tasks

### **Example Data Structure:**
```redis
# User Session
session:user_123 = {
  "user_id": 123,
  "email": "user@example.com",
  "role": "USER",
  "last_activity": "2024-01-15T10:30:00Z"
}

# Cached Price Data
cache:prices:item_123:region_1 = [
  {"price": 2500, "shop": "ABC Market"},
  {"price": 2600, "shop": "XYZ Store"}
]

# Background Task Queue
celery:tasks = [
  "send_notification:user_456:price_alert",
  "update_price_history:item_123"
]
```

---

## 🔄 How They Work Together

### **Scenario 1: User Adds a Price Entry**

```
1. User logs in → Redis checks session
2. User submits price → FastAPI receives data
3. PostgreSQL validates user permissions
4. MongoDB stores the price entry
5. Redis triggers background tasks
6. PostgreSQL updates shop statistics
```

### **Scenario 2: User Views Prices**

```
1. User searches for rice prices → FastAPI receives request
2. Redis checks for cached results
3. If not cached → MongoDB queries price entries
4. PostgreSQL gets shop and item details
5. Redis caches the results
6. User sees prices with shop information
```

### **Scenario 3: Price Alert System**

```
1. New price added → MongoDB stores entry
2. Redis queue receives alert task
3. Background worker processes task
4. PostgreSQL finds users who favorited this shop
5. Redis sends notifications to users
6. Users receive real-time alerts
```

---

## 📊 Data Flow Examples

### **When a Contributor Adds a Price:**

```python
# 1. Check user session (Redis)
session = redis.get(f"session:user_{user_id}")

# 2. Validate user permissions (PostgreSQL)
user = db.query(User).filter(User.id == user_id).first()
if user.role not in ["CONTRIBUTOR", "RETAILER", "ADMIN"]:
    raise HTTPException(403, "Not authorized")

# 3. Store price entry (MongoDB)
price_doc = {
    "itemId": item_id,
    "price": price,
    "type": price_type,
    "timestamp": datetime.now(),
    "submittedBy": {"id": user_id, "name": user.full_name}
}
mongodb.collection("price_entries").insert_one(price_doc)

# 4. Queue background tasks (Redis)
redis.lpush("celery:tasks", "create_price_alerts")
redis.lpush("celery:tasks", "update_price_history")
```

### **When a User Searches Prices:**

```python
# 1. Check cache first (Redis)
cached_results = redis.get(f"prices:item_{item_id}:region_{region_id}")
if cached_results:
    return json.loads(cached_results)

# 2. Query MongoDB for prices
prices = mongodb.collection("price_entries").find({
    "itemId": item_id,
    "location.region_id": region_id
}).sort("timestamp", -1).limit(50)

# 3. Get shop details from PostgreSQL
shop_ids = [p["shopId"] for p in prices if p.get("shopId")]
shops = db.query(Shop).filter(Shop.id.in_(shop_ids)).all()

# 4. Cache results (Redis)
redis.setex(f"prices:item_{item_id}:region_{region_id}", 300, json.dumps(results))
```

---

## 🎯 Why This Architecture?

### **Benefits:**

1. **Performance** - Each database is optimized for its specific task
2. **Scalability** - Can handle large amounts of data efficiently
3. **Flexibility** - Easy to add new features without changing existing data
4. **Reliability** - If one database fails, others can still work
5. **Real-time** - Fast responses for user interactions

### **Real-world Analogy:**

Think of it like a **restaurant kitchen**:

- **PostgreSQL** = **Recipe Book** (structured, reliable, permanent)
  - Contains all the recipes, ingredient lists, staff information
  
- **MongoDB** = **Daily Specials Board** (flexible, changes often)
  - Contains today's prices, special offers, customer orders
  
- **Redis** = **Kitchen Counter** (fast access, temporary)
  - Contains current orders, chef's notes, immediate tasks

---

## 🔧 Technical Implementation

### **Connection Setup:**

```python
# PostgreSQL (SQLAlchemy)
from sqlalchemy import create_engine
engine = create_engine("postgresql://user:pass@localhost/potato_db")

# MongoDB (Motor - async)
from motor.motor_asyncio import AsyncIOMotorClient
mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")

# Redis
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
```

### **Data Synchronization:**

```python
# When price is added
async def add_price_entry(price_data):
    # 1. Store in MongoDB
    mongo_result = await mongo_collection.insert_one(price_data)
    
    # 2. Update PostgreSQL statistics
    await update_shop_statistics(price_data.shop_id)
    
    # 3. Queue Redis tasks
    redis_client.lpush("tasks", "send_notifications")
    redis_client.lpush("tasks", "update_cache")
```

---

## 🚨 Common Questions

### **Q: Why not use just one database?**
**A:** Each database is optimized for different types of data:
- PostgreSQL: Structured, relational data
- MongoDB: Flexible, document-based data  
- Redis: Fast, temporary data

### **Q: What happens if one database fails?**
**A:** The system can still function partially:
- If Redis fails: Users need to log in again, but core features work
- If MongoDB fails: Can't add new prices, but existing data is still accessible
- If PostgreSQL fails: Can't register users, but price viewing still works

### **Q: How do you keep data consistent?**
**A:** Through careful application logic:
- Primary data goes to the appropriate database
- Background tasks synchronize data between databases
- Cache invalidation ensures fresh data

---

## 📈 Performance Benefits

### **Speed Comparison:**
- **PostgreSQL**: ~10-50ms for complex queries
- **MongoDB**: ~5-20ms for document queries  
- **Redis**: ~1-5ms for cached data

### **Storage Efficiency:**
- **PostgreSQL**: Optimized for structured data
- **MongoDB**: Flexible schema, good for varied data
- **Redis**: In-memory, very fast but limited storage

---

## 🎓 Learning Points

### **What You've Learned:**
1. **Database Design** - Choosing the right tool for each job
2. **System Architecture** - How different components work together
3. **Performance Optimization** - Using caching and specialized databases
4. **Data Modeling** - Structuring data for different use cases
5. **Real-world Applications** - How modern systems handle complex data

### **Why This Matters:**
- **Scalability** - Your system can handle thousands of users
- **Performance** - Fast response times for better user experience
- **Maintainability** - Easy to add new features
- **Reliability** - System continues working even if parts fail

---

## 💡 Presentation Tips

### **When explaining to your teacher:**

1. **Start with the problem** - "We need to handle different types of data efficiently"
2. **Use analogies** - "Like a restaurant kitchen with different tools"
3. **Show the flow** - "When a user adds a price, here's what happens..."
4. **Emphasize benefits** - "This makes our system fast, reliable, and scalable"
5. **Demonstrate understanding** - "Each database has a specific purpose"

### **Key Points to Highlight:**
- ✅ You understand when to use each database
- ✅ You can explain the data flow
- ✅ You know how they work together
- ✅ You understand the benefits of this architecture
- ✅ You can handle real-world scenarios

This three-database architecture is a **modern, scalable solution** that shows you understand **enterprise-level system design**! 🚀
