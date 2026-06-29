import os
import time
import hmac
import hashlib
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict

# Thử import các thư viện bên ngoài, nếu không có sẽ tự viết fallback bằng standard library
try:
    import jwt
    HAS_JWT = True
except ImportError:
    HAS_JWT = False

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

# Load cấu hình
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "rag_lawyer_secret_key_default_2026")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "5"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "1"))


class SecurityHelper:
    """
    SecurityHelper hỗ trợ băm mật khẩu và quản lý JWT.
    Có cơ chế tự động fallback sang Python stdlib nếu thiếu thư viện ngoài.
    """
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Băm mật khẩu sử dụng bcrypt nếu có, ngược lại fallback sang PBKDF2.
        """
        if HAS_BCRYPT:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        else:
            # Fallback dùng PBKDF2 SHA256 an toàn tích hợp sẵn trong python stdlib
            salt = os.urandom(16)
            salt_hex = salt.hex()
            # Băm với 100,000 vòng lặp
            db_hash = hashlib.pbkdf2_hmac(
                "sha256", 
                password.encode("utf-8"), 
                salt, 
                100000
            )
            return f"pbkdf2_sha256$100000${salt_hex}${db_hash.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Xác minh mật khẩu khớp với mật khẩu đã băm.
        """
        if not hashed_password:
            return False
            
        if HAS_BCRYPT and not hashed_password.startswith("pbkdf2_sha256$"):
            try:
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"), 
                    hashed_password.encode("utf-8")
                )
            except Exception:
                # Nếu có lỗi định dạng, thử fallback sang pbkdf2
                pass
                
        # Xác minh dạng pbkdf2
        if hashed_password.startswith("pbkdf2_sha256$"):
            try:
                parts = hashed_password.split("$")
                if len(parts) != 4:
                    return False
                _, iterations_str, salt_hex, hash_hex = parts
                iterations = int(iterations_str)
                salt = bytes.fromhex(salt_hex)
                current_hash = hashlib.pbkdf2_hmac(
                    "sha256", 
                    plain_password.encode("utf-8"), 
                    salt, 
                    iterations
                )
                return hmac.compare_digest(current_hash.hex(), hash_hex)
            except Exception:
                return False
                
        return False

    @classmethod
    def _base64url_encode(cls, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    @classmethod
    def _base64url_decode(cls, data: str) -> bytes:
        padding = "=" * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode(data + padding)

    @classmethod
    def create_token(
        cls, 
        data: Dict[str, Any], 
        expires_delta: timedelta,
        token_type: str = "access"
    ) -> str:
        """
        Tạo JWT token (Access hoặc Refresh).
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({
            "exp": int(expire.timestamp()),
            "type": token_type,
            "iat": int(datetime.now(timezone.utc).timestamp())
        })
        
        if HAS_JWT:
            return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        else:
            # Tự build JWT thủ công bằng stdlib (HMAC + SHA256)
            header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
            
            header_b64 = cls._base64url_encode(json.dumps(header).encode("utf-8"))
            payload_b64 = cls._base64url_encode(json.dumps(to_encode).encode("utf-8"))
            
            signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            
            # Chọn hash algorithm
            digestmod = hashlib.sha256
            if JWT_ALGORITHM == "HS384":
                digestmod = hashlib.sha384
            elif JWT_ALGORITHM == "HS512":
                digestmod = hashlib.sha512
                
            signature = hmac.new(
                JWT_SECRET_KEY.encode("utf-8"), 
                signature_input, 
                digestmod
            ).digest()
            signature_b64 = cls._base64url_encode(signature)
            
            return f"{header_b64}.{payload_b64}.{signature_b64}"

    @classmethod
    def create_access_token(cls, data: Dict[str, Any]) -> str:
        """
        Tạo Access Token có hiệu lực 5 phút.
        """
        return cls.create_token(
            data, 
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), 
            "access"
        )

    @classmethod
    def create_refresh_token(cls, data: Dict[str, Any]) -> str:
        """
        Tạo Refresh Token có hiệu lực 1 ngày.
        """
        return cls.create_token(
            data, 
            timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), 
            "refresh"
        )

    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """
        Giải mã và xác minh tính hợp lệ của JWT token.
        Ném ValueError nếu token không hợp lệ hoặc hết hạn.
        """
        if HAS_JWT:
            try:
                return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            except jwt.ExpiredSignatureError:
                raise ValueError("TOKEN_EXPIRED")
            except jwt.InvalidTokenError:
                raise ValueError("TOKEN_INVALID")
        else:
            # Xác thực JWT thủ công
            try:
                parts = token.split(".")
                if len(parts) != 3:
                    raise ValueError("TOKEN_INVALID")
                
                header_b64, payload_b64, signature_b64 = parts
                
                # Tính toán lại chữ ký để verify
                signature_input = f"{header_b64}.{payload_b64}".encode("utf-8")
                
                digestmod = hashlib.sha256
                if JWT_ALGORITHM == "HS384":
                    digestmod = hashlib.sha384
                elif JWT_ALGORITHM == "HS512":
                    digestmod = hashlib.sha512
                    
                expected_signature = hmac.new(
                    JWT_SECRET_KEY.encode("utf-8"), 
                    signature_input, 
                    digestmod
                ).digest()
                expected_signature_b64 = cls._base64url_encode(expected_signature)
                
                if not hmac.compare_digest(signature_b64, expected_signature_b64):
                    raise ValueError("TOKEN_INVALID")
                
                # Giải mã payload
                payload_json = cls._base64url_decode(payload_b64).decode("utf-8")
                payload = json.loads(payload_json)
                
                # Check expiration
                exp = payload.get("exp")
                if exp is None:
                    raise ValueError("TOKEN_INVALID")
                
                if int(time.time()) > exp:
                    raise ValueError("TOKEN_EXPIRED")
                    
                return payload
            except ValueError as e:
                raise e
            except Exception:
                raise ValueError("TOKEN_INVALID")
