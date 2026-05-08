import os

# Конфигурация бота
TOKEN = os.getenv("TOKEN", "8612001103:AAEZs0KLDzIot0ebn16wQA5Fp-9JqORyCLM")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "1460226868,856763259").split(",")]

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://gvhwuewphctsvailghpw.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2aHd1ZXdwaGN0c3ZhaWxnaHB3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgyNTc4MDUsImV4cCI6MjA5MzgzMzgwNX0.403Evq0O0FuOIgJYJDb-EeYPVmw78AfBMgW2JoXkvAg")
