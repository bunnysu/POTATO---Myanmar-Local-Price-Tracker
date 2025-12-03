# 🚀 Potato Backend Startup Guide

This guide will help you get the Potato Backend up and running quickly.

## 📋 Prerequisites

- Python 3.8+ installed
- PostgreSQL installed and running
- pip (Python package manager)

## 🗄️ Step 1: Database Setup

### Option A: Automatic Setup (Recommended)
```bash
cd backend
python setup_database.py
```

### Option B: Manual Setup
1. **Create database**:
   ```bash
   createdb -U postgres potato_db
   ```

2. **Set PostgreSQL password** (if needed):
   ```bash
   psql -U postgres
   ALTER USER postgres PASSWORD 'password';
   \q
   ```

## 📦 Step 2: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 🧪 Step 3: Test the System

```bash
python test_db.py
```

This will test:
- Database connection
- Model imports
- Security functions

## 🚀 Step 4: Start the Server

### Option A: Using Startup Script (Recommended)
```bash
python start_backend.py
```

### Option B: Manual Start
```bash
cd backend/app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## ✅ Step 5: Verify Everything Works

1. **Check server health**: http://localhost:8000/health
2. **View API docs**: http://localhost:8000/docs
3. **Test registration**: http://localhost:8000/api/users/register

## 🔑 Step 6: Create Admin Users (Optional)

```bash
cd backend
python seed_admin_users.py
```

This creates:
- **Admin**: `admin@potato.com` / `admin123`
- **Contributor**: `contributor@potato.com` / `contributor123`

## 🌐 Frontend Integration

1. **Start frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

2. **Test registration** at: http://localhost:5173/register

## 🚨 Common Issues & Solutions

### Database Connection Failed
- Check if PostgreSQL is running
- Verify database credentials in `config.env`
- Run `python setup_database.py`

### Port Already in Use
- Kill process using port 8000
- Or use different port: `--port 8001`

### Import Errors
- Check file structure
- Run `pip install -r requirements.txt`
- Verify Python path

## 📱 Testing the Registration System

1. **Open browser** to: http://localhost:5173/register
2. **Fill out form** with test data
3. **Choose user type** (General User or Retailer)
4. **Complete registration**
5. **Check backend logs** for success/errors

## 🔍 Debugging

- **Backend logs**: Console output when running server
- **Database logs**: Check PostgreSQL logs
- **Frontend logs**: Browser developer console
- **API testing**: Use http://localhost:8000/docs

## 📞 Need Help?

1. **Check troubleshooting guide**: `TROUBLESHOOTING.md`
2. **Run test script**: `python test_db.py`
3. **Check health endpoint**: http://localhost:8000/health
4. **Review error messages** carefully

## 🎯 Quick Commands Reference

```bash
# Setup everything
python setup_database.py
python start_backend.py

# Test system
python test_db.py

# Create admin users
python seed_admin_users.py

# Manual server start
cd app && uvicorn main:app --reload --port 8000
```

## 🎉 Success Indicators

- ✅ Database connection successful
- ✅ Server running on http://localhost:8000
- ✅ Health endpoint returns "healthy"
- ✅ Frontend can connect to backend
- ✅ Registration form works
- ✅ Users can be created in database

---

**Happy coding! 🥔✨**



