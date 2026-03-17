import re

with open('src/memento/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Match the fields in RelationshipProperties
pattern = r'\s*# Bi-temporal tracking fields.*?\n\s*valid_from.*?valid_from\)\s*valid_until.*?valid_until\)\s*recorded_at.*?recorded_at\)\s*invalidated_by.*?invalidated_by\)'
# Because the fields might be defined differently, I'll use a broader regex or specific lines.
