import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pymongo.errors import DuplicateKeyError

from app.storage.mongodb import MongoDBManager
from app.core.security import SecurityHelper
from app.core.error_code import ErrorCode
from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse


class UserService:
    """
    UserService quản lý tạo user, xác thực, đăng nhập, đăng ký.
    Áp dụng Singleton Pattern và tương tác với MongoDB.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Đảm bảo quá trình khởi tạo database collection chỉ chạy một lần duy nhất
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._init_db()

    def _init_db(self):
        """
        Khởi tạo kết nối đến MongoDB và tạo các index unique cho user.
        """
        try:
            self.mongo_manager = MongoDBManager()
            self.client = self.mongo_manager.get_client()
            db_name = os.getenv("MONGODB_DB_NAME", "rag_lawyer")
            self.db = self.client[db_name]
            self.collection = self.db["users"]
            
            # Tạo unique index trên username, email và id
            self.collection.create_index("id", unique=True)
            self.collection.create_index("username", unique=True)
            self.collection.create_index("email", unique=True)
        except Exception as e:
            # Chống lỗi: Ghi log hoặc ném ngoại lệ khi không kết nối được database
            raise RuntimeError(f"UserService failed to initialize MongoDB connection: {str(e)}") from e

    def register(self, user_data: UserRegister) -> UserResponse:
        """
        Đăng ký tài khoản người dùng mới.
        """
        try:
            username_lower = user_data.username.lower()
            email_lower = user_data.email.lower()
            
            # Kiểm tra xem tên đăng nhập hoặc email đã được sử dụng chưa
            existing_user = self.collection.find_one({
                "$or": [
                    {"username": username_lower},
                    {"email": email_lower}
                ]
            })
            
            if existing_user:
                raise ValueError(ErrorCode.USER_ALREADY_EXISTS.value)
            
            # Mã hóa mật khẩu
            hashed_password = SecurityHelper.get_password_hash(str(user_data.password))
            
            # Tạo bản ghi người dùng mới
            user_id = uuid.uuid4().hex
            new_user = {
                "id": user_id,
                "username": username_lower,
                "email": email_lower,
                "hashed_password": hashed_password,
                "created_at": datetime.now(timezone.utc)
            }
            
            # Lưu vào MongoDB
            self.collection.insert_one(new_user)
            
            return UserResponse(
                id=new_user["id"],
                username=new_user["username"],
                email=new_user["email"],
                created_at=new_user["created_at"]
            )
            
        except DuplicateKeyError:
            raise ValueError(ErrorCode.USER_ALREADY_EXISTS.value)
        except ValueError as e:
            # Re-raise value error từ các nghiệp vụ logic
            raise e
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi đăng ký người dùng: {str(e)}") from e

    def login(self, login_data: UserLogin) -> TokenResponse:
        """
        Đăng nhập người dùng bằng email hoặc username.
        """
        try:
            identity_lower = login_data.identity.lower()
            
            # Tìm kiếm người dùng dựa trên email hoặc username
            user = self.collection.find_one({
                "$or": [
                    {"username": identity_lower},
                    {"email": identity_lower}
                ]
            })
            
            if not user:
                raise ValueError(ErrorCode.INVALID_CREDENTIALS.value)
            
            # Xác minh mật khẩu
            is_valid = SecurityHelper.verify_password(
                login_data.password, 
                user["hashed_password"]
            )
            if not is_valid:
                raise ValueError(ErrorCode.INVALID_CREDENTIALS.value)
            
            # Tạo JWT Access và Refresh Token
            # Payload chứa id người dùng
            token_payload = {
                "sub": user["id"],
                "username": user["username"],
                "email": user["email"]
            }
            
            access_token = SecurityHelper.create_access_token(token_payload)
            refresh_token = SecurityHelper.create_refresh_token(token_payload)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi đăng nhập: {str(e)}") from e

    def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """
        Lấy thông tin người dùng dựa trên user_id.
        """
        try:
            user = self.collection.find_one({"id": user_id})
            if not user:
                return None
                
            return UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                created_at=user["created_at"]
            )
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi lấy thông tin người dùng: {str(e)}") from e
            
    def get_user_by_token(self, token: str) -> Optional[UserResponse]:
        """
        Giải mã JWT token và lấy thông tin người dùng.
        """
        try:
            # decode_token tự ném ValueError (TOKEN_INVALID hoặc TOKEN_EXPIRED)
            payload = SecurityHelper.decode_token(token)
            
            # Check token type
            if payload.get("type") != "access":
                raise ValueError(ErrorCode.TOKEN_INVALID.value)
                
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError(ErrorCode.TOKEN_INVALID.value)
                
            return self.get_user_by_id(user_id)
        except ValueError as e:
            raise e
        except Exception:
            raise ValueError(ErrorCode.TOKEN_INVALID.value)

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Giải mã refresh token, kiểm tra tính hợp lệ và trả về access token mới.
        """
        try:
            # decode_token tự ném ValueError (TOKEN_INVALID hoặc TOKEN_EXPIRED)
            payload = SecurityHelper.decode_token(refresh_token)
            
            # Check token type
            if payload.get("type") != "refresh":
                raise ValueError(ErrorCode.TOKEN_INVALID.value)
                
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError(ErrorCode.TOKEN_INVALID.value)
                
            # Kiểm tra xem user có tồn tại không
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValueError(ErrorCode.TOKEN_INVALID.value)
                
            # Tạo payload mới cho access token
            token_payload = {
                "sub": user.id,
                "username": user.username,
                "email": user.email
            }
            
            access_token = SecurityHelper.create_access_token(token_payload)
            new_refresh_token = SecurityHelper.create_refresh_token(token_payload)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer"
            )
        except ValueError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"Lỗi hệ thống khi refresh token: {str(e)}") from e
