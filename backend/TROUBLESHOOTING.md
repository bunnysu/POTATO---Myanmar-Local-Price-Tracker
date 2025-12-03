# 🚨 Troubleshooting Guide

This guide will help you resolve common issues with the Potato Backend.

## 🔍 Quick Diagnosis

### 1. Test Database Connection
```bash
python test_db.py
```

### 2. Check Server Health
```bash
curl http://localhost:8000/health
```

### 3. View API Documentation
Open http://localhost:8000/docs in your browser

## 🗄️ Database Issues

### PostgreSQL Connection Failed
**Error**: `connection to server at "localhost" (127.0.0.1), port 5432 failed`

**Solutions**:
1. **Check if PostgreSQL is running**:
   ```bash
   # Windows
   services.msc  # Look for "PostgreSQL" service
   
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   ```

2. **Start PostgreSQL service**:
   ```bash
   # Windows
   net start postgresql-x64-15
   
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   ```

3. **Create the database**:
   ```bash
   python setup_database.py
   ```

### Database Authentication Failed
**Error**: `authentication failed for user "postgres"`

**Solutions**:
1. **Reset PostgreSQL password**:
   ```bash
   # Connect as postgres user
   sudo -u postgres psql
   
   # Set new password
   ALTER USER postgres PASSWORD 'password';
   \q
   ```

2. **Update config.env** with correct credentials

### Database Doesn't Exist
**Error**: `database "potato_db" does not exist`

**Solutions**:
1. **Create database manually**:
   ```bash
   createdb -U postgres potato_db
   ```

2. **Or use the setup script**:
   ```bash
   python setup_database.py
   ```

## 🐍 Python/Dependencies Issues

### Module Not Found
**Error**: `ModuleNotFoundError: No module named 'sqlalchemy'`

**Solutions**:
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Check Python environment**:
   ```bash
   python --version
   pip list | grep fastapi
   ```

### Import Errors
**Error**: `ImportError: cannot import name 'UserRole'`

**Solutions**:
1. **Check file paths**:
   ```bash
   python -c "from app.db.postgres_models import UserRole; print('OK')"
   ```

2. **Verify file structure**:
   ```
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── db/
   │   │   ├── __init__.py
   │   │   ├── postgres_models.py
   │   │   └── database.py
   │   └── ...
   ```

## 🌐 Server Issues

### Port Already in Use
**Error**: `Address already in use`

**Solutions**:
1. **Find process using port 8000**:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # macOS/Linux
   lsof -i :8000
   ```

2. **Kill the process**:
   ```bash
   # Windows
   taskkill /PID <PID> /F
   
   # macOS/Linux
   kill -9 <PID>
   ```

3. **Use different port**:
   ```bash
   uvicorn main:app --reload --port 8001
   ```

### CORS Issues
**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solutions**:
1. **Check CORS configuration** in `main.py`
2. **Verify frontend URL** in CORS settings
3. **Restart backend server**

## 🔐 Authentication Issues

### JWT Token Invalid
**Error**: `Could not validate credentials`

**Solutions**:
1. **Check SECRET_KEY** in config.env
2. **Verify token expiration** settings
3. **Check token format** in request headers

### Login Fails
**Error**: `Incorrect email or password`

**Solutions**:
1. **Check user exists** in database
2. **Verify password hashing** is working
3. **Check database connection**

## 📱 Frontend Issues

### API Calls Fail
**Error**: `Failed to fetch` or `Network Error`

**Solutions**:
1. **Check backend URL** in `frontend/src/lib/api.ts`
2. **Verify backend is running** on port 8000
3. **Check CORS configuration**
4. **Test API endpoints** directly:
   ```bash
   curl http://localhost:8000/api/regions/
   ```

### Registration Form Issues
**Error**: Form validation fails or submission errors

**Solutions**:
1. **Check browser console** for JavaScript errors
2. **Verify form data** matches backend schema
3. **Check network tab** for API response details

## 🛠️ Debugging Steps

### 1. Enable Debug Logging
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. Check Database State
```bash
# Connect to database
psql -U postgres -d potato_db

# List tables
\dt

# Check users
SELECT * FROM users;

# Check regions
SELECT * FROM regions;
```

### 3. Test Individual Components
```bash
# Test database models
python -c "from app.db.postgres_models import User; print('Models OK')"

# Test security functions
python -c "from app.core.security import get_password_hash; print('Security OK')"

# Test API schemas
python -c "from app.schemas.user import UserCreate; print('Schemas OK')"
```

## 📞 Getting Help

### 1. Check Logs
- **Backend logs**: Console output when running server
- **Database logs**: PostgreSQL log files
- **Frontend logs**: Browser developer console

### 2. Common Commands
```bash
# Start backend
python start_backend.py

# Setup database
python setup_database.py

# Test system
python test_db.py

# Seed admin users
python seed_admin_users.py
```

### 3. Verify Installation
```bash
# Check Python version
python --version

# Check pip packages
pip list

# Check PostgreSQL
psql --version

# Check database connection
python -c "from app.db.database import engine; print(engine.execute('SELECT 1').fetchone())"
```

## 🎯 Quick Fix Checklist

- [ ] PostgreSQL service is running
- [ ] Database 'potato_db' exists
- [ ] User 'postgres' has correct password
- [ ] All Python dependencies are installed
- [ ] Backend server is running on port 8000
- [ ] Frontend is pointing to correct backend URL
- [ ] CORS is properly configured
- [ ] JWT secret key is set

## 🚀 Still Having Issues?

1. **Run the test script**: `python test_db.py`
2. **Check the health endpoint**: `http://localhost:8000/health`
3. **Review error logs** carefully
4. **Verify file permissions** and paths
5. **Check firewall/antivirus** settings
6. **Try a different port** if 8000 is blocked

Remember: Most issues are related to database connectivity or missing dependencies. Start with the database setup script!



