"""Shared Supabase client instances."""
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SVC_KEY

# Anon client — used for auth (login, signup, password reset)
anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Service client — used for all DB reads/writes server-side (bypasses RLS)
svc_client = create_client(SUPABASE_URL, SUPABASE_SVC_KEY)
