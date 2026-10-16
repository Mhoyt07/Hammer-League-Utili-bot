
import firebase_store as fb
fb.put("test", {"hello": "world"})
print(fb.get("test"))