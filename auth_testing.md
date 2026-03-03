# Auth-Gated App Testing Playbook

## Step 1: Create Test User & Session
```bash
mongosh --eval "
use('sous_chef_linguini_db');
var userId = 'test-user-' + Date.now();
var sessionToken = 'test_session_' + Date.now();
db.users.insertOne({
  user_id: userId,
  email: 'test.user.' + Date.now() + '@example.com',
  username: 'testuser',
  name: 'Test User',
  avatar_url: 'https://via.placeholder.com/150',
  provider: 'local',
  role: 'user',
  is_verified: true,
  created_at: new Date(),
  last_login: new Date()
});
db.user_sessions.insertOne({
  user_id: userId,
  session_token: sessionToken,
  expires_at: new Date(Date.now() + 7*24*60*60*1000),
  created_at: new Date()
});
print('Session token: ' + sessionToken);
print('User ID: ' + userId);
"
```

## Step 2: Test Backend API
```bash
# Test auth endpoint
curl -X GET "$API_URL/api/auth/me" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"

# Test protected review endpoint (should work with auth)
curl -X POST "$API_URL/api/recipes/spaghetti-alla-carbonara-italy/review" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -d '{"rating": 5, "comment": "Delicious!"}'

# Test protected review endpoint (should fail without auth)
curl -X POST "$API_URL/api/recipes/spaghetti-alla-carbonara-italy/review" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "comment": "Delicious!"}'
```

## Step 3: Browser Testing
```python
# Set cookie and navigate
await page.context.add_cookies([{
    "name": "session_token",
    "value": "YOUR_SESSION_TOKEN",
    "domain": "localhost",
    "path": "/",
    "httpOnly": True,
    "secure": False,
    "sameSite": "Lax"
}])
await page.goto("http://localhost:3000/en/recipe/spaghetti-alla-carbonara-italy")
```

## Quick Debug
```bash
# Check data format
mongosh --eval "
use('sous_chef_linguini_db');
db.users.find().limit(2).pretty();
db.user_sessions.find().limit(2).pretty();
db.recipe_reviews.find().limit(2).pretty();
"

# Clean test data
mongosh --eval "
use('sous_chef_linguini_db');
db.users.deleteMany({email: /test\.user\./});
db.user_sessions.deleteMany({session_token: /test_session/});
"
```

## Checklist
- [ ] User document has user_id field (custom UUID, MongoDB's _id is separate)
- [ ] Session user_id matches user's user_id exactly
- [ ] All queries use `{"_id": 0}` projection to exclude MongoDB's _id
- [ ] Backend queries use user_id (not _id or id)
- [ ] API returns user data with user_id field (not 401/404)
- [ ] Browser loads dashboard (not login page)
- [ ] Review form shows for logged-in users
- [ ] Review form hidden for logged-out users (shows login prompt)
- [ ] One review per user per recipe enforced
- [ ] User can update their own review
- [ ] User can delete their own review

## Success Indicators
✅ /api/auth/me returns user data
✅ Review form visible when logged in
✅ "Login to review" message when logged out
✅ CRUD operations work for reviews

## Failure Indicators
❌ "User not found" errors
❌ 401 Unauthorized responses
❌ Review form visible when logged out
❌ Multiple reviews per user per recipe
