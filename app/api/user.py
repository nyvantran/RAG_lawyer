from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, TokenRefreshRequest
from app.service.user import UserService
from app.core.error_code import ErrorCode
from app.core.exceptions import AppException

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


def get_user_service() -> UserService:
    """
    Dependency cung cấp instance Singleton của UserService.
    """
    return UserService()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """
    Dependency lấy thông tin người dùng hiện tại từ JWT token.
    Ném AppException 401 nếu token không hợp lệ hoặc hết hạn.
    """
    token = credentials.credentials
    try:
        user = service.get_user_by_token(token)
        if not user:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code=ErrorCode.TOKEN_INVALID,
                message="Tài khoản không tồn tại"
            )
        return user
    except ValueError as e:
        error_code_val = e.args[0]
        
        # Ánh xạ mã lỗi để trả về thông điệp dễ hiểu
        message = "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại" if error_code_val == ErrorCode.TOKEN_EXPIRED.value else "Token xác thực không hợp lệ"
        
        # Chuyển đổi chuỗi thành Enum tương ứng
        try:
            err_enum = ErrorCode(error_code_val)
        except ValueError:
            err_enum = ErrorCode.TOKEN_INVALID
            
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=err_enum,
            message=message
        )
    except AppException as e:
        raise e
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi xác thực hệ thống: {str(e)}"
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister, 
    service: UserService = Depends(get_user_service)
):
    """
    Đăng ký tài khoản người dùng mới.
    """
    try:
        user = service.register(user_data)
        return {
            "success": True,
            "data": user,
            "message": "Đăng ký tài khoản thành công"
        }
    except ValueError as e:
        error_code_val = e.args[0]
        message = "Tên đăng nhập hoặc email đã tồn tại" if error_code_val == ErrorCode.USER_ALREADY_EXISTS.value else str(e)
        
        try:
            err_enum = ErrorCode(error_code_val)
        except ValueError:
            err_enum = ErrorCode.USER_ALREADY_EXISTS
            
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=err_enum,
            message=message
        )
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi đăng ký hệ thống: {str(e)}"
        )


@router.post("/login")
def login(
    login_data: UserLogin, 
    service: UserService = Depends(get_user_service)
):
    """
    Đăng nhập tài khoản bằng email hoặc username.
    Trả về access token và refresh token.
    """
    try:
        tokens = service.login(login_data)
        return {
            "success": True,
            "data": tokens,
            "message": "Đăng nhập thành công"
        }
    except ValueError as e:
        error_code_val = e.args[0]
        message = "Tên đăng nhập hoặc mật khẩu không chính xác" if error_code_val == ErrorCode.INVALID_CREDENTIALS.value else str(e)
        
        try:
            err_enum = ErrorCode(error_code_val)
        except ValueError:
            err_enum = ErrorCode.INVALID_CREDENTIALS
            
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=err_enum,
            message=message
        )
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi đăng nhập hệ thống: {str(e)}"
        )


@router.get("/me", response_model=None)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Lấy thông tin tài khoản hiện đang đăng nhập thông qua Bearer Token.
    """
    return {
        "success": True,
        "data": current_user,
        "message": "Lấy thông tin tài khoản thành công"
    }


@router.post("/refresh")
def refresh_token(
    refresh_data: TokenRefreshRequest,
    service: UserService = Depends(get_user_service)
):
    """
    Refresh access token từ refresh token hợp lệ.
    """
    try:
        tokens = service.refresh_token(refresh_data.refresh_token)
        return {
            "success": True,
            "data": tokens,
            "message": "Làm mới token thành công"
        }
    except ValueError as e:
        error_code_val = e.args[0]
        message = "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại" if error_code_val == ErrorCode.TOKEN_EXPIRED.value else "Token xác thực không hợp lệ"
        
        try:
            err_enum = ErrorCode(error_code_val)
        except ValueError:
            err_enum = ErrorCode.TOKEN_INVALID
            
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=err_enum,
            message=message
        )
    except Exception as e:
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"Lỗi refresh token hệ thống: {str(e)}"
        )
