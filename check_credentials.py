#!/usr/bin/env python3
"""Check credentials format."""

import os
from dotenv import load_dotenv

load_dotenv()

access_id = os.getenv('SUMO_ACCESS_ID')
access_key = os.getenv('SUMO_ACCESS_KEY')

print(f'Access ID: "{access_id}"')
print(f'Access ID length: {len(access_id)}')
print(f'Access Key: "{access_key[:10]}...{access_key[-10:]}"')
print(f'Access Key length: {len(access_key)}')

# Check for whitespace
if access_id != access_id.strip():
    print('⚠️ Access ID has leading/trailing whitespace')
else:
    print('✅ Access ID format looks good')

if access_key != access_key.strip():
    print('⚠️ Access Key has leading/trailing whitespace')  
else:
    print('✅ Access Key format looks good')

# Check for non-printable characters
if any(ord(c) < 32 or ord(c) > 126 for c in access_id):
    print('⚠️ Access ID contains non-printable characters')
    
if any(ord(c) < 32 or ord(c) > 126 for c in access_key):
    print('⚠️ Access Key contains non-printable characters')