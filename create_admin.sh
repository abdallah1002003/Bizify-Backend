#!/bin/bash
echo "ALLOW_ADMIN_BOOTSTRAP=true" >> .env
echo "ADMIN_BOOTSTRAP_TOKEN=my-super-secret-token" >> .env

echo "✅ Environment configured for Admin Bootstrap..."
echo "Sending request to create the admin account..."

# Make the request to create the admin account
# Make sure the server is running on port 8001
curl -X POST "http://127.0.0.1:8001/api/v1/auth/bootstrap-admin" \
     -H "Content-Type: application/json" \
     -H "X-Bootstrap-Token: my-super-secret-token" \
     -d '{
           "name": "Super Admin",
           "email": "admin@example.com",
           "password": "SecurePassword123"
         }'

echo -e "\n\n✅ Request sent successfully."

# Disable bootstrap in env
sed -i '' '/ALLOW_ADMIN_BOOTSTRAP=true/d' .env
sed -i '' '/ADMIN_BOOTSTRAP_TOKEN=my-super-secret-token/d' .env
echo "ALLOW_ADMIN_BOOTSTRAP=false" >> .env

echo "🔒 System secured. Admin Bootstrap disabled."
