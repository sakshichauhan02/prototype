import sys
import os
import base64

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend folder is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.memory_service import memory_service

def test_encryption_upgrade():
    print("=== Testing Memory Encryption Upgrade to AES-256-GCM ===")
    
    test_fact = "My favorite food is sushi and I love hiking."
    print(f"\nOriginal Fact: '{test_fact}'")
    
    # 1. Test Encryption
    encrypted = memory_service.encrypt_fact(test_fact)
    print(f"Encrypted Fact string: {encrypted}")
    
    if encrypted.startswith("aeth_aes:"):
        print("✅ Success: Fact encrypted with new cryptographic prefix 'aeth_aes:'.")
    else:
        print("❌ Failure: Fact does not have the 'aeth_aes:' prefix.")
        return
        
    # 2. Test Decryption
    decrypted = memory_service.decrypt_fact(encrypted)
    print(f"Decrypted Fact: '{decrypted}'")
    
    if decrypted == test_fact:
        print("✅ Success: Decryption recovered the exact original fact.")
    else:
        print("❌ Failure: Decrypted fact does not match the original.")
        return
        
    # 3. Test Backward Compatibility
    # "My favorite food is sushi and I love hiking." in Base64:
    # "TXkgZmF2b3JpdGUgZm9vZCBpcyBzdXNoaSBhbmQgSSBsb3ZlIGhpa2luZy4="
    legacy_obfuscated = "aeth_enc:TXkgZmF2b3JpdGUgZm9vZCBpcyBzdXNoaSBhbmQgSSBsb3ZlIGhpa2luZy4="
    print(f"\nLegacy Fact format: '{legacy_obfuscated}'")
    legacy_decrypted = memory_service.decrypt_fact(legacy_obfuscated)
    print(f"Decrypted Legacy Fact: '{legacy_decrypted}'")
    
    if legacy_decrypted == test_fact:
        print("✅ Success: Backward compatibility verified. Old base64 obfuscated values decrypt correctly.")
    else:
        print("❌ Failure: Backward compatibility failed to decrypt old entries.")
        return
        
    # 4. Test Tamper Resistance (GCM Integrity Checking)
    print("\nTesting Tamper Resistance...")
    # Change a character in the ciphertext to simulate data tampering
    payload_part = encrypted.split("aeth_aes:")[1]
    raw_payload = list(base64.b64decode(payload_part))
    
    # Flip a bit in the ciphertext part (which is after IV (12) + Tag (16) = 28 bytes)
    if len(raw_payload) > 30:
        raw_payload[29] ^= 0x01
        tampered_payload_str = base64.b64encode(bytes(raw_payload)).decode("utf-8")
        tampered_encrypted = f"aeth_aes:{tampered_payload_str}"
        
        tampered_decrypted = memory_service.decrypt_fact(tampered_encrypted)
        if tampered_decrypted == tampered_encrypted:
            print("✅ Success: AES-256-GCM authentication caught the tampered ciphertext and gracefully fell back without crashing.")
        else:
            print(f"❌ Failure: Decryption succeeded or did not handle GCM authentication error correctly. Got: '{tampered_decrypted}'")
    else:
        print("⚠️ Skipped tamper test due to short payload.")

if __name__ == "__main__":
    test_encryption_upgrade()
